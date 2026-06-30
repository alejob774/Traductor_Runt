# main.py
"""
Entry point de la app RUNT Data Transformer.

Lanza una QApplication de PySide6 y abre la MainWindow.
Compatible con PyInstaller (--onefile --windowed).
"""
import sys
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RUNT Data Transformer")
    app.setOrganizationName("GM Colombia - Pricing")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
