import os
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon, QWidget
from qfluentwidgets import (
    CheckBox,
    FluentIcon as FIF,
    FluentWindow,
    InfoBar,
    MessageBox,
    NavigationItemPosition,
    Theme,
    ToolTipFilter,
    ToolTipPosition,
    setTheme,
)

from modules.network_monitor import NetworkMonitor
from modules.settings import load_settings, save_settings, set_auto_start
from ui.converter_interface import ConverterInterface
from ui.disclaimer import DISCLAIMER_TEXT, DisclaimerDialog
from ui.ip_interface import IPInterface
from ui.settings_interface import SettingsInterface
from ui.shredder_interface import ShredderInterface
from ui.speed_test_interface import SpeedTestInterface
from ui.system_interface import SystemInterface
from ui.window_tool_interface import WindowToolInterface


def get_app_version():
    default_version = "v1.3.0"
    try:
        # 寻找 README.md 的路径
        # 1. 尝试在当前执行文件所在目录找
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        # 2. 尝试在代码根目录找 (针对开发环境，main.py 在 Windows Desktop Tool 目录下)
        base_dir = os.path.dirname(exe_dir)
        
        paths_to_check = [
            os.path.join(exe_dir, "README.md"),
            os.path.join(base_dir, "README.md"),
            "README.md"
        ]
        
        for readme_path in paths_to_check:
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "版本" in line and "v" in line:
                            # 匹配 **版本：v1.3.0** 这种格式
                            parts = line.strip().split("版本：", 1)
                            if len(parts) > 1:
                                tail = parts[1].strip()
                                # 移除末尾的加粗星号和空格
                                version = tail.split(" ")[0].strip("*").strip()
                                if version:
                                    return version
    except Exception:
        pass
    return default_version


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()

        self.is_online = True
        self._network_status_initialized = False

        self.ip_interface = IPInterface(self)
        self.system_interface = SystemInterface(self)
        self.speed_interface = SpeedTestInterface(self)
        self.shredder_interface = ShredderInterface(self)
        self.converter_interface = ConverterInterface(self)
        self.window_tool_interface = WindowToolInterface(self)
        self.settings_interface = SettingsInterface(self)

        self.init_navigation()

        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.status_changed.connect(self._on_network_status_changed)
        self.network_monitor.start()

        self.init_window()
        self.init_tray()
        self.connect_signals()

        self.load_config_to_ui()

        QTimer.singleShot(500, self.check_disclaimer)

    def check_disclaimer(self):
        if not self.settings.get("disclaimer_accepted", False):
            self.show_disclaimer(is_first_time=True)

    def show_disclaimer(self, is_first_time=False):
        content = DISCLAIMER_TEXT

        try:
            if os.path.exists("disclaimer.txt"):
                with open("disclaimer.txt", "r", encoding="utf-8") as f:
                    content = f.read()
        except Exception:
            pass

        title = "免责声明" if not is_first_time else "欢迎使用 - 免责声明"
        w = DisclaimerDialog(title, content, self.window())
        w.yesButton.setText("我已阅读并同意")
        w.cancelButton.setText("拒绝并退出" if is_first_time else "关闭")

        if w.exec():
            if is_first_time:
                self.settings["disclaimer_accepted"] = True
                save_settings(self.settings)
                InfoBar.success("感谢支持", "您已同意免责声明，可以开始使用了", duration=3000, parent=self.window())
        else:
            if is_first_time:
                QApplication.quit()
                sys.exit(0)

    def init_navigation(self):
        self.addSubInterface(self.ip_interface, FIF.GLOBE, "IP查询")
        self.addSubInterface(self.speed_interface, FIF.SPEED_HIGH, "网速测试")
        self.addSubInterface(self.shredder_interface, FIF.BROOM, "文件粉碎")
        self.addSubInterface(self.converter_interface, FIF.PHOTO, "格式转换")
        self.addSubInterface(self.window_tool_interface, FIF.SEARCH, "窗口定位")
        self.addSubInterface(self.system_interface, FIF.APPLICATION, "系统功能")
        self.addSubInterface(self.settings_interface, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)

        self.net_status_item = self.navigationInterface.addItem(
            routeKey="NetStatus",
            icon=FIF.WIFI,
            text="正在检查网络...",
            onClick=lambda: self.system_interface.show_network_details(self.is_online),
            position=NavigationItemPosition.BOTTOM,
            selectable=False,
        )

        import webbrowser

        self.github_item = self.navigationInterface.addItem(
            routeKey="GitHub",
            icon=FIF.GITHUB,
            text="GitHub",
            onClick=lambda: webbrowser.open("https://github.com/liaozixing/Windows-Desktop-Tool"),
            position=NavigationItemPosition.BOTTOM,
            selectable=False,
        )
        self.github_item.setToolTip("项目地址")
        self.github_item.installEventFilter(ToolTipFilter(self.github_item, 500, ToolTipPosition.RIGHT))

    def _on_network_status_changed(self, is_online):
        self.is_online = is_online
        status_text = "网络已连接" if is_online else "网络未连接"
        should_notify = bool(getattr(self, "_network_status_initialized", False))

        if is_online:
            status_icon = FIF.WIFI
            color = QColor(39, 174, 96)
        else:
            status_icon = FIF.INFO
            color = QColor(232, 17, 35)

        widget = self.navigationInterface.widget("NetStatus")
        if widget:
            widget.setText(status_text)
            widget.setIcon(status_icon)

        for interface_attr in [
            "ip_interface",
            "speed_interface",
            "converter_interface",
            "system_interface",
            "shredder_interface",
            "window_tool_interface",
        ]:
            if hasattr(self, interface_attr):
                interface = getattr(self, interface_attr)
                if hasattr(interface, "update_network_status"):
                    interface.update_network_status(is_online)

        if should_notify:
            if not is_online:
                InfoBar.warning("网络连接已断开", "查询 IP、网速测试等网络功能将暂时不可用。", duration=5000, parent=self)
            else:
                if hasattr(self, "_last_online_state") and not self._last_online_state:
                    InfoBar.success("网络已恢复", "所有网络功能已恢复正常使用。", duration=3000, parent=self)

        self._last_online_state = is_online
        self._network_status_initialized = True

    def init_window(self):
        version = get_app_version()
        self.setWindowTitle(f"全能Windows桌面工具 {version}")
        self.resize(750, 520)

        icon_path = "app.ico"
        if not os.path.exists(icon_path):
            icon_path = "app.svg"

        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, icon_path)

        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(self.app_icon)

        setTheme(Theme.DARK)
        QTimer.singleShot(100, self._sync_theme_styles)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)

        if hasattr(self, "app_icon"):
            self.tray_icon.setIcon(self.app_icon)
        else:
            icon_path = "app.svg"
            if hasattr(sys, "_MEIPASS"):
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
        self.ip_interface.btn_view_disclaimer.clicked.connect(lambda: self.show_disclaimer(is_first_time=False))
        self.ip_interface.btn_query.clicked.connect(self.ip_interface.query_ip)
        self.speed_interface.btn_start.clicked.connect(self.speed_interface.start_speed_test)
        self.speed_interface.btn_settings.clicked.connect(self.speed_interface.toggle_settings)
        self.speed_interface.unit_box.currentTextChanged.connect(self.speed_interface.on_speed_unit_changed)
        self.speed_interface.range_box.currentTextChanged.connect(self.speed_interface.on_speed_range_changed)

        self.settings_interface.cb_auto_start.stateChanged.connect(self.settings_interface.update_settings)
        self.settings_interface.cb_minimize_tray.stateChanged.connect(self.settings_interface.update_settings)
        self.settings_interface.theme_box.currentTextChanged.connect(self.settings_interface.update_settings)
        self.settings_interface.btn_disclaimer.clicked.connect(lambda: self.show_disclaimer(is_first_time=False))

    def _sync_theme_styles(self):
        theme_setting = self.settings.get("theme", "深色")

        if theme_setting == "浅色":
            is_dark = False
            setTheme(Theme.LIGHT)
        else:
            is_dark = True
            setTheme(Theme.DARK)

        if hasattr(self, "speed_interface"):
            self.speed_interface.set_theme(is_dark)
        if hasattr(self, "window_tool_interface"):
            self.window_tool_interface.set_theme(is_dark)
        if hasattr(self, "shredder_interface"):
            self.shredder_interface.set_theme(is_dark)
        if hasattr(self, "converter_interface"):
            self.converter_interface.set_theme(is_dark)

        QTimer.singleShot(150, lambda: self._update_title_bar_style(is_dark))

    def _update_title_bar_style(self, is_dark):
        if not is_dark:
            self.titleBar.titleLabel.setStyleSheet(
                """
                QLabel {
                    color: rgba(0, 0, 0, 0.85);
                    font-weight: 500;
                    background: transparent;
                }
            """
            )
            button_qss = ""
        else:
            self.titleBar.titleLabel.setStyleSheet(
                """
                QLabel {
                    color: rgba(255, 255, 255, 0.95);
                    font-weight: 500;
                    background: transparent;
                }
            """
            )

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

        for btn in [self.titleBar.minBtn, self.titleBar.maxBtn, self.titleBar.closeBtn]:
            if btn:
                btn.setStyleSheet(button_qss)

        for btn in self.titleBar.findChildren(QWidget):
            if "TitleBarButton" in btn.__class__.__name__:
                btn.setStyleSheet(button_qss)

        self.titleBar.update()

    def apply_accent_color(self, color_hex):
        color = QColor(color_hex)
        self.speed_interface.btn_start.set_accent_color(color)
        self.speed_interface.gauge.set_accent_color(color)
        self.speed_interface.dl_chart.set_accent_color(color)
        self.speed_interface.ul_chart.set_accent_color(color)

        self.window_tool_interface.accent_color = color_hex
        self.window_tool_interface.target_btn.update()

        data_style = f"color:{color_hex}; font-size:18px; font-weight:700;"
        self.speed_interface.dl_value.setStyleSheet(data_style)
        self.speed_interface.ul_value.setStyleSheet(data_style)

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
        self.setStyleSheet(style)

    def load_config_to_ui(self):
        self.settings_interface.cb_auto_start.setChecked(self.settings.get("auto_start", False))
        self.settings_interface.cb_minimize_tray.setChecked(self.settings.get("minimize_to_tray", True))

        current_theme = self.settings.get("theme", "深色")
        if current_theme == "跟随系统":
            current_theme = "深色"
        self.settings_interface.theme_box.setCurrentText(current_theme)

        accent_color = self.settings.get("accent_color", "#1677ff")
        self.apply_accent_color(accent_color)

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

    def quit_app(self):
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
            self.tray_icon.deleteLater()

        if hasattr(self, "network_monitor"):
            try:
                self.network_monitor.stop()
            except Exception:
                pass

        # 调用各接口的停止方法进行清理
        for interface_attr in [
            "ip_interface",
            "speed_interface",
            "system_interface",
            "shredder_interface",
            "converter_interface",
            "window_tool_interface",
        ]:
            if hasattr(self, interface_attr):
                interface = getattr(self, interface_attr)
                if hasattr(interface, "stop_worker"):
                    try:
                        interface.stop_worker()
                    except Exception:
                        pass

        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

