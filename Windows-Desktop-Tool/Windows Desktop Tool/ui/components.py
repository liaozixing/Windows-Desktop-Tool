from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty, QPointF, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QPainterPath


class GaugeWidget(QWidget):
    """ 仪表盘控件 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._value = 0.0
        self._max_value = 100.0
        self.unit = "Mbps"
        self.title = "速度"
        self.is_dark = False

        # 默认颜色设置
        self.accent_color = QColor(22, 119, 255)
        self.needle_color = QColor(22, 119, 255)
        self._update_colors()

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        self.setMinimumSize(220, 220)

    def _update_colors(self):
        """ 根据主题更新颜色配置 """
        if self.is_dark:
            self.text_color = QColor(224, 224, 224)    # #e0e0e0
            self.subtext_color = QColor(160, 160, 160) # #a0a0a0
            self.ring_bg_color = QColor(51, 51, 51)    # #333333
            self.tick_color = QColor(77, 77, 77)       # #4d4d4d
            self.center_bg = QColor(43, 43, 43)        # #2b2b2b
        else:
            self.text_color = QColor(51, 51, 51)
            self.subtext_color = QColor(102, 102, 102)
            self.ring_bg_color = QColor(229, 233, 242)
            self.tick_color = QColor(189, 195, 206)
            self.center_bg = QColor(245, 247, 250)

    def set_dark_mode(self, is_dark):
        """ 设置深色模式 """
        self.is_dark = is_dark
        self._update_colors()
        self.update()

    @pyqtProperty(float)
    def value(self):
        """ 获取当前数值 """
        return float(self._value)

    @value.setter
    def value(self, v):
        """ 设置当前数值并重绘 """
        self._value = float(v)
        self.update()

    def set_value(self, v, animated=True):
        """ 设置数值，支持动画过渡 """
        v = float(v)
        if animated:
            self.animation.stop()
            self.animation.setStartValue(float(self._value))
            self.animation.setEndValue(v)
            self.animation.start()
        else:
            self.value = v

    def set_max_value(self, max_v):
        """ 设置最大量程 """
        self._max_value = float(max_v)
        self.update()

    def set_accent_color(self, color):
        """ 设置主题强调色 """
        if isinstance(color, str):
            color = QColor(color)
        self.accent_color = color
        self.needle_color = color
        self.update()

    def paintEvent(self, event):
        """ 绘图事件：绘制仪表盘各组件 """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)

        # 平移并缩放坐标系以适应控件大小
        painter.translate(w / 2, h / 2)
        painter.scale(side / 220, side / 220)

        self._draw_gauge(painter)  # 绘制刻度盘
        self._draw_needle(painter) # 绘制指针
        self._draw_text(painter)   # 绘制中心文字

    def _draw_gauge(self, painter):
        """ 绘制圆环、进度条及刻度 """
        rect = QRectF(-90, -90, 180, 180)

        start_deg = 225.0
        span_deg = 270.0

        # 绘制背景圆环
        bg_pen = QPen(self.ring_bg_color, 12)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, int(start_deg * 16), int(-span_deg * 16))

        # 计算并绘制进度圆环
        progress = 0.0
        if self._max_value > 0:
            progress = min(max(self._value / self._max_value, 0.0), 1.0)

        if progress > 0:
            progress_pen = QPen()
            progress_pen.setWidth(12)
            progress_pen.setCapStyle(Qt.RoundCap)
            progress_pen.setColor(self.accent_color)
            painter.setPen(progress_pen)
            painter.drawArc(rect, int(start_deg * 16), int(-(progress * span_deg) * 16))

        # 绘制刻度线
        painter.setPen(QPen(self.tick_color, 1))
        for i in range(51):
            angle = start_deg - (i * (span_deg / 50))
            major = (i % 5 == 0)
            painter.save()
            painter.rotate(-angle)
            painter.setPen(QPen(self.tick_color, 2 if major else 1))
            painter.drawLine(0, -90, 0, -78 if major else -84)
            painter.restore()

        # 绘制刻度数值
        for i in range(11):
            angle = start_deg - (i * (span_deg / 10))
            val = int(i * (self._max_value / 10))
            painter.save()
            painter.rotate(-angle)
            painter.translate(0, -58)
            painter.rotate(angle)
            painter.setPen(QPen(self.subtext_color))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(-18, -10, 36, 20), Qt.AlignCenter, str(val))
            painter.restore()

    def _draw_needle(self, painter):
        """ 绘制动态指针 """
        painter.save()
        progress = 0.0
        if self._max_value > 0:
            progress = min(max(self._value / self._max_value, 0.0), 1.0)
        start_deg = 225.0
        span_deg = 270.0
        angle = start_deg - (progress * span_deg)
        painter.rotate(-angle)

        # 绘制指针形状
        needle = QPolygonF([QPointF(-4, 0), QPointF(4, 0), QPointF(0, -78)])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.needle_color.red(), self.needle_color.green(), self.needle_color.blue(), 220))
        painter.drawPolygon(needle)

        # 绘制中心圆点装饰
        painter.setBrush(self.center_bg)
        painter.drawEllipse(QRectF(-11, -11, 22, 22))
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(QRectF(-6, -6, 12, 12))
        painter.restore()

    def _draw_text(self, painter):
        """ 绘制数值、单位及标题 """
        painter.save()
        painter.setPen(self.text_color)
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(QRectF(-90, -10, 180, 42), Qt.AlignCenter, f"{self._value:.1f}")

        painter.setPen(self.subtext_color)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(QRectF(-70, 30, 140, 22), Qt.AlignCenter, self.unit)

        painter.setPen(self.text_color)
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(QRectF(-90, 54, 180, 26), Qt.AlignCenter, self.title)
        painter.restore()


class LineChartWidget(QWidget):
    """ 线性图表控件 """
    def __init__(self, parent=None, accent=None):
        super().__init__(parent=parent)
        self._values = []
        self.max_points = 90
        self.accent = accent or QColor(22, 119, 255)
        self.fill_alpha = 40
        self.is_dark = False
        self._update_colors()
        self.setMinimumHeight(100)

    def _update_colors(self):
        """ 更新网格及背景颜色 """
        if self.is_dark:
            self.grid_color = QColor(51, 51, 51)      # #333333
            self.bg_color = QColor(0, 0, 0, 0)
        else:
            self.grid_color = QColor(235, 238, 245)
            self.bg_color = QColor(255, 255, 255, 0)

    def set_dark_mode(self, is_dark):
        """ 设置深色模式 """
        self.is_dark = is_dark
        self._update_colors()
        self.update()

    def set_accent_color(self, color):
        """ 设置图表线条颜色 """
        if isinstance(color, str):
            color = QColor(color)
        self.accent = color
        self.update()

    def clear(self):
        """ 清空图表数据 """
        self._values = []
        self.update()

    def add_value(self, v):
        """ 添加新的数据点并更新界面 """
        self._values.append(float(v))
        if len(self._values) > self.max_points:
            self._values = self._values[-self.max_points:]
        self.update()

    def paintEvent(self, event):
        """ 绘图事件：绘制网格、曲线及填充区域 """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, self.bg_color)

        # 绘制背景网格线
        painter.setPen(QPen(self.grid_color, 1))
        for i in range(1, 9):
            x = int(w * i / 9)
            painter.drawLine(x, 0, x, h)
        for i in range(1, 5):
            y = int(h * i / 5)
            painter.drawLine(0, y, w, y)

        if len(self._values) < 2:
            return

        max_v = max(self._values)
        max_v = max(max_v, 1.0)

        # 计算所有数据点的坐标
        points = []
        for idx, v in enumerate(self._values):
            x = int(idx * (w - 1) / max(len(self._values) - 1, 1))
            y = int(h - 1 - (v / max_v) * (h - 6))
            points.append(QPointF(x, y))

        path = QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            path.lineTo(points[1])
        else:
            # 使用 Catmull-Rom 样条曲线算法生成平滑曲线
            # 这种算法保证曲线经过所有数据点，不会出现"扭扭"或偏离的问题
            tension = 0.25  # 张力系数，0.2-0.3 效果较好
            
            for i in range(len(points) - 1):
                p0 = points[i-1] if i > 0 else points[i]
                p1 = points[i]
                p2 = points[i+1]
                p3 = points[i+2] if i < len(points) - 2 else points[i+1]
                
                # 计算控制点
                cp1_x = p1.x() + (p2.x() - p0.x()) * tension
                cp1_y = p1.y() + (p2.y() - p0.y()) * tension
                
                cp2_x = p2.x() - (p3.x() - p1.x()) * tension
                cp2_y = p2.y() - (p3.y() - p1.y()) * tension
                
                path.cubicTo(QPointF(cp1_x, cp1_y), QPointF(cp2_x, cp2_y), p2)

        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), h)
        fill_path.lineTo(points[0].x(), h)
        fill_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), self.fill_alpha))
        painter.drawPath(fill_path)

        painter.setPen(QPen(self.accent, 2))
        painter.drawPath(path)


class CircleStartButton(QPushButton):
    """ 圆形启动按钮控件 """
    def set_accent_color(self, color):
        """ 动态设置按钮强调色及其悬停/按下状态 """
        if isinstance(color, QColor):
            color_name = color.name()
        else:
            color_name = str(color)
            color = QColor(color_name)
            
        # 衍生出悬停和按下的颜色深度
        hover = color.lighter(110).name()
        pressed = color.darker(110).name()
        
        self.setStyleSheet(f"""
            QPushButton{{
                background-color: {color_name};
                border: none;
                border-radius: 70px;
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover{{ background-color: {hover}; }}
            QPushButton:pressed{{ background-color: {pressed}; }}
            QPushButton:disabled{{ 
                background-color: rgba(128, 128, 128, 0.15); 
                color: rgba(128, 128, 128, 0.4); 
            }}
        """)

    def __init__(self, text="开始测速", parent=None):
        super().__init__(text, parent=parent)
        self.setFixedSize(140, 140)
        self.setCursor(Qt.PointingHandCursor)
        # 初始默认样式（渐变色）
        self.setStyleSheet(
            "QPushButton{"
            "background-color:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1677ff, stop:1 #4096ff);"
            "border:none;"
            "border-radius:70px;"
            "color:#ffffff;"
            "font-size:16px;"
            "font-weight:700;"
            "}"
            "QPushButton:hover{background-color:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4096ff, stop:1 #69b1ff);}"
            "QPushButton:pressed{background-color:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0958d9, stop:1 #1677ff);}"
            "QPushButton:disabled{background-color:#e6f4ff;color:rgba(0,0,0,0.25);}"
        )
