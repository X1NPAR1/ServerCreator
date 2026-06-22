"""Step 5 — server.properties configuration questions."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from ui.base_step import BaseStep
from ui.common import card, title_label
from ui.widgets.styled_combo import StyledComboBox

_GAMEMODES = ("survival", "creative", "adventure", "spectator")


class ConfigStep(BaseStep):
    """Collects the gameplay options written to ``server.properties``."""

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        layout.addWidget(title_label(self.t("cfg_title")))

        panel = card()
        form = QFormLayout(panel)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        self._online = QCheckBox()
        self._online.setChecked(True)
        form.addRow(self.t("cfg_online"), self._online)

        self._max_players = QSpinBox()
        self._max_players.setRange(1, 1000)
        self._max_players.setValue(20)
        form.addRow(self.t("cfg_max_players"), self._max_players)

        self._gamemode = StyledComboBox()
        for mode in _GAMEMODES:
            self._gamemode.addItem(self.t(f"gm_{mode}"), mode)
        form.addRow(self.t("cfg_gamemode"), self._gamemode)

        self._hardcore = QCheckBox()
        form.addRow(self.t("cfg_hardcore"), self._hardcore)

        self._whitelist = QCheckBox()
        form.addRow(self.t("cfg_whitelist"), self._whitelist)

        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(25565)
        form.addRow(self.t("cfg_port"), self._port)

        self._pvp = QCheckBox()
        self._pvp.setChecked(True)
        form.addRow(self.t("cfg_pvp"), self._pvp)

        self._nether = QCheckBox()
        self._nether.setChecked(True)
        form.addRow(self.t("cfg_nether"), self._nether)

        self._seed = QLineEdit()
        form.addRow(self.t("cfg_seed"), self._seed)

        layout.addWidget(panel)
        layout.addStretch(1)

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        self._online.setChecked(self.session.online_mode)
        self._max_players.setValue(self.session.max_players)
        index = self._gamemode.findData(self.session.gamemode)
        self._gamemode.setCurrentIndex(index if index >= 0 else 0)
        self._hardcore.setChecked(self.session.hardcore)
        self._whitelist.setChecked(self.session.whitelist)
        self._port.setValue(self.session.server_port)
        self._pvp.setChecked(self.session.pvp)
        self._nether.setChecked(self.session.allow_nether)
        self._seed.setText(self.session.level_seed)

    def commit(self) -> None:
        self.session.online_mode = self._online.isChecked()
        self.session.max_players = self._max_players.value()
        self.session.gamemode = self._gamemode.currentData()
        self.session.hardcore = self._hardcore.isChecked()
        self.session.whitelist = self._whitelist.isChecked()
        self.session.server_port = self._port.value()
        self.session.pvp = self._pvp.isChecked()
        self.session.allow_nether = self._nether.isChecked()
        self.session.level_seed = self._seed.text().strip()
