"""Base class shared by every wizard step."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from core.session import ServerSession
from translations import Translator


class BaseStep(QWidget):
    """
    Common contract for wizard steps.

    Subclasses populate their widgets in :meth:`on_enter`, validate input via
    :meth:`can_advance`, and persist their values into the shared session in
    :meth:`commit`. They emit :data:`validity_changed` whenever the value of
    :meth:`can_advance` may have changed so the navigation bar can enable or
    disable the *Next* button.
    """

    validity_changed = pyqtSignal()

    def __init__(self, session: ServerSession, translator: Translator, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.tr_ = translator

    def t(self, key: str, **kwargs) -> str:
        """Shortcut to the translator."""
        return self.tr_.t(key, **kwargs)

    # -- lifecycle hooks (overridden as needed) ----------------------------- #
    def on_enter(self) -> None:
        """Called every time the step becomes visible."""

    def commit(self) -> None:
        """Persist the step's widget values into the shared session."""

    def can_advance(self) -> bool:
        """Return whether the wizard may advance past this step."""
        return True
