from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, CheckBox, StrongBodyLabel, ComboBox,
                            PushButton, TextEdit, CaptionLabel, FluentIcon as FIF)
from config import APP_VERSION

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
        update_label = StrongBodyLabel("更新", self)
        update_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(update_label)

        self.cb_auto_check_updates = CheckBox("启动时自动检查更新", self)
        self.cb_auto_check_updates.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.cb_auto_check_updates)

        self.btn_check_updates = PushButton(FIF.INFO, "检查更新", self)
        self.btn_check_updates.setFixedWidth(250)
        layout.addWidget(self.btn_check_updates)

        self.btn_open_releases = PushButton(FIF.GITHUB, "打开发布页", self)
        self.btn_open_releases.setFixedWidth(250)
        layout.addWidget(self.btn_open_releases)

        self.update_status = CaptionLabel("", self)
        self.update_status.setWordWrap(True)
        layout.addWidget(self.update_status)


        # 免责声明按钮
        layout.addSpacing(20)
        disclaimer_label = StrongBodyLabel("法律声明", self)
        disclaimer_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(disclaimer_label)
        
        self.btn_disclaimer = PushButton(FIF.INFO, "查看免责声明", self)
        self.btn_disclaimer.setFixedWidth(250)
        layout.addWidget(self.btn_disclaimer)

        layout.addSpacing(30)
        # 使用程序中的版本号
        changelog_label = StrongBodyLabel(f"更新日志 ({APP_VERSION})", self)
        changelog_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(changelog_label)

        self.changelog_display = TextEdit(self)
        self.changelog_display.setReadOnly(True)
        self.changelog_display.setFixedHeight(150)
        
        # 从更新日志模块加载日志（自动从 README.md 同步）
        try:
            from modules.changelog import format_changelog_text, sync_changelog_from_readme
            # 启动时自动同步 README.md 中的最近更新
            sync_changelog_from_readme()
            # 加载并显示更新日志
            changelog_text = format_changelog_text(max_entries=10)
            self.changelog_display.setText(changelog_text)
        except Exception:
            # 如果加载失败，使用默认文本
            from config import CHANGELOG_TEXT
            self.changelog_display.setText(CHANGELOG_TEXT)
        layout.addWidget(self.changelog_display)

        layout.addStretch(1)

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def set_theme(self, is_dark):
        """ 设置页面主题 """
        if is_dark:
            bg_color = "#1d1d1d"
            text_color = "#e0e0e0"
        else:
            bg_color = "#f7f9fc"
            text_color = "#333333"

        self.setStyleSheet(f"#SettingsInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
