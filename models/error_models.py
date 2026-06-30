# models/error_models.py
"""
Modelos de error usados por Validator para reportar incidencias.

Uso:
    errors = ErrorCollector()
    errors.add_error(
        country="COLOMBIA",
        row=42,
        column="BRAND",
        value="GENERAL MOTRS",
        message="Pair (BRAND, MODEL) not in Dictionary."
    )

    if errors.has_errors():
        df = errors.to_dataframe()
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List

import pandas as pd


@dataclass
class ValidationError:
    """
    Representa una sola incidencia detectada por el Validator.
    - country: hoja/país en el que ocurrió.
    - row:     número de fila del DB (1-based, incluyendo header).
               Usar 0 cuando el error es estructural (no de una fila concreta).
    - column:  nombre de la columna afectada o etiqueta lógica
               (ej. 'BRAND', 'BRAND+MODEL', 'DICTIONARY').
    - value:   valor original que causó el error (como string).
    - message: descripción legible del problema.
    """
    country: str
    row: int
    column: str
    value: str
    message: str


@dataclass
class ErrorCollector:
    """Acumula errores de validación y expone helpers para inspeccionarlos."""
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(
        self,
        country: str,
        row: int,
        column: str,
        value: str,
        message: str,
    ) -> None:
        self.errors.append(
            ValidationError(
                country=str(country),
                row=int(row),
                column=str(column),
                value=str(value),
                message=str(message),
            )
        )

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __len__(self) -> int:
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def to_dataframe(self) -> pd.DataFrame:
        """Convierte los errores a un DataFrame para mostrarlos en la UI."""
        if not self.errors:
            return pd.DataFrame(
                columns=["country", "row", "column", "value", "message"]
            )
        return pd.DataFrame([asdict(e) for e in self.errors])

    def clear(self) -> None:
        self.errors.clear()