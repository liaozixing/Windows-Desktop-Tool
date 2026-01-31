"""
免责声明对话框模块
"""
from PyQt5.QtCore import QTimer
from qfluentwidgets import MessageBox, BodyLabel, ScrollArea

from config import APP_VERSION
from disclaimer import DISCLAIMER_TEXT

class DisclaimerDialog(MessageBox):
    """自定义免责声明对话框，包含倒计时和滚动校验"""
    def __init__(self, title, content, parent=None):
        super().__init__(title, "", parent)
        self.content_text = content
        
        # 替换默认的 contentLabel
        self.scroll_area = ScrollArea(self.widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(300)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.text_label = BodyLabel(content, self.scroll_area)
        self.text_label.setWordWrap(True)
        self.text_label.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.text_label)
        
        self.textLayout.insertWidget(1, self.scroll_area)
        
        # 倒计时逻辑
        self.countdown = 5
        self.yesButton.setEnabled(False)
        self.yesButton.setText(f"我已阅读并同意 ({self.countdown}s)")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        
        # 滚动校验逻辑
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
        if value >= bar.maximum() - 5:  # 允许 5 像素误差
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

