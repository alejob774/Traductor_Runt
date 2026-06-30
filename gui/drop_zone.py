from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt, Signal

class DropZone(QFrame):
    file_dropped = Signal(str)

    def __init__(self, title):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedHeight(180)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #ebeef5; border-radius: 8px; background-color: #fafafa;
            }
            QFrame:hover { border-color: #409eff; background-color: #f5f7fa; }
        """)

        layout = QVBoxLayout(self)
        self.label = QLabel(f"<b>{title}</b><br><small>Drag & Drop here</small>")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #606266; border: none;")
        layout.addWidget(self.label)

        self.status_label = QLabel("No file selected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #909399; font-size: 10px; border: none;")
        layout.addWidget(self.status_label)

        self.btn_browse = QPushButton("Select File")
        self.btn_browse.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #dcdfe6; border-radius: 4px; padding: 4px; }
            QPushButton:hover { color: #409eff; border-color: #c6e2ff; background-color: #ecf5ff; }
        """)
        self.btn_browse.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.btn_browse)

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel (*.xlsx *.xls *.xlsm)")
        if path: self.file_dropped.emit(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()
        else: e.ignore()

    def dropEvent(self, e):
        path = e.mimeData().urls()[0].toLocalFile()
        self.file_dropped.emit(path)