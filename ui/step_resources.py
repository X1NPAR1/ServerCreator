"""Step 4 — RAM and performance settings."""

from __future__ import annotations

import os

import psutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from ui.base_step import BaseStep
from ui.common import card, title_label
from utils import human_readable_size

_MIN_MB = 512


class ResourcesStep(BaseStep):
    """RAM allocation sliders plus JVM-flag and start-script options."""

    def __init__(self, session, translator, parent=None) -> None:
        super().__init__(session, translator, parent)
        total = psutil.virtual_memory().total
        self._total_mb = max(_MIN_MB, total // (1024 * 1024))
        self._max_allowed = max(_MIN_MB, int(self._total_mb * 0.8))
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        layout.addWidget(title_label(self.t("res_title")))

        info = QLabel(
            f"{self.t('res_total_ram', ram=human_readable_size(self._total_mb * 1024 * 1024))}    "
            f"{self.t('res_cores', cores=os.cpu_count() or psutil.cpu_count() or 1)}"
        )
        info.setObjectName("Secondary")
        layout.addWidget(info)

        panel = card()
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(14)

        self._xmx_slider, self._xmx_spin = self._ram_row(
            inner, self.t("res_xmx"), int(self._total_mb * 0.5)
        )
        self._xms_slider, self._xms_spin = self._ram_row(
            inner, self.t("res_xms"), int(self._total_mb * 0.5)
        )
        # Keep Xms <= Xmx automatically.
        self._xmx_spin.valueChanged.connect(self._sync_xms_ceiling)

        self._aikar = QCheckBox(self.t("res_aikar"))
        self._aikar.setChecked(True)
        inner.addWidget(self._aikar)

        self._script = QCheckBox(self.t("res_script"))
        self._script.setChecked(True)
        inner.addWidget(self._script)

        layout.addWidget(panel)
        layout.addStretch(1)

    def _ram_row(self, parent_layout, label_text: str, default: int):
        parent_layout.addWidget(QLabel(label_text))
        row = QHBoxLayout()
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(_MIN_MB, self._max_allowed)
        spin = QSpinBox()
        spin.setRange(_MIN_MB, self._max_allowed)
        spin.setSuffix(" MB")
        spin.setSingleStep(256)
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        value = min(self._max_allowed, max(_MIN_MB, default))
        spin.setValue(value)
        slider.setValue(value)
        row.addWidget(slider, 1)
        row.addWidget(spin)
        parent_layout.addLayout(row)
        return slider, spin

    def _sync_xms_ceiling(self, xmx_value: int) -> None:
        self._xms_spin.setMaximum(xmx_value)
        self._xms_slider.setMaximum(xmx_value)

    # -- BaseStep ----------------------------------------------------------- #
    def on_enter(self) -> None:
        if self.session.xmx_mb:
            self._xmx_spin.setValue(min(self._max_allowed, max(_MIN_MB, self.session.xmx_mb)))
        if self.session.xms_mb:
            self._xms_spin.setValue(min(self._xmx_spin.value(), max(_MIN_MB, self.session.xms_mb)))
        self._aikar.setChecked(self.session.use_aikar_flags)
        self._script.setChecked(self.session.generate_start_script)

    def commit(self) -> None:
        self.session.xmx_mb = self._xmx_spin.value()
        self.session.xms_mb = min(self._xms_spin.value(), self._xmx_spin.value())
        self.session.use_aikar_flags = self._aikar.isChecked()
        self.session.generate_start_script = self._script.isChecked()
