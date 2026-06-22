"""Step 2 — Minecraft version selection (loaded in a background thread)."""

from __future__ import annotations

from typing import List

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from core.java_manager import required_java_for
from core.version_manager import VersionManager
from ui.base_step import BaseStep
from ui.common import card, subtitle_label, title_label
from ui.widgets.styled_combo import StyledComboBox


class _VersionWorker(QThread):
    """Fetches versions for a platform without blocking the UI."""

    done = pyqtSignal(list, bool)  # versions, from_cache_only

    def __init__(self, platform: str, parent=None) -> None:
        super().__init__(parent)
        self._platform = platform

    def run(self) -> None:  # noqa: D401
        manager = VersionManager()
        had_cache = bool(manager.cached_versions(self._platform))
        versions = manager.get_versions(self._platform)
        # If a live fetch produced nothing new and we only have cache, flag it.
        fell_back = (not manager.is_cache_fresh(self._platform)) and had_cache and bool(versions)
        self.done.emit(versions, fell_back)


class VersionStep(BaseStep):
    """Presents the supported versions for the chosen platform."""

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._worker: _VersionWorker | None = None
        self._loaded_platform = ""
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        layout.addWidget(title_label(self.t("version_title")))

        panel = card()
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(10)

        inner.addWidget(QLabel(self.t("version_label")))
        self._combo = StyledComboBox()
        self._combo.currentIndexChanged.connect(self._on_change)
        inner.addWidget(self._combo)

        self._status = QLabel(self.t("version_loading"))
        self._status.setObjectName("Secondary")
        inner.addWidget(self._status)

        self._java_note = QLabel("")
        self._java_note.setObjectName("Warning")
        self._java_note.setWordWrap(True)
        inner.addWidget(self._java_note)

        layout.addWidget(panel)
        layout.addStretch(1)

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        if self.session.platform == self._loaded_platform and self._combo.count():
            return
        self._loaded_platform = self.session.platform
        self._combo.clear()
        self._combo.setEnabled(False)
        self._status.setText(self.t("version_loading"))
        self._java_note.clear()
        self.validity_changed.emit()

        self._worker = _VersionWorker(self.session.platform, self)
        self._worker.done.connect(self._on_loaded)
        self._worker.start()

    def _on_loaded(self, versions: List[str], fell_back: bool) -> None:
        self._combo.setEnabled(True)
        if not versions:
            self._status.setText(self.t("version_none"))
            self.validity_changed.emit()
            return
        self._combo.addItems(versions)
        if self.session.mc_version in versions:
            self._combo.setCurrentText(self.session.mc_version)
        self._status.setText(self.t("version_load_failed") if fell_back else "")
        self._on_change()
        self.validity_changed.emit()

    def _on_change(self) -> None:
        version = self._combo.currentText()
        if version:
            java = required_java_for(version)
            self._java_note.setText(self.t("version_java_note", java=java))
        self.validity_changed.emit()

    def can_advance(self) -> bool:
        return bool(self._combo.currentText())

    def commit(self) -> None:
        self.session.mc_version = self._combo.currentText()
        self.session.required_java = required_java_for(self.session.mc_version)
