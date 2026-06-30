# models/mapping.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Mapping:
    """
    Selección de columnas del archivo DB del RUNT que hace el usuario en la UI.
    - brand_column:  columna del DB que contiene la MARCA (ej. 'MARCA').
    - model_column:  columna del DB que contiene el MODELO (ej. 'LINEA').
    - month_column:  columna del DB que contiene el MES (número 1-12,
                     nombre 'ENERO'/'JAN', o fecha completa 'YYYY-MM-DD').
    - value_column:  (opcional) columna numérica con la cantidad a sumar.
                     Si es None, cada fila del DB cuenta como 1 registro.
    """
    brand_column: str
    model_column: str
    month_column: str
    value_column: Optional[str] = None
