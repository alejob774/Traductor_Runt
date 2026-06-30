# core/exporter.py
import pandas as pd
from core.normalizer import MONTH_ORDER


class Exporter:
    """
    Exporta el DataFrame final (wide) con orden fijo y tipos correctos:
      COUNTRY, YEAR, BRAND, NAMEPLATE, SEGMENT, JAN..DEC
    """

    FIXED_COLS = ["COUNTRY", "YEAR", "BRAND", "NAMEPLATE", "SEGMENT"]

    @staticmethod
    def save_to_excel(df: pd.DataFrame, output_path: str) -> bool:
        if df is None or df.empty:
            return False

        expected_columns = Exporter.FIXED_COLS + MONTH_ORDER

        # 1. Garantizar que existen los 12 meses
        for m in MONTH_ORDER:
            if m not in df.columns:
                df[m] = 0

        # 2. Reordenar columnas exactamente
        final_order = [c for c in expected_columns if c in df.columns]
        df = df[final_order].copy()

        # 3. Tipos: meses -> numérico, YEAR -> string limpio
        for m in MONTH_ORDER:
            if m in df.columns:
                df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0.0)
        if "YEAR" in df.columns:
            df["YEAR"] = (
                df["YEAR"].astype(str).str.replace(r"\.0$", "", regex=True)
            )

        # 4. Escribir con xlsxwriter y autoajustar columnas
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data_Normalized")
            workbook = writer.book
            worksheet = writer.sheets["Data_Normalized"]

            num_format  = workbook.add_format({"num_format": "#,##0"})
            text_format = workbook.add_format({"text_wrap": False})

            for i, col in enumerate(df.columns):
                col_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                if col in MONTH_ORDER:
                    worksheet.set_column(i, i, col_len, num_format)
                else:
                    worksheet.set_column(i, i, col_len, text_format)

        return True