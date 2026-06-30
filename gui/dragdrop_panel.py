import os


from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QWidget, QLabel, QVBoxLayout, QFileDialog


class DragDropPanel(QFrame):
    # This is the missing line that caused your error:
    file_dropped = Signal(str)

    def __init__(self, title):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setStyleSheet("""
            QFrame { 
                border: 2px dashed #aaa; 
                border-radius: 10px; 
                background: #f9f9f9; 
            }
            QFrame:hover {
                background: #f0f4f7;
                border-color: #3498db;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        
        self.status_label = QLabel("Drag & Drop file here\nor click to browse")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.status_label)

    def mousePressEvent(self, event):
        """Allows clicking the panel to open a file browser."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls *.csv)"
        )
        if file_path:
            self.file_dropped.emit(file_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            self.file_dropped.emit(file_path)