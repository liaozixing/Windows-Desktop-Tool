from PyQt5.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    CheckBox,
    ComboBox,
    FluentIcon as FIF,
    InfoBar,
    MessageBox,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TextEdit,
)

from modules.system_functions import clean_cache


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
            "v1.2.0 (2026-01-19)\n"
            "1. [重构] 格式转换界面：合并图片与文档转换，新增视频转换功能（支持 MP4/MKV 等）。\n"
            "2. [优化] 配置保存：配置文件迁移至 %APPDATA% 目录，彻底解决权限不足导致的保存失败问题。\n"
            "3. [新增] 退出确认：新增退出确认对话框，支持“最小化到托盘”选项并记忆用户偏好。\n"
            "4. [优化] 版本号同步：窗口标题自动同步 README 文档版本号，无需手动修改代码。\n"
            "5. [安全] 免责声明升级：强制阅读倒计时与代码内置声明文本，提升合规性。\n"
            "6. [调整] IP 查询优化：取消启动自动查询，改为手动触发，保护用户隐私。"
        )
        layout.addWidget(self.changelog_display)

        layout.addStretch(1)

    def on_clean_cache(self):
        msg_box = MessageBox(
            "确认清理缓存",
            "确定要清理所有 __pycache__ 文件夹吗？\n这不会影响程序运行，但下次启动时可能会略微变慢。",
            self.window(),
        )
        msg_box.yesButton.setText("确定清理")
        msg_box.cancelButton.setText("取消")

        if msg_box.exec_():
            count = clean_cache(".")
            InfoBar.success("清理成功", f"已成功清理 {count} 个缓存目录。", duration=3000, parent=self.window())

    def update_settings(self):
        mw = self.window()
        mw.settings["auto_start"] = self.cb_auto_start.isChecked()
        mw.settings["minimize_to_tray"] = self.cb_minimize_tray.isChecked()
        mw.settings["theme"] = self.theme_box.currentText()
        from modules.settings import save_settings, set_auto_start
        save_settings(mw.settings)
        set_auto_start(mw.settings["auto_start"])
        mw._sync_theme_styles()

