# gui/main_window.py
"""
Ventana principal de la app RUNT Data Transformer.
"""
import json
import os
import traceback

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QPushButton, QMessageBox, QDialog, QLabel,
    QFileDialog,
)

from .drop_zone import DropZone
from .config_panel import ConfigPanel
from .preview_panel import PreviewPanel
from .sheet_selector import SheetSelectorDialog
from .dialogs import ErrorReportDialog, NativeDialogs

from core.table_detector import TableDetector
from core.validator import Validator
from core.mapper import Mapper
from core.exporter import Exporter
from models.config import Config


# ---------------------------------------------------------------------------
# info_messages.json
# ---------------------------------------------------------------------------
INFO_FILE = os.path.join(os.path.dirname(__file__), "info_messages.json")


def _load_info_message(key: str) -> dict:
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, {"title": "Info", "message": "No information available."})
    except FileNotFoundError:
        return {"title": "Info", "message": f"Info file not found:\n{INFO_FILE}"}
    except json.JSONDecodeError as e:
        return {"title": "Error", "message": f"Could not parse info_messages.json:\n{e}"}


INFO_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #409eff;
        border: 1.5px solid #409eff;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton:hover { background-color: #409eff; color: white; }
    QPushButton:pressed { background-color: #2980d9; color: white; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RUNT Data Transformer")
        self.resize(1180, 640)

        # Estado
        self.dict_path: str | None = None
        self.db_path: str | None = None
        self.dict_dfs: dict | None = None
        self.source_df: pd.DataFrame | None = None
        self.final_df: pd.DataFrame | None = None

        self._build_ui()
        self._wire_signals()

    # =====================================================================
    # UI
    # =====================================================================
    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Barra superior (botón ⓘ a la derecha)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(15, 8, 15, 0)
        top_bar.addStretch()
        self.info_btn = QPushButton("ⓘ")
        self.info_btn.setFixedSize(24, 24)
        self.info_btn.setToolTip("How to use RUNT Data Transformer")
        self.info_btn.setStyleSheet(INFO_BTN_STYLE)
        self.info_btn.clicked.connect(self._show_info)
        top_bar.addWidget(self.info_btn)
        outer_layout.addLayout(top_bar)

        # Contenido principal
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(15)

        # Columna izquierda: drop zones
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.dict_drop = DropZone("Dictionary System")
        self.data_drop = DropZone("Source Data File (RUNT)")
        left_layout.addWidget(self.dict_drop)
        left_layout.addWidget(self.data_drop)
        left_layout.addStretch()

        # Columna central: preview + mapeo
        self.preview_panel = PreviewPanel()

        # Columna derecha: config + ejecutar
        right_frame = QFrame()
        right_frame.setFixedWidth(300)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.config_panel = ConfigPanel()
        right_layout.addWidget(self.config_panel)

        self.process_btn = QPushButton("EXECUTE TRANSFORMATION")
        self.process_btn.setFixedHeight(50)
        self.process_btn.setStyleSheet(
            "background-color: #409eff; color: white; "
            "font-weight: bold; border-radius: 8px;"
        )
        right_layout.addWidget(self.process_btn)

        main_layout.addWidget(left_frame, 1)
        main_layout.addWidget(self.preview_panel, 2)
        main_layout.addWidget(right_frame, 1)
        outer_layout.addWidget(content_widget)

    def _wire_signals(self):
        self.dict_drop.file_dropped.connect(self._on_dict_dropped)
        self.data_drop.file_dropped.connect(self._on_db_dropped)
        self.process_btn.clicked.connect(self._on_execute)

    # =====================================================================
    # Helpers UI
    # =====================================================================
    @staticmethod
    def _drop_zone_set_loaded(zone: DropZone, filename: str):
        """Tu DropZone no tiene método set_loaded; actualizamos directamente
        el status_label que sí es público."""
        zone.status_label.setText(f"✅ {filename}")
        zone.status_label.setStyleSheet(
            "color: #27ae60; font-size: 10px; font-weight: bold; border: none;"
        )

    # =====================================================================
    # Carga de Dictionary
    # =====================================================================
    def _on_dict_dropped(self, path: str):
        try:
            xls = pd.ExcelFile(path)
            self.dict_dfs = {name: xls.parse(name) for name in xls.sheet_names}
        except Exception as e:
            NativeDialogs.show_error("Error", f"Could not read Dictionary:\n{e}")
            return

        self.dict_path = path
        self._drop_zone_set_loaded(self.dict_drop, os.path.basename(path))

        # Llenar combo de país (excluyendo SEGMENT)
        countries = [s for s in self.dict_dfs.keys() if s.upper() != "SEGMENT"]
        if not countries:
            NativeDialogs.show_error(
                "Invalid Dictionary",
                "No country sheets found in the Dictionary."
            )
            return
        self.config_panel.set_countries(countries)

    # =====================================================================
    # Carga del DB del RUNT
    # =====================================================================
    def _on_db_dropped(self, path: str):
        try:
            xls = pd.ExcelFile(path)
            if len(xls.sheet_names) > 1:
                dlg = SheetSelectorDialog(xls.sheet_names)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                sheet_name = dlg.get_selected_sheet()
            else:
                sheet_name = xls.sheet_names[0]

            raw = pd.read_excel(
                path, sheet_name=sheet_name, header=None, dtype=object
            )

            # Detectar fila de encabezado (o respetar valor manual del SpinBox)
            manual_start = self.config_panel.spin_start_row.value()
            if manual_start > 1:
                start = manual_start - 1   # SpinBox es base-1
            else:
                start = TableDetector.find_start_row(raw)
                self.config_panel.spin_start_row.setValue(start + 1)

            self.source_df = TableDetector.get_clean_table(raw, start)

        except Exception as e:
            NativeDialogs.show_error("Error", f"Could not read DB:\n{e}")
            return

        self.db_path = path
        self._drop_zone_set_loaded(self.data_drop, os.path.basename(path))

        # Llenar PreviewPanel (combos + tabla de headers)
        cols = [str(c) for c in self.source_df.columns]
        self.preview_panel.fill_mapping_combos(cols)
        self.preview_panel.display_headers(cols)

    # =====================================================================
    # Ejecución
    # =====================================================================
    def _on_execute(self):
        # Prerrequisitos
        if self.dict_dfs is None:
            NativeDialogs.show_error("Missing file", "Please load the Dictionary first.")
            return
        if self.source_df is None:
            NativeDialogs.show_error("Missing file", "Please load the RUNT DB first.")
            return

        # País + año
        country = self.config_panel.combo_country.currentText()
        try:
            year = int(self.config_panel.input_year.text().strip())
            if not (2000 <= year <= 2100):
                raise ValueError("Year must be between 2000 and 2100.")
        except ValueError as e:
            NativeDialogs.show_error("Invalid year", str(e))
            return

        # Mapeo de columnas (lo expone el PreviewPanel)
        try:
            mapping = self.preview_panel.get_mapping()
        except Exception as e:
            NativeDialogs.show_error(
                "Invalid mapping",
                f"Please complete the column mapping (Brand/Model/Month):\n{e}"
            )
            return

        config = Config(country=country, year=year)

        # Validación
        try:
            validator = Validator(config, mapping, self.dict_dfs)
            errors = validator.validate_all(self.source_df)
        except Exception as e:
            NativeDialogs.show_error(
                "Validation error",
                f"{e}\n\n{traceback.format_exc()}"
            )
            return

        if errors.has_errors():
            report = self._format_error_report(errors)
            dlg = ErrorReportDialog(report)
            dlg.exec()
            # Las filas con problemas se descartan; seguimos.

        # Transformación
        try:
            mapper = Mapper(config, mapping, self.dict_dfs)
            self.final_df = mapper.process_transformation(self.source_df)
        except Exception as e:
            NativeDialogs.show_error(
                "Transformation error",
                f"{e}\n\n{traceback.format_exc()}"
            )
            return

        if self.final_df is None or self.final_df.empty:
            NativeDialogs.show_error(
                "No results",
                "The transformation produced no rows. Check that the Dictionary "
                "contains the (BRAND RUNT, MODEL RUNT) pairs present in the DB."
            )
            return

        # Guardar
        default_name = f"RUNT_{country}_{year}_normalized.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save normalized Excel", default_name, "Excel files (*.xlsx)"
        )
        if not path:
            return

        try:
            Exporter.save_to_excel(self.final_df, path)
        except Exception as e:
            NativeDialogs.show_error("Save error", f"{e}")
            return

        NativeDialogs.show_success()

    # =====================================================================
    # Helpers
    # =====================================================================
    @staticmethod
    def _format_error_report(error_collector) -> str:
        """Convierte el ErrorCollector en texto monoespaciado para el modal."""
        lines = [
            f"{'Row':>6}  {'Column':<20}  {'Value':<30}  Message",
            f"{'-'*6}  {'-'*20}  {'-'*30}  {'-'*40}",
        ]
        for e in error_collector.errors:
            lines.append(
                f"{e.row:>6}  {e.column[:20]:<20}  "
                f"{str(e.value)[:30]:<30}  {e.message}"
            )
        return "\n".join(lines)

    def _show_info(self):
        info = _load_info_message("main_window")
        dialog = QDialog(self)
        dialog.setWindowTitle(info["title"])
        dialog.setFixedSize(650, 320)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(15)

        label = QLabel(info["message"])
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(label, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.exec()