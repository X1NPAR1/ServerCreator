"""
ServerCreator — application entry point.

Run with ``python main.py``. Bootstraps the Qt application, installs a global
exception handler (so an unexpected error shows a dialog and is logged instead
of silently terminating the process), performs the permanent first-launch
language selection, and shows the main application shell.
"""

from __future__ import annotations

import os
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.config import AppConfig
from translations import Translator
from ui.app_shell import AppShell
from ui.common import app_icon
from ui.language_selector import LanguageSelector
from ui.theme import build_stylesheet
from utils import app_data_dir
from version import APP_NAME


def _install_exception_hook() -> None:
    """
    Route uncaught exceptions to a dialog and a log file.

    PyQt6 terminates the process on an unhandled exception raised inside a slot.
    Capturing it here keeps the application alive and tells the user what went
    wrong instead of closing without explanation.
    """
    log_file = os.path.join(app_data_dir(), "error.log")

    def handler(exc_type, exc_value, exc_tb) -> None:
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except OSError:
            pass
        sys.stderr.write(text)
        try:
            QMessageBox.critical(
                None,
                "ServerCreator — Error",
                f"An unexpected error occurred:\n\n{exc_value}\n\n"
                f"Details were written to:\n{log_file}",
            )
        except Exception:  # noqa: BLE001 — never recurse out of the hook
            pass

    sys.excepthook = handler


def _set_windows_app_id() -> None:
    """Set an explicit AppUserModelID so Windows shows the bundled logo."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("X1NPAR1.ServerCreator")
    except Exception:  # noqa: BLE001 — cosmetic only
        pass


def main() -> int:
    """Construct and run the application; return the process exit code."""
    _set_windows_app_id()
    _install_exception_hook()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("X1NPAR1")
    app.setWindowIcon(app_icon())
    # The window hides to the tray on close; do not quit when it is hidden.
    app.setQuitOnLastWindowClosed(False)

    config = AppConfig()
    app.setStyleSheet(build_stylesheet(config.theme))

    # First-launch language selection. The choice is permanent.
    if not config.is_language_set():
        selector = LanguageSelector()
        selector.exec()
        config.set_language(selector.selected_language)

    translator = Translator(config.language)

    shell = AppShell(config, translator)
    shell.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
