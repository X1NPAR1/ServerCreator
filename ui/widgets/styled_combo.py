"""A combo box pre-configured for the application's look and feel."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox


class StyledComboBox(QComboBox):
    """
    A :class:`QComboBox` that disables the mouse wheel from changing the
    selection (which is a common source of accidental edits) while remaining
    keyboard accessible.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(34)

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        event.ignore()
