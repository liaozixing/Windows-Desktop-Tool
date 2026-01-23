from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as FIF,
    InfoBar,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
)

from modules.window_tool import get_window_info_at, open_file_location
from ui.window_target import HighlightWindow, TargetWidget


class WindowToolInterface(QWidget):
    """ 窗口弹窗定位工具界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("WindowToolInterface")
        self.accent_color = "#1677ff"

        self.highlighter = HighlightWindow()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("窗口弹窗定位工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet(
            "background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;"
        )
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self.desc = BodyLabel("拖动下方的靶子到目标窗口上，松开即可识别窗口信息。", self)
        layout.addWidget(self.desc)

        target_container = QHBoxLayout()
        target_container.addStretch(1)
        self.target_btn = TargetWidget(self)
        target_container.addWidget(self.target_btn)
        target_container.addStretch(1)
        layout.addLayout(target_container)

        self.info_group = QWidget()
        info_layout = QGridLayout(self.info_group)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)

        self.label_style = "font-size: 13px; font-weight: 600;"
        self.value_style = "font-size: 13px; color: #666666;"

        self.add_info_row(info_layout, "窗口标题:", 0)
        self.add_info_row(info_layout, "进程名称:", 1)
        self.add_info_row(info_layout, "窗口句柄:", 2)
        self.add_info_row(info_layout, "进程 ID:", 3)
        self.add_info_row(info_layout, "程序路径:", 4)

        self.info_group.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 8px;")
        layout.addWidget(self.info_group)

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

        self.target_btn.targetHovered.connect(self.on_target_hovered)
        self.target_btn.targetReleased.connect(self.on_target_released)
        self.btn_open_loc.clicked.connect(self.on_open_location)
        self.btn_copy_path.clicked.connect(self.on_copy_path)
        self.btn_copy_title.clicked.connect(self.on_copy_title)
        self.btn_kill_proc.clicked.connect(self.on_kill_process)

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

        attr_name = f"val_{row}"
        setattr(self, attr_name, value)

    def on_target_hovered(self, x, y):
        """ 拖动过程中的实时高亮 """
        info = get_window_info_at(x, y)
        if info and info.get("rect"):
            if info["hwnd"] != int(self.window().winId()):
                self.highlighter.show_highlight(info["rect"], self.accent_color)
            else:
                self.highlighter.hide()
        else:
            self.highlighter.hide()

    def on_target_released(self, x, y):
        self.highlighter.hide()

        info = get_window_info_at(x, y)
        if not info:
            InfoBar.warning("提示", "未识别到有效窗口", duration=2000, parent=self.window())
            return

        self.current_info = info
        self.val_0.setText(info["title"] if info["title"] else "(无标题)")
        self.val_1.setText(info["process_name"])
        self.val_2.setText(hex(info["hwnd"]))
        self.val_3.setText(str(info["pid"]))
        self.val_4.setText(info["process_path"])

        self.btn_open_loc.setEnabled(bool(info["process_path"] and info["process_path"] != "未知"))
        self.btn_copy_path.setEnabled(bool(info["process_path"] and info["process_path"] != "未知"))
        self.btn_copy_title.setEnabled(bool(info["title"]))
        self.btn_kill_proc.setEnabled(bool(info["pid"]))

        InfoBar.success("识别成功", f"已定位到窗口: {info['process_name']}", duration=2000, parent=self.window())

    def on_open_location(self):
        if self.current_info and self.current_info["process_path"]:
            if not open_file_location(self.current_info["process_path"]):
                InfoBar.error("错误", "无法打开文件位置，路径可能不存在或无权限访问", duration=3000, parent=self.window())

    def on_copy_path(self):
        if self.current_info and self.current_info["process_path"]:
            from PyQt5.QtWidgets import QApplication

            QApplication.clipboard().setText(self.current_info["process_path"])
            InfoBar.success("成功", "程序路径已复制到剪贴板", duration=2000, parent=self.window())

    def on_copy_title(self):
        if self.current_info and self.current_info["title"]:
            from PyQt5.QtWidgets import QApplication

            QApplication.clipboard().setText(self.current_info["title"])
            InfoBar.success("成功", "窗口标题已复制到剪贴板", duration=2000, parent=self.window())

    def on_kill_process(self):
        if not self.current_info or not self.current_info["pid"]:
            return

        import psutil

        pid = self.current_info["pid"]
        name = self.current_info["process_name"]

        msg_box = MessageBox(
            "确认结束进程",
            f"确定要结束进程 {name} (PID: {pid}) 吗？\n未保存的数据将会丢失！",
            self.window(),
        )
        msg_box.yesButton.setText("确定结束")
        msg_box.cancelButton.setText("取消")

        if msg_box.exec_():
            try:
                proc = psutil.Process(pid)
                proc.kill()
                InfoBar.success("成功", f"进程 {name} 已结束", duration=3000, parent=self.window())
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

        for i in range(5):
            getattr(self, f"val_{i}").setStyleSheet(f"color:{val_color}; font-size: 13px;")

    def stop_worker(self):
        """ 停止相关工作线程或关闭悬浮窗口 """
        if hasattr(self, "highlighter"):
            try:
                self.highlighter.close()
            except Exception:
                pass
        if hasattr(self.target_btn, "ghost") and self.target_btn.ghost:
            try:
                self.target_btn.ghost.close()
            except Exception:
                pass
