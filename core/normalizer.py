# core/normalizer.py
import pandas as pd
import unicodedata
import re

# Mapa de meses (español + inglés, abreviado y largo) -> abreviación canónica EN.
# La salida siempre se escribe en MAYÚSCULAS (JAN, FEB, ...).
_MONTH_MAP = {
    # Español
    "ENE": "JAN", "ENERO": "JAN",
    "FEB": "FEB", "FEBRERO": "FEB",
    "MAR": "MAR", "MARZO": "MAR",
    "ABR": "APR", "ABRIL": "APR",
    "MAY": "MAY", "MAYO": "MAY",
    "JUN": "JUN", "JUNIO": "JUN",
    "JUL": "JUL", "JULIO": "JUL",
    "AGO": "AUG", "AGOSTO": "AUG",
    "SEP": "SEP", "SEPT": "SEP", "SEPTIEMBRE": "SEP",
    "OCT": "OCT", "OCTUBRE": "OCT",
    "NOV": "NOV", "NOVIEMBRE": "NOV",
    "DIC": "DEC", "DICIEMBRE": "DEC",
    # Inglés
    "JAN": "JAN", "JANUARY": "JAN",
    "FEBRUARY": "FEB",
    "MARCH": "MAR",
    "APR": "APR", "APRIL": "APR",
    "JUNE": "JUN",
    "JULY": "JUL",
    "AUG": "AUG", "AUGUST": "AUG",
    "SEPTEMBER": "SEP",
    "OCTOBER": "OCT",
    "NOVEMBER": "NOV",
    "DEC": "DEC", "DECEMBER": "DEC",
}

# Orden canónico de meses (se usa también en mapper/exporter).
MONTH_ORDER = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]


class Normalizer:
    @staticmethod
    def standardize_text(text) -> str:
        """
        Normaliza texto para comparaciones:
        - Quita espacios al inicio/final
        - Todo a MAYÚSCULAS
        - Elimina acentos/tildes
        - Colapsa espacios múltiples
        """
        if pd.isna(text) or text is None:
            return ""
        text = str(text).strip().upper()
        # Eliminar tildes/acentos
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        # Colapsar espacios múltiples
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def parse_month(value) -> str:
        """
        Convierte un valor cualquiera de la columna MONTH del DB a la
        abreviación canónica en inglés y MAYÚSCULAS: JAN, FEB, ..., DEC.

        Soporta:
        - Número int/float 1-12        -> mes correspondiente
        - Strings tipo '01', '1', '12' -> mes correspondiente
        - Nombres ES/EN largos o cortos: 'enero', 'ENE', 'January', 'jan-24', etc.
        - Fechas completas: '2024-03-15', datetime, Timestamp, '15/03/2024'

        Devuelve "" si no se puede interpretar.
        """
        if pd.isna(value) or value is None:
            return ""

        # Caso 1: ya es un datetime/Timestamp
        if isinstance(value, (pd.Timestamp,)):
            return MONTH_ORDER[value.month - 1]

        # Caso 2: numérico 1-12
        try:
            n = int(float(value))
            if 1 <= n <= 12:
                return MONTH_ORDER[n - 1]
        except (ValueError, TypeError):
            pass

        # Caso 3: texto -> intentar como fecha completa
        text = str(value).strip()
        if not text:
            return ""

        dt = pd.to_datetime(text, errors="coerce", dayfirst=True)
        if pd.notnull(dt):
            return MONTH_ORDER[dt.month - 1]

        # Caso 4: texto -> nombre de mes (es/en)
        norm = Normalizer.standardize_text(text)
        # Si viene como 'ENE-24', 'JAN/2024', etc., extraer la parte de mes
        m = re.match(r"([A-Z]+)", norm)
        if m:
            token = m.group(1)
            if token in _MONTH_MAP:
                return _MONTH_MAP[token]

        return ""

    @staticmethod
    def format_excel_date(val):
        """Asegura que las fechas sean objetos datetime (helper legacy)."""
        if isinstance(val, pd.Timestamp):
            return val
        try:
            return pd.to_datetime(val)
        except Exception:
            return val