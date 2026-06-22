"""A progress bar that animates value changes smoothly."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QProgressBar


class AnimatedProgressBar(QProgressBar):
    """A :class:`QProgressBar` whose value transitions are animated."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self._animation = QPropertyAnimation(self, b"value", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def animate_to(self, target: int) -> None:
        """Animate the bar smoothly to ``target`` (0–100)."""
        target = max(0, min(100, int(target)))
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(target)
        self._animation.start()
