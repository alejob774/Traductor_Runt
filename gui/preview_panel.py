# gui/preview_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QHeaderView, QGroupBox,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt

from models.mapping import Mapping

# Centinela usado en el combo opcional VALUE para indicar "ninguna columna".
NONE_VALUE_TOKEN = "(none)"


class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración general del layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        # --- SECCIÓN DE MAPEO DE COLUMNAS ---
        self.map_group = QGroupBox("COLUMN MAPPING")
        self.map_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 25px;
                background: #fdfdfd;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        map_h_layout = QHBoxLayout(self.map_group)

        # Inicialización de los desplegables (ComboBoxes)
        # NOTA: 3 obligatorios (Brand/Model/Month) + 1 opcional (Value).
        self.map_brand = QComboBox()
        self.map_model = QComboBox()
        self.map_month = QComboBox()
        self.map_value = QComboBox()  # opcional — si "(none)" se cuenta 1 por fila

        # Creación dinámica de etiquetas y layouts para los combos
        for label, combo in [
            ("Brand:",       self.map_brand),
            ("Model:",       self.map_model),
            ("Month:",       self.map_month),
            ("Value (opt.):", self.map_value),
        ]:
            v_box = QVBoxLayout()
            v_box.addWidget(QLabel(label))
            v_box.addWidget(combo)
            map_h_layout.addLayout(v_box)

        self.layout.addWidget(self.map_group)

        # --- SECCIÓN DE VISTA PREVIA (TABLA) ---
        self.preview_group = QGroupBox("DETECTED HEADER PREVIEW")
        self.preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 25px;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_group)

        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.table.setFixedHeight(80)
        self.table.verticalHeader().setVisible(False)
        # Solo lectura para el usuario
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        preview_layout.addWidget(self.table)
        self.layout.addWidget(self.preview_group)

    # ---------------------------------------------------------
    def fill_mapping_combos(self, columns):
        """
        Llena los combos con las columnas detectadas y realiza una búsqueda
        lineal para auto-seleccionar el valor por defecto basado en alias
        comunes del RUNT.

        Keywords RUNT:
          - Brand:  'marca', 'brand'
          - Model:  'linea', 'modelo', 'model'
          - Month:  'mes', 'fecha', 'periodo', 'month'
          - Value:  'cantidad', 'unidad', 'registro', 'total', 'qty'
                    (opcional — si no hay match queda en "(none)")
        """
        # Para los obligatorios: si encuentra keyword, lo selecciona;
        # si no, deja el primero.
        required_mappings = {
            self.map_brand:  ["marca", "brand"],
            self.map_model:  ["linea", "línea", "modelo", "model"],
            self.map_month:  ["mes", "fecha", "periodo", "período", "month"],
        }

        for combo, keywords in required_mappings.items():
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(columns)

            found_index = -1
            for i, col_name in enumerate(columns):
                col_lower = str(col_name).lower()
                if any(key in col_lower for key in keywords):
                    found_index = i
                    break

            if found_index != -1:
                combo.setCurrentIndex(found_index)
            else:
                combo.setCurrentIndex(0 if columns else -1)
            combo.blockSignals(False)

        # Para el opcional VALUE: prepend "(none)" y solo auto-seleccionar
        # si realmente hay un match con las keywords típicas.
        value_keywords = ["cantidad", "unidad", "unidades",
                          "registro", "registros", "total", "qty"]
        self.map_value.blockSignals(True)
        self.map_value.clear()
        self.map_value.addItem(NONE_VALUE_TOKEN)
        self.map_value.addItems(columns)

        match_idx = -1
        for i, col_name in enumerate(columns):
            col_lower = str(col_name).lower()
            if any(key in col_lower for key in value_keywords):
                match_idx = i + 1   # +1 porque "(none)" está en la posición 0
                break

        self.map_value.setCurrentIndex(match_idx if match_idx != -1 else 0)
        self.map_value.blockSignals(False)

    # ---------------------------------------------------------
    def display_headers(self, headers):
        """
        Muestra los nombres de las columnas en la tabla de vista previa.
        """
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(
            [f"Col {i+1}" for i in range(len(headers))]
        )
        for i, h in enumerate(headers):
            item = QTableWidgetItem(str(h))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(0, i, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    # ---------------------------------------------------------
    def get_mapping(self) -> Mapping:
        """
        Devuelve el objeto Mapping con la selección actual de columnas.
        Lanza ValueError si falta alguno de los campos obligatorios.
        """
        brand = self.map_brand.currentText().strip()
        model = self.map_model.currentText().strip()
        month = self.map_month.currentText().strip()
        value_raw = self.map_value.currentText().strip()

        if not brand or not model or not month:
            raise ValueError(
                "Please select a column for Brand, Model and Month."
            )

        value = None if value_raw in (NONE_VALUE_TOKEN, "") else value_raw

        return Mapping(
            brand_column=brand,
            model_column=model,
            month_column=month,
            value_column=value,
        )