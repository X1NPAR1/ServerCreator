"""Step 6 — live installation with a colour-coded log and progress bar."""

from __future__ import annotations

import os
import shutil

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.installer import InstallerWorker
from ui.base_step import BaseStep
from ui.common import title_label
from ui.widgets.animated_progress import AnimatedProgressBar
from ui.widgets.log_viewer import LogViewer

# Plain (non-tokenised) log keys that should also update the status line.
_STATUS_KEYS = {
    "log_verifying", "log_running_first", "log_eula", "log_configuring",
    "log_editing", "log_motd", "log_scripts", "log_done", "log_cleanup",
}


class InstallStep(BaseStep):
    """Drives :class:`InstallerWorker` and renders its output."""

    # Emitted when the user must return to the name/location step.
    back_requested = pyqtSignal()
    # Emitted with (server jar name, resolved java path) when installation succeeds.
    install_succeeded = pyqtSignal(str, str)

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._worker: InstallerWorker | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(title_label(self.t("install_title")))

        self._status = QLabel("")
        self._status.setObjectName("Secondary")
        layout.addWidget(self._status)

        self._progress = AnimatedProgressBar()
        layout.addWidget(self._progress)

        self._log = LogViewer()
        layout.addWidget(self._log, 1)

        buttons = QHBoxLayout()
        copy_btn = QPushButton(self.t("btn_copy_log"))
        copy_btn.clicked.connect(self._copy_log)
        save_btn = QPushButton(self.t("btn_save_log"))
        save_btn.clicked.connect(self._save_log)
        buttons.addWidget(copy_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    # -- lifecycle ---------------------------------------------------------- #
    def on_enter(self) -> None:
        # Pre-flight: handle an already-existing target folder.
        path = self.session.install_path
        if os.path.exists(path) and os.listdir(path):
            answer = QMessageBox.question(
                self,
                self.t("install_overwrite_title"),
                self.t("install_overwrite_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.back_requested.emit()
                return
            shutil.rmtree(path, ignore_errors=True)

        # The worker now ensures Java (installing it automatically if missing),
        # so installation can begin immediately.
        self._start()

    def _start(self) -> None:
        self._busy = False
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._status.setText("")
        self._worker = InstallerWorker(self.session, self.tr_.language, self)
        self._worker.log.connect(self._on_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.busy.connect(self._on_busy)
        self._worker.finished_install.connect(self._on_finished)
        self._worker.start()

    # -- worker callbacks --------------------------------------------------- #
    def _on_log(self, level: str, message: str) -> None:
        text = self._translate_message(message)
        self._log.append_line(level, text)
        # Surface high-level phase messages in the status line above the bar.
        if message.startswith("::") or message in _STATUS_KEYS:
            self._status.setText(text)

    def _translate_message(self, message: str) -> str:
        """Resolve installer message tokens into the active language."""
        if message.startswith("::") and message.count("::") >= 2:
            _, key, arg = message.split("::", 2)
            mapping = {
                "log_creating_dir": "path",
                "log_downloading": "file",
                "log_downloaded": "file",
                "log_java_ok": "v",
                "log_java_missing": "v",
                "log_java_installing": "v",
                "log_java_ready": "v",
                "log_building": "t",
            }
            kw = {mapping.get(key, "value"): arg} if arg else {}
            return self.t(key, **kw)
        return self.t(message)  # falls back to the raw text for free-form errors

    def _on_busy(self, busy: bool) -> None:
        """Switch the progress bar between determinate and indeterminate."""
        self._busy = busy
        if busy:
            self._progress.setRange(0, 0)  # animated "busy" indicator
        else:
            self._progress.setRange(0, 100)

    def _on_progress(self, downloaded: int, total: int) -> None:
        if self._busy:
            return
        if total > 0:
            self._progress.setRange(0, 100)
            self._progress.animate_to(int(downloaded * 100 / total))

    def _on_finished(self, success: bool, payload: str) -> None:
        if success:
            self._progress.setRange(0, 100)
            self._progress.animate_to(100)
            java_path = self._worker.java_path if self._worker else "java"
            self.install_succeeded.emit(payload, java_path)
        elif payload != "cancelled":
            self._progress.setRange(0, 100)
            QMessageBox.critical(self, self.t("error_title"), self.t("log_failed", error=payload))

    # -- log actions -------------------------------------------------------- #
    def _copy_log(self) -> None:
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(self._log.plain_text())

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, self.t("btn_save_log"), "servercreator-log.txt", "*.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._log.plain_text())
            QMessageBox.information(self, self.t("info_title"), self.t("log_saved", path=path))
        except OSError as exc:
            QMessageBox.critical(self, self.t("error_title"), str(exc))

    def stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
