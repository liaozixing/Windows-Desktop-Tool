import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from qfluentwidgets import (SubtitleLabel, BodyLabel, CaptionLabel, PrimaryPushButton, 
                            PushButton, FluentIcon as FIF, InfoBar, 
                            StrongBodyLabel, TextEdit, ImageLabel,
                            CardWidget)

from modules.qrcode_tool import generate_qr_image

class QRCodeInterface(QWidget):
    """ 二维码工具界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("QRCodeInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 头部
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("二维码工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 生成页面布局 (直接显示)
        self.init_gen_page(layout)

    def init_gen_page(self, parent_layout):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(20)

        # 左侧输入区
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(StrongBodyLabel("输入内容"))
        self.input_text = TextEdit()
        self.input_text.setPlaceholderText("在此输入想要生成二维码的文本或链接...")
        left_layout.addWidget(self.input_text)
        
        btn_layout = QHBoxLayout()
        self.btn_gen = PrimaryPushButton(FIF.SYNC, "生成二维码", self)
        self.btn_gen.clicked.connect(self.do_generate)
        btn_layout.addWidget(self.btn_gen)
        btn_layout.addStretch(1)
        left_layout.addLayout(btn_layout)
        
        layout.addWidget(left_panel, 1)

        # 右侧预览区
        right_panel = CardWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignCenter)
        
        self.qr_display = ImageLabel()
        self.qr_display.setFixedSize(200, 200)
        self.qr_display.setStyleSheet("border: 2px dashed rgba(0,0,0,0.1); border-radius: 8px;")
        self.qr_display.setAlignment(Qt.AlignCenter)
        self.qr_display.setText("预览区域")
        
        right_layout.addWidget(self.qr_display)
        
        action_layout = QHBoxLayout()
        self.btn_save = PushButton(FIF.SAVE, "保存图片", self)
        self.btn_copy_img = PushButton(FIF.COPY, "复制图片", self)
        self.btn_save.setEnabled(False)
        self.btn_copy_img.setEnabled(False)
        
        self.btn_save.clicked.connect(self.save_qr_image)
        self.btn_copy_img.clicked.connect(self.copy_qr_image)
        
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_copy_img)
        right_layout.addLayout(action_layout)
        
        layout.addWidget(right_panel, 1)
        self.current_qr_pixmap = None
        
        parent_layout.addLayout(layout)

    def do_generate(self):
        text = self.input_text.toPlainText()
        if not text:
            InfoBar.warning("提示", "请输入内容", duration=2000, parent=self.window())
            return
            
        pixmap = generate_qr_image(text, size=10)
        if pixmap:
            self.current_qr_pixmap = pixmap
            # 缩放显示
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_display.setPixmap(scaled)
            self.btn_save.setEnabled(True)
            self.btn_copy_img.setEnabled(True)
            InfoBar.success("成功", "二维码已生成", duration=2000, parent=self.window())
        else:
            InfoBar.error("错误", "生成失败", duration=2000, parent=self.window())

    def save_qr_image(self):
        if not self.current_qr_pixmap: return
        path, _ = QFileDialog.getSaveFileName(self, "保存二维码", "qrcode.png", "PNG 图片 (*.png)")
        if path:
            self.current_qr_pixmap.save(path, "PNG")
            InfoBar.success("成功", "图片已保存", duration=2000, parent=self.window())

    def copy_qr_image(self):
        if not self.current_qr_pixmap: return
        QApplication.clipboard().setPixmap(self.current_qr_pixmap)
        InfoBar.success("成功", "图片已复制到剪贴板", duration=2000, parent=self.window())

    def update_network_status(self, is_online):
        pass

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, text_color = "#1d1d1d", "#e0e0e0"
            card_bg = "rgba(255, 255, 255, 0.05)"
            border_color = "rgba(255, 255, 255, 0.1)"
            
            # 输入框深色样式
            input_bg = "rgba(255, 255, 255, 0.08)"
            input_color = "#ffffff"
            input_border = "rgba(255, 255, 255, 0.1)"
            selection_bg = "#0078d4"
        else:
            bg_color, text_color = "#f7f9fc", "#333333"
            card_bg = "rgba(255, 255, 255, 0.5)"
            border_color = "rgba(0, 0, 0, 0.1)"
            
            # 输入框浅色样式
            input_bg = "rgba(255, 255, 255, 0.7)"
            input_color = "#000000"
            input_border = "rgba(0, 0, 0, 0.1)"
            selection_bg = "#0078d4"

        self.setStyleSheet(f"#QRCodeInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        
        # 显式设置输入框样式，解决深色模式下背景为白色的问题
        input_style = f"""
            TextEdit {{
                background-color: {input_bg};
                color: {input_color};
                border: 1px solid {input_border};
                border-radius: 6px;
                selection-background-color: {selection_bg};
            }}
            TextEdit:hover {{
                background-color: {input_bg};
                border: 1px solid {selection_bg};
            }}
            TextEdit:focus {{
                background-color: {input_bg};
                border-bottom: 2px solid {selection_bg};
            }}
        """
        self.input_text.setStyleSheet(input_style)
