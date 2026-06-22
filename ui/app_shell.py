"""
Top-level application shell.

Provides the persistent chrome (logo, theme switch, version), a left navigation
rail with "Create Server" and "My Servers", and routes between the creation
wizard and the server manager. Also hosts the tray icon, the silent update
check and the safe-quit logic that warns when servers are still running.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from core.config import AppConfig
from core.server_registry import ServerRecord, ServerRegistry
from core.server_runtime import RuntimeManager
from core.updater import UpdateChecker, UpdateDownloader, launch_installer_and_exit
from translations import Translator
from ui.common import app_icon, make_logo_label
from ui.create_wizard import CreateWizard
from ui.servers_view import ServersView
from ui.theme import build_stylesheet
from ui.widgets.styled_combo import StyledComboBox
from version import APP_VERSION

_PAGE_CREATE = 0
_PAGE_SERVERS = 1


class AppShell(QMainWindow):
    """The single main window hosting the whole application."""

    def __init__(self, config: AppConfig, translator: Translator) -> None:
        super().__init__()
        self.config = config
        self.tr_ = translator
        self.registry = ServerRegistry()
        self.registry.prune_missing()
        self.runtimes = RuntimeManager(self)
        self._force_quit = False
        self._tray_hint_shown = False

        self.setWindowTitle(f"{self.t('app_name')}  v{APP_VERSION}  —  {self.t('publisher_by')}")
        self.setWindowIcon(app_icon())
        # Larger, fixed-size window: cannot be maximised, layout stays intact.
        self.setFixedSize(1180, 820)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self._build()
        self._apply_theme(self.config.theme)
        self._setup_tray()
        self._route_initial()
        QTimer.singleShot(1500, self._check_for_updates)

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
        body.addWidget(self._build_nav_rail())

        self._stack = QStackedWidget()
        self.wizard = CreateWizard(self.tr_)
        self.servers = ServersView(self.registry, self.runtimes, self.tr_)
        self._stack.addWidget(self.wizard)     # index 0
        self._stack.addWidget(self.servers)    # index 1
        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

        self.wizard.server_created.connect(self._on_server_created)
        self.wizard.manage_requested.connect(lambda: self._navigate(_PAGE_SERVERS))
        self.servers.create_requested.connect(lambda: self._navigate(_PAGE_CREATE, reset=True))
        self.servers.became_empty.connect(lambda: self._navigate(_PAGE_CREATE, reset=True))

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(58)
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
        idx = self._theme_combo.findData(self.config.theme)
        self._theme_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_change)
        layout.addWidget(self._theme_combo)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Secondary")
        layout.addWidget(version)
        return bar

    def _build_nav_rail(self) -> QFrame:
        rail = QFrame()
        rail.setObjectName("NavRail")
        rail.setFixedWidth(210)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_create = self._nav_item("＋  " + self.t("nav_create"))
        self._nav_servers = self._nav_item("🖥  " + self.t("nav_servers"))
        self._nav_create.clicked.connect(lambda: self._navigate(_PAGE_CREATE, reset=True))
        self._nav_servers.clicked.connect(lambda: self._navigate(_PAGE_SERVERS))
        layout.addWidget(self._nav_create)
        layout.addWidget(self._nav_servers)
        layout.addStretch(1)
        return rail

    def _nav_item(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("NavItem")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._nav_group.addButton(button)
        return button

    # ------------------------------------------------------------------ route
    def _route_initial(self) -> None:
        if self.registry.count() == 0:
            self._navigate(_PAGE_CREATE, reset=True)
        else:
            self._navigate(_PAGE_SERVERS)

    def _navigate(self, page: int, reset: bool = False) -> None:
        # With no servers the manager is unavailable; always steer to creation.
        if page == _PAGE_SERVERS and self.registry.count() == 0:
            page = _PAGE_CREATE
            reset = True
        self._nav_servers.setEnabled(self.registry.count() > 0)
        if page == _PAGE_CREATE:
            if reset:
                self.wizard.reset()
            self._nav_create.setChecked(True)
            self._stack.setCurrentIndex(_PAGE_CREATE)
        else:
            self.servers.refresh()
            self._nav_servers.setChecked(True)
            self._stack.setCurrentIndex(_PAGE_SERVERS)

    def _on_server_created(self, record: ServerRecord) -> None:
        self.registry.add(record)
        self._nav_servers.setEnabled(True)
        # Take the user straight to the new server's console and start it
        # automatically; they can stop it or leave it running from there.
        self._navigate(_PAGE_SERVERS)
        self.servers.open_detail(record, auto_start=True)

    # ------------------------------------------------------------------ theme
    def _on_theme_change(self) -> None:
        theme = self._theme_combo.currentData()
        self.config.set_theme(theme)
        self._apply_theme(theme)

    def _apply_theme(self, theme: str) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(theme))

    # ------------------------------------------------------------------- tray
    def _setup_tray(self) -> None:
        self._tray = QSystemTrayIcon(app_icon(), self)
        self._tray.setToolTip(f"{self.t('app_name')} v{APP_VERSION}")
        menu = QMenu()
        show_action = QAction(self.t("tray_show"), self)
        show_action.triggered.connect(self._restore_window)
        quit_action = QAction(self.t("tray_quit"), self)
        quit_action.triggered.connect(self._quit_requested)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_window()

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---------------------------------------------------------------- updates
    def _check_for_updates(self) -> None:
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._prompt_update)
        self._update_checker.start()

    def _prompt_update(self, version: str, url: str) -> None:
        answer = QMessageBox.question(
            self, self.t("update_title"),
            self.t("update_text", version=version, current=APP_VERSION),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._download_update(url)

    def _download_update(self, url: str) -> None:
        dialog = QProgressDialog(self.t("update_downloading"), self.t("btn_cancel"), 0, 100, self)
        dialog.setWindowTitle(self.t("update_title"))
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setAutoClose(False)
        downloader = UpdateDownloader(url, self)
        downloader.progress.connect(lambda d, t: dialog.setValue(int(d * 100 / t)) if t else None)
        downloader.failed.connect(lambda: (dialog.close(), QMessageBox.warning(
            self, self.t("warning_title"), self.t("update_failed"))))
        downloader.completed.connect(lambda path: self._update_ready(dialog, path))
        dialog.canceled.connect(downloader.terminate)
        downloader.start()
        dialog.exec()

    def _update_ready(self, dialog: QProgressDialog, installer_path: str) -> None:
        # The update installs silently in the background and relaunches the app
        # automatically when finished, so no further confirmation is required.
        dialog.close()
        self.runtimes.stop_all()
        self._force_quit = True
        self._tray.hide()
        launch_installer_and_exit(installer_path)

    # ----------------------------------------------------------------- quit
    def _quit_requested(self) -> None:
        """Quit from the tray: warn if servers are running, then stop them."""
        if not self._confirm_stop_running():
            return
        self._force_quit = True
        self.runtimes.stop_all()
        self.wizard.stop_workers()
        self._tray.hide()
        QApplication.instance().quit()

    def _confirm_stop_running(self) -> bool:
        running = self.runtimes.running()
        if not running:
            return True
        names = "\n".join(f"  • {r.record.name}" for r in running)
        answer = QMessageBox.question(
            self, self.t("close_running_title"),
            self.t("close_running_text", servers=names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # The window's close button minimises to the tray so servers keep
        # running in the background. Real exit happens through the tray's Quit.
        if self._force_quit:
            self.runtimes.stop_all()
            self.wizard.stop_workers()
            self._tray.hide()
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()
        if not self._tray_hint_shown and QSystemTrayIcon.supportsMessages():
            self._tray.showMessage(
                self.t("app_name"), self.t("tray_running_bg"),
                QSystemTrayIcon.MessageIcon.Information, 4000,
            )
            self._tray_hint_shown = True
