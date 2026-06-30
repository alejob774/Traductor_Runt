# core/mapper.py
import pandas as pd
from core.normalizer import Normalizer, MONTH_ORDER


class Mapper:
    """
    Transformación principal:
      DB RUNT (BRAND, MODEL, MONTH [, VALUE])  --->  archivo de salida wide:
        COUNTRY, YEAR, BRAND, NAMEPLATE, SEGMENT, JAN..DEC

    Lookups usados:
      - dict_dfs[country]: BRAND RUNT, MODEL RUNT -> BRAND, NAMEPLATE (canónicos)
      - dict_dfs['SEGMENT']: NAMEPLATE -> SEGMENT
    """

    def __init__(self, config, mapping, dictionary_dfs):
        self.config = config
        self.mapping = mapping
        # Copia defensiva (no mutar el dict original)
        self.dict_dfs = {sheet: df.copy() for sheet, df in dictionary_dfs.items()}
        self.norm = Normalizer()

    # ---------------------------------------------------------
    # Construcción de lookups a partir del Dictionary
    # ---------------------------------------------------------
    def _build_lookups(self):
        country = self.config.country.upper()

        # Resolver nombre real de la hoja del país (case-insensitive)
        country_sheet = next(
            (k for k in self.dict_dfs if k.upper() == country),
            None,
        )
        segment_sheet = next(
            (k for k in self.dict_dfs if k.upper() == "SEGMENT"),
            None,
        )
        if country_sheet is None or segment_sheet is None:
            return None, None

        df_country = self.dict_dfs[country_sheet]
        df_segment = self.dict_dfs[segment_sheet]

        # Normalizar nombres de columnas del Dictionary
        df_country.columns = [str(c).strip().upper() for c in df_country.columns]
        df_segment.columns = [str(c).strip().upper() for c in df_segment.columns]

        # Lookup principal: (brand_norm, model_norm) -> {BRAND, NAMEPLATE}
        country_lookup = {}
        for _, row in df_country.iterrows():
            b_raw = row.get("BRAND RUNT")
            m_raw = row.get("MODEL RUNT")
            if pd.isna(b_raw) or pd.isna(m_raw):
                continue
            key = (
                self.norm.standardize_text(b_raw),
                self.norm.standardize_text(m_raw),
            )
            # En caso de duplicados, prevalece la primera definición
            if key not in country_lookup:
                country_lookup[key] = {
                    "BRAND":     str(row.get("BRAND", "")).strip().upper(),
                    "NAMEPLATE": str(row.get("NAMEPLATE", "")).strip().upper(),
                }

        # Lookup de segmento: NAMEPLATE (mayúsculas) -> SEGMENT
        segment_lookup = {
            str(row["NAMEPLATE"]).strip().upper():
                str(row.get("SEGMENT", "OTROS")).strip().upper()
            for _, row in df_segment.iterrows()
            if pd.notna(row.get("NAMEPLATE"))
        }

        return country_lookup, segment_lookup

    # ---------------------------------------------------------
    # Transformación principal
    # ---------------------------------------------------------
    def process_transformation(self, source_df: pd.DataFrame) -> pd.DataFrame:
        country_lookup, segment_lookup = self._build_lookups()
        if country_lookup is None:
            return pd.DataFrame()

        country = self.config.country.upper()
        year_str = str(int(self.config.year))

        # Filtrar filas con BRAND/MODEL presentes
        df = source_df.copy()
        df = df[
            df[self.mapping.brand_column].notna()
            & df[self.mapping.model_column].notna()
            & df[self.mapping.month_column].notna()
        ]
        if df.empty:
            return pd.DataFrame()

        # Excluir filas de tipo TOTAL/ALL
        b_str = df[self.mapping.brand_column].astype(str).str.upper()
        df = df[~b_str.str.contains("TOTAL|ALL", regex=True, na=False)]

        # ---------------------------------------------------------
        # Columnas auxiliares normalizadas
        # ---------------------------------------------------------
        df["_B_NORM"] = df[self.mapping.brand_column].apply(self.norm.standardize_text)
        df["_M_NORM"] = df[self.mapping.model_column].apply(self.norm.standardize_text)
        df["_MONTH"]  = df[self.mapping.month_column].apply(self.norm.parse_month)

        # VALUE: si no hay columna se cuenta 1 por fila
        if self.mapping.value_column:
            df["_VALUE"] = pd.to_numeric(
                df[self.mapping.value_column], errors="coerce"
            ).fillna(0.0)
        else:
            df["_VALUE"] = 1.0

        # Descartar filas sin lookup o sin mes válido
        df["_LOOKUP"] = list(zip(df["_B_NORM"], df["_M_NORM"]))
        df = df[df["_LOOKUP"].isin(country_lookup.keys())]
        df = df[df["_MONTH"] != ""]
        if df.empty:
            return pd.DataFrame()

        # Resolver BRAND / NAMEPLATE canónicos desde el lookup
        df["BRAND"]     = df["_LOOKUP"].map(lambda k: country_lookup[k]["BRAND"])
        df["NAMEPLATE"] = df["_LOOKUP"].map(lambda k: country_lookup[k]["NAMEPLATE"])
        df["SEGMENT"]   = df["NAMEPLATE"].map(
            lambda n: segment_lookup.get(n, "OTROS")
        )
        df["COUNTRY"]   = country
        df["YEAR"]      = year_str

        # ---------------------------------------------------------
        # Agregación: sumar VALUE por (COUNTRY, YEAR, BRAND, NAMEPLATE,
        # SEGMENT, MONTH) y pivotear MONTH a columnas.
        # ---------------------------------------------------------
        fixed_cols = ["COUNTRY", "YEAR", "BRAND", "NAMEPLATE", "SEGMENT"]

        grouped = (
            df.groupby(fixed_cols + ["_MONTH"], as_index=False)["_VALUE"]
              .sum()
        )

        pivoted = grouped.pivot_table(
            index=fixed_cols,
            columns="_MONTH",
            values="_VALUE",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        pivoted.columns.name = None

        # Garantizar las 12 columnas de mes, en orden
        for m in MONTH_ORDER:
            if m not in pivoted.columns:
                pivoted[m] = 0

        output_cols = fixed_cols + MONTH_ORDER
        return pivoted[output_cols]