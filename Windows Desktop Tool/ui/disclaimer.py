from PyQt5.QtCore import QTimer
from qfluentwidgets import BodyLabel, MessageBox, ScrollArea


DISCLAIMER_TEXT = """免责声明与用户协议

欢迎使用本 Windows 桌面工具集（以下简称“本软件”）。在您开始使用本软件之前，请务必仔细阅读并理解以下条款：

1. 软件性质与授权
本软件是一款集合了网络监控、文件粉碎、格式转换、窗口定位及系统快捷工具的实用程序。本软件按“现状”提供，不附带任何形式的明示或暗示担保。

2. 数据风险提示
- 【文件粉碎】：此功能将采用物理覆盖方式彻底删除文件，粉碎后的数据将无法通过任何技术手段恢复。请在操作前务必确认文件无误。
- 【格式转换】：在文档或图片转换过程中，可能会因源文件格式复杂或兼容性问题导致部分内容丢失或排版错乱。
- 【系统工具】：本软件提供的系统快捷方式（如组策略、注册表等）涉及系统核心设置。错误的操作可能导致系统不稳定甚至崩溃。

3. 责任限制
- 用户在使用本软件过程中，因操作不当、误删除、误修改或不可抗力导致的任何数据丢失、硬件损坏、系统异常或间接损失，开发者及关联方均不承担任何法律责任。
- 一切后果由用户自行承担。

4. 隐私说明
本软件的大部分功能（除 IP 查询、网速测试外）均在本地运行，不收集、不上传用户的任何个人文件或隐私数据。

5. 同意声明
点击“我已阅读并同意”按钮，即表示您已充分理解并接受本协议的所有条款。如果您不同意本协议的内容，请立即关闭并卸载本软件。

使用本软件即视为您已阅读并同意本声明。"""


class DisclaimerDialog(MessageBox):
    """ 自定义免责声明对话框，包含倒计时和滚动校验 """

    def __init__(self, title, content, parent=None):
        super().__init__(title, "", parent)
        self.content_text = content

        self.scroll_area = ScrollArea(self.widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(300)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        self.text_label = BodyLabel(content, self.scroll_area)
        self.text_label.setWordWrap(True)
        self.text_label.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.text_label)

        self.textLayout.insertWidget(1, self.scroll_area)

        self.countdown = 5
        self.yesButton.setEnabled(False)
        self.yesButton.setText(f"我已阅读并同意 ({self.countdown}s)")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.is_scrolled_to_bottom = False
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll)

    def update_timer(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.yesButton.setText(f"我已阅读并同意 ({self.countdown}s)")
        else:
            self.timer.stop()
            self.check_ready()

    def check_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        if value >= bar.maximum() - 5:
            self.is_scrolled_to_bottom = True
            self.check_ready()

    def check_ready(self):
        if self.countdown <= 0 and self.is_scrolled_to_bottom:
            self.yesButton.setEnabled(True)
            self.yesButton.setText("我已阅读并同意")
        elif self.countdown <= 0 and not self.is_scrolled_to_bottom:
            self.yesButton.setText("请滑到底部以继续")
        elif self.countdown > 0:
            self.yesButton.setText(f"我已阅读并同意 ({self.countdown}s)")

