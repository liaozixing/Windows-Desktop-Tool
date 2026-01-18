import sys
import os
import socket
import subprocess
from modules.file_converter import (svg_to_ico, image_convert, pdf_to_word, 
                                   word_to_pdf, word_to_excel, excel_to_word)
from modules.network_monitor import NetworkMonitor
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView, QSystemTrayIcon, QMenu, QAction, QGridLayout, QStackedLayout, QSizePolicy, QColorDialog, QFileIconProvider, QFileDialog, QStackedWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QFileInfo, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QColor

from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF, 
                            SubtitleLabel, PrimaryPushButton, PushButton, TextEdit, 
                            TableWidget, CheckBox, MessageBox, InfoBar, InfoBarPosition,
                            setTheme, Theme, SettingCardGroup, SwitchSettingCard,
                            ComboBox, ProgressBar, StrongBodyLabel, DisplayLabel,
                            CaptionLabel, setCustomStyleSheet, ThemeColor, BodyLabel, 
                            SearchLineEdit, TransparentToolButton, qconfig, isDarkTheme,
                            ToolTipFilter, ToolTipPosition)

from ui.components import GaugeWidget, LineChartWidget, CircleStartButton
from modules.ip_query import get_public_ip_info
from modules.system_functions import (open_cmd, open_task_manager, open_explorer, 
                                     open_group_policy, fix_group_policy, open_run_dialog, 
                                     get_activation_status, clean_cache)
from modules.settings import load_settings, save_settings, set_auto_start
from modules.network_speed import run_speed_test
from modules.window_tool import get_window_info_at, open_file_location
from modules.file_shredder import ShredderWorker, is_system_path, ValidationWorker
from modules.system_info import get_system_info, SystemInfoWorker

class IPWorker(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        result = get_public_ip_info()
        self.finished.emit(result)

class SpeedTestWorker(QThread):
    progress = pyqtSignal(str)
    metric = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(self, provider="auto", parent=None):
        super().__init__(parent=parent)
        self.provider = provider

    def run(self):
        result = run_speed_test(self.progress.emit, provider=self.provider, metric_callback=self.metric.emit)
        self.finished.emit(result)

class GPFixWorker(QThread):
    """ 组策略修复线程 """
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def run(self):
        success, message = fix_group_policy(self.progress.emit)
        self.finished.emit(success, message)

class IPInterface(QWidget):
    """ IP 查询界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("IPInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("公网 IP 查询", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 网络需求标识
        self.net_tag = CaptionLabel("需要网络", self)
        self.net_tag.setStyleSheet("background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.net_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # IP 信息卡片
        self.info_card = QWidget()
        self.info_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1);")
        card_layout = QVBoxLayout(self.info_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        self.ip_info_display = TextEdit()
        self.ip_info_display.setReadOnly(True)
        self.ip_info_display.setPlaceholderText("点击下方按钮获取您的公网 IP 信息...")
        self.ip_info_display.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #e0e0e0;")
        card_layout.addWidget(self.ip_info_display)
        
        layout.addWidget(self.info_card)

        # 操作按钮
        self.btn_query = PrimaryPushButton(FIF.GLOBE, "立即查询公网IP", self)
        self.btn_query.setFixedHeight(40)
        layout.addWidget(self.btn_query)
        
        layout.addStretch(1)

    def update_network_status(self, is_online):
        """ 更新网络状态相关的 UI """
        self.btn_query.setEnabled(is_online)
        
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
            self.btn_query.setText("网络未连接")
            self.ip_info_display.setPlaceholderText("网络未连接，无法查询 IP 信息")
            self.net_tag.setText("需要网络 (未连接)")
            self.net_tag.setStyleSheet("background-color: rgba(232, 17, 35, 0.2); color: #e81123; padding: 2px 8px; border-radius: 4px;")
        else:
            self.btn_query.setText("立即查询公网IP")
            self.ip_info_display.setPlaceholderText("点击下方按钮获取您的公网 IP 信息...")
            self.net_tag.setText("需要网络")
            self.net_tag.setStyleSheet("background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;")
        
        self._ani2 = QPropertyAnimation(self._net_tag_opacity, b"opacity")
        self._ani2.setDuration(300)
        self._ani2.setStartValue(0.1)
        self._ani2.setEndValue(1.0)
        self._ani2.start()

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, text_color, card_bg = "#1d1d1d", "#e0e0e0", "rgba(255, 255, 255, 0.05)"
        else:
            bg_color, text_color, card_bg = "#f7f9fc", "#333333", "rgba(0, 0, 0, 0.05)"
        
        self.setStyleSheet(f"#IPInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.info_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px; border: 1px solid {'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.1)'};")
        self.ip_info_display.setStyleSheet(f"background: transparent; border: none; font-size: 14px; color: {text_color};")

class SystemInterface(QWidget):
    """ 系统功能界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SystemInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("系统工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 网络需求标识 (离线可用)
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 快捷工具栏 (还原原来的布局)
        tools_layout = QGridLayout()
        self.btn_cmd = PushButton(FIF.COMMAND_PROMPT, "命令行", self)
        self.btn_taskmgr = PushButton(FIF.BASKETBALL, "任务管理器", self)
        self.btn_explorer = PushButton(FIF.FOLDER, "资源管理器", self)
        self.btn_gpedit = PushButton(FIF.SETTING, "组策略", self)
        self.btn_run = PushButton(FIF.SEND, "运行框", self)
        self.btn_env = PushButton(FIF.SETTING, "环境变量", self)
        
        tools_layout.addWidget(self.btn_cmd, 0, 0)
        tools_layout.addWidget(self.btn_taskmgr, 0, 1)
        tools_layout.addWidget(self.btn_explorer, 0, 2)
        tools_layout.addWidget(self.btn_gpedit, 1, 0)
        tools_layout.addWidget(self.btn_run, 1, 1)
        tools_layout.addWidget(self.btn_env, 1, 2)
        layout.addLayout(tools_layout)

        layout.addSpacing(20)
        self.other_title = SubtitleLabel("其他工具", self)
        self.other_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(self.other_title)

        other_layout = QGridLayout()
        self.btn_activation = PushButton(FIF.ACCEPT, "系统激活状态", self)
        self.btn_sys_info = PushButton(FIF.INFO, "本机配置信息", self)
        other_layout.addWidget(self.btn_activation, 0, 0)
        other_layout.addWidget(self.btn_sys_info, 0, 1)
        other_layout.setColumnStretch(2, 1)
        layout.addLayout(other_layout)

        layout.addStretch(1)

        # 绑定信号
        self.btn_cmd.clicked.connect(open_cmd)
        self.btn_taskmgr.clicked.connect(open_task_manager)
        self.btn_explorer.clicked.connect(lambda: open_explorer())
        self.btn_gpedit.clicked.connect(self.open_gpedit)
        self.btn_run.clicked.connect(open_run_dialog)
        self.btn_env.clicked.connect(lambda: os.system("rundll32.exe sysdm.cpl,EditEnvironmentVariables"))
        self.btn_activation.clicked.connect(self.show_activation_status)
        self.btn_sys_info.clicked.connect(self.show_system_info)

        # 检查是否为家庭版并禁用组策略按钮
        self._check_home_edition()

    def _check_home_edition(self):
        """ 检查 Windows 版本，如果是家庭版则禁用组策略按钮并添加提示 """
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            edition, _ = winreg.QueryValueEx(key, "EditionID")
            if "HOME" in edition.upper():
                self.btn_gpedit.setEnabled(False)
                self.btn_gpedit.setToolTip("此功能在 Windows 家庭版中不可用")
                # 安装 ToolTipFilter 以支持 Fluent UI 样式的提示
                self.btn_gpedit.installEventFilter(ToolTipFilter(self.btn_gpedit, 500, ToolTipPosition.TOP))
        except:
            pass

    def update_network_status(self, is_online):
        """ 更新网络状态 (系统工具大多数离线可用，不需要特殊处理) """
        pass

    def open_gpedit(self):
        if not open_group_policy():
            # 如果找不到组策略，提示用户修复
            mb = MessageBox(
                "组策略编辑器未找到", 
                "系统中未找到组策略编辑器（gpedit.msc）。这通常是因为您使用的是 Windows 家庭版。\n\n是否要一键安装并启用组策略功能？", 
                self.window()
            )
            mb.yesButton.setText("立即安装")
            mb.noButton.setText("取消")
            if mb.exec_():
                # 调用主窗口的修复方法
                if hasattr(self.window(), 'start_gp_fix'):
                    self.window().start_gp_fix()

    def show_activation_status(self):
        status = get_activation_status()
        MessageBox("系统激活状态", status, self.window()).exec_()

    def show_system_info(self):
        # 创建加载提示
        self.sys_info_mb = MessageBox("请稍候", "正在深度扫描硬件配置，请稍候...", self.window())
        self.sys_info_mb.yesButton.hide()
        self.sys_info_mb.cancelButton.hide()
        
        # 启动后台线程获取信息
        self.sys_info_thread = QThread()
        self.sys_info_worker = SystemInfoWorker()
        self.sys_info_worker.moveToThread(self.sys_info_thread)
        self.sys_info_thread.started.connect(self.sys_info_worker.run)
        self.sys_info_worker.finished.connect(self._on_sys_info_finished)
        self.sys_info_worker.finished.connect(self.sys_info_thread.quit)
        self.sys_info_worker.finished.connect(self.sys_info_worker.deleteLater)
        self.sys_info_thread.finished.connect(self.sys_info_thread.deleteLater)
        
        self.sys_info_thread.start()
        self.sys_info_mb.exec_()

    def _on_sys_info_finished(self, info):
        if hasattr(self, 'sys_info_mb'):
            self.sys_info_mb.accept()
            
        if 'error' in info:
            MessageBox("获取信息失败", info['error'], self.window()).exec_()
            return
        
        info_str = (
            f"💻 计算机名称:  {info.get('node', '未知')}\n"
            f"💿 操作系统:    {info.get('os', '未知')}\n"
            f"🧠 处理器:      {info.get('processor', '未知')}\n"
            f"📟 内存总量:    {info.get('memory_total', '未知')}\n"
            f"🎨 显卡型号:    {info.get('gpu', '未知')}\n\n"
            f"💽 硬盘总容量:  {info.get('disk_summary', '未知')}\n"
            f"----------------------------------\n"
            f"{info.get('disk_details', '未知')}"
        )
        
        mb = MessageBox("本机配置信息", info_str, self.window())
        mb.yesButton.setText("确定")
        mb.cancelButton.hide()
        mb.exec_()

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
        
        # 测速设置入口（齿轮图标）
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
        
        # 网络需求标识
        self.net_tag = CaptionLabel("需要网络", self.right_panel)
        self.net_tag.setStyleSheet("background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;")
        top_row.addWidget(self.net_tag)
        
        top_row.addStretch(1)
        
        # 右上角设置按钮
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
        # 更新自定义组件
        self.gauge.set_dark_mode(is_dark)
        self.dl_chart.set_dark_mode(is_dark)
        self.ul_chart.set_dark_mode(is_dark)

        # Win11 原生深色风格配色 (低饱和度、暗灰、非纯黑)
        if is_dark:
            bg_color = "#1d1d1d"      # Win11 Mica/Acrylic 背景底色
            left_bg = "#2b2b2b"      # 侧边/面板色
            border_color = "#333333" # 弱对比分割线
            box_bg = "#323232"       # 容器背景
            text_color = "#e0e0e0"   # 浅灰文字，不过亮
            sub_text = "#a0a0a0"     # 辅助文字
            highlight = "#383838"    # 高亮/悬停色
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

        # 字号规范调整
        self.summary_label.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:600;")
        
        # 数据值采用标准字号 (16-18px)
        data_style = f"color:{{color}}; font-size:18px; font-weight:700;"
        # Note: color will be applied via apply_accent_color for dl/ul values
        self.ping_value.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:700;")
        self.jitter_value.setStyleSheet(f"color:{text_color}; font-size:16px; font-weight:700;")
        
        # 描述文字字号 (12-13px)
        desc_style = f"color:{sub_text}; font-size:12px;"
        self.dl_title.setStyleSheet(desc_style)
        self.ul_title.setStyleSheet(desc_style)
        self.status_label.setStyleSheet(desc_style)
        
        # IP 信息字号
        self.ip_value.setStyleSheet(f"color:{text_color}; font-size:12px; font-weight:600;")
        self.loc_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")
        self.isp_value.setStyleSheet(f"color:{sub_text}; font-size:12px;")

        # 按钮样式同步 (低饱和度悬停效果)
        btn_style = f"""
            TransparentToolButton{{color:{sub_text}; border-radius:4px;}}
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

class HighlightWindow(QWidget):
    """ 目标窗口高亮边框 """
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
        # 绘制矩形边框，稍微往内缩一点
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
    """ 拖动时的影子靶子 """
    def __init__(self, parent=None):
        super().__init__(None) # 顶层窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(64, 64)
        self.accent_color = "#1677ff"

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(0.7) # 半透明效果
        
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
    """ 定位靶子控件 """
    targetReleased = pyqtSignal(int, int)
    targetHovered = pyqtSignal(int, int) # 新增：拖动过程中的实时坐标信号

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
        
        # 绘制靶心样式
        color = QColor(self.parent().accent_color if hasattr(self.parent(), 'accent_color') else "#1677ff")
        painter.setPen(QPen(color, 3))
        
        # 外圈
        painter.drawEllipse(10, 10, 44, 44)
        # 内圈
        painter.drawEllipse(22, 22, 20, 20)
        # 十字准星
        painter.drawLine(32, 5, 32, 20)
        painter.drawLine(32, 44, 32, 59)
        painter.drawLine(5, 32, 20, 32)
        painter.drawLine(44, 32, 59, 32)
        # 中心点
        painter.setBrush(color)
        painter.drawEllipse(30, 30, 4, 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.setCursor(Qt.BlankCursor) # 拖动时隐藏鼠标
            
            # 创建影子靶子
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
            # 实时发射坐标信号
            self.targetHovered.emit(global_pos.x(), global_pos.y())

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.releaseMouse()
            self.setCursor(Qt.PointingHandCursor)
            
            if self.ghost:
                self.ghost.hide()
            
            # 获取全局坐标
            global_pos = event.globalPos()
            self.targetReleased.emit(global_pos.x(), global_pos.y())

class WindowToolInterface(QWidget):
    """ 窗口弹窗定位工具界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("WindowToolInterface")
        self.accent_color = "#1677ff"
        
        # 高亮边框窗口
        self.highlighter = HighlightWindow()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("窗口弹窗定位工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 离线标识
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 简介
        self.desc = BodyLabel("拖动下方的靶子到目标窗口上，松开即可识别窗口信息。", self)
        layout.addWidget(self.desc)

        # 靶子容器
        target_container = QHBoxLayout()
        target_container.addStretch(1)
        self.target_btn = TargetWidget(self)
        target_container.addWidget(self.target_btn)
        target_container.addStretch(1)
        layout.addLayout(target_container)

        # 信息显示区域
        self.info_group = QWidget()
        info_layout = QGridLayout(self.info_group)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        
        # 样式定义
        self.label_style = "font-size: 13px; font-weight: 600;"
        self.value_style = "font-size: 13px; color: #666666;"

        # 初始化显示项
        self.add_info_row(info_layout, "窗口标题:", 0)
        self.add_info_row(info_layout, "进程名称:", 1)
        self.add_info_row(info_layout, "窗口句柄:", 2)
        self.add_info_row(info_layout, "进程 ID:", 3)
        self.add_info_row(info_layout, "程序路径:", 4)

        self.info_group.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 8px;")
        layout.addWidget(self.info_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.btn_open_loc = PrimaryPushButton(FIF.FOLDER, "打开文件位置", self)
        self.btn_copy_path = PushButton(FIF.COPY, "复制路径", self)
        self.btn_copy_title = PushButton(FIF.COPY, "复制窗口标题", self)
        self.btn_kill_proc = PushButton(FIF.DELETE, "结束进程", self)
        self.btn_kill_proc.setStyleSheet("PushButton { color: #ff4d4f; } PushButton:hover { color: #ff7875; }")
        
        btn_layout.addWidget(self.btn_open_loc)
        btn_layout.addWidget(self.btn_copy_path)
        btn_layout.addWidget(self.btn_copy_title)
        btn_layout.addWidget(self.btn_kill_proc)
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)
        
        layout.addStretch(1)

        # 绑定信号
        self.target_btn.targetHovered.connect(self.on_target_hovered)
        self.target_btn.targetReleased.connect(self.on_target_released)
        self.btn_open_loc.clicked.connect(self.on_open_location)
        self.btn_copy_path.clicked.connect(self.on_copy_path)
        self.btn_copy_title.clicked.connect(self.on_copy_title)
        self.btn_kill_proc.clicked.connect(self.on_kill_process)
        
        # 初始状态
        self.current_info = None
        self.btn_open_loc.setEnabled(False)
        self.btn_copy_path.setEnabled(False)
        self.btn_copy_title.setEnabled(False)
        self.btn_kill_proc.setEnabled(False)

    def add_info_row(self, layout, label_text, row):
        label = BodyLabel(label_text, self)
        label.setStyleSheet(self.label_style)
        value = BodyLabel("--", self)
        value.setStyleSheet(self.value_style)
        value.setWordWrap(True)
        
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)
        
        # 保存引用以便更新
        attr_name = f"val_{row}"
        setattr(self, attr_name, value)

    def on_target_hovered(self, x, y):
        """ 拖动过程中的实时高亮 """
        info = get_window_info_at(x, y)
        if info and info.get('rect'):
            # 排除当前程序窗口的高亮 (避免干扰)
            if info['hwnd'] != int(self.window().winId()):
                self.highlighter.show_highlight(info['rect'], self.accent_color)
            else:
                self.highlighter.hide()
        else:
            self.highlighter.hide()

    def on_target_released(self, x, y):
        # 释放时立即隐藏高亮边框
        self.highlighter.hide()
        
        info = get_window_info_at(x, y)
        if not info:
            InfoBar.warning("提示", "未识别到有效窗口", duration=2000, parent=self.window())
            return

        self.current_info = info
        self.val_0.setText(info['title'] if info['title'] else "(无标题)")
        self.val_1.setText(info['process_name'])
        self.val_2.setText(hex(info['hwnd']))
        self.val_3.setText(str(info['pid']))
        self.val_4.setText(info['process_path'])
        
        self.btn_open_loc.setEnabled(bool(info['process_path'] and info['process_path'] != "未知"))
        self.btn_copy_path.setEnabled(bool(info['process_path'] and info['process_path'] != "未知"))
        self.btn_copy_title.setEnabled(bool(info['title']))
        self.btn_kill_proc.setEnabled(bool(info['pid']))
        
        InfoBar.success("识别成功", f"已定位到窗口: {info['process_name']}", duration=2000, parent=self.window())

    def on_open_location(self):
        if self.current_info and self.current_info['process_path']:
            if not open_file_location(self.current_info['process_path']):
                InfoBar.error("错误", "无法打开文件位置，路径可能不存在或无权限访问", duration=3000, parent=self.window())

    def on_copy_path(self):
        if self.current_info and self.current_info['process_path']:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.current_info['process_path'])
            InfoBar.success("成功", "程序路径已复制到剪贴板", duration=2000, parent=self.window())

    def on_copy_title(self):
        if self.current_info and self.current_info['title']:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.current_info['title'])
            InfoBar.success("成功", "窗口标题已复制到剪贴板", duration=2000, parent=self.window())

    def on_kill_process(self):
        if not self.current_info or not self.current_info['pid']:
            return
            
        import psutil
        pid = self.current_info['pid']
        name = self.current_info['process_name']
        
        msg_box = MessageBox(
            "确认结束进程",
            f"确定要结束进程 {name} (PID: {pid}) 吗？\n未保存的数据将会丢失！",
            self.window()
        )
        msg_box.yesButton.setText("确定结束")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec_():
            try:
                proc = psutil.Process(pid)
                proc.kill()
                InfoBar.success("成功", f"进程 {name} 已结束", duration=3000, parent=self.window())
                # 重置界面
                self.current_info = None
                for i in range(5):
                    getattr(self, f"val_{i}").setText("--")
                self.btn_open_loc.setEnabled(False)
                self.btn_copy_path.setEnabled(False)
                self.btn_copy_title.setEnabled(False)
                self.btn_kill_proc.setEnabled(False)
            except Exception as e:
                InfoBar.error("失败", f"无法结束进程: {str(e)}", duration=3000, parent=self.window())

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def set_theme(self, is_dark):
        """ 设置页面主题 """
        if is_dark:
            bg_color = "#1d1d1d"
            text_color = "#e0e0e0"
            val_color = "#a0a0a0"
            group_bg = "rgba(255,255,255,0.05)"
        else:
            bg_color = "#f7f9fc"
            text_color = "#333333"
            val_color = "#666666"
            group_bg = "rgba(0,0,0,0.05)"

        self.setStyleSheet(f"#WindowToolInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.desc.setStyleSheet(f"color:{val_color};")
        self.info_group.setStyleSheet(f"background-color: {group_bg}; border-radius: 8px;")
        
        # 更新所有标签
        for i in range(5):
            getattr(self, f"val_{i}").setStyleSheet(f"color:{val_color}; font-size: 13px;")

class ShredderInterface(QWidget):
    """ 文件粉碎界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ShredderInterface")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("文件粉碎", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 离线标识
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self.desc = BodyLabel("将需要销毁的文件或文件夹拖入此处，或点击下方按钮添加。", self)
        layout.addWidget(self.desc)

        # 文件列表
        self.file_list = TableWidget(self)
        self.file_list.setColumnCount(3)
        self.file_list.setHorizontalHeaderLabels(["路径", "类型", "当前状态"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.file_list.setColumnWidth(1, 100)
        self.file_list.setColumnWidth(2, 120)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.file_list)

        # 按钮栏
        btn_layout = QHBoxLayout()
        self.btn_add_file = PushButton(FIF.ADD, "添加文件", self)
        self.btn_add_folder = PushButton(FIF.FOLDER, "添加文件夹", self)
        self.btn_remove = PushButton(FIF.REMOVE, "移除选中", self)
        self.btn_clear = PushButton(FIF.DELETE, "清空列表", self)
        self.btn_shred = PrimaryPushButton(FIF.BROOM, "立即粉碎", self)
        
        btn_layout.addWidget(self.btn_add_file)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_shred)
        layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("", self)
        layout.addWidget(self.status_label)

        # 绑定信号
        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_shred.clicked.connect(self.start_shredding)

        self.paths = set()
        self.system_paths = set() # 新增：记录系统文件路径
        self.update_desc()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_paths(files)

    def add_files(self):
        from PyQt5.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*.*)")
        if files:
            self.add_paths(files)

    def add_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths):
        to_validate = []
        for path in paths:
            path = os.path.normpath(path)
            if path in self.paths or path in self.system_paths:
                continue

            # 快速路径校验（不检查进程占用，防止 UI 卡死）
            is_sys, reason = is_system_path(path, check_processes=False)
            
            row = self.file_list.rowCount()
            self.file_list.insertRow(row)
            
            # 路径列：使用中间省略
            fm = self.file_list.fontMetrics()
            elided_path = fm.elidedText(path, Qt.ElideMiddle, 400) # 初始宽度，拉伸会自动更新吗？不，TableWidget 不会自动更新 elidedText
            # 更好的做法是存储原始路径在 UserRole，显示 elided
            path_item = QTableWidgetItem(elided_path)
            path_item.setData(Qt.UserRole, path)
            path_item.setToolTip(path)
            self.file_list.setItem(row, 0, path_item)
            
            if is_sys:
                self.system_paths.add(path)
                # 类型列
                type_item = QTableWidgetItem("【系统文件】")
                type_item.setForeground(QColor("#ff4d4f"))
                self.file_list.setItem(row, 1, type_item)
                
                # 状态列
                status_item = QTableWidgetItem("禁止粉碎 (系统文件)")
                status_item.setForeground(QColor("#ff4d4f"))
                self.file_list.setItem(row, 2, status_item)
                
                InfoBar.warning(
                    "安全提示",
                    f"检测到系统关键文件：{os.path.basename(path)}\n已自动标记为禁止粉碎，如需移除请手动清空列表。",
                    duration=5000,
                    parent=self.window()
                )
            else:
                self.paths.add(path)
                # 更准确的类型显示
                if os.path.isdir(path):
                    file_type = "文件夹"
                else:
                    ext = os.path.splitext(path)[1].lower()
                    type_map = {
                        '.py': 'Python 脚本',
                        '.html': 'HTML 文档',
                        '.htm': 'HTML 文档',
                        '.txt': '文本文件',
                        '.pdf': 'PDF 文档',
                        '.docx': 'Word 文档',
                        '.xlsx': 'Excel 表格',
                        '.jpg': 'JPEG 图片',
                        '.png': 'PNG 图片',
                        '.exe': '可执行程序',
                        '.zip': '压缩文件',
                        '.rar': '压缩文件'
                    }
                    file_type = type_map.get(ext, f"{ext[1:].upper() if ext else '未知'} 文件")
                
                self.file_list.setItem(row, 1, QTableWidgetItem(file_type))
                self.file_list.setItem(row, 2, QTableWidgetItem("待粉碎"))
                to_validate.append(path)
        
        # 启动后台校验 worker 检查占用情况
        if to_validate:
            self.status_label.setText("正在执行深度安全检查...")
            self.validator = ValidationWorker(to_validate)
            self.validator.finished.connect(self.on_validation_finished)
            self.validator.start()
            
        self.update_desc()

    def show_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        path = self.file_list.item(row, 0).data(Qt.UserRole)
        
        menu = QMenu(self)
        copy_path_action = QAction(FIF.COPY.icon(), "复制路径", self)
        open_loc_action = QAction(FIF.FOLDER.icon(), "打开文件位置", self)
        remove_action = QAction(FIF.REMOVE.icon(), "从列表中移除", self)
        
        copy_path_action.triggered.connect(lambda: QApplication.clipboard().setText(path))
        open_loc_action.triggered.connect(lambda: open_file_location(path))
        remove_action.triggered.connect(self.remove_selected)
        
        menu.addAction(copy_path_action)
        menu.addAction(open_loc_action)
        menu.addSeparator()
        menu.addAction(remove_action)
        
        menu.exec_(self.file_list.viewport().mapToGlobal(pos))

    def on_validation_finished(self, path, is_sys, reason):
        """ 后台深度校验回调 """
        self.status_label.setText("")
        if is_sys:
            # 发现是被系统占用的文件，将其转入系统文件列表
            if path in self.paths:
                self.paths.remove(path)
            self.system_paths.add(path)
            
            # 更新 UI 状态
            for row in range(self.file_list.rowCount()):
                if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                    # 更新类型列
                    type_item = QTableWidgetItem("【系统占用】")
                    type_item.setForeground(QColor("#ff4d4f"))
                    self.file_list.setItem(row, 1, type_item)
                    
                    # 更新状态列
                    status_item = QTableWidgetItem("禁止粉碎 (系统占用)")
                    status_item.setForeground(QColor("#ff4d4f"))
                    self.file_list.setItem(row, 2, status_item)
                    break
            
            InfoBar.warning(
                "安全提示",
                f"文件被系统关键进程占用：{os.path.basename(path)}\n已标记为禁止操作。",
                duration=3000,
                parent=self.window()
            )
            self.update_desc()

    def remove_path(self, path):
        """ 移除指定路径的文件 """
        for row in range(self.file_list.rowCount()):
            if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                self.file_list.removeRow(row)
                break
        if path in self.paths:
            self.paths.remove(path)
        if path in self.system_paths:
            self.system_paths.remove(path)
        self.update_desc()

    def remove_selected(self):
        selected_ranges = self.file_list.selectedRanges()
        if not selected_ranges:
            return
        
        # 从后往前删，避免索引偏移
        rows_to_remove = []
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows_to_remove.append(row)
        
        rows_to_remove = sorted(list(set(rows_to_remove)), reverse=True)
        for row in rows_to_remove:
            path = self.file_list.item(row, 0).data(Qt.UserRole)
            if path in self.paths:
                self.paths.remove(path)
            if path in self.system_paths:
                self.system_paths.remove(path)
            self.file_list.removeRow(row)
        self.update_desc()

    def clear_list(self):
        self.paths.clear()
        self.system_paths.clear()
        self.file_list.setRowCount(0)
        self.update_desc()

    def update_desc(self):
        if not self.paths and not self.system_paths:
            self.desc.setText("当前没有待粉碎文件，请拖入需要处理的文件。")
            self.btn_shred.setEnabled(False)
        elif self.system_paths and not self.paths:
            self.desc.setText("列表仅包含系统关键文件，已禁止粉碎操作。")
            self.btn_shred.setEnabled(False)
        elif self.system_paths and self.paths:
            self.desc.setText(f"已选择 {len(self.paths)} 个项目，包含系统文件（已跳过）。")
            self.btn_shred.setEnabled(True)
        else:
            self.desc.setText(f"已选择 {len(self.paths)} 个项目，准备粉碎。")
            self.btn_shred.setEnabled(True)

    def start_shredding(self):
        if not self.paths:
            InfoBar.warning("提示", "请先添加需要粉碎的文件或文件夹", duration=2000, parent=self.window())
            return

        msg_box = MessageBox(
            "确认粉碎",
            "确定要粉碎选中的文件吗？粉碎后数据将无法恢复，且会尝试解除占用强制删除！",
            self.window()
        )
        msg_box.yesButton.setText("确定粉碎")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec_():
            self.set_controls_enabled(False)
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            self.worker = ShredderWorker(list(self.paths))
            self.worker.progress.connect(self.on_progress)
            self.worker.file_finished.connect(self.on_file_finished)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

    def on_file_finished(self, path, success, msg):
        """ 单个文件处理完成的回调 """
        for row in range(self.file_list.rowCount()):
            if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                status_item = QTableWidgetItem(msg)
                if success:
                    status_item.setForeground(QColor("#27ae60")) # 绿色
                else:
                    status_item.setForeground(QColor("#ff4d4f")) # 红色
                self.file_list.setItem(row, 2, status_item)
                break

    def set_controls_enabled(self, enabled):
        """ 控制界面按钮的可操作性 """
        self.btn_shred.setEnabled(enabled)
        self.btn_add_file.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def on_finished(self, success, fail, errors):
        self.set_controls_enabled(True)
        self.progress_bar.hide()
        self.status_label.setText("")
        
        if fail == 0:
            InfoBar.success("粉碎完成", "文件已彻底粉碎，无法恢复", duration=3000, parent=self.window())
        else:
            msg = f"成功: {success}, 失败: {fail}"
            if errors:
                msg += "\n部分错误: " + "\n".join(errors[:3])
            InfoBar.error("部分项目粉碎失败", msg, duration=5000, parent=self.window())
        
        # 粉碎完成后移除已成功粉碎的路径记录，但保留在列表中显示
        paths_to_remove = []
        for path in self.paths:
            # 检查列表中该路径的状态
            for row in range(self.file_list.rowCount()):
                if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                    if self.file_list.item(row, 2).text() == "已粉碎":
                        paths_to_remove.append(path)
                    break
        
        for p in paths_to_remove:
            self.paths.remove(p)
            
        self.update_desc()

    def set_theme(self, is_dark):
        if is_dark:
            bg_color = "#1d1d1d"
            text_color = "#e0e0e0"
            sub_text = "#a0a0a0"
        else:
            bg_color = "#f7f9fc"
            text_color = "#333333"
            sub_text = "#666666"

        self.setStyleSheet(f"#ShredderInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.desc.setStyleSheet(f"color:{sub_text};")
        self.status_label.setStyleSheet(f"color:{sub_text};")

class ConverterInterface(QWidget):
    """ 综合格式转换界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ConverterInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("万能格式转换", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 离线标识
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 分类切换按钮
        self.category_layout = QHBoxLayout()
        self.btn_img_cat = PushButton("图片转换", self)
        self.btn_doc_cat = PushButton("文档转换", self)
        self.category_layout.addWidget(self.btn_img_cat)
        self.category_layout.addWidget(self.btn_doc_cat)
        self.category_layout.addStretch(1)
        layout.addLayout(self.category_layout)

        # 堆栈布局处理不同分类
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        # --- 图片转换面板 ---
        self.img_panel = QWidget()
        img_layout = QVBoxLayout(self.img_panel)
        img_layout.setContentsMargins(0, 10, 0, 0)
        img_layout.setSpacing(15)

        self.img_card = QWidget()
        self.img_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        img_card_layout = QVBoxLayout(self.img_card)
        
        self.img_type_box = ComboBox()
        self.img_type_box.addItems(["SVG 转 ICO", "SVG 转 PNG", "图片通用转换 (PNG/JPG/WebP/BMP)"])
        img_card_layout.addWidget(StrongBodyLabel("转换模式"))
        img_card_layout.addWidget(self.img_type_box)

        self.img_path_edit = SearchLineEdit()
        self.img_path_edit.setPlaceholderText("选择源图片文件...")
        self.img_path_edit.setReadOnly(True)
        self.img_path_edit.searchButton.hide() # 隐藏失效的放大镜按钮
        self.btn_img_browse = PushButton("选择文件")
        
        row = QHBoxLayout()
        row.addWidget(self.img_path_edit)
        row.addWidget(self.btn_img_browse)
        img_card_layout.addLayout(row)

        self.img_target_format = ComboBox()
        self.img_target_format.addItems(["PNG", "JPG", "WebP", "BMP", "ICO"])
        self.img_target_format.hide() # 仅在通用转换时显示
        self.img_target_label = StrongBodyLabel("目标格式")
        self.img_target_label.hide()
        img_card_layout.addWidget(self.img_target_label)
        img_card_layout.addWidget(self.img_target_format)

        self.btn_img_convert = PrimaryPushButton("开始转换图片")
        self.btn_img_convert.setEnabled(False)
        img_card_layout.addWidget(self.btn_img_convert)
        img_layout.addWidget(self.img_card)
        img_layout.addStretch(1)

        # --- 文档转换面板 ---
        self.doc_panel = QWidget()
        doc_layout = QVBoxLayout(self.doc_panel)
        doc_layout.setContentsMargins(0, 10, 0, 0)
        doc_layout.setSpacing(15)

        self.doc_card = QWidget()
        self.doc_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        doc_card_layout = QVBoxLayout(self.doc_card)

        self.doc_type_box = ComboBox()
        self.doc_type_box.addItems(["PDF 转 Word", "Word 转 PDF", "Word 提取表格到 Excel", "Excel 转 Word 表格"])
        doc_card_layout.addWidget(StrongBodyLabel("转换模式"))
        doc_card_layout.addWidget(self.doc_type_box)

        self.doc_path_edit = SearchLineEdit()
        self.doc_path_edit.setPlaceholderText("选择源文档文件...")
        self.doc_path_edit.setReadOnly(True)
        self.doc_path_edit.searchButton.hide() # 隐藏失效的放大镜按钮
        self.btn_doc_browse = PushButton("选择文件")
        
        row2 = QHBoxLayout()
        row2.addWidget(self.doc_path_edit)
        row2.addWidget(self.btn_doc_browse)
        doc_card_layout.addLayout(row2)

        self.btn_doc_convert = PrimaryPushButton("开始转换文档")
        self.btn_doc_convert.setEnabled(False)
        doc_card_layout.addWidget(self.btn_doc_convert)
        doc_layout.addWidget(self.doc_card)
        doc_layout.addStretch(1)

        self.stack.addWidget(self.img_panel)
        self.stack.addWidget(self.doc_panel)

        # 信号绑定
        self.btn_img_cat.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_doc_cat.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.btn_img_browse.clicked.connect(self.select_img_file)
        self.btn_doc_browse.clicked.connect(self.select_doc_file)
        
        self.btn_img_convert.clicked.connect(self.do_img_convert)
        self.btn_doc_convert.clicked.connect(self.do_doc_convert)
        
        self.img_path_edit.textChanged.connect(lambda t: self.btn_img_convert.setEnabled(bool(t)))
        self.doc_path_edit.textChanged.connect(lambda t: self.btn_doc_convert.setEnabled(bool(t)))
        
        self.img_type_box.currentIndexChanged.connect(self.on_img_type_changed)

    def on_img_type_changed(self, index):
        is_general = index == 2
        self.img_target_label.setVisible(is_general)
        self.img_target_format.setVisible(is_general)

    def select_img_file(self):
        mode = self.img_type_box.currentText()
        filter_str = "图片文件 (*.svg *.png *.jpg *.jpeg *.webp *.bmp)"
        if "SVG" in mode:
            filter_str = "SVG 文件 (*.svg)"
        
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", filter_str)
        if path:
            self.img_path_edit.setText(path)

    def select_doc_file(self):
        mode = self.doc_type_box.currentText()
        filter_str = "文档文件 (*.pdf *.docx *.xlsx *.xls)"
        if "PDF" in mode: filter_str = "PDF 文件 (*.pdf)"
        elif "Word" in mode: filter_str = "Word 文档 (*.docx)"
        elif "Excel" in mode: filter_str = "Excel 表格 (*.xlsx *.xls)"
        
        path, _ = QFileDialog.getOpenFileName(self, "选择文档", "", filter_str)
        if path:
            self.doc_path_edit.setText(path)

    def do_img_convert(self):
        input_path = self.img_path_edit.text()
        mode = self.img_type_box.currentText()
        
        if mode == "SVG 转 ICO":
            default_name = os.path.splitext(os.path.basename(input_path))[0] + ".ico"
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 ICO", default_name, "ICO 图标 (*.ico)")
            if save_path:
                success, msg = svg_to_ico(input_path, save_path)
        elif mode == "SVG 转 PNG":
            # 复用逻辑，这里简单处理
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 PNG", "output.png", "PNG 图片 (*.png)")
            if save_path:
                from modules.file_converter import image_convert
                # 注意：这里需要专门的 SVG -> PNG，由于 SVG 是矢量，用 QImage 渲染
                renderer = QSvgRenderer(input_path)
                image = QImage(1024, 1024, QImage.Format_ARGB32)
                image.fill(Qt.transparent)
                painter = QPainter(image)
                renderer.render(painter)
                painter.end()
                success = image.save(save_path, "PNG")
                msg = "成功" if success else "失败"
        else:
            target_fmt = self.img_target_format.currentText()
            save_path, _ = QFileDialog.getSaveFileName(self, f"保存 {target_fmt}", f"output.{target_fmt.lower()}", f"{target_fmt} 图片 (*.{target_fmt.lower()})")
            if save_path:
                success, msg = image_convert(input_path, save_path, target_fmt)

        if save_path:
            if success: InfoBar.success("转换成功", "文件已保存", duration=3000, parent=self.window())
            else: InfoBar.error("转换失败", msg, duration=5000, parent=self.window())

    def do_doc_convert(self):
        input_path = self.doc_path_edit.text()
        mode = self.doc_type_box.currentText()
        success, msg = False, "未执行"
        save_path = None

        if mode == "PDF 转 Word":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Word", "output.docx", "Word 文档 (*.docx)")
            if save_path: success, msg = pdf_to_word(input_path, save_path)
        elif mode == "Word 转 PDF":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 PDF", "output.pdf", "PDF 文档 (*.pdf)")
            if save_path: success, msg = word_to_pdf(input_path, save_path)
        elif mode == "Word 提取表格到 Excel":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Excel", "tables.xlsx", "Excel 表格 (*.xlsx)")
            if save_path: success, msg = word_to_excel(input_path, save_path)
        elif mode == "Excel 转 Word 表格":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Word", "output.docx", "Word 文档 (*.docx)")
            if save_path: success, msg = excel_to_word(input_path, save_path)

        if save_path:
            if success: InfoBar.success("转换成功", "文件已保存", duration=3000, parent=self.window())
            else: InfoBar.error("转换失败", msg, duration=5000, parent=self.window())

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, text_color, sub_text, card_bg = "#1d1d1d", "#e0e0e0", "#a0a0a0", "rgba(255, 255, 255, 0.05)"
        else:
            bg_color, text_color, sub_text, card_bg = "#f7f9fc", "#333333", "#666666", "rgba(0, 0, 0, 0.05)"

        self.setStyleSheet(f"#ConverterInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.img_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px;")
        self.doc_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px;")

class SettingsInterface(QWidget):
    """ 设置界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingsInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        self.title = SubtitleLabel("应用设置", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(self.title)

        self.cb_auto_start = CheckBox("开机自启动", self)
        self.cb_auto_start.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.cb_auto_start)

        self.cb_minimize_tray = CheckBox("关闭时最小化到系统托盘", self)
        self.cb_minimize_tray.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.cb_minimize_tray)

        layout.addSpacing(20)
        theme_label = StrongBodyLabel("应用主题", self)
        theme_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(theme_label)
        
        self.theme_box = ComboBox(self)
        self.theme_box.addItems(["浅色", "深色"])
        self.theme_box.setFixedWidth(200)
        layout.addWidget(self.theme_box)

        layout.addSpacing(20)
        cache_label = StrongBodyLabel("缓存清理", self)
        cache_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(cache_label)
        
        self.btn_clean_cache = PushButton(FIF.DELETE, "清理缓存 (__pycache__)", self)
        self.btn_clean_cache.setFixedWidth(250)
        self.btn_clean_cache.clicked.connect(self.on_clean_cache)
        layout.addWidget(self.btn_clean_cache)

        # 免责声明按钮
        layout.addSpacing(20)
        disclaimer_label = StrongBodyLabel("法律声明", self)
        disclaimer_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(disclaimer_label)
        
        self.btn_disclaimer = PushButton(FIF.INFO, "查看免责声明", self)
        self.btn_disclaimer.setFixedWidth(250)
        layout.addWidget(self.btn_disclaimer)

        layout.addSpacing(30)
        changelog_label = StrongBodyLabel("更新日志 (v1.1.9)", self)
        changelog_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(changelog_label)

        self.changelog_display = TextEdit(self)
        self.changelog_display.setReadOnly(True)
        self.changelog_display.setFixedHeight(150)
        self.changelog_display.setText(
            "v1.1.9 (2026-01-18)\n"
            "1. [优化] 硬件扫描加速：本机配置信息改为后台异步加载，点击即显提示，不再卡顿。\n"
            "2. [修复] 显卡精准识别：显卡型号现在可以显示具体型号（如 RTX 4060），不再仅显示品牌。\n"
            "3. [修复] 网络详情修复：解决部分系统环境下 netsh 命令编码导致的获取信息失败问题。\n"
            "4. [适配] 家庭版识别：针对 Windows 家庭版自动禁用组策略按钮并添加悬停提示。\n"
            "5. [优化] 磁盘类型识别：增加缓存机制，提升 SSD/HDD 识别效率。\n"
            "6. [新增] 免责声明：加入首次启动强制确认机制，确保软件合规使用。"
        )
        layout.addWidget(self.changelog_display)

        layout.addStretch(1)

    def on_clean_cache(self):
        msg_box = MessageBox(
            "确认清理缓存",
            "确定要清理所有 __pycache__ 文件夹吗？\n这不会影响程序运行，但下次启动时可能会略微变慢。",
            self.window()
        )
        msg_box.yesButton.setText("确定清理")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec_():
            count = clean_cache(".")
            InfoBar.success(
                "清理成功",
                f"已成功清理 {count} 个缓存目录。",
                duration=3000,
                parent=self.window()
            )

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self._speed_phase = None
        self._speed_latest_value = 0.0
        self._speed_dl_latest = 0.0
        self._speed_ul_latest = 0.0
        self._last_speed_result = None
        self._speed_chart_timer = QTimer(self)
        self._speed_chart_timer.setInterval(500)
        self._speed_chart_timer.timeout.connect(self._append_speed_chart_point)
        
        # 网络监控
        self.is_online = True
        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.status_changed.connect(self._on_network_status_changed)
        self.network_monitor.start()

        # 初始化界面
        self.ip_interface = IPInterface(self)
        self.system_interface = SystemInterface(self)
        self.speed_interface = SpeedTestInterface(self)
        self.shredder_interface = ShredderInterface(self)
        self.converter_interface = ConverterInterface(self)
        self.window_tool_interface = WindowToolInterface(self)
        self.settings_interface = SettingsInterface(self)

        self.init_navigation()
        self.init_window()
        self.init_tray()
        self.connect_signals()
        
        # 加载配置
        self.load_config_to_ui()
        self._load_speed_ip_info()

        # 首次启动检查免责声明
        QTimer.singleShot(500, self.check_disclaimer)

    def check_disclaimer(self):
        """ 检查是否已同意免责声明 """
        if not self.settings.get("disclaimer_accepted", False):
            self.show_disclaimer(is_first_time=True)

    def show_disclaimer(self, is_first_time=False):
        """ 显示免责声明弹窗 """
        try:
            with open("disclaimer.txt", "r", encoding="utf-8") as f:
                content = f.read()
        except:
            content = "免责声明文件丢失，请联系开发者。"

        title = "免责声明" if not is_first_time else "欢迎使用 - 免责声明"
        w = MessageBox(title, content, self.window())
        w.yesButton.setText("我已阅读并同意")
        w.cancelButton.setText("拒绝并退出" if is_first_time else "关闭")

        if w.exec():
            if is_first_time:
                self.settings["disclaimer_accepted"] = True
                save_settings(self.settings)
                InfoBar.success("感谢支持", "您已同意免责声明，可以开始使用了", duration=3000, parent=self.window())
        else:
            if is_first_time:
                # 拒绝同意，退出程序
                QApplication.quit()
                sys.exit(0)

    def init_navigation(self):
        self.addSubInterface(self.ip_interface, FIF.GLOBE, 'IP查询')
        self.addSubInterface(self.speed_interface, FIF.SPEED_HIGH, '网速测试')
        self.addSubInterface(self.shredder_interface, FIF.BROOM, '文件粉碎')
        self.addSubInterface(self.converter_interface, FIF.PHOTO, '格式转换')
        self.addSubInterface(self.window_tool_interface, FIF.SEARCH, '窗口定位')
        self.addSubInterface(self.system_interface, FIF.APPLICATION, '系统功能')
        self.addSubInterface(self.settings_interface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)
        
        # 添加网络状态标识 (底部)
        self.net_status_item = self.navigationInterface.addItem(
            routeKey='NetStatus',
            icon=FIF.WIFI,
            text='正在检查网络...',
            onClick=self._show_network_details,
            position=NavigationItemPosition.BOTTOM,
            selectable=False
        )
        # self.net_status_item.setEnabled(False) # 已启用，支持点击查看详情

        # 添加 GitHub 图标 (点击直接跳转，不进入选中状态)
        import webbrowser
        self.github_item = self.navigationInterface.addItem(
            routeKey='GitHub',
            icon=FIF.GITHUB,
            text='GitHub',
            onClick=lambda: webbrowser.open("https://github.com/liaozixing/Windows-Desktop-Tool"),
            position=NavigationItemPosition.BOTTOM,
            selectable=False
        )
        # 为 GitHub 添加悬停提示
        self.github_item.setToolTip("项目地址")
        self.github_item.installEventFilter(ToolTipFilter(self.github_item, 500, ToolTipPosition.RIGHT))

    def _show_network_details(self):
        """ 显示详细的网络连接信息 """
        details = "正在获取网络信息..."
        if not self.is_online:
            details = "❌ 当前未连接到互联网"
        else:
            try:
                # 获取本地 IP
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                # 获取无线网络信息 (针对 Windows)
                ssid = "未知 (可能为有线连接)"
                signal = "未知"
                try:
                    # 使用 chcp 65001 确保输出为 UTF-8 编码，或者捕获异常
                    cmd = "netsh wlan show interfaces"
                    # 使用 subprocess.run 配合 capture_output 以便更精细地控制编码
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
                    output = result.stdout
                    
                    for line in output.split('\n'):
                        if " SSID" in line and "BSSID" not in line:
                            ssid = line.split(":")[1].strip()
                        if "信号" in line or "Signal" in line:
                            signal = line.split(":")[1].strip()
                except:
                    pass
                
                details = (
                    f"✅ 网络已连接\n\n"
                    f"🌐 本地 IP: {local_ip}\n"
                    f"📶 无线名称 (SSID): {ssid}\n"
                    f"📡 信号强度: {signal}\n"
                    f"💻 计算机名: {hostname}"
                )
            except Exception as e:
                details = f"✅ 网络已连接\n(详细信息获取失败: {str(e)})"

        mb = MessageBox("网络连接详情", details, self)
        mb.yesButton.setText("确定")
        mb.cancelButton.hide()
        mb.exec_()

    def _on_network_status_changed(self, is_online):
        """ 网络状态改变回调 """
        self.is_online = is_online
        status_text = "网络已连接" if is_online else "网络未连接"
        
        # 使用不同的图标表示状态
        if is_online:
            status_icon = FIF.WIFI
            color = QColor(39, 174, 96) # 绿色
        else:
            status_icon = FIF.INFO # 离线状态图标
            color = QColor(232, 17, 35) # 红色
        
        # 更新导航栏显示
        widget = self.navigationInterface.widget('NetStatus')
        if widget:
            widget.setText(status_text)
            widget.setIcon(status_icon)
        
        # 通知各界面更新 UI 状态
        for interface_attr in ['ip_interface', 'speed_interface', 'converter_interface', 
                             'system_interface', 'shredder_interface', 'window_tool_interface']:
            if hasattr(self, interface_attr):
                interface = getattr(self, interface_attr)
                if hasattr(interface, 'update_network_status'):
                    interface.update_network_status(is_online)
        
        # 提示信息
        if not is_online:
            InfoBar.warning(
                "网络连接已断开",
                "查询 IP、网速测试等网络功能将暂时不可用。",
                duration=5000,
                parent=self
            )
        else:
            # 只有当从离线变为在线时才提示（避免启动时提示）
            if hasattr(self, '_last_online_state') and not self._last_online_state:
                InfoBar.success(
                    "网络已恢复",
                    "所有网络功能已恢复正常使用。",
                    duration=3000,
                    parent=self
                )
        
        self._last_online_state = is_online

    def init_window(self):
        self.setWindowTitle("全能Windows桌面工具 v1.1.9")
        self.resize(750, 520)
        
        # 使用 SVG 图标，确保矢量图形在任何缩放比例下都清晰且保留透明度
        icon_path = "app.svg"
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
        
        # 内存中仅保留一份图标资源
        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(self.app_icon)
        
        # 强制设置初始主题为深色
        setTheme(Theme.DARK)
        
        # 确保在窗口首次显示时再次强制刷新一次主题样式
        QTimer.singleShot(100, self._sync_theme_styles)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # 系统托盘图标也必须保留透明度，使用同一份图标资源
        if hasattr(self, 'app_icon'):
            self.tray_icon.setIcon(self.app_icon)
        else:
             icon_path = "app.svg"
             if hasattr(sys, '_MEIPASS'):
                 icon_path = os.path.join(sys._MEIPASS, icon_path)
             self.tray_icon.setIcon(QIcon(icon_path))
        
        tray_menu = QMenu()
        show_action = QAction("显示主界面", self)
        show_action.triggered.connect(self.showNormal)
        
        exit_action = QAction("退出程序", self)
        exit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def connect_signals(self):
        self.ip_interface.btn_query.clicked.connect(self.query_ip)
        self.speed_interface.btn_start.clicked.connect(self.start_speed_test)
        self.speed_interface.btn_settings.clicked.connect(self.speed_interface.toggle_settings)
        self.speed_interface.unit_box.currentTextChanged.connect(self._on_speed_unit_changed)
        self.speed_interface.range_box.currentTextChanged.connect(self._on_speed_range_changed)

        self.settings_interface.cb_auto_start.stateChanged.connect(self.update_settings)
        self.settings_interface.cb_minimize_tray.stateChanged.connect(self.update_settings)
        self.settings_interface.theme_box.currentTextChanged.connect(self.update_settings)
        self.settings_interface.btn_disclaimer.clicked.connect(lambda: self.show_disclaimer(is_first_time=False))

    def _sync_theme_styles(self):
        """ 同步所有子界面和标题栏的主题样式 """
        theme_setting = self.settings.get("theme", "深色")
        
        if theme_setting == "浅色":
            is_dark = False
            setTheme(Theme.LIGHT)
        else:
            # 默认深色
            is_dark = True
            setTheme(Theme.DARK)
        
        # 同步子界面主题
        if hasattr(self, 'speed_interface'):
            self.speed_interface.set_theme(is_dark)
        if hasattr(self, 'window_tool_interface'):
            self.window_tool_interface.set_theme(is_dark)
        if hasattr(self, 'shredder_interface'):
            self.shredder_interface.set_theme(is_dark)
        if hasattr(self, 'converter_interface'):
            self.converter_interface.set_theme(is_dark)
        
        # 修复标题栏颜色
        QTimer.singleShot(150, lambda: self._update_title_bar_style(is_dark))

    def _update_title_bar_style(self, is_dark):
        """ 
        更新标题栏样式，确保控制按钮（最小化、最大化、关闭）
        在深色模式下具有高对比度（符合 WCAG 2.1 AA 标准）
        """
        if not is_dark:
            # 浅色模式：深色文字
            self.titleBar.titleLabel.setStyleSheet("""
                QLabel {
                    color: rgba(0, 0, 0, 0.85);
                    font-weight: 500;
                    background: transparent;
                }
            """)
            button_qss = ""
        else:
            # 深色模式：高对比度浅色文字
            self.titleBar.titleLabel.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.95);
                    font-weight: 500;
                    background: transparent;
                }
            """)
            
            # 针对控制按钮的样式优化，确保透明通道保留并符合无障碍标准
            button_qss = """
                TitleBarButton {
                    color: #FFFFFF;
                    background-color: transparent;
                    border: none;
                }
                TitleBarButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                }
                TitleBarButton:pressed {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                #closeBtn:hover {
                    background-color: #E81123;
                    color: white;
                }
            """
        
        # 统一应用样式到标题栏按钮
        for btn in [self.titleBar.minBtn, self.titleBar.maxBtn, self.titleBar.closeBtn]:
            if btn:
                btn.setStyleSheet(button_qss)
        
        # 查找并更新其他可能的标题栏按钮（如全屏、置顶按钮等）
        for btn in self.titleBar.findChildren(QWidget):
            if "TitleBarButton" in btn.__class__.__name__:
                btn.setStyleSheet(button_qss)
        
        # 强制刷新标题栏以应用样式，确保响应时间 < 200ms
        self.titleBar.update()

    def apply_accent_color(self, color_hex):
        color = QColor(color_hex)
        # Update speed interface components
        self.speed_interface.btn_start.set_accent_color(color)
        self.speed_interface.gauge.set_accent_color(color)
        self.speed_interface.dl_chart.set_accent_color(color)
        self.speed_interface.ul_chart.set_accent_color(color)
        
        # Update window tool components
        self.window_tool_interface.accent_color = color_hex
        self.window_tool_interface.target_btn.update()
        
        # Update labels with standardized font sizes
        data_style = f"color:{color_hex}; font-size:18px; font-weight:700;"
        self.speed_interface.dl_value.setStyleSheet(data_style)
        self.speed_interface.ul_value.setStyleSheet(data_style)
        
        # Apply theme color to all buttons globally
        style = f"""
            PrimaryPushButton {{
                background-color: {color_hex};
                border: 1px solid {color_hex};
            }}
            PrimaryPushButton:hover {{
                background-color: {color.lighter(110).name()};
                border: 1px solid {color.lighter(110).name()};
            }}
            PrimaryPushButton:pressed {{
                background-color: {color.darker(110).name()};
                border: 1px solid {color.darker(110).name()};
            }}
            PushButton {{
                color: {color_hex};
                border: 1px solid {color_hex};
            }}
            PushButton:hover {{
                background-color: {color_hex}1A;
            }}
        """
        # We use a dedicated style property to avoid overwriting other styles
        self.setStyleSheet(style)

    def load_config_to_ui(self):
        self.settings_interface.cb_auto_start.setChecked(self.settings.get("auto_start", False))
        self.settings_interface.cb_minimize_tray.setChecked(self.settings.get("minimize_to_tray", True))
        
        # 处理可能的“跟随系统”旧配置
        current_theme = self.settings.get("theme", "深色")
        if current_theme == "跟随系统":
            current_theme = "深色"
        self.settings_interface.theme_box.setCurrentText(current_theme)
        
        # Apply accent color
        accent_color = self.settings.get("accent_color", "#1677ff")
        self.apply_accent_color(accent_color)

    def _load_speed_ip_info(self):
        # 启动时自动查询一次IP
        self.query_ip()

    def start_gp_fix(self):
        """ 启动组策略修复流程 """
        self.gp_fix_mb = MessageBox("正在安装组策略", "正在初始化安装程序...", self)
        self.gp_fix_mb.yesButton.hide()
        self.gp_fix_mb.noButton.setText("后台运行")
        
        self.gp_worker = GPFixWorker()
        self.gp_worker.progress.connect(self.on_gp_fix_progress)
        self.gp_worker.finished.connect(self.on_gp_fix_finished)
        self.gp_worker.start()
        
        self.gp_fix_mb.exec_()

    def on_gp_fix_progress(self, msg):
        if hasattr(self, 'gp_fix_mb') and self.gp_fix_mb.isVisible():
            self.gp_fix_mb.contentLabel.setText(msg)

    def on_gp_fix_finished(self, success, message):
        if hasattr(self, 'gp_fix_mb') and self.gp_fix_mb.isVisible():
            self.gp_fix_mb.done(0)
            
        if success:
            InfoBar.success("修复成功", message, duration=5000, parent=self)
            # 尝试打开
            open_group_policy()
        else:
            # 针对管理员权限报错进行友好提示
            if "管理员权限" in message:
                message = "修复失败：需要管理员权限。请尝试右键以管理员身份运行本程序后再重试。"
            InfoBar.error("修复失败", message, duration=5000, parent=self)

    def query_ip(self):
        if not self.is_online:
            InfoBar.warning("网络未连接", "请检查您的网络连接后再试", duration=3000, parent=self)
            return
        self.ip_interface.ip_info_display.setText("正在查询中，请稍候...")
        self.ip_worker = IPWorker()
        self.ip_worker.finished.connect(self.display_ip_info)
        self.ip_worker.start()

    def display_ip_info(self, info):
        if info["status"] == "success":
            raw_isp = info.get('isp', '')
            isp = "其他"
            
            # More aggressive ISP cleaning
            if any(k in raw_isp for k in ["Mobile", "移动", "CMCC"]):
                isp = "移动"
            elif any(k in raw_isp for k in ["Unicom", "联通"]):
                isp = "联通"
            elif any(k in raw_isp for k in ["Telecom", "电信"]):
                isp = "电信"
            elif any(k in raw_isp for k in ["Broadnet", "广电"]):
                isp = "广电"
            
            # For IP Interface (keep full info)
            text = (f"公网IP: {info['ip']}\n"
                    f"国家: {info['country']}\n"
                    f"地区: {info['region']}\n"
                    f"城市: {info['city']}\n"
                    f"运营商: {raw_isp}\n"
                    f"数据来源: {info.get('source', '未知')}")
            self.ip_interface.ip_info_display.setText(text)
            
            # For Speed Test Interface (simplified)
            self.speed_interface.ip_value.setText(str(info['ip']))
            self.speed_interface.isp_value.setText(isp)
            
            # Show location attribution
            region = info.get('region', '')
            city = info.get('city', '')
            loc = f"{region} {city}".strip()
            self.speed_interface.loc_value.setText(loc if loc else "未知地区")
            
            InfoBar.success("查询成功", "公网IP信息已更新", duration=2000, parent=self)
        else:
            self.ip_interface.ip_info_display.setText(f"查询失败: {info['message']}")
            self.speed_interface.ip_value.setText("--")
            self.speed_interface.isp_value.setText("查询失败")
            self.speed_interface.loc_value.setText("--")
            InfoBar.error("查询失败", info['message'], duration=3000, parent=self)

    def start_speed_test(self):
        if not self.is_online:
            InfoBar.warning("网络未连接", "请检查您的网络连接后再试", duration=3000, parent=self)
            return
        self.speed_interface.set_running(True)
        self.speed_interface.btn_start.setEnabled(False)
        self.speed_interface.dl_chart.clear()
        self.speed_interface.ul_chart.clear()
        self.speed_interface.dl_value.setText("--")
        self.speed_interface.ul_value.setText("--")
        self.speed_interface.ping_value.setText("--")
        self.speed_interface.jitter_value.setText("--")

        self.speed_interface.gauge.set_max_value(500)
        self.speed_interface.gauge.set_value(0, animated=False)
        self.speed_interface.gauge.title = "准备中"
        self.speed_interface.gauge.unit = self.speed_interface.unit_box.currentText()
        self.speed_interface.gauge.update()
        self.speed_interface.status_label.setText("正在准备测速...")

        self._speed_phase = "prepare"
        self._speed_latest_value = 0.0
        self._speed_dl_latest = 0.0
        self._speed_ul_latest = 0.0
        self._last_speed_result = None

        if self._speed_chart_timer.isActive():
            self._speed_chart_timer.stop()
        self._speed_chart_timer.start()

        self.speed_worker = SpeedTestWorker(provider="cloudflare", parent=self)
        self.speed_worker.progress.connect(self.on_speed_test_progress)
        self.speed_worker.metric.connect(self.on_speed_test_metric)
        self.speed_worker.finished.connect(self.on_speed_test_finished)
        self.speed_worker.start()

    def on_speed_test_progress(self, msg):
        self.speed_interface.status_label.setText(msg)
        if "延迟" in msg:
            self._speed_phase = "ping"
            self.speed_interface.gauge.title = "延迟"
        elif "下载" in msg:
            self._speed_phase = "download"
            self.speed_interface.gauge.title = "下载"
        elif "上传" in msg:
            self._speed_phase = "upload"
            self.speed_interface.gauge.title = "上传"

    def on_speed_test_metric(self, metric):
        unit = self.speed_interface.unit_box.currentText()
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
            self.speed_interface.dl_value.setText(f"{display_value:.2f}")
        elif phase == "upload":
            self._speed_ul_latest = display_value
            self.speed_interface.ul_value.setText(f"{display_value:.2f}")

        max_v = float(getattr(self.speed_interface.gauge, "_max_value", 100.0))
        if max_v <= 0:
            max_v = 100.0
        if display_value > max_v * 0.95:
            new_max = ((int(display_value) // 50) + 1) * 50
            self.speed_interface.gauge.set_max_value(float(new_max))

        self.speed_interface.gauge.unit = unit
        self.speed_interface.gauge.set_value(display_value, animated=True)

    def on_speed_test_finished(self, result):
        if self._speed_chart_timer.isActive():
            self._speed_chart_timer.stop()
        self.speed_interface.set_running(False)
        self.speed_interface.btn_start.setEnabled(True)
        
        if result.get("status") == "success":
            self.speed_interface.status_label.setText("测速完成")
            self._last_speed_result = result
            unit = self.speed_interface.unit_box.currentText()
            factor = 1.0 if unit == "Mbps" else 0.125
            dl_val = float(result.get("download", 0.0)) * factor
            ul_val = float(result.get("upload", 0.0)) * factor
            ping = result.get("ping")
            jitter = result.get("jitter")
            self.speed_interface.dl_value.setText(f"{dl_val:.2f}")
            self.speed_interface.ul_value.setText(f"{ul_val:.2f}")
            self.speed_interface.ping_value.setText(f"{float(ping):.0f}" if ping is not None else "--")
            self.speed_interface.jitter_value.setText(f"{float(jitter):.2f}" if jitter is not None else "--")
            InfoBar.success("测速完成", f"下载: {dl_val:.2f} {unit}, 上传: {ul_val:.2f} {unit}", duration=3000, parent=self)
        else:
            self.speed_interface.status_label.setText("测速失败")
            InfoBar.error("测速失败", result.get("message", "未知错误"), duration=3000, parent=self)

    def _append_speed_chart_point(self):
        # 0.5s定时器追加当前最新值到图表
        if self._speed_phase == "download":
            self.speed_interface.dl_chart.add_value(self._speed_dl_latest)
        elif self._speed_phase == "upload":
            self.speed_interface.ul_chart.add_value(self._speed_ul_latest)

    def _on_speed_unit_changed(self, unit):
        self.speed_interface.gauge.unit = unit

    def _on_speed_range_changed(self, text):
        if text == "自动":
            return
        try:
            v = float(text)
        except Exception:
            return
        self.speed_interface.gauge.set_max_value(v)

    def refresh_process_list(self):
        # 移除已废弃的进程管理逻辑
        pass

    def update_settings(self):
        self.settings["auto_start"] = self.settings_interface.cb_auto_start.isChecked()
        self.settings["minimize_to_tray"] = self.settings_interface.cb_minimize_tray.isChecked()
        self.settings["theme"] = self.settings_interface.theme_box.currentText()
        save_settings(self.settings)
        set_auto_start(self.settings["auto_start"])
        self._sync_theme_styles()

    def closeEvent(self, event):
        if self.settings.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("全能桌面工具", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
        else:
            self.quit_app()

    def quit_app(self):
        # 关闭所有辅助窗口
        if hasattr(self, 'window_tool_interface'):
            self.window_tool_interface.highlighter.close()
            if self.window_tool_interface.target_btn.ghost:
                self.window_tool_interface.target_btn.ghost.close()
        
        self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
