"""A colour-coded, auto-scrolling log viewer."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QPlainTextEdit

from ui.theme import status_color


class LogViewer(QPlainTextEdit):
    """
    Read-only log widget with per-line colouring and smart auto-scroll.

    Auto-scroll follows new output only while the user is already at the bottom;
    if the user scrolls up to read earlier lines, appending no longer yanks the
    viewport back down.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LogViewer")
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)

    def append_line(self, level: str, message: str) -> None:
        """Append ``message`` coloured according to ``level``."""
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 4

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MovePosition.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(status_color(level)))
        cursor.insertText(f"[{level}] {message}\n", fmt)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def plain_text(self) -> str:
        """Return the full log content as plain text."""
        return self.toPlainText()
