"""
Detailed management view for a single server.

Presents the server's live console (with command input), an editable
``server.properties`` table, world tools (new world / backup) and a live
information panel. Start/stop and delete controls live in the header. The
underlying :class:`ServerRuntime` is owned by the application shell so the
server keeps running while the user navigates elsewhere.
"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core import world_manager
from core.server_configurator import read_properties, write_properties
from core.server_registry import ServerRecord, ServerRegistry
from core.server_runtime import ServerRuntime
from translations import Translator


def _format_uptime(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class ServerDetail(QWidget):
    """Management surface for one server."""

    back_requested = pyqtSignal()
    deleted = pyqtSignal(str)  # path of the deleted server

    def __init__(
        self,
        record: ServerRecord,
        runtime: ServerRuntime,
        registry: ServerRegistry,
        translator: Translator,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.runtime = runtime
        self.registry = registry
        self.tr_ = translator
        self._build()
        self._connect_runtime()
        self._refresh_state(self.runtime.is_running())

        self._info_timer = QTimer(self)
        self._info_timer.setInterval(1000)
        self._info_timer.timeout.connect(self._refresh_info)
        self._info_timer.start()

    def t(self, key: str, **kwargs) -> str:
        return self.tr_.t(key, **kwargs)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        root.addLayout(self._build_header())

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_console_tab(), self.t("tab_console"))
        self._tabs.addTab(self._build_properties_tab(), self.t("tab_properties"))
        self._tabs.addTab(self._build_worlds_tab(), self.t("tab_worlds"))
        self._tabs.addTab(self._build_info_tab(), self.t("tab_info"))
        root.addWidget(self._tabs, 1)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        back = QPushButton(self.t("btn_back_to_list"))
        back.clicked.connect(self.back_requested.emit)
        row.addWidget(back)

        name = QLabel(self.record.name)
        name.setObjectName("Title")
        row.addWidget(name)

        self._badge = QLabel()
        self._badge.setObjectName("BadgeStopped")
        row.addWidget(self._badge)
        row.addStretch(1)

        self._start_btn = QPushButton(self.t("btn_start_server"))
        self._start_btn.setObjectName("Primary")
        self._start_btn.clicked.connect(self._start)
        self._stop_btn = QPushButton(self.t("btn_stop_server"))
        self._stop_btn.clicked.connect(self._stop)
        open_btn = QPushButton(self.t("btn_open_folder"))
        open_btn.clicked.connect(self._open_folder)
        delete_btn = QPushButton(self.t("btn_delete_server"))
        delete_btn.clicked.connect(self._delete)
        for btn in (self._start_btn, self._stop_btn, open_btn, delete_btn):
            row.addWidget(btn)
        return row

    # ---- console tab ------------------------------------------------------ #
    def _build_console_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        self._console = QPlainTextEdit()
        self._console.setObjectName("LogViewer")
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(6000)
        self._console.setPlainText(self.runtime.console_text())
        layout.addWidget(self._console, 1)

        self._cmd = QLineEdit()
        self._cmd.setPlaceholderText(self.t("console_input_placeholder"))
        self._cmd.returnPressed.connect(self._send_command)
        layout.addWidget(self._cmd)
        return page

    # ---- properties tab --------------------------------------------------- #
    def _build_properties_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels([self.t("props_key"), self.t("props_value")])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        save = QPushButton(self.t("props_save"))
        save.setObjectName("Primary")
        save.clicked.connect(self._save_properties)
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignRight)
        self._load_properties()
        return page

    def _load_properties(self) -> None:
        props = read_properties(self.record.path)
        self._table.setRowCount(0)
        for key, value in props.items():
            row = self._table.rowCount()
            self._table.insertRow(row)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, key_item)
            self._table.setItem(row, 1, QTableWidgetItem(value))

    def _save_properties(self) -> None:
        overrides = {}
        for row in range(self._table.rowCount()):
            key = self._table.item(row, 0)
            value = self._table.item(row, 1)
            if key is not None:
                overrides[key.text()] = value.text() if value else ""
        if write_properties(self.record.path, overrides):
            QMessageBox.information(self, self.t("info_title"), self.t("props_saved"))

    # ---- worlds tab ------------------------------------------------------- #
    def _build_worlds_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        self._world_current = QLabel()
        self._world_current.setObjectName("Accent")
        layout.addWidget(self._world_current)

        self._world_list = QListWidget()
        layout.addWidget(self._world_list, 1)

        row = QHBoxLayout()
        new_btn = QPushButton(self.t("worlds_new"))
        new_btn.clicked.connect(self._new_world)
        backup_btn = QPushButton(self.t("worlds_backup"))
        backup_btn.setObjectName("Primary")
        backup_btn.clicked.connect(self._backup_world)
        row.addWidget(new_btn)
        row.addWidget(backup_btn)
        row.addStretch(1)
        layout.addLayout(row)
        self._load_worlds()
        return page

    def _load_worlds(self) -> None:
        self._world_current.setText(
            self.t("worlds_current", name=world_manager.current_level_name(self.record.path))
        )
        self._world_list.clear()
        self._world_list.addItems(world_manager.list_worlds(self.record.path))

    def _new_world(self) -> None:
        name, ok = QInputDialog.getText(self, self.t("worlds_new"), self.t("worlds_new_prompt"))
        if not ok or not name.strip():
            return
        try:
            world_manager.create_world(self.record.path, name.strip())
            QMessageBox.information(self, self.t("info_title"), self.t("worlds_new_done", name=name.strip()))
            self._load_worlds()
        except ValueError as exc:
            QMessageBox.warning(self, self.t("warning_title"), str(exc))

    def _backup_world(self) -> None:
        if self.runtime.is_running():
            QMessageBox.warning(self, self.t("warning_title"), self.t("worlds_backup_running"))
            return
        item = self._world_list.currentItem()
        world = item.text() if item else world_manager.current_level_name(self.record.path)
        try:
            dest = os.path.join(self.record.path, "backups")
            archive = world_manager.backup_world(self.record.path, world, dest)
            QMessageBox.information(self, self.t("info_title"), self.t("worlds_backup_done", path=archive))
        except (FileNotFoundError, OSError) as exc:
            QMessageBox.critical(self, self.t("error_title"), str(exc))

    # ---- info tab --------------------------------------------------------- #
    def _build_info_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(10)
        self._info_labels: dict[str, QLabel] = {}
        rows = [
            ("status", self.t("info_status")),
            ("players", self.t("info_players")),
            ("uptime", self.t("info_uptime")),
            ("cpu", self.t("info_cpu")),
            ("memory", self.t("info_memory")),
            ("platform", self.t("info_platform")),
            ("version", self.t("info_version")),
            ("port", self.t("info_port")),
            ("path", self.t("info_path")),
        ]
        for key, label_text in rows:
            row = QHBoxLayout()
            caption = QLabel(label_text + ":")
            caption.setObjectName("Secondary")
            caption.setFixedWidth(180)
            value = QLabel("—")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._info_labels[key] = value
            row.addWidget(caption)
            row.addWidget(value, 1)
            layout.addLayout(row)
        layout.addStretch(1)

        # Static values.
        self._info_labels["platform"].setText(self.record.platform or "—")
        self._info_labels["version"].setText(self.record.mc_version or "—")
        self._info_labels["port"].setText(str(self.record.port))
        self._info_labels["path"].setText(self.record.path)
        self._cpu_value = "—"
        self._mem_value = "—"
        return page

    # ------------------------------------------------------------ runtime glue
    def _connect_runtime(self) -> None:
        self.runtime.output.connect(self._on_output)
        self.runtime.state_changed.connect(self._refresh_state)
        self.runtime.stats_changed.connect(self._on_stats)

    def _on_output(self, text: str) -> None:
        self._console.moveCursor(self._console.textCursor().MoveOperation.End)
        self._console.insertPlainText(text)
        bar = self._console.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_stats(self, cpu: float, mem_mb: float) -> None:
        self._cpu_value = f"{cpu:.0f} %"
        self._mem_value = f"{mem_mb:.0f} MB"

    def _refresh_state(self, running: bool) -> None:
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._cmd.setEnabled(running)
        self._badge.setText(self.t("server_status_running") if running else self.t("server_status_stopped"))
        self._badge.setObjectName("BadgeRunning" if running else "BadgeStopped")
        self._badge.style().unpolish(self._badge)
        self._badge.style().polish(self._badge)
        if not running:
            self._cpu_value = "—"
            self._mem_value = "—"

    def _refresh_info(self) -> None:
        running = self.runtime.is_running()
        labels = self._info_labels
        labels["status"].setText(self.t("server_status_running") if running else self.t("server_status_stopped"))
        if running:
            labels["players"].setText(f"{self.runtime.online_players} / {self.runtime.max_players}")
            labels["uptime"].setText(_format_uptime(self.runtime.uptime_seconds()))
        else:
            labels["players"].setText(self.t("stat_not_available"))
            labels["uptime"].setText(self.t("stat_not_available"))
        labels["cpu"].setText(self._cpu_value)
        labels["memory"].setText(self._mem_value)

    # ----------------------------------------------------------------- actions
    def _start(self) -> None:
        if not self.runtime.is_running():
            self._console.appendPlainText(self.t("console_server_started"))
            self.runtime.start()

    def _stop(self) -> None:
        self.runtime.stop()

    def _send_command(self) -> None:
        text = self._cmd.text().strip()
        if not text:
            return
        self._console.appendPlainText(f"> {text}")
        self.runtime.send_command(text)
        self._cmd.clear()

    def _open_folder(self) -> None:
        if os.path.isdir(self.record.path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.record.path))

    def _delete(self) -> None:
        answer = QMessageBox.question(
            self,
            self.t("delete_confirm_title"),
            self.t("delete_confirm_text", name=self.record.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if self.runtime.is_running():
            self.runtime.stop(force_after_ms=1000)
        self._info_timer.stop()
        world_manager.delete_server(self.record.path)
        self.registry.remove(self.record.path)
        self.deleted.emit(self.record.path)

    def stop_timers(self) -> None:
        self._info_timer.stop()
