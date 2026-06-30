# core/validator.py
import pandas as pd
from models.error_models import ErrorCollector
from core.normalizer import Normalizer


class Validator:
    """
    Valida el DB del RUNT contra el Dictionary:
      - La hoja del país debe existir.
      - Cada (BRAND RUNT, MODEL RUNT) del DB debe existir en el diccionario.
      - El valor de MONTH debe ser parseable a 1-12.
      - Si se indicó VALUE_COLUMN, debe ser numérica.
    """

    REQUIRED_DICT_COLS = ["BRAND RUNT", "MODEL RUNT", "BRAND", "NAMEPLATE"]

    def __init__(self, config, mapping, dictionary_dfs):
        self.config = config
        self.mapping = mapping
        # Copia defensiva
        self.dict_dfs = {sheet: df.copy() for sheet, df in dictionary_dfs.items()}
        self.errors = ErrorCollector()
        self.norm = Normalizer()

    def _check_dictionary_structure(self) -> bool:
        country = self.config.country.upper()

        if country not in {k.upper() for k in self.dict_dfs.keys()}:
            self.errors.add_error(
                country, 0, "DICTIONARY", country,
                f"Country sheet '{country}' not found in Dictionary."
            )
            return False

        if "SEGMENT" not in {k.upper() for k in self.dict_dfs.keys()}:
            self.errors.add_error(
                country, 0, "DICTIONARY", "SEGMENT",
                "Sheet 'SEGMENT' not found in Dictionary."
            )
            return False

        # Resolver nombre real de hoja (case-insensitive)
        sheet_name = next(k for k in self.dict_dfs if k.upper() == country)
        df_country = self.dict_dfs[sheet_name]
        df_country.columns = [str(c).strip().upper() for c in df_country.columns]

        missing = [c for c in self.REQUIRED_DICT_COLS if c not in df_country.columns]
        if missing:
            self.errors.add_error(
                country, 0, "DICTIONARY", ",".join(missing),
                f"Country sheet is missing required columns: {missing}"
            )
            return False

        return True

    def validate_all(self, source_df: pd.DataFrame) -> ErrorCollector:
        if not self._check_dictionary_structure():
            return self.errors

        country = self.config.country.upper()
        sheet_name = next(k for k in self.dict_dfs if k.upper() == country)
        df_country = self.dict_dfs[sheet_name]

        # Set de pares válidos (brand_norm, model_norm)
        valid_pairs = set()
        for _, row in df_country.iterrows():
            b = self.norm.standardize_text(row.get("BRAND RUNT"))
            m = self.norm.standardize_text(row.get("MODEL RUNT"))
            if b and m:
                valid_pairs.add((b, m))

        # Validar columnas presentes en el DB
        for col_name, col_key in [
            (self.mapping.brand_column, "BRAND"),
            (self.mapping.model_column, "MODEL"),
            (self.mapping.month_column, "MONTH"),
        ]:
            if col_name not in source_df.columns:
                self.errors.add_error(
                    country, 0, col_key, col_name,
                    f"Column '{col_name}' not found in DB."
                )
        if self.mapping.value_column and self.mapping.value_column not in source_df.columns:
            self.errors.add_error(
                country, 0, "VALUE", self.mapping.value_column,
                f"Column '{self.mapping.value_column}' not found in DB."
            )

        # Si faltan columnas críticas, no seguimos validando filas
        if self.errors.has_errors():
            return self.errors

        # Validación fila a fila (capada para no inundar el reporte)
        MAX_ROW_ERRORS = 200
        row_err_count = 0

        for index, row in source_df.iterrows():
            if row_err_count >= MAX_ROW_ERRORS:
                break

            row_num = index + 2  # +2 = header + base-1 humano
            raw_brand = row.get(self.mapping.brand_column)
            raw_model = row.get(self.mapping.model_column)
            raw_month = row.get(self.mapping.month_column)

            # Saltar filas claramente vacías o de totales
            if pd.isna(raw_brand) or pd.isna(raw_model):
                continue
            if "TOTAL" in str(raw_brand).upper() or "ALL" in str(raw_brand).upper():
                continue

            b = self.norm.standardize_text(raw_brand)
            m = self.norm.standardize_text(raw_model)

            if (b, m) not in valid_pairs:
                self.errors.add_error(
                    country, row_num, "BRAND+MODEL",
                    f"{raw_brand} / {raw_model}",
                    f"Pair (BRAND='{raw_brand}', MODEL='{raw_model}') not in Dictionary."
                )
                row_err_count += 1
                continue

            # Validar mes parseable
            if not self.norm.parse_month(raw_month):
                self.errors.add_error(
                    country, row_num, self.mapping.month_column,
                    str(raw_month),
                    f"MONTH value '{raw_month}' is not a valid month (1-12, name, or date)."
                )
                row_err_count += 1
                continue

            # Validar VALUE si aplica
            if self.mapping.value_column:
                v = row.get(self.mapping.value_column)
                if pd.notna(v):
                    try:
                        float(v)
                    except (ValueError, TypeError):
                        self.errors.add_error(
                            country, row_num, self.mapping.value_column,
                            str(v),
                            f"VALUE '{v}' is not numeric."
                        )
                        row_err_count += 1

        return self.errors