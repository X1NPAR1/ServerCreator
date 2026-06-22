"""
ServerCreator — application entry point.

Run with ``python main.py``. Bootstraps the Qt application, applies the saved
theme, performs first-launch language selection (permanent) and shows the main
wizard window.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from core.config import AppConfig
from translations import Translator
from ui.common import app_icon
from ui.language_selector import LanguageSelector
from ui.main_window import MainWindow
from ui.theme import build_stylesheet
from version import APP_NAME


def _set_windows_app_id() -> None:
    """
    Set an explicit AppUserModelID so Windows shows the bundled logo on the
    taskbar instead of the generic Python icon. No-op on other platforms.
    """
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("X1NPAR1.ServerCreator")
    except Exception:  # noqa: BLE001 — cosmetic only, never fatal
        pass


def main() -> int:
    """Construct and run the application; return the process exit code."""
    _set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("X1NPAR1")
    app.setWindowIcon(app_icon())

    config = AppConfig()
    app.setStyleSheet(build_stylesheet(config.theme))

    # First-launch language selection. The choice is permanent.
    if not config.is_language_set():
        selector = LanguageSelector()
        selector.exec()
        config.set_language(selector.selected_language)

    translator = Translator(config.language)

    window = MainWindow(config, translator)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
