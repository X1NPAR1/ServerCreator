"""Step 7 — completion screen."""

from __future__ import annotations

import os
import subprocess
import sys

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ui.base_step import BaseStep
from ui.common import card, make_logo_label


class CompleteStep(BaseStep):
    """Shown after a successful installation."""

    new_server_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        layout.addStretch(1)

        header = QHBoxLayout()
        header.addStretch(1)
        header.addWidget(make_logo_label(64))
        check = QLabel("✓")
        check.setObjectName("Accent")
        check.setStyleSheet("font-size: 48px; font-weight: 700;")
        header.addWidget(check)
        header.addStretch(1)
        layout.addLayout(header)

        title = QLabel(self.t("complete_title"))
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        panel = card()
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(20, 16, 20, 16)
        inner.addWidget(QLabel(self.t("complete_path")))
        self._path_label = QLabel("")
        self._path_label.setObjectName("Accent")
        self._path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._path_label.setWordWrap(True)
        inner.addWidget(self._path_label)
        layout.addWidget(panel)

        buttons = QHBoxLayout()
        open_btn = QPushButton(self.t("btn_open_folder"))
        open_btn.clicked.connect(self._open_folder)
        launch_btn = QPushButton(self.t("btn_launch_server"))
        launch_btn.setObjectName("Primary")
        launch_btn.clicked.connect(self._launch)
        new_btn = QPushButton(self.t("btn_new_server"))
        new_btn.clicked.connect(self.new_server_requested.emit)
        close_btn = QPushButton(self.t("btn_close"))
        close_btn.clicked.connect(self.close_requested.emit)
        for btn in (open_btn, launch_btn, new_btn, close_btn):
            buttons.addWidget(btn)
        layout.addLayout(buttons)
        layout.addStretch(1)

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        self._path_label.setText(self.session.install_path)

    def _open_folder(self) -> None:
        path = self.session.install_path
        if os.path.isdir(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _launch(self) -> None:
        script = os.path.join(self.session.install_path, "start.bat" if os.name == "nt" else "start.sh")
        if not os.path.exists(script):
            QMessageBox.warning(self, self.t("warning_title"), self.t("complete_path"))
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(script)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["bash", script], cwd=self.session.install_path)
        except OSError as exc:
            QMessageBox.critical(self, self.t("error_title"), str(exc))
