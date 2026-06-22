"""
Main application window: top bar, step sidebar, stacked wizard and navigation.

The window owns the shared :class:`ServerSession` and injects it into every
step. It also triggers the silent update check shortly after start-up.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.config import AppConfig
from core.session import ServerSession
from core.updater import UpdateChecker, UpdateDownloader, launch_installer_and_exit
from translations import Translator
from ui.common import app_icon, make_logo_label
from ui.step_complete import CompleteStep
from ui.step_config import ConfigStep
from ui.step_directory import DirectoryStep
from ui.step_install import InstallStep
from ui.step_resources import ResourcesStep
from ui.step_version import VersionStep
from ui.step_welcome import WelcomeStep
from ui.theme import build_stylesheet
from ui.widgets.styled_combo import StyledComboBox
from version import APP_VERSION


class MainWindow(QMainWindow):
    """Top-level wizard window."""

    def __init__(self, config: AppConfig, translator: Translator) -> None:
        super().__init__()
        self.config = config
        self.tr_ = translator
        self.session = ServerSession()

        self.setWindowTitle(f"{self.t('app_name')}  v{APP_VERSION}  —  {self.t('publisher_by')}")
        self.setWindowIcon(app_icon())
        self.resize(960, 680)
        self.setMinimumSize(820, 600)

        self._build()
        self._apply_theme(self.config.theme)
        self._go_to(0)
        QTimer.singleShot(1200, self._check_for_updates)

    def t(self, key: str, **kwargs) -> str:
        return self.tr_.t(key, **kwargs)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        self._build_steps()
        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

        root.addWidget(self._build_nav_bar())

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.addWidget(make_logo_label(32))
        name = QLabel(self.t("app_name"))
        name.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(name)
        layout.addStretch(1)

        layout.addWidget(QLabel(self.t("theme_label")))
        self._theme_combo = StyledComboBox()
        self._theme_combo.addItem(self.t("theme_dark"), "dark")
        self._theme_combo.addItem(self.t("theme_light"), "light")
        index = self._theme_combo.findData(self.config.theme)
        self._theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_change)
        layout.addWidget(self._theme_combo)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Secondary")
        layout.addWidget(version)
        return bar

    def _build_sidebar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("SideBar")
        bar.setFixedWidth(190)
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(14)
        self._step_labels: list[QLabel] = []
        names = ("step_welcome", "step_version", "step_directory", "step_resources",
                 "step_config", "step_install", "step_complete")
        for index, key in enumerate(names, start=1):
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
        self.install.install_succeeded.connect(lambda _jar: self._go_to(6))
        self.complete.new_server_requested.connect(self._restart_wizard)
        self.complete.close_requested.connect(self.close)

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

    # ----------------------------------------------------------- navigation
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
        # Step 5 (config) -> Step 6 (install): the Next button reads "Start".
        self._go_to(self._current + 1)

    def _go_back(self) -> None:
        if self._current == 6:  # from complete, "back" restarts
            return
        self._go_to(self._current - 1)

    def _refresh_nav(self) -> None:
        step = self._steps[self._current]
        # Hide navigation entirely on install/complete steps.
        on_install = self._current == 5
        on_complete = self._current == 6
        self._back_btn.setVisible(not on_install and not on_complete and self._current > 0)
        self._next_btn.setVisible(not on_install and not on_complete)
        self._next_btn.setEnabled(step.can_advance())
        # The step before installation starts it; relabel the button.
        self._next_btn.setText(self.t("btn_start") if self._current == 4 else self.t("btn_next"))

    def _update_sidebar(self) -> None:
        for index, label in enumerate(self._step_labels):
            if index < self._current:
                label.setObjectName("StepDone")
                prefix = "✓"
            elif index == self._current:
                label.setObjectName("StepActive")
                prefix = "▶"
            else:
                label.setObjectName("StepPending")
                prefix = f"{index + 1}."
            names = ("step_welcome", "step_version", "step_directory", "step_resources",
                     "step_config", "step_install", "step_complete")
            label.setText(f"{prefix}  {self.t(names[index])}")
            label.style().unpolish(label)
            label.style().polish(label)

    def _restart_wizard(self) -> None:
        self.session.reset()
        self._go_to(0)

    # ----------------------------------------------------------------- theme
    def _on_theme_change(self) -> None:
        theme = self._theme_combo.currentData()
        self.config.set_theme(theme)
        self._apply_theme(theme)

    def _apply_theme(self, theme: str) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(theme))

    # ---------------------------------------------------------------- updates
    def _check_for_updates(self) -> None:
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._prompt_update)
        self._update_checker.start()

    def _prompt_update(self, version: str, url: str) -> None:
        answer = QMessageBox.question(
            self,
            self.t("update_title"),
            self.t("update_text", version=version, current=APP_VERSION),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._download_update(url)

    def _download_update(self, url: str) -> None:
        dialog = QProgressDialog(self.t("update_downloading"), self.t("btn_cancel"), 0, 100, self)
        dialog.setWindowTitle(self.t("update_title"))
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setAutoClose(False)

        downloader = UpdateDownloader(url, self)
        downloader.progress.connect(
            lambda d, t: dialog.setValue(int(d * 100 / t)) if t else None
        )
        downloader.failed.connect(lambda: self._update_failed(dialog))
        downloader.completed.connect(lambda path: self._update_ready(dialog, path))
        dialog.canceled.connect(downloader.terminate)
        downloader.start()
        dialog.exec()

    def _update_failed(self, dialog: QProgressDialog) -> None:
        dialog.close()
        QMessageBox.warning(self, self.t("warning_title"), self.t("update_failed"))

    def _update_ready(self, dialog: QProgressDialog, installer_path: str) -> None:
        dialog.close()
        QMessageBox.information(self, self.t("update_title"), self.t("update_ready"))
        launch_installer_and_exit(installer_path)

    # ------------------------------------------------------------------ close
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self.install.stop()
        super().closeEvent(event)
