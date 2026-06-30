from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem

class PreviewHeaders(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Detected Columns Preview:")
        self.label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.layout.addWidget(self.label)

        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.layout.addWidget(self.table)

    def display_headers(self, columns):
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        for i, col in enumerate(columns):
            self.table.setItem(0, i, QTableWidgetItem("Sample Data"))
        self.table.resizeColumnsToContents()