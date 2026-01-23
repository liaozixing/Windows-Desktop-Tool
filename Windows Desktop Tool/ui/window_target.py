from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget


class HighlightWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.border_color = QColor("#1677ff")
        self.hide()

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.border_color, 4)
        painter.setPen(pen)
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)

    def show_highlight(self, rect, color):
        if not rect:
            self.hide()
            return
        self.border_color = QColor(color)
        x, y, w, h = rect
        self.setGeometry(x, y, w, h)
        self.show()
        self.update()


class GhostTarget(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(64, 64)
        self.accent_color = "#1677ff"

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(0.7)

        color = QColor(self.accent_color)
        painter.setPen(QPen(color, 3))

        painter.drawEllipse(10, 10, 44, 44)
        painter.drawEllipse(22, 22, 20, 20)
        painter.drawLine(32, 5, 32, 20)
        painter.drawLine(32, 44, 32, 59)
        painter.drawLine(5, 32, 20, 32)
        painter.drawLine(44, 32, 59, 32)
        painter.setBrush(color)
        painter.drawEllipse(30, 30, 4, 4)


class TargetWidget(QWidget):
    targetReleased = pyqtSignal(int, int)
    targetHovered = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.is_dragging = False
        self.setCursor(Qt.PointingHandCursor)
        self.ghost = None

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(self.parent().accent_color if hasattr(self.parent(), 'accent_color') else "#1677ff")
        painter.setPen(QPen(color, 3))

        painter.drawEllipse(10, 10, 44, 44)
        painter.drawEllipse(22, 22, 20, 20)
        painter.drawLine(32, 5, 32, 20)
        painter.drawLine(32, 44, 32, 59)
        painter.drawLine(5, 32, 20, 32)
        painter.drawLine(44, 32, 59, 32)
        painter.setBrush(color)
        painter.drawEllipse(30, 30, 4, 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.setCursor(Qt.BlankCursor)

            if not self.ghost:
                self.ghost = GhostTarget()
            self.ghost.accent_color = self.parent().accent_color

            global_pos = event.globalPos()
            self.ghost.move(global_pos.x() - 32, global_pos.y() - 32)
            self.ghost.show()

            self.grabMouse()

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.ghost:
            global_pos = event.globalPos()
            self.ghost.move(global_pos.x() - 32, global_pos.y() - 32)
            self.targetHovered.emit(global_pos.x(), global_pos.y())

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.releaseMouse()
            self.setCursor(Qt.PointingHandCursor)

            if self.ghost:
                self.ghost.hide()

            global_pos = event.globalPos()
            self.targetReleased.emit(global_pos.x(), global_pos.y())
