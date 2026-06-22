"""Step 3 — server name and installation location, with live validation."""

from __future__ import annotations

import os
import re

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ui.base_step import BaseStep
from ui.common import card, horizontal_divider, title_label
from utils import default_servers_dir, free_space_bytes

# Allowed characters: letters, digits, space, hyphen, underscore.
_NAME_PATTERN = re.compile(r"^[\w\- ]+$", re.UNICODE)
_MIN_FREE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


class DirectoryStep(BaseStep):
    """Collects the server name and the parent installation directory."""

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        layout.addWidget(title_label(self.t("dir_title")))

        panel = card()
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(10)

        # --- Server name ---
        inner.addWidget(self._section_title(self.t("server_name_label")))
        inner.addWidget(self._muted(self.t("server_name_desc")))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(self.t("server_name_label"))
        self._name_edit.textChanged.connect(self._revalidate)
        inner.addWidget(self._name_edit)
        self._name_error = self._error_label()
        inner.addWidget(self._name_error)

        inner.addWidget(horizontal_divider())

        # --- Location ---
        inner.addWidget(self._section_title(self.t("install_loc_label")))
        inner.addWidget(self._muted(self.t("install_loc_desc")))
        loc_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setReadOnly(True)
        self._dir_edit.setText(self.session.base_directory or default_servers_dir())
        browse = QPushButton(self.t("btn_browse"))
        browse.clicked.connect(self._browse)
        loc_row.addWidget(self._dir_edit, 1)
        loc_row.addWidget(browse)
        inner.addLayout(loc_row)
        self._dir_error = self._error_label()
        inner.addWidget(self._dir_error)

        # --- Preview ---
        self._preview = QLabel("")
        self._preview.setObjectName("Accent")
        self._preview.setWordWrap(True)
        inner.addWidget(self._preview)

        layout.addWidget(panel)
        layout.addStretch(1)

    # -- helpers ------------------------------------------------------------ #
    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 16px; font-weight: 600;")
        return label

    def _muted(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("Secondary")
        label.setWordWrap(True)
        return label

    def _error_label(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("Error")
        label.setWordWrap(True)
        return label

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, self.t("install_loc_label"), self._dir_edit.text()
        )
        if chosen:
            self._dir_edit.setText(chosen)
        self._revalidate()

    # -- validation --------------------------------------------------------- #
    def _validate_name(self) -> bool:
        name = self._name_edit.text().strip()
        if not name:
            self._name_error.setText(self.t("name_err_empty"))
            return False
        if len(name) < 3 or len(name) > 64:
            self._name_error.setText(self.t("name_err_length"))
            return False
        if not _NAME_PATTERN.match(name):
            self._name_error.setText(self.t("name_err_chars"))
            return False
        self._name_error.clear()
        return True

    def _validate_dir(self) -> bool:
        directory = self._dir_edit.text().strip()
        if not directory:
            self._dir_error.setText(self.t("dir_err_writable"))
            return False
        probe = directory
        while probe and not os.path.exists(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        if probe and not os.access(probe, os.W_OK):
            self._dir_error.setText(self.t("dir_err_writable"))
            return False
        if free_space_bytes(directory) < _MIN_FREE_BYTES:
            self._dir_error.setText(self.t("dir_warn_space"))  # warning, not blocking
        else:
            self._dir_error.clear()
        return True

    def _revalidate(self) -> None:
        name_ok = self._validate_name()
        dir_ok = self._validate_dir()
        self._name_edit.setObjectName("Valid" if name_ok else "Invalid")
        self._refresh_style(self._name_edit)

        name = self._name_edit.text().strip()
        directory = self._dir_edit.text().strip()
        if name_ok and directory:
            full = os.path.join(directory, name)
            self._preview.setText(self.t("install_path_preview", path=full))
        else:
            self._preview.clear()
        self.validity_changed.emit()

    @staticmethod
    def _refresh_style(widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        if self.session.server_name:
            self._name_edit.setText(self.session.server_name)
        if self.session.base_directory:
            self._dir_edit.setText(self.session.base_directory)
        self._revalidate()

    def can_advance(self) -> bool:
        return self._validate_name() and bool(self._dir_edit.text().strip())

    def commit(self) -> None:
        self.session.server_name = self._name_edit.text().strip()
        self.session.base_directory = self._dir_edit.text().strip()
