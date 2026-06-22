"""Step 1 — welcome and platform selection."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.version_manager import PLATFORMS, RECOMMENDED_PLATFORMS
from ui.base_step import BaseStep
from ui.common import subtitle_label, title_label

_PLATFORM_LABELS = {
    "vanilla": "Vanilla",
    "paper": "Paper",
    "purpur": "Purpur",
    "spigot": "Spigot",
    "craftbukkit": "CraftBukkit",
    "fabric": "Fabric",
    "forge": "Forge",
    "neoforge": "NeoForge",
}


class WelcomeStep(BaseStep):
    """Lets the user pick a server platform from a grid of cards."""

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._buttons = QButtonGroup(self)
        self._buttons.setExclusive(True)
        self._buttons.buttonClicked.connect(lambda _b: self.validity_changed.emit())
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(title_label(self.t("welcome_title")))
        header.addStretch(1)
        help_btn = QPushButton(self.t("welcome_help"))
        help_btn.setObjectName("Link")
        help_btn.clicked.connect(self._show_help)
        header.addWidget(help_btn)
        layout.addLayout(header)

        layout.addWidget(subtitle_label(self.t("app_tagline")))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 8, 0, 0)

        for index, platform in enumerate(PLATFORMS):
            card = self._make_card(platform)
            self._buttons.addButton(card)
            grid.addWidget(card, index // 2, index % 2)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def _make_card(self, platform: str) -> QPushButton:
        recommended = platform in RECOMMENDED_PLATFORMS
        name = _PLATFORM_LABELS.get(platform, platform.title())
        badge = f"   ★ {self.t('platform_recommended')}" if recommended else ""
        description = self.t(f"platform_{platform}_desc")
        card = QPushButton()
        card.setObjectName("PlatformCard")
        card.setCheckable(True)
        card.setProperty("platform", platform)
        card.setMinimumHeight(96)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 12, 14, 12)
        heading = QLabel(f"{name}{badge}")
        heading.setObjectName("Accent" if recommended else "StepDone")
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        desc = QLabel(description)
        desc.setObjectName("Secondary")
        desc.setWordWrap(True)
        inner.addWidget(heading)
        inner.addWidget(desc)
        return card

    def _show_help(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(self.t("info_title"))
        box.setText(self.t("platform_help_text"))
        box.exec()

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        if self.session.platform:
            for button in self._buttons.buttons():
                if button.property("platform") == self.session.platform:
                    button.setChecked(True)
        self.validity_changed.emit()

    def can_advance(self) -> bool:
        return self._buttons.checkedButton() is not None

    def commit(self) -> None:
        button = self._buttons.checkedButton()
        if button is not None:
            self.session.platform = button.property("platform")
