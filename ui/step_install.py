"""Step 6 — live installation with a colour-coded log and progress bar."""

from __future__ import annotations

import os
import shutil

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core import java_manager
from core.installer import InstallerWorker
from ui.base_step import BaseStep
from ui.common import title_label
from ui.widgets.animated_progress import AnimatedProgressBar
from ui.widgets.log_viewer import LogViewer


class InstallStep(BaseStep):
    """Drives :class:`InstallerWorker` and renders its output."""

    # Emitted when the user must return to the name/location step.
    back_requested = pyqtSignal()
    # Emitted with the resolved server jar name when installation succeeds.
    install_succeeded = pyqtSignal(str)

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._worker: InstallerWorker | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(title_label(self.t("install_title")))

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

        if not self._check_java():
            return
        self._start()

    def _check_java(self) -> bool:
        required = self.session.required_java
        found, major, _ = java_manager.detect_java()
        if found and major is not None and major >= required:
            return True
        if not found:
            text = self.t("java_missing_text", required=required)
        else:
            text = self.t("java_outdated_text", found=major, required=required)
        box = QMessageBox(self)
        box.setWindowTitle(self.t("java_missing_title"))
        box.setText(text)
        download = box.addButton(self.t("java_download"), QMessageBox.ButtonRole.ActionRole)
        cont = box.addButton(self.t("btn_continue"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(self.t("btn_cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is download:
            QDesktopServices.openUrl(QUrl(java_manager.JAVA_DOWNLOAD_URL))
            self.back_requested.emit()
            return False
        if clicked is cont:
            self._start()
            return False  # _start already launched
        self.back_requested.emit()
        return False

    def _start(self) -> None:
        self._progress.setValue(0)
        self._worker = InstallerWorker(self.session, self.tr_.language, self)
        self._worker.log.connect(self._on_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_install.connect(self._on_finished)
        self._worker.start()

    # -- worker callbacks --------------------------------------------------- #
    def _on_log(self, level: str, message: str) -> None:
        self._log.append_line(level, self._translate_message(message))

    def _translate_message(self, message: str) -> str:
        """Resolve installer message tokens into the active language."""
        if message.startswith("::") and message.count("::") >= 2:
            _, key, arg = message.split("::", 2)
            mapping = {
                "log_creating_dir": "path",
                "log_downloading": "file",
            }
            kw = {mapping.get(key, "value"): arg}
            return self.t(key, **kw)
        translated = self.t(message)
        return translated  # falls back to the raw text for free-form errors

    def _on_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            self._progress.animate_to(int(downloaded * 100 / total))

    def _on_finished(self, success: bool, payload: str) -> None:
        if success:
            self._progress.animate_to(100)
            self.install_succeeded.emit(payload)
        elif payload != "cancelled":
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
