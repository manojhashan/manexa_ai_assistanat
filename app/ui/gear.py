"""Small native gear; remains available even when WebGL fails."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton


class SettingsGear(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 42)
        self.setAccessibleName("Open MANEXA settings")
        self.setToolTip("Settings · Ctrl+,")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(60)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        if self.isVisible() and self.window().isActiveWindow():
            self._angle = (self._angle + (1.1 if self.underMouse() else 0.12)) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(21, 21)
        hover = self.underMouse() or self.hasFocus()
        if hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(32, 148, 184, 20))
            painter.drawEllipse(QRectF(-20, -20, 40, 40))
        painter.rotate(self._angle)
        path = QPainterPath()
        for i in range(64):
            angle = i / 64 * math.tau
            radius = 10.8 if i % 8 in (2, 3, 4, 5) else 8.8
            point = QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
            if i == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        painter.setPen(QPen(QColor("#6cdff7" if hover else "#395f72"), 1.1))
        painter.setBrush(QColor(2, 5, 11, 150))
        painter.drawPath(path)
        painter.drawEllipse(QRectF(-3.6, -3.6, 7.2, 7.2))
