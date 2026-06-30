# models/config.py
from dataclasses import dataclass

@dataclass
class Config:
    """
    Configuración seleccionada por el usuario en la UI.
    - country: nombre de la hoja del Dictionary a usar (ej. 'COLOMBIA').
    - year: año que se escribirá en la columna YEAR del archivo de salida.
    """
    country: str
    year: int