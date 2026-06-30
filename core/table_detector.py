# core/table_detector.py
import pandas as pd
import numpy as np


class TableDetector:
    """
    Detecta la fila de encabezados de una hoja del DB RUNT.

    Algoritmo:
      Recorre las primeras 50 filas y asigna a cada una un SCORE basado en
      múltiples señales (no solo keywords). Elige la fila con mayor score.

      Score por fila:
        + 10  por cada celda cuyo VALOR EXACTO sea una keyword conocida
        +  3  por cada celda que CONTIENE una keyword (subcadena)
        +  2  por cada celda no nula adicional (más allá del mínimo)
        +  5  si la densidad de strings (no fechas/números) es alta
        -  5  si la siguiente fila parece otro header (descarta titulares)
        -  3  por cada celda que parece dato numérico (no texto)
        - 20  si la fila tiene menos de 3 celdas no nulas (descartada)

      Esto evita el bug típico del RUNT donde un título arriba
      ('REPORTE DE MATRICULAS POR MARCA Y MODELO') hace match falso.
    """

    # Keywords EXACTAS — valores que típicamente aparecen SOLOS en una celda
    # de encabezado del RUNT (case-insensitive, sin acentos).
    EXACT_KEYWORDS = {
        # Brand
        "MARCA", "MARCA HOMOLOGADA", "BRAND",
        # Model
        "LINEA", "MODELO", "MODEL", "VERSION",
        # Month / Date
        "MES", "FECHA", "PERIODO", "MONTH", "FECHA REGISTRO",
        "FECHA DE REGISTRO", "FECHA MATRICULA",
        # Year
        "ANIO", "ANO", "AÑO", "YEAR",
        # Class / Segment
        "CLASE", "TIPO", "CARROCERIA", "SEGMENTO", "SEGMENT",
        "NAMEPLATE",
        # Value
        "CANTIDAD", "UNIDAD", "UNIDADES", "REGISTRO", "REGISTROS",
        "QTY", "QUANTITY",
        # Other common RUNT columns
        "COLOR", "COMBUSTIBLE", "CILINDRAJE", "MODELO ANIO",
        "MODELO AÑO", "PLACA", "DEPARTAMENTO", "MUNICIPIO",
    }

    # Keywords que pueden aparecer como SUBCADENA en headers más largos
    # (peso menor que las exactas).
    SUBSTRING_KEYWORDS = [
        "MARCA", "BRAND",
        "LINEA", "MODEL", "VERSION",
        "MES", "FECHA", "PERIODO", "MONTH",
        "CANTIDAD", "UNIDAD", "REGISTRO", "TOTAL", "QTY",
        "ANIO", "AÑO", "YEAR",
        "CLASE", "SEGMENTO", "SEGMENT", "NAMEPLATE",
    ]

    @staticmethod
    def _normalize(text) -> str:
        """Mayúsculas + sin acentos + sin espacios extra."""
        import unicodedata
        if pd.isna(text) or text is None:
            return ""
        s = str(text).strip().upper()
        s = "".join(
            c for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )
        return " ".join(s.split())  # colapsar espacios

    @staticmethod
    def _score_row(row: pd.Series) -> tuple[int, dict]:
        """Calcula el score de una fila y devuelve (score, debug_info)."""
        non_null = [v for v in row.values if pd.notna(v) and str(v).strip() != ""]
        n = len(non_null)

        # Filas con menos de 3 celdas no nulas no pueden ser un header válido
        if n < 3:
            return -100, {"reason": "too few non-null cells", "n": n}

        normalized = [TableDetector._normalize(v) for v in non_null]

        score = 0
        exact_matches = 0
        substring_matches = 0
        numeric_count = 0

        for val in normalized:
            # Match exacto (valor completo == keyword) - peso alto
            if val in TableDetector.EXACT_KEYWORDS:
                score += 10
                exact_matches += 1
                continue

            # Match por subcadena - peso medio
            matched_sub = False
            for kw in TableDetector.SUBSTRING_KEYWORDS:
                if kw in val and len(val) <= 40:  # evita matchear títulos largos
                    score += 3
                    substring_matches += 1
                    matched_sub = True
                    break
            if matched_sub:
                continue

            # Penalización si parece dato numérico puro (probable fila de datos)
            try:
                float(val.replace(",", "."))
                numeric_count += 1
                score -= 3
            except ValueError:
                pass

        # Bonus por densidad / cantidad de columnas
        score += min(n, 15) * 2   # cap para no premiar filas con cientos de cols
        if n >= 4:
            score += 5

        # Si todas las celdas son strings (no numéricas), bonus
        if numeric_count == 0 and n >= 3:
            score += 5

        return score, {
            "n_cells": n,
            "exact_matches": exact_matches,
            "substring_matches": substring_matches,
            "numeric_count": numeric_count,
        }

    @staticmethod
    def find_start_row(df: pd.DataFrame) -> int:
        """
        Devuelve el índice (0-based) de la fila de encabezado más probable.
        Si nada gana, devuelve 0.
        """
        search_limit = min(50, len(df))
        if search_limit == 0:
            return 0

        best_row = 0
        best_score = -10**9

        for i in range(search_limit):
            score, _ = TableDetector._score_row(df.iloc[i])
            # Empate -> nos quedamos con la PRIMERA (la más arriba)
            if score > best_score:
                best_score = score
                best_row = i

        # Si el mejor score es paupérrimo, fallback a fila 0
        if best_score <= 0:
            return 0
        return best_row

    @staticmethod
    def get_clean_table(df: pd.DataFrame, start_row: int) -> pd.DataFrame:
        """
        Asigna encabezado desde `start_row`, elimina esa fila y limpia
        errores típicos de Excel.

        - start_row debe ser 0-based.
        - Si start_row queda fuera de rango, lo clamp-ea a [0, len-1].
        """
        if df is None or df.empty:
            return pd.DataFrame()

        # Clamp defensivo (por si el SpinBox manda un valor fuera de rango)
        start_row = max(0, min(start_row, len(df) - 1))

        df_clean = df.iloc[start_row:].copy()
        df_clean.columns = df_clean.iloc[0]
        df_clean = df_clean.iloc[1:].reset_index(drop=True)

        df_clean = df_clean.replace(
            [np.inf, -np.inf, "#N/A", "#REF!", "#VALUE!", "#DIV/0!"],
            np.nan,
        )

        # Limpiar columnas con nombre NaN o vacío
        df_clean = df_clean.loc[:, df_clean.columns.notna()]
        df_clean.columns = [str(c).strip() for c in df_clean.columns]
        df_clean = df_clean.loc[:, [c != "" and c.lower() != "nan"
                                    for c in df_clean.columns]]

        # Eliminar filas 100% vacías (típico al final de un export)
        df_clean = df_clean.dropna(how="all").reset_index(drop=True)

        return df_clean