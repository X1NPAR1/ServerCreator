"""Small UI factory helpers shared across the wizard steps."""

from __future__ import annotations

import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel

from utils import logo_path


def make_logo_label(size: int) -> QLabel:
    """
    Return a :class:`QLabel` showing the application logo at ``size`` px.

    If the logo file is missing, an empty (but correctly sized) label is
    returned so layouts remain stable — per the requirement that a missing
    logo must never raise.
    """
    label = QLabel()
    label.setFixedSize(QSize(size, size))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    path = logo_path()
    if os.path.exists(path):
        pixmap = QIcon(path).pixmap(QSize(size, size))
        if not pixmap.isNull():
            label.setPixmap(pixmap)
    return label


def app_icon() -> QIcon:
    """Return the application icon, or an empty icon if the file is missing."""
    path = logo_path()
    return QIcon(path) if os.path.exists(path) else QIcon()


def title_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Title")
    label.setWordWrap(True)
    return label


def subtitle_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Subtitle")
    label.setWordWrap(True)
    return label


def card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    return frame


def horizontal_divider() -> QFrame:
    line = QFrame()
    line.setObjectName("Divider")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line
