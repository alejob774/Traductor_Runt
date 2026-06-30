# gui/dialogs.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QMessageBox
from tkinter import messagebox, Tk

class ErrorReportDialog(QDialog):
    """Ventana modal que lista todos los errores encontrados."""
    def __init__(self, error_report, lang="ES"):
        super().__init__()
        self.setWindowTitle("Validation Errors")
        self.setMinimumSize(700, 450)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("The following inconsistencies were found:")
        label.setStyleSheet("font-weight: bold; color: #c0392b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        # Área de scroll para manejar cientos de errores si es necesario
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # IMPORTANTE: Aquí definimos el widget de contenido que faltaba importar
        content_widget = QWidget() 
        content_layout = QVBoxLayout(content_widget)
        
        text_report = QLabel(error_report)
        # Fuente monoespaciada para que las columnas del reporte se vean alineadas
        text_report.setStyleSheet("""
            font-family: 'Consolas', 'Monaco', monospace; 
            font-size: 11px; 
            background-color: #fdf2f2; 
            padding: 10px;
            border: 1px solid #fadbd8;
        """)
        text_report.setWordWrap(True)
        text_report.setTextInteractionFlags(text_report.textInteractionFlags().TextSelectableByMouse)
        
        content_layout.addWidget(text_report)
        content_layout.addStretch() # Empuja el texto hacia arriba
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

class NativeDialogs:
    @staticmethod
    def show_error(title, message):
        """Usa Tkinter para un error crítico rápido (nativo de Windows)."""
        root = Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()

    @staticmethod
    def show_success(lang="ES"):
        root = Tk()
        root.withdraw()
        msg = "Process completed successfully."
        title = "Success"
        messagebox.showinfo(title, msg)
        root.destroy()
