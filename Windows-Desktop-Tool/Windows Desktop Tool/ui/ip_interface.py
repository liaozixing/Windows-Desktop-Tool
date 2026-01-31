import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QThread
from qfluentwidgets import (SubtitleLabel, PrimaryPushButton, PushButton, TextEdit, 
                            BodyLabel, CaptionLabel, FluentIcon as FIF)

class IPInterface(QWidget):
    """ IP 查询界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("IPInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 顶部免责声明 (显眼提示)
        self.disclaimer_banner = QWidget(self)
        self.disclaimer_banner.setObjectName("DisclaimerBanner")
        banner_layout = QHBoxLayout(self.disclaimer_banner)
        banner_layout.setContentsMargins(15, 10, 15, 10)
        
        # 注意：这里需要根据主题调整颜色，简单起见使用黄色背景警告色
        self.disclaimer_banner.setStyleSheet("""
            #DisclaimerBanner {
                background-color: rgba(255, 193, 7, 0.15);
                border: 1px solid rgba(255, 193, 7, 0.3);
                border-radius: 6px;
            }
        """)
        
        warn_label = BodyLabel("⚠️ 严正声明：本工具仅供安全研究与技术交流，请勿用于非法用途。使用即代表您已同意免责声明。", self.disclaimer_banner)
        # 适配深色/浅色模式的文字颜色，这里使用橙色系以示警告
        warn_label.setStyleSheet("color: #d35400; font-weight: bold;")
        banner_layout.addWidget(warn_label, 1)
        
        self.btn_view_disclaimer = PushButton("查看详情", self.disclaimer_banner)
        self.btn_view_disclaimer.setFixedSize(80, 28)
        banner_layout.addWidget(self.btn_view_disclaimer)
        
        layout.addWidget(self.disclaimer_banner)
        
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
