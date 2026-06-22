"""
The "Create Server" wizard as a self-contained widget.

Hosts the seven-step flow (step sidebar + stacked pages + bottom navigation) and
emits :data:`server_created` with a :class:`ServerRecord` once installation
succeeds. It contains no window chrome so it can be embedded in the application
shell next to the "My Servers" view.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal

from core.server_registry import ServerRecord
from core.session import ServerSession
from translations import Translator
from ui.step_complete import CompleteStep
from ui.step_config import ConfigStep
from ui.step_directory import DirectoryStep
from ui.step_install import InstallStep
from ui.step_resources import ResourcesStep
from ui.step_version import VersionStep
from ui.step_welcome import WelcomeStep

_STEP_KEYS = (
    "step_welcome", "step_version", "step_directory", "step_resources",
    "step_config", "step_install", "step_complete",
)


class CreateWizard(QWidget):
    """Embeddable seven-step server creation wizard."""

    server_created = pyqtSignal(object)   # ServerRecord
    manage_requested = pyqtSignal()       # user asked to view My Servers

    def __init__(self, translator: Translator, parent=None) -> None:
        super().__init__(parent)
        self.tr_ = translator
        self.session = ServerSession()
        self._current = 0
        self._build()
        self.reset()

    def t(self, key: str, **kwargs) -> str:
        return self.tr_.t(key, **kwargs)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self._stack = QStackedWidget()
        self._build_steps()
        right.addWidget(self._stack, 1)
        right.addWidget(self._build_nav_bar())
        container = QWidget()
        container.setLayout(right)
        root.addWidget(container, 1)

    def _build_sidebar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("SideBar")
        bar.setFixedWidth(196)
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(14)
        self._step_labels: list[QLabel] = []
        for index, key in enumerate(_STEP_KEYS, start=1):
            label = QLabel(f"{index}.  {self.t(key)}")
            label.setObjectName("StepPending")
            self._step_labels.append(label)
            layout.addWidget(label)
        layout.addStretch(1)
        return bar

    def _build_steps(self) -> None:
        self.welcome = WelcomeStep(self.session, self.tr_)
        self.version = VersionStep(self.session, self.tr_)
        self.directory = DirectoryStep(self.session, self.tr_)
        self.resources = ResourcesStep(self.session, self.tr_)
        self.config_step = ConfigStep(self.session, self.tr_)
        self.install = InstallStep(self.session, self.tr_)
        self.complete = CompleteStep(self.session, self.tr_)
        self._steps = [
            self.welcome, self.version, self.directory, self.resources,
            self.config_step, self.install, self.complete,
        ]
        for step in self._steps:
            step.validity_changed.connect(self._refresh_nav)
            self._stack.addWidget(step)

        self.install.back_requested.connect(lambda: self._go_to(2))
        self.install.install_succeeded.connect(self._on_installed)
        self.complete.new_server_requested.connect(self.reset)
        self.complete.manage_requested.connect(self.manage_requested.emit)
        self.complete.close_requested.connect(self.manage_requested.emit)

    def _build_nav_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)
        self._back_btn = QPushButton(self.t("btn_back"))
        self._back_btn.clicked.connect(self._go_back)
        layout.addWidget(self._back_btn)
        layout.addStretch(1)
        self._next_btn = QPushButton(self.t("btn_next"))
        self._next_btn.setObjectName("Primary")
        self._next_btn.clicked.connect(self._go_next)
        layout.addWidget(self._next_btn)
        return bar

    # ------------------------------------------------------------ navigation
    def reset(self) -> None:
        """Reset the wizard to its first step with a clean session."""
        self.session.reset()
        self._go_to(0)

    def _go_to(self, index: int) -> None:
        index = max(0, min(len(self._steps) - 1, index))
        self._current = index
        self._stack.setCurrentIndex(index)
        self._steps[index].on_enter()
        self._update_sidebar()
        self._refresh_nav()

    def _go_next(self) -> None:
        step = self._steps[self._current]
        if not step.can_advance():
            return
        step.commit()
        self._go_to(self._current + 1)

    def _go_back(self) -> None:
        if self._current in (5, 6):
            return
        self._go_to(self._current - 1)

    def _refresh_nav(self) -> None:
        step = self._steps[self._current]
        on_install = self._current == 5
        on_complete = self._current == 6
        self._back_btn.setVisible(not on_install and not on_complete and self._current > 0)
        self._next_btn.setVisible(not on_install and not on_complete)
        self._next_btn.setEnabled(step.can_advance())
        self._next_btn.setText(self.t("btn_start") if self._current == 4 else self.t("btn_next"))

    def _update_sidebar(self) -> None:
        for index, label in enumerate(self._step_labels):
            if index < self._current:
                prefix, obj = "✓", "StepDone"
            elif index == self._current:
                prefix, obj = "▶", "StepActive"
            else:
                prefix, obj = f"{index + 1}.", "StepPending"
            label.setObjectName(obj)
            label.setText(f"{prefix}  {self.t(_STEP_KEYS[index])}")
            label.style().unpolish(label)
            label.style().polish(label)

    # --------------------------------------------------------------- finish
    def _on_installed(self, jar_name: str, java_path: str = "java") -> None:
        record = ServerRecord(
            name=self.session.server_name,
            path=self.session.install_path,
            platform=self.session.platform,
            mc_version=self.session.mc_version,
            port=self.session.server_port,
            jar=jar_name or "server.jar",
            xms_mb=self.session.xms_mb,
            xmx_mb=self.session.xmx_mb,
            use_aikar_flags=self.session.use_aikar_flags,
            java_path=java_path or "java",
        )
        self.server_created.emit(record)
        self._go_to(6)

    def stop_workers(self) -> None:
        """Stop any in-flight installation worker (called on app close)."""
        self.install.stop()
