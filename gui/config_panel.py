from PySide6.QtWidgets import ( QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QSpinBox, QGroupBox, )

class ConfigPanel(QWidget):

# ====================================================================
# CONSTRUCTOR — TODO el código de UI va DENTRO de este __init__
# ====================================================================
    def __init__(self):
        super().__init__()

    # ---- Layout principal --------------------------------------------
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(25)

    # ---- Estilos globales del panel ----------------------------------
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 25px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 8px;
                color: #2c3e50;
            }
            QLabel {
                color: #5a5e66;
                margin-top: 5px;
            }
            QComboBox, QLineEdit, QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 6px;
                min-height: 28px;
            }
        """)

    # ---- Construir los widgets ---------------------------------------
        self.init_ui()

# ====================================================================
# Helper: par (label arriba, widget abajo)
# ====================================================================
    def create_field(self, label_text, widget):
        container = QVBoxLayout()
        container.setSpacing(4)
        container.addWidget(QLabel(label_text))
        container.addWidget(widget)
        return container

# ====================================================================
# ÚNICO GRUPO: PROJECT SETTINGS
# (El bloque CYCLE & STAGE fue eliminado.)
# ====================================================================
    def init_ui(self):
        group_proj = QGroupBox("PROJECT SETTINGS")
        layout_proj = QVBoxLayout(group_proj)

    # Combo de país — se llena al cargar el Dictionary
        self.combo_country = QComboBox()
        self.combo_country.addItem("(load Dictionary first)")
        self.combo_country.setEnabled(False)

    # Año
        self.input_year = QLineEdit("2024")
        self.input_year.setPlaceholderText("e.g. 2024")

    # Fila del encabezado en la DB del RUNT (1-based)
        self.spin_start_row = QSpinBox()
        self.spin_start_row.setRange(1, 1000)
        self.spin_start_row.setValue(1)
        self.spin_start_row.setToolTip(
            "Row number (1-based) where the data header is located. "
            "Auto-detected when you load the DB; override if needed."
        )

        layout_proj.addLayout(self.create_field("Target Country:", self.combo_country))
        layout_proj.addLayout(self.create_field("Target Year:", self.input_year))
        layout_proj.addLayout(self.create_field("Header Row Index:", self.spin_start_row))

        self.main_layout.addWidget(group_proj)
        self.main_layout.addStretch()

# ====================================================================
# API pública — llamada desde MainWindow al cargar el Dictionary
    # ====================================================================
    def set_countries(self, country_list):
        self.combo_country.clear()
        self.combo_country.addItems(country_list)
        self.combo_country.setEnabled(True)