"""
First-launch language selection dialog.

Shown only once, before any other window. The chosen language is persisted and,
per the product requirement, becomes permanent — there is deliberately no way to
change it afterwards from within the application.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from translations import DEFAULT_LANGUAGE, LANGUAGE_NAMES, SUPPORTED_LANGUAGES, Translator
from ui.common import app_icon, make_logo_label


class LanguageSelector(QDialog):
    """Modal dialog returning the selected language code."""

    # Bilingual labels (the user has no language context yet).
    _TITLE = "Choose your language  /  Dilinizi seçin"
    _SUBTITLE = (
        "This selection is permanent and cannot be changed later.\n"
        "Bu seçim kalıcıdır ve sonradan değiştirilemez."
    )
    _CONFIRM = "Confirm  /  Onayla"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.selected_language = DEFAULT_LANGUAGE
        self.setWindowTitle("ServerCreator")
        self.setWindowIcon(app_icon())
        self.setModal(True)
        self.setFixedSize(440, 360)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        logo = make_logo_label(64)
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(self._TITLE)
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(self._SUBTITLE)
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        self._group = QButtonGroup(self)
        for code in SUPPORTED_LANGUAGES:
            radio = QRadioButton(LANGUAGE_NAMES.get(code, code))
            radio.setProperty("lang_code", code)
            if code == DEFAULT_LANGUAGE:
                radio.setChecked(True)
            self._group.addButton(radio)
            layout.addWidget(radio, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)

        confirm = QPushButton(self._CONFIRM)
        confirm.setObjectName("Primary")
        confirm.clicked.connect(self._confirm)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(confirm)
        row.addStretch(1)
        layout.addLayout(row)

    def _confirm(self) -> None:
        checked = self._group.checkedButton()
        if checked is not None:
            self.selected_language = checked.property("lang_code") or DEFAULT_LANGUAGE
        self.accept()
