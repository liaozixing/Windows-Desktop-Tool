import sys
import os
import socket
import subprocess
# 延迟导入优化启动速度
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtGui import QIcon, QColor

from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF, 
                            MessageBox, InfoBar, setTheme, Theme, 
                            ToolTipFilter, ToolTipPosition, CheckBox)

# 导入配置和声明
from config import APP_VERSION
from disclaimer import DISCLAIMER_TEXT

# 导入自定义界面
from ui.ip_interface import IPInterface
from ui.system_interface import SystemInterface
from ui.speed_test_interface import SpeedTestInterface
from ui.shredder_interface import ShredderInterface
from ui.converter_interface import ConverterInterface
from ui.window_tool_interface import WindowToolInterface
from ui.qrcode_interface import QRCodeInterface
from ui.settings_interface import SettingsInterface
from ui.background_workers import IPWorker, SpeedTestWorker, GPFixWorker, UpdateCheckWorker
from ui.disclaimer_dialog import DisclaimerDialog

# 延迟导入（按需加载）
from modules.network_monitor import NetworkMonitor
from modules.system_functions import open_group_policy
from modules.settings import load_settings, save_settings, set_auto_start
from modules.window_tool import open_file_location

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
        
        # 优化：延迟初始化网络监控（在窗口显示后）
        self.is_online = True
        self.network_monitor = None

        # 初始化界面
        self.ip_interface = IPInterface(self)
        self.system_interface = SystemInterface(self)
        self.speed_interface = SpeedTestInterface(self)
        self.shredder_interface = ShredderInterface(self)
        self.converter_interface = ConverterInterface(self)
        self.qrcode_interface = QRCodeInterface(self)
        self.window_tool_interface = WindowToolInterface(self)
        self.settings_interface = SettingsInterface(self)

        self.init_navigation()
        self.init_window()
        self.init_tray()
        self.connect_signals()
        
        # 加载配置
        self.load_config_to_ui()
        
        # 延迟初始化网络监控（不阻塞启动）
        QTimer.singleShot(100, self._init_network_monitor)
        
        # 首次启动检查免责声明（延迟执行，不阻塞启动）
        QTimer.singleShot(500, self.check_disclaimer)

        QTimer.singleShot(2500, self._auto_check_updates_on_startup)
    
    def _init_network_monitor(self):
        """延迟初始化网络监控"""
        try:
            self.network_monitor = NetworkMonitor(self)
            self.network_monitor.status_changed.connect(self._on_network_status_changed)
            self.network_monitor.start()
        except Exception:
            pass

    def check_disclaimer(self):
        """ 检查是否已同意免责声明 """
        if not self.settings.get("disclaimer_accepted", False):
            self.show_disclaimer(is_first_time=True)

    def show_disclaimer(self, is_first_time=False):
        """ 显示免责声明弹窗 """
        content = DISCLAIMER_TEXT
        
        title = "免责声明" if not is_first_time else "欢迎使用 - 免责声明"
        w = DisclaimerDialog(title, content, self)
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
                self.quit_app(force=True)

    def init_navigation(self):
        self.addSubInterface(self.ip_interface, FIF.GLOBE, 'IP查询')
        self.addSubInterface(self.speed_interface, FIF.SPEED_HIGH, '网速测试')
        self.addSubInterface(self.shredder_interface, FIF.BROOM, '文件粉碎')
        self.addSubInterface(self.converter_interface, FIF.PHOTO, '格式转换')
        self.addSubInterface(self.qrcode_interface, FIF.QRCODE, '二维码')
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

        # 添加 GitHub 图标
        import webbrowser
        self.github_item = self.navigationInterface.addItem(
            routeKey='GitHub',
            icon=FIF.GITHUB,
            text='GitHub',
            onClick=lambda: webbrowser.open("https://github.com/liaozixing/Windows-Desktop-Tool"),
            position=NavigationItemPosition.BOTTOM,
            selectable=False
        )
        self.github_item.setToolTip("项目地址")
        self.github_item.installEventFilter(ToolTipFilter(self.github_item, 500, ToolTipPosition.RIGHT))

    def _show_network_details(self):
        """ 显示详细的网络连接信息 """
        details = "正在获取网络信息..."
        if not self.is_online:
            details = "❌ 当前未连接到互联网"
        else:
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                ssid = "未知 (可能为有线连接)"
                signal = "未知"
                try:
                    cmd = "netsh wlan show interfaces"
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
        
        if is_online:
            status_icon = FIF.WIFI
        else:
            status_icon = FIF.INFO
        
        widget = self.navigationInterface.widget('NetStatus')
        if widget:
            widget.setText(status_text)
            widget.setIcon(status_icon)
        
        for interface_attr in ['ip_interface', 'speed_interface', 'converter_interface', 'qrcode_interface',
                             'system_interface', 'shredder_interface', 'window_tool_interface']:
            if hasattr(self, interface_attr):
                interface = getattr(self, interface_attr)
                if hasattr(interface, 'update_network_status'):
                    interface.update_network_status(is_online)
        
        if not is_online:
            InfoBar.warning("网络连接已断开", "查询 IP、网速测试等网络功能将暂时不可用。", duration=5000, parent=self)
        else:
            if hasattr(self, '_last_online_state') and not self._last_online_state:
                InfoBar.success("网络已恢复", "所有网络功能已恢复正常使用。", duration=3000, parent=self)
        
        self._last_online_state = is_online

    def init_window(self):
        self.setWindowTitle(f"Windows桌面工具 {APP_VERSION}")
        self.resize(750, 520)
        
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_dir, "app.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, "app.svg")
        
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
        else:
            self.app_icon = QIcon()
        
        self.setWindowIcon(self.app_icon)
        setTheme(Theme.DARK)
        QTimer.singleShot(100, self._sync_theme_styles)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if hasattr(self, 'app_icon') and not self.app_icon.isNull():
            self.tray_icon.setIcon(self.app_icon)
        
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
        self.ip_interface.btn_view_disclaimer.clicked.connect(lambda: self.show_disclaimer(is_first_time=False))
        self.ip_interface.btn_query.clicked.connect(self.query_ip)
        self.speed_interface.btn_start.clicked.connect(self.start_speed_test)
        # self.speed_interface.btn_settings.clicked.connect(self.speed_interface.toggle_settings) # Already connected in SpeedTestInterface
        self.speed_interface.unit_box.currentTextChanged.connect(self._on_speed_unit_changed)
        self.speed_interface.range_box.currentTextChanged.connect(self._on_speed_range_changed)

        self.settings_interface.cb_auto_start.toggled.connect(self.update_settings)
        self.settings_interface.cb_minimize_tray.toggled.connect(self.update_settings)
        self.settings_interface.theme_box.currentTextChanged.connect(self.update_settings)
        self.settings_interface.cb_auto_check_updates.toggled.connect(self.update_settings)
        self.settings_interface.btn_check_updates.clicked.connect(lambda: self.check_updates(interactive=True))
        self.settings_interface.btn_open_releases.clicked.connect(self.open_releases_page)
        self.settings_interface.btn_disclaimer.clicked.connect(lambda: self.show_disclaimer(is_first_time=False))

    def _sync_theme_styles(self):
        theme_setting = self.settings.get("theme", "深色")
        is_dark = theme_setting != "浅色"
        setTheme(Theme.DARK if is_dark else Theme.LIGHT)
        
        for interface_attr in ['speed_interface', 'window_tool_interface', 'shredder_interface', 'converter_interface', 'qrcode_interface', 'settings_interface']:
            if hasattr(self, interface_attr):
                getattr(self, interface_attr).set_theme(is_dark)
        
        QTimer.singleShot(150, lambda: self._update_title_bar_style(is_dark))

    def _update_title_bar_style(self, is_dark):
        if not is_dark:
            self.titleBar.titleLabel.setStyleSheet("QLabel { color: rgba(0, 0, 0, 0.85); font-weight: 500; background: transparent; }")
            button_qss = ""
        else:
            self.titleBar.titleLabel.setStyleSheet("QLabel { color: rgba(255, 255, 255, 0.95); font-weight: 500; background: transparent; }")
            button_qss = """
                TitleBarButton { color: #FFFFFF; background-color: transparent; border: none; }
                TitleBarButton:hover { background-color: rgba(255, 255, 255, 0.15); }
                TitleBarButton:pressed { background-color: rgba(255, 255, 255, 0.1); }
                #closeBtn:hover { background-color: #E81123; color: white; }
            """
        for btn in [self.titleBar.minBtn, self.titleBar.maxBtn, self.titleBar.closeBtn]:
            if btn: btn.setStyleSheet(button_qss)
        self.titleBar.update()

    def apply_accent_color(self, color_hex):
        color = QColor(color_hex)
        self.speed_interface.btn_start.set_accent_color(color)
        self.speed_interface.gauge.set_accent_color(color)
        self.speed_interface.dl_chart.set_accent_color(color)
        self.speed_interface.ul_chart.set_accent_color(color)
        self.window_tool_interface.accent_color = color_hex
        self.window_tool_interface.target_btn.update()
        
        data_style = f"color:{color_hex}; font-size:28px; font-weight:800;"
        self.speed_interface.dl_value.setStyleSheet(data_style)
        self.speed_interface.ul_value.setStyleSheet(data_style)
        
        style = f"""
            PrimaryPushButton {{ background-color: {color_hex}; border: 1px solid {color_hex}; }}
            PrimaryPushButton:hover {{ background-color: {color.lighter(110).name()}; border: 1px solid {color.lighter(110).name()}; }}
            PrimaryPushButton:pressed {{ background-color: {color.darker(110).name()}; border: 1px solid {color.darker(110).name()}; }}
            PushButton {{ color: {color_hex}; border: 1px solid {color_hex}; }}
            PushButton:hover {{ background-color: {color_hex}1A; }}
        """
        self.setStyleSheet(style)

    def load_config_to_ui(self):
        self.settings_interface.cb_auto_start.blockSignals(True)
        self.settings_interface.cb_minimize_tray.blockSignals(True)
        self.settings_interface.theme_box.blockSignals(True)
        self.settings_interface.cb_auto_check_updates.blockSignals(True)

        self.settings_interface.cb_auto_start.setChecked(self.settings.get("auto_start", False))
        self.settings_interface.cb_minimize_tray.setChecked(self.settings.get("minimize_to_tray", True))
        current_theme = self.settings.get("theme", "深色")
        if current_theme == "跟随系统":
            current_theme = "深色"
        self.settings_interface.theme_box.setCurrentText(current_theme)
        self.settings_interface.cb_auto_check_updates.setChecked(self.settings.get("auto_check_updates", True))

        self.settings_interface.cb_auto_check_updates.blockSignals(False)
        self.settings_interface.theme_box.blockSignals(False)
        self.settings_interface.cb_minimize_tray.blockSignals(False)
        self.settings_interface.cb_auto_start.blockSignals(False)
        accent_color = self.settings.get("accent_color", "#1677ff")
        self.apply_accent_color(accent_color)
        if hasattr(self.settings_interface, "update_status"):
            self.settings_interface.update_status.setText("")

    def start_gp_fix(self):
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
            open_group_policy()
        else:
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
            if any(k in raw_isp for k in ["Mobile", "移动", "CMCC"]): isp = "移动"
            elif any(k in raw_isp for k in ["Unicom", "联通"]): isp = "联通"
            elif any(k in raw_isp for k in ["Telecom", "电信"]): isp = "电信"
            elif any(k in raw_isp for k in ["Broadnet", "广电"]): isp = "广电"
            
            text = (f"公网IP: {info['ip']}\n国家: {info['country']}\n地区: {info['region']}\n"
                    f"城市: {info['city']}\n运营商: {raw_isp}\n数据来源: {info.get('source', '未知')}")
            self.ip_interface.ip_info_display.setText(text)
            self.speed_interface.ip_value.setText(str(info['ip']))
            self.speed_interface.isp_value.setText(isp)
            region, city = info.get('region', ''), info.get('city', '')
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
        self._refresh_speed_test_ip_info()
        self.speed_interface.set_running(True)
        self.speed_interface.btn_start.setEnabled(False)
        self.speed_interface.dl_chart.clear()
        self.speed_interface.ul_chart.clear()
        self.speed_interface.gauge.set_max_value(500)
        self.speed_interface.gauge.set_value(0, animated=False)
        self._speed_phase = "prepare"
        self._speed_latest_value = 0.0
        self._speed_dl_latest = 0.0
        self._speed_ul_latest = 0.0
        if self._speed_chart_timer.isActive(): self._speed_chart_timer.stop()
        self._speed_chart_timer.start()
        self.speed_worker = SpeedTestWorker(provider="cloudflare", parent=self)
        self.speed_worker.progress.connect(self.on_speed_test_progress)
        self.speed_worker.metric.connect(self.on_speed_test_metric)
        self.speed_worker.finished.connect(self.on_speed_test_finished)
        self.speed_worker.start()

    def _refresh_speed_test_ip_info(self):
        if not self.is_online:
            return
        if getattr(self, "speed_ip_worker", None) and self.speed_ip_worker.isRunning():
            return
        if hasattr(self, "speed_interface"):
            try:
                if self.speed_interface.ip_value.text().strip() in ("--", ""):
                    self.speed_interface.ip_value.setText("获取中…")
                if self.speed_interface.loc_value.text().strip() in ("--", ""):
                    self.speed_interface.loc_value.setText("获取中…")
                if self.speed_interface.isp_value.text().strip() in ("--", ""):
                    self.speed_interface.isp_value.setText("获取中…")
            except Exception:
                pass

        self.speed_ip_worker = IPWorker()
        self.speed_ip_worker.finished.connect(self._on_speed_test_ip_info_finished)
        self.speed_ip_worker.start()

    def _on_speed_test_ip_info_finished(self, info):
        if not info or info.get("status") != "success":
            if hasattr(self, "speed_interface"):
                try:
                    if self.speed_interface.ip_value.text().strip() == "获取中…":
                        self.speed_interface.ip_value.setText("--")
                    if self.speed_interface.loc_value.text().strip() == "获取中…":
                        self.speed_interface.loc_value.setText("--")
                    if self.speed_interface.isp_value.text().strip() == "获取中…":
                        self.speed_interface.isp_value.setText("--")
                except Exception:
                    pass
            return

        ip = str(info.get("ip", "--"))
        raw_isp = info.get("isp", "")
        isp = "其他"
        if any(k in raw_isp for k in ["Mobile", "移动", "CMCC"]):
            isp = "移动"
        elif any(k in raw_isp for k in ["Unicom", "联通"]):
            isp = "联通"
        elif any(k in raw_isp for k in ["Telecom", "电信"]):
            isp = "电信"
        elif any(k in raw_isp for k in ["Broadnet", "广电"]):
            isp = "广电"

        region, city = info.get("region", ""), info.get("city", "")
        loc = f"{region} {city}".strip()
        if hasattr(self, "speed_interface"):
            self.speed_interface.ip_value.setText(ip)
            self.speed_interface.isp_value.setText(isp)
            self.speed_interface.loc_value.setText(loc if loc else "未知地区")

    def on_speed_test_progress(self, msg):
        self.speed_interface.status_label.setText(msg)
        if "延迟" in msg: self._speed_phase = "ping"
        elif "下载" in msg: self._speed_phase = "download"
        elif "上传" in msg: self._speed_phase = "upload"

    def on_speed_test_metric(self, metric):
        unit = self.speed_interface.unit_box.currentText()
        factor = 1.0 if unit == "Mbps" else 0.125
        try: mbps = float(metric.get("mbps", 0.0))
        except: return
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
        if display_value > max_v * 0.95:
            self.speed_interface.gauge.set_max_value(float(((int(display_value) // 50) + 1) * 50))
        self.speed_interface.gauge.set_value(display_value, animated=True)

    def on_speed_test_finished(self, result):
        if self._speed_chart_timer.isActive(): self._speed_chart_timer.stop()
        self.speed_interface.set_running(False)
        self.speed_interface.btn_start.setEnabled(True)
        if result.get("status") == "success":
            self.speed_interface.status_label.setText("测速完成")
            unit = self.speed_interface.unit_box.currentText()
            factor = 1.0 if unit == "Mbps" else 0.125
            dl_val, ul_val = float(result.get("download", 0.0)) * factor, float(result.get("upload", 0.0)) * factor
            ping, jitter = result.get("ping"), result.get("jitter")
            self.speed_interface.dl_value.setText(f"{dl_val:.2f}")
            self.speed_interface.ul_value.setText(f"{ul_val:.2f}")
            self.speed_interface.ping_value.setText(f"{float(ping):.0f}" if ping is not None else "--")
            self.speed_interface.jitter_value.setText(f"{float(jitter):.2f}" if jitter is not None else "--")
            InfoBar.success("测速完成", f"下载: {dl_val:.2f} {unit}, 上传: {ul_val:.2f} {unit}", duration=3000, parent=self)
        else:
            self.speed_interface.status_label.setText("测速失败")
            InfoBar.error("测速失败", result.get("message", "未知错误"), duration=3000, parent=self)

    def _append_speed_chart_point(self):
        if self._speed_phase == "download": self.speed_interface.dl_chart.add_value(self._speed_dl_latest)
        elif self._speed_phase == "upload": self.speed_interface.ul_chart.add_value(self._speed_ul_latest)

    def _on_speed_unit_changed(self, unit):
        self.speed_interface.gauge.unit = unit

    def _on_speed_range_changed(self, text):
        if text == "自动": return
        try: v = float(text)
        except: return
        self.speed_interface.gauge.set_max_value(v)

    def update_settings(self):
        self.settings["auto_start"] = self.settings_interface.cb_auto_start.isChecked()
        self.settings["minimize_to_tray"] = self.settings_interface.cb_minimize_tray.isChecked()
        self.settings["theme"] = self.settings_interface.theme_box.currentText()
        self.settings["auto_check_updates"] = self.settings_interface.cb_auto_check_updates.isChecked()
        save_settings(self.settings)
        set_auto_start(self.settings["auto_start"])
        self._sync_theme_styles()

    def open_releases_page(self):
        import webbrowser
        webbrowser.open("https://github.com/liaozixing/Windows-Desktop-Tool/releases")

    def _auto_check_updates_on_startup(self):
        if not self.settings.get("auto_check_updates", True):
            return
        self.check_updates(interactive=False)

    def check_updates(self, interactive=True):
        if getattr(self, "update_worker", None) and self.update_worker.isRunning():
            return

        if hasattr(self.settings_interface, "update_status"):
            self.settings_interface.update_status.setText("正在检查更新…")
        if hasattr(self.settings_interface, "btn_check_updates"):
            self.settings_interface.btn_check_updates.setEnabled(False)

        self.update_worker = UpdateCheckWorker("liaozixing/Windows-Desktop-Tool", APP_VERSION, parent=self)
        self.update_worker.finished.connect(lambda result: self._on_update_check_finished(result, interactive))
        self.update_worker.start()

    def _on_update_check_finished(self, result, interactive):
        if hasattr(self.settings_interface, "btn_check_updates"):
            self.settings_interface.btn_check_updates.setEnabled(True)

        status = (result or {}).get("status")
        if status != "success":
            message = (result or {}).get("message", "检查更新失败")
            if hasattr(self.settings_interface, "update_status"):
                self.settings_interface.update_status.setText(f"检查失败：{message}")
            if interactive:
                InfoBar.error("检查更新失败", message, duration=4000, parent=self)
            return

        current_version = result.get("current_version", APP_VERSION)
        latest_version = result.get("latest_version", "")
        url = result.get("url") or "https://github.com/liaozixing/Windows-Desktop-Tool/releases"
        update_available = bool(result.get("update_available"))

        if update_available:
            if hasattr(self.settings_interface, "update_status"):
                self.settings_interface.update_status.setText(f"发现新版本：{latest_version}（当前 {current_version}）")

            if interactive:
                mb = MessageBox(
                    "发现新版本",
                    f"当前版本：{current_version}\n最新版本：{latest_version}\n\n是否打开发布页？",
                    self
                )
                mb.yesButton.setText("打开发布页")
                mb.cancelButton.setText("稍后")
                if mb.exec_():
                    import webbrowser
                    webbrowser.open(url)
            else:
                InfoBar.success("发现新版本", f"{current_version} → {latest_version}", duration=5000, parent=self)
                if hasattr(self, "tray_icon"):
                    try:
                        self.tray_icon.showMessage(
                            "全能桌面工具",
                            f"发现新版本 {latest_version}，可在设置页检查更新",
                            QSystemTrayIcon.Information,
                            4000
                        )
                    except Exception:
                        pass
        else:
            if hasattr(self.settings_interface, "update_status"):
                self.settings_interface.update_status.setText(f"已是最新版本：{current_version}")
            if interactive:
                InfoBar.success("已是最新版本", f"当前版本：{current_version}", duration=2500, parent=self)

    def closeEvent(self, event):
        mb = MessageBox("退出程序", "确定要退出全能Windows桌面工具吗？", self)
        cb = CheckBox("点击关闭时最小化到系统托盘", mb)
        cb.setChecked(self.settings.get("minimize_to_tray", True))
        mb.textLayout.addWidget(cb)
        mb.yesButton.setText("确定")
        mb.cancelButton.setText("取消")
        if mb.exec_():
            minimize = cb.isChecked()
            self.settings["minimize_to_tray"] = minimize
            save_settings(self.settings)
            self.settings_interface.cb_minimize_tray.setChecked(minimize)
            if minimize:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage("全能桌面工具", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
            else:
                event.accept()
                self.quit_app()
        else:
            event.ignore()

    def quit_app(self, force=False):
        """优化后的退出方法，快速释放资源并清理缓存"""
        if hasattr(self, '_speed_chart_timer'): self._speed_chart_timer.stop()
        if hasattr(self, 'network_monitor') and self.network_monitor:
            try:
                self.network_monitor.stop(timeout_ms=200)
                if self.network_monitor.isRunning() and not self.network_monitor.wait(200):
                    self.network_monitor.terminate()
            except: pass
        
        # 优化：并行停止所有工作线程，减少等待时间
        workers = ['speed_worker', 'ip_worker', 'speed_ip_worker', 'gp_worker', 'update_worker']
        for worker_name in workers:
            worker = getattr(self, worker_name, None)
            if worker and hasattr(worker, 'isRunning') and worker.isRunning():
                try:
                    worker.quit()
                    # 减少等待时间到 200ms，如果不停止则强制终止
                    if not worker.wait(200):
                        worker.terminate()
                except: pass
        
        # 清理托盘图标
        if hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
            except: pass
        
        if force:
            sys.exit(0)
        else:
            QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
