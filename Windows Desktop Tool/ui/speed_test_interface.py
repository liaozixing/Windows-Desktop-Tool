from PyQt5.QtCore import QPropertyAnimation, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QStackedLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    DisplayLabel,
    FluentIcon as FIF,
    StrongBodyLabel,
    TransparentToolButton,
)

from ui.components import CircleStartButton, GaugeWidget, LineChartWidget


class SpeedTestInterface(QWidget):
    """ 网速测试界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SpeedTestInterface")
        self._speed_phase = None
        self._speed_latest_value = 0.0
        self._speed_dl_latest = 0.0
        self._speed_ul_latest = 0.0
        self._last_speed_result = None
        self._speed_chart_timer = QTimer(self)
        self._speed_chart_timer.setInterval(500)
        self._speed_chart_timer.timeout.connect(self.append_speed_chart_point)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.left_panel = QWidget(self)
        self.left_panel.setFixedWidth(280)
        layout.addWidget(self.left_panel)

        self.right_panel = QWidget(self)
        layout.addWidget(self.right_panel, 1)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(16, 20, 16, 20)
        left_layout.setSpacing(12)

        top_container = QWidget(self.left_panel)
        self.left_stack = QStackedLayout(top_container)
        self.left_stack.setContentsMargins(0, 0, 0, 0)

        start_wrap = QWidget(top_container)
        start_wrap_layout = QVBoxLayout(start_wrap)
        start_wrap_layout.setContentsMargins(0, 0, 0, 0)
        start_wrap_layout.addStretch(1)
        start_row = QHBoxLayout()
        start_row.addStretch(1)
        self.btn_start = CircleStartButton("测速", start_wrap)
        start_row.addWidget(self.btn_start)
        start_row.addStretch(1)
        start_wrap_layout.addLayout(start_row)
        start_wrap_layout.addStretch(1)

        gauge_wrap = QWidget(top_container)
        gauge_wrap_layout = QVBoxLayout(gauge_wrap)
        gauge_wrap_layout.setContentsMargins(0, 0, 0, 0)
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
        gauge_wrap_layout.addStretch(1)

        self.left_stack.addWidget(start_wrap)
        self.left_stack.addWidget(gauge_wrap)
        self.left_stack.setCurrentIndex(0)

        left_layout.addWidget(top_container, 0)

        self.info_box = QWidget(self.left_panel)
        ib = QGridLayout(self.info_box)
        ib.setContentsMargins(10, 8, 10, 8)
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

        self.settings_bar = QWidget(self.left_panel)
        sb = QGridLayout(self.settings_bar)
        sb.setContentsMargins(10, 8, 10, 8)
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

        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.summary_label = StrongBodyLabel("网络状况检测", self.right_panel)
        top_row.addWidget(self.summary_label)

        self.net_tag = CaptionLabel("需要网络", self.right_panel)
        self.net_tag.setStyleSheet(
            "background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;"
        )
        top_row.addWidget(self.net_tag)

        top_row.addStretch(1)

        self.btn_settings = TransparentToolButton(FIF.SETTING, self.right_panel)
        self.btn_settings.setFixedSize(32, 32)
        top_row.addWidget(self.btn_settings)

        right_layout.addLayout(top_row)

        self.dl_value = DisplayLabel("--", self.right_panel)
        self.ul_value = DisplayLabel("--", self.right_panel)

        self.dl_title = StrongBodyLabel("下载", self.right_panel)
        self.ul_title = StrongBodyLabel("上传", self.right_panel)

        self.dl_chart = LineChartWidget(self.right_panel, accent=QColor(22, 119, 255))
        self.ul_chart = LineChartWidget(self.right_panel, accent=QColor(54, 207, 201))

        charts = QGridLayout()
        charts.setContentsMargins(0, 0, 0, 0)
        charts.setHorizontalSpacing(16)
        charts.setVerticalSpacing(12)

        charts.addWidget(self.dl_title, 0, 0)
        charts.addWidget(self.dl_value, 1, 0)
        charts.addWidget(self.dl_chart, 0, 1, 2, 1)

        charts.addWidget(self.ul_title, 2, 0)
        charts.addWidget(self.ul_value, 3, 0)
        charts.addWidget(self.ul_chart, 2, 1, 2, 1)

        charts.setColumnStretch(0, 1)
        charts.setColumnStretch(1, 3)
        right_layout.addLayout(charts, 1)

        bottom = QGridLayout()
        bottom.setHorizontalSpacing(24)
        bottom.setVerticalSpacing(4)

        self.ping_value = DisplayLabel("--", self.right_panel)
        self.jitter_value = DisplayLabel("--", self.right_panel)

        ping_title = StrongBodyLabel("时延/ms", self.right_panel)
        jitter_title = StrongBodyLabel("抖动/ms", self.right_panel)

        bottom.addWidget(ping_title, 0, 0)
        bottom.addWidget(self.ping_value, 1, 0)
        bottom.addWidget(jitter_title, 0, 1)
        bottom.addWidget(self.jitter_value, 1, 1)
        bottom.setColumnStretch(0, 1)
        bottom.setColumnStretch(1, 1)
        right_layout.addLayout(bottom)

        self.status_label = CaptionLabel("准备就绪", self.right_panel)
        right_layout.addWidget(self.status_label)

    def set_theme(self, is_dark):
        """ 设置页面主题 - 对齐 Win11 原生深色风格 """
        self.gauge.set_dark_mode(is_dark)
        self.dl_chart.set_dark_mode(is_dark)
        self.ul_chart.set_dark_mode(is_dark)

        if is_dark:
            bg_color = "#1d1d1d"
            left_bg = "#2b2b2b"
            border_color = "#333333"
            box_bg = "#323232"
            text_color = "#e0e0e0"
            sub_text = "#a0a0a0"
            highlight = "#383838"
        else:
            bg_color = "#f7f9fc"
            left_bg = "#ffffff"
            border_color = "#e5e8ef"
            box_bg = "#f0f2f5"
            text_color = "#333333"
            sub_text = "#666666"
            highlight = "#f0f0f0"

        self.setStyleSheet(f"#SpeedTestInterface{{background-color:{bg_color};}}")
        self.left_panel.setStyleSheet(f"background-color:{left_bg}; border-right:1px solid {border_color};")
        self.right_panel.setStyleSheet(f"background-color:{bg_color};")

        box_style = f"background-color:{box_bg}; border:1px solid {border_color}; border-radius:8px;"
        self.settings_bar.setStyleSheet(box_style)
        self.info_box.setStyleSheet(box_style)

        self.summary_label.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:600;")

        data_style = f"color:{{color}}; font-size:18px; font-weight:700;"
        self.ping_value.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:700;")
        self.jitter_value.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:700;")

        desc_style = f"color:{sub_text}; font-size:12px;"
        self.dl_title.setStyleSheet(desc_style)
        self.ul_title.setStyleSheet(desc_style)
        self.status_label.setStyleSheet(desc_style)

        self.ip_value.setStyleSheet(f"color:{text_color}; font-size:12px; font-weight:600;")
        self.loc_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")
        self.isp_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")

        btn_style = f"""
            TransparentToolButton{{color:{sub_text}; border-radius:4px;}}
            TransparentToolButton:hover{{background:{highlight};}}
        """
        self.btn_settings.setStyleSheet(btn_style)

        for widget in self.findChildren(QWidget):
            widget.update()

    def set_running(self, running):
        self.left_stack.setCurrentIndex(1 if running else 0)

    def update_network_status(self, is_online):
        """ 更新网络状态相关的 UI """
        self.btn_start.setEnabled(is_online)

        from PyQt5.QtWidgets import QGraphicsOpacityEffect

        if not hasattr(self, "_net_tag_opacity"):
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
            self.net_tag.setStyleSheet(
                "background-color: rgba(232, 17, 35, 0.2); color: #e81123; padding: 2px 8px; border-radius: 4px;"
            )
        else:
            self.status_label.setText("准备就绪")
            self.gauge.title = "准备就绪"
            self.net_tag.setText("需要网络")
            self.net_tag.setStyleSheet(
                "background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;"
            )

        self._ani2 = QPropertyAnimation(self._net_tag_opacity, b"opacity")
        self._ani2.setDuration(300)
        self._ani2.setStartValue(0.1)
        self._ani2.setEndValue(1.0)
        self._ani2.start()

    def toggle_settings(self):
        self.settings_bar.setVisible(not self.settings_bar.isVisible())

    def start_speed_test(self):
        if not self.window().is_online:
            from qfluentwidgets import InfoBar
            InfoBar.warning("网络未连接", "请检查您的网络连接后再试", duration=3000, parent=self.window())
            return

        self.set_running(True)
        self.btn_start.setEnabled(False)
        self.dl_chart.clear()
        self.ul_chart.clear()
        self.dl_value.setText("--")
        self.ul_value.setText("--")
        self.ping_value.setText("--")
        self.jitter_value.setText("--")

        self.gauge.set_max_value(500)
        self.gauge.set_value(0, animated=False)
        self.gauge.title = "准备中"
        self.gauge.unit = self.unit_box.currentText()
        self.gauge.update()
        self.status_label.setText("正在准备测速...")

        self._speed_phase = "prepare"
        self._speed_latest_value = 0.0
        self._speed_dl_latest = 0.0
        self._speed_ul_latest = 0.0
        self._last_speed_result = None

        if self._speed_chart_timer.isActive():
            self._speed_chart_timer.stop()
        self._speed_chart_timer.start()

        from ui.workers import SpeedTestWorker
        self.speed_worker = SpeedTestWorker(provider="cloudflare", parent=self)
        self.speed_worker.progress.connect(self.on_speed_test_progress)
        self.speed_worker.metric.connect(self.on_speed_test_metric)
        self.speed_worker.finished.connect(self.on_speed_test_finished)
        self.speed_worker.start()

    def on_speed_test_progress(self, msg):
        self.status_label.setText(msg)
        if "延迟" in msg:
            self._speed_phase = "ping"
            self.gauge.title = "延迟"
        elif "下载" in msg:
            self._speed_phase = "download"
            self.gauge.title = "下载"
        elif "上传" in msg:
            self._speed_phase = "upload"
            self.gauge.title = "上传"

    def on_speed_test_metric(self, metric):
        unit = self.unit_box.currentText()
        factor = 1.0 if unit == "Mbps" else 0.125
        try:
            mbps = float(metric.get("mbps", 0.0))
        except Exception:
            return

        phase = metric.get("phase") or self._speed_phase or "download"

        display_value = mbps * factor
        self._speed_latest_value = display_value
        if phase == "download":
            self._speed_dl_latest = display_value
            self.dl_value.setText(f"{display_value:.2f}")
        elif phase == "upload":
            self._speed_ul_latest = display_value
            self.ul_value.setText(f"{display_value:.2f}")

        max_v = float(getattr(self.gauge, "_max_value", 100.0))
        if max_v <= 0:
            max_v = 100.0
        if display_value > max_v * 0.95:
            new_max = ((int(display_value) // 50) + 1) * 50
            self.gauge.set_max_value(float(new_max))

        self.gauge.unit = unit
        self.gauge.set_value(display_value, animated=True)

    def on_speed_test_finished(self, result):
        if self._speed_chart_timer.isActive():
            self._speed_chart_timer.stop()
        self.set_running(False)
        self.btn_start.setEnabled(True)

        from qfluentwidgets import InfoBar
        if result.get("status") == "success":
            self.status_label.setText("测速完成")
            self._last_speed_result = result
            unit = self.unit_box.currentText()
            factor = 1.0 if unit == "Mbps" else 0.125
            dl_val = float(result.get("download", 0.0)) * factor
            ul_val = float(result.get("upload", 0.0)) * factor
            ping = result.get("ping")
            jitter = result.get("jitter")
            self.dl_value.setText(f"{dl_val:.2f}")
            self.ul_value.setText(f"{ul_val:.2f}")
            self.ping_value.setText(f"{float(ping):.0f}" if ping is not None else "--")
            self.jitter_value.setText(f"{float(jitter):.2f}" if jitter is not None else "--")
            InfoBar.success("测速完成", f"下载: {dl_val:.2f} {unit}, 上传: {ul_val:.2f} {unit}", duration=3000, parent=self.window())
        else:
            self.status_label.setText("测速失败")
            InfoBar.error("测速失败", result.get("message", "未知错误"), duration=3000, parent=self.window())

    def append_speed_chart_point(self):
        if self._speed_phase == "download":
            self.dl_chart.add_value(self._speed_dl_latest)
        elif self._speed_phase == "upload":
            self.ul_chart.add_value(self._speed_ul_latest)

    def on_speed_unit_changed(self, unit):
        self.gauge.unit = unit

    def on_speed_range_changed(self, text):
        if text == "自动":
            return
        try:
            v = float(text)
        except Exception:
            return
        self.gauge.set_max_value(v)

    def stop_worker(self):
        if hasattr(self, "speed_worker") and self.speed_worker.isRunning():
            self.speed_worker.quit()
        if self._speed_chart_timer.isActive():
            self._speed_chart_timer.stop()
