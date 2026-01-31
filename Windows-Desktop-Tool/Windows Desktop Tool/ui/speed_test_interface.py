from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout
from PyQt5.QtCore import QPropertyAnimation, QTimer
from PyQt5.QtGui import QColor
from qfluentwidgets import (StrongBodyLabel, BodyLabel, CaptionLabel, ComboBox,
                            DisplayLabel, TransparentToolButton, FluentIcon as FIF)

from ui.components import GaugeWidget, LineChartWidget, CircleStartButton

class SpeedTestInterface(QWidget):
    """ 网速测试界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SpeedTestInterface")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.left_panel = QWidget(self)
        self.left_panel.setFixedWidth(280)
        layout.addWidget(self.left_panel)

        self.right_panel = QWidget(self)
        layout.addWidget(self.right_panel, 1)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(16, 18, 16, 18)
        left_layout.setSpacing(12)

        self.left_title = StrongBodyLabel("网速测试", self.left_panel)
        left_layout.addWidget(self.left_title)

        top_container = QWidget(self.left_panel)
        self.left_stack = QStackedLayout(top_container)
        self.left_stack.setContentsMargins(0, 0, 0, 0)

        start_wrap = QWidget(top_container)
        start_wrap_layout = QVBoxLayout(start_wrap)
        start_wrap_layout.setContentsMargins(10, 10, 10, 10)
        start_wrap_layout.setSpacing(10)
        start_wrap_layout.addStretch(1)
        start_row = QHBoxLayout()
        start_row.addStretch(1)
        self.btn_start = CircleStartButton("测速", start_wrap)
        start_row.addWidget(self.btn_start)
        start_row.addStretch(1)
        start_wrap_layout.addLayout(start_row)
        self.left_hint = CaptionLabel("点击开始后将依次测试延迟、下载与上传", start_wrap)
        self.left_hint.setWordWrap(True)
        start_wrap_layout.addWidget(self.left_hint)
        start_wrap_layout.addStretch(1)

        gauge_wrap = QWidget(top_container)
        gauge_wrap_layout = QVBoxLayout(gauge_wrap)
        gauge_wrap_layout.setContentsMargins(10, 10, 10, 10)
        gauge_wrap_layout.setSpacing(10)
        gauge_wrap_layout.addStretch(1)
        gauge_row = QHBoxLayout()
        gauge_row.addStretch(1)
        self.gauge = GaugeWidget(gauge_wrap)
        self.gauge.title = "准备就绪"
        self.gauge.unit = "Mbps"
        self.gauge.set_max_value(100)
        gauge_row.addWidget(self.gauge)
        gauge_row.addStretch(1)
        gauge_wrap_layout.addLayout(gauge_row)
        self.running_hint = CaptionLabel("测试中…关闭窗口不会影响后台测速", gauge_wrap)
        self.running_hint.setWordWrap(True)
        gauge_wrap_layout.addWidget(self.running_hint)
        gauge_wrap_layout.addStretch(1)

        self.left_stack.addWidget(start_wrap)
        self.left_stack.addWidget(gauge_wrap)
        self.left_stack.setCurrentIndex(0)

        left_layout.addWidget(top_container, 0)

        self.info_box = QWidget(self.left_panel)
        ib = QGridLayout(self.info_box)
        ib.setContentsMargins(12, 10, 12, 10)
        ib.setHorizontalSpacing(8)
        ib.setVerticalSpacing(8)
        ib.setColumnStretch(0, 0)
        ib.setColumnStretch(1, 1)

        ib.addWidget(StrongBodyLabel("IP", self.info_box), 0, 0)
        self.ip_value = BodyLabel("--", self.info_box)
        self.ip_value.setWordWrap(True)
        ib.addWidget(self.ip_value, 0, 1)

        ib.addWidget(StrongBodyLabel("归属", self.info_box), 1, 0)
        self.loc_value = BodyLabel("--", self.info_box)
        self.loc_value.setWordWrap(True)
        ib.addWidget(self.loc_value, 1, 1)

        ib.addWidget(StrongBodyLabel("运营商", self.info_box), 2, 0)
        self.isp_value = BodyLabel("--", self.info_box)
        self.isp_value.setWordWrap(True)
        ib.addWidget(self.isp_value, 2, 1)

        left_layout.addWidget(self.info_box)
        
        # 测速设置入口（齿轮图标）
        self.settings_bar = QWidget(self.left_panel)
        sb = QGridLayout(self.settings_bar)
        sb.setContentsMargins(12, 10, 12, 10)
        sb.setHorizontalSpacing(8)
        sb.setVerticalSpacing(6)
        sb.addWidget(StrongBodyLabel("单位", self.settings_bar), 0, 0)
        self.unit_box = ComboBox(self.settings_bar)
        self.unit_box.addItems(["Mbps", "MB/s"])
        sb.addWidget(self.unit_box, 0, 1)
        sb.addWidget(StrongBodyLabel("量程", self.settings_bar), 1, 0)
        self.range_box = ComboBox(self.settings_bar)
        self.range_box.addItems(["自动", "50", "100", "200", "500", "1000"])
        sb.addWidget(self.range_box, 1, 1)
        left_layout.addWidget(self.settings_bar)
        self.settings_bar.hide()
        
        left_layout.addStretch(1)

        right_panel_container = QVBoxLayout(self.right_panel)
        right_panel_container.setContentsMargins(20, 18, 20, 18)
        right_panel_container.setSpacing(12)

        top_row = QHBoxLayout()
        self.summary_label = StrongBodyLabel("开始测速以获取准确结果", self.right_panel)
        top_row.addWidget(self.summary_label)
        
        # 网络需求标识
        self.net_tag = CaptionLabel("需要网络", self.right_panel)
        self.net_tag.setStyleSheet("background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;")
        top_row.addWidget(self.net_tag)
        
        top_row.addStretch(1)
        
        # 右上角设置按钮
        self.btn_settings = TransparentToolButton(FIF.SETTING, self.right_panel)
        self.btn_settings.setFixedSize(32, 32)
        top_row.addWidget(self.btn_settings)
        
        right_panel_container.addLayout(top_row)

        self.stats_box = QWidget(self.right_panel)
        stats_layout = QGridLayout(self.stats_box)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setHorizontalSpacing(12)
        stats_layout.setVerticalSpacing(12)
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 1)

        self.dl_tile = QWidget(self.stats_box)
        dl_tile_layout = QVBoxLayout(self.dl_tile)
        dl_tile_layout.setContentsMargins(14, 12, 14, 12)
        dl_tile_layout.setSpacing(6)
        self.dl_title = CaptionLabel("下载", self.dl_tile)
        dl_tile_layout.addWidget(self.dl_title)
        dl_value_row = QHBoxLayout()
        dl_value_row.setContentsMargins(0, 0, 0, 0)
        dl_value_row.setSpacing(6)
        self.dl_value = DisplayLabel("--", self.dl_tile)
        self.dl_unit = CaptionLabel(self.unit_box.currentText(), self.dl_tile)
        dl_value_row.addWidget(self.dl_value)
        dl_value_row.addWidget(self.dl_unit)
        dl_value_row.addStretch(1)
        dl_tile_layout.addLayout(dl_value_row)
        stats_layout.addWidget(self.dl_tile, 0, 0)

        self.ul_tile = QWidget(self.stats_box)
        ul_tile_layout = QVBoxLayout(self.ul_tile)
        ul_tile_layout.setContentsMargins(14, 12, 14, 12)
        ul_tile_layout.setSpacing(6)
        self.ul_title = CaptionLabel("上传", self.ul_tile)
        ul_tile_layout.addWidget(self.ul_title)
        ul_value_row = QHBoxLayout()
        ul_value_row.setContentsMargins(0, 0, 0, 0)
        ul_value_row.setSpacing(6)
        self.ul_value = DisplayLabel("--", self.ul_tile)
        self.ul_unit = CaptionLabel(self.unit_box.currentText(), self.ul_tile)
        ul_value_row.addWidget(self.ul_value)
        ul_value_row.addWidget(self.ul_unit)
        ul_value_row.addStretch(1)
        ul_tile_layout.addLayout(ul_value_row)
        stats_layout.addWidget(self.ul_tile, 0, 1)

        self.ping_tile = QWidget(self.stats_box)
        ping_tile_layout = QVBoxLayout(self.ping_tile)
        ping_tile_layout.setContentsMargins(14, 12, 14, 12)
        ping_tile_layout.setSpacing(6)
        self.ping_title = CaptionLabel("延迟", self.ping_tile)
        ping_tile_layout.addWidget(self.ping_title)
        ping_value_row = QHBoxLayout()
        ping_value_row.setContentsMargins(0, 0, 0, 0)
        ping_value_row.setSpacing(6)
        self.ping_value = DisplayLabel("--", self.ping_tile)
        self.ping_unit = CaptionLabel("ms", self.ping_tile)
        ping_value_row.addWidget(self.ping_value)
        ping_value_row.addWidget(self.ping_unit)
        ping_value_row.addStretch(1)
        ping_tile_layout.addLayout(ping_value_row)
        stats_layout.addWidget(self.ping_tile, 1, 0)

        self.jitter_tile = QWidget(self.stats_box)
        jitter_tile_layout = QVBoxLayout(self.jitter_tile)
        jitter_tile_layout.setContentsMargins(14, 12, 14, 12)
        jitter_tile_layout.setSpacing(6)
        self.jitter_title = CaptionLabel("抖动", self.jitter_tile)
        jitter_tile_layout.addWidget(self.jitter_title)
        jitter_value_row = QHBoxLayout()
        jitter_value_row.setContentsMargins(0, 0, 0, 0)
        jitter_value_row.setSpacing(6)
        self.jitter_value = DisplayLabel("--", self.jitter_tile)
        self.jitter_unit = CaptionLabel("ms", self.jitter_tile)
        jitter_value_row.addWidget(self.jitter_value)
        jitter_value_row.addWidget(self.jitter_unit)
        jitter_value_row.addStretch(1)
        jitter_tile_layout.addLayout(jitter_value_row)
        stats_layout.addWidget(self.jitter_tile, 1, 1)

        right_panel_container.addWidget(self.stats_box)

        self.charts_box = QWidget(self.right_panel)
        charts_layout = QHBoxLayout(self.charts_box)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(12)

        self.dl_chart_box = QWidget(self.charts_box)
        dl_chart_box_layout = QVBoxLayout(self.dl_chart_box)
        dl_chart_box_layout.setContentsMargins(14, 12, 14, 12)
        dl_chart_box_layout.setSpacing(8)
        self.dl_chart_title = StrongBodyLabel("下载曲线", self.dl_chart_box)
        dl_chart_box_layout.addWidget(self.dl_chart_title)
        self.dl_chart = LineChartWidget(self.dl_chart_box, accent=QColor(22, 119, 255))
        dl_chart_box_layout.addWidget(self.dl_chart, 1)
        charts_layout.addWidget(self.dl_chart_box, 1)

        self.ul_chart_box = QWidget(self.charts_box)
        ul_chart_box_layout = QVBoxLayout(self.ul_chart_box)
        ul_chart_box_layout.setContentsMargins(14, 12, 14, 12)
        ul_chart_box_layout.setSpacing(8)
        self.ul_chart_title = StrongBodyLabel("上传曲线", self.ul_chart_box)
        ul_chart_box_layout.addWidget(self.ul_chart_title)
        self.ul_chart = LineChartWidget(self.ul_chart_box, accent=QColor(22, 119, 255))
        ul_chart_box_layout.addWidget(self.ul_chart, 1)
        charts_layout.addWidget(self.ul_chart_box, 1)

        right_panel_container.addWidget(self.charts_box, 1)

        self.status_label = CaptionLabel("准备就绪", self.right_panel)
        right_panel_container.addWidget(self.status_label)

        # 信号
        self.btn_settings.clicked.connect(self.toggle_settings)
        self.unit_box.currentTextChanged.connect(self._sync_unit_labels)
        self._sync_unit_labels()

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, left_bg, box_bg, border_color = "#1d1d1d", "#252525", "rgba(255,255,255,0.05)", "rgba(255,255,255,0.1)"
            text_color = "#e0e0e0"
            sub_text = "#a0a0a0"
            highlight = "#333333"
        else:
            bg_color, left_bg, box_bg, border_color = "#f7f9fc", "#ffffff", "rgba(0,0,0,0.03)", "rgba(0,0,0,0.08)"
            text_color = "#333333"
            sub_text = "#666666"
            highlight = "#f0f0f0"

        self.setStyleSheet(f"#SpeedTestInterface{{background-color:{bg_color};}}")
        self.left_panel.setStyleSheet(f"background-color:{left_bg}; border-right:1px solid {border_color};")
        self.right_panel.setStyleSheet(f"background-color:{bg_color};")
        
        box_style = f"background-color:{box_bg}; border:1px solid {border_color}; border-radius:8px;"
        self.settings_bar.setStyleSheet(box_style)
        self.info_box.setStyleSheet(box_style)
        self.left_stack.widget(0).setStyleSheet(box_style)
        self.left_stack.widget(1).setStyleSheet(box_style)
        self.stats_box.setStyleSheet("background: transparent;")
        tile_style = f"background-color:{box_bg}; border:1px solid {border_color}; border-radius:10px;"
        self.dl_tile.setStyleSheet(tile_style)
        self.ul_tile.setStyleSheet(tile_style)
        self.ping_tile.setStyleSheet(tile_style)
        self.jitter_tile.setStyleSheet(tile_style)
        self.dl_chart_box.setStyleSheet(tile_style)
        self.ul_chart_box.setStyleSheet(tile_style)

        self.gauge.set_dark_mode(is_dark)
        self.dl_chart.set_dark_mode(is_dark)
        self.ul_chart.set_dark_mode(is_dark)

        # 字号规范调整
        self.summary_label.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:600;")
        self.left_title.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:600;")
        self.left_hint.setStyleSheet(f"color:{sub_text}; font-size:12px;")
        self.running_hint.setStyleSheet(f"color:{sub_text}; font-size:12px;")
        
        # 描述文字字号 (12-13px)
        desc_style = f"color:{sub_text}; font-size:12px;"
        self.dl_title.setStyleSheet(desc_style)
        self.ul_title.setStyleSheet(desc_style)
        self.ping_title.setStyleSheet(desc_style)
        self.jitter_title.setStyleSheet(desc_style)
        self.status_label.setStyleSheet(desc_style)
        self.dl_unit.setStyleSheet(desc_style)
        self.ul_unit.setStyleSheet(desc_style)
        self.ping_unit.setStyleSheet(desc_style)
        self.jitter_unit.setStyleSheet(desc_style)

        self.dl_value.setStyleSheet(f"color:{text_color}; font-size:28px; font-weight:800;")
        self.ul_value.setStyleSheet(f"color:{text_color}; font-size:28px; font-weight:800;")
        self.ping_value.setStyleSheet(f"color:{text_color}; font-size:28px; font-weight:800;")
        self.jitter_value.setStyleSheet(f"color:{text_color}; font-size:28px; font-weight:800;")

        self.dl_chart_title.setStyleSheet(f"color:{text_color}; font-size:13px; font-weight:700;")
        self.ul_chart_title.setStyleSheet(f"color:{text_color}; font-size:13px; font-weight:700;")
        
        # IP 信息字号
        self.ip_value.setStyleSheet(f"color:{text_color}; font-size:12px; font-weight:600;")
        self.loc_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")
        self.isp_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")

        # 按钮样式同步 (低饱和度悬停效果)
        # 将设置按钮图标颜色改为蓝色主题
        btn_style = f"""
            TransparentToolButton{{color:#1677ff; border-radius:4px;}}
            TransparentToolButton:hover{{background:{highlight};}}
        """
        self.btn_settings.setStyleSheet(btn_style)
        
        # 强制刷新子部件
        for widget in self.findChildren(QWidget):
            widget.update()

    def set_running(self, running):
        self.left_stack.setCurrentIndex(1 if running else 0)

    def update_network_status(self, is_online):
        """ 更新网络状态相关的 UI """
        self.btn_start.setEnabled(is_online)
        
        # 添加淡入淡出动画
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        if not hasattr(self, '_net_tag_opacity'):
            self._net_tag_opacity = QGraphicsOpacityEffect(self.net_tag)
            self.net_tag.setGraphicsEffect(self._net_tag_opacity)
        
        self._ani = QPropertyAnimation(self._net_tag_opacity, b"opacity")
        self._ani.setDuration(300)
        self._ani.setStartValue(1.0)
        self._ani.setEndValue(0.1)
        self._ani.finished.connect(lambda: self._on_net_tag_fade_out_finished(is_online))
        self._ani.start()

    def _on_net_tag_fade_out_finished(self, is_online):
        if not is_online:
            self.status_label.setText("网络未连接")
            self.gauge.title = "网络未连接"
            self.net_tag.setText("需要网络 (未连接)")
            self.net_tag.setStyleSheet("background-color: rgba(232, 17, 35, 0.2); color: #e81123; padding: 2px 8px; border-radius: 4px;")
        else:
            self.status_label.setText("准备就绪")
            self.gauge.title = "准备就绪"
            self.net_tag.setText("需要网络")
            self.net_tag.setStyleSheet("background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;")
        
        self._ani2 = QPropertyAnimation(self._net_tag_opacity, b"opacity")
        self._ani2.setDuration(300)
        self._ani2.setStartValue(0.1)
        self._ani2.setEndValue(1.0)
        self._ani2.start()

    def toggle_settings(self):
        self.settings_bar.setVisible(not self.settings_bar.isVisible())

    def _sync_unit_labels(self):
        unit = self.unit_box.currentText()
        self.dl_unit.setText(unit)
        self.ul_unit.setText(unit)
