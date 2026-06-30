
import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox
)

# ---------------------------------------------------------------------------
# Path to the customizable info messages file.
# Place info_messages.json in the same folder as this file.
# To edit messages, open info_messages.json and modify the "sheet_selector" key.
# ---------------------------------------------------------------------------
INFO_FILE = os.path.join(os.path.dirname(__file__), "info_messages.json")


def _load_info_message(key: str) -> dict:
    """
    Load a specific info message block from info_messages.json.

    Args:
        key (str): The top-level key in the JSON (e.g. "sheet_selector").

    Returns:
        dict: A dict with "title" and "message" keys.
    """
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, {"title": "Info", "message": "No information available."})
    except FileNotFoundError:
        return {"title": "Info", "message": f"Info file not found:\n{INFO_FILE}"}
    except json.JSONDecodeError as e:
        return {"title": "Error", "message": f"Could not parse info_messages.json:\n{e}"}


# ---------------------------------------------------------------------------
# Shared stylesheet for the circular info button (ⓘ).
# Used in both SheetSelectorDialog and MainWindow.
# ---------------------------------------------------------------------------
INFO_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #409eff;
        border: 1.5px solid #409eff;
        border-radius: 11px;
        font-size: 12px;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton:hover {
        background-color: #409eff;
        color: white;
    }
    QPushButton:pressed {
        background-color: #2980d9;
        color: white;
    }
"""


class SheetSelectorDialog(QDialog):
    def __init__(self, sheets):
        super().__init__()
        self.setWindowTitle("Select Sheet")
        self.setFixedSize(340, 155)  # Compact fixed size for a clean look

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        # ── Top row: label + info button ────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        label = QLabel("Select sheet to process:")
        top_row.addWidget(label)
        top_row.addStretch()  # Push the info button to the far right

        # Small circular ⓘ button
        self.info_btn = QPushButton("ⓘ")
        self.info_btn.setFixedSize(22, 22)
        self.info_btn.setToolTip("Click for more information about this dialog")
        self.info_btn.setStyleSheet(INFO_BTN_STYLE)
        self.info_btn.clicked.connect(self._show_info)
        top_row.addWidget(self.info_btn)

        main_layout.addLayout(top_row)

        # ── Sheet combo box ──────────────────────────────────────────────────
        self.combo = QComboBox()
        self.combo.addItems(sheets)
        main_layout.addWidget(self.combo)

        # ── Accept button ────────────────────────────────────────────────────
        self.btn = QPushButton("Accept")
        self.btn.clicked.connect(self.accept)
        main_layout.addWidget(self.btn)

    def _show_info(self):
        """Display the info pop-up using the 'sheet_selector' entry in info_messages.json."""
        info = _load_info_message("sheet_selector")
        msg = QMessageBox(self)
        msg.setWindowTitle(info["title"])
        msg.setText(info["message"])
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def get_selected_sheet(self) -> str:
        return self.combo.currentText()
