from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    TextEdit,
)


class IPInterface(QWidget):
    """ IP 查询界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("IPInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        self.disclaimer_banner = QWidget(self)
        self.disclaimer_banner.setObjectName("DisclaimerBanner")
        banner_layout = QHBoxLayout(self.disclaimer_banner)
        banner_layout.setContentsMargins(15, 10, 15, 10)

        self.disclaimer_banner.setStyleSheet(
            """
            #DisclaimerBanner {
                background-color: rgba(255, 193, 7, 0.15);
                border: 1px solid rgba(255, 193, 7, 0.3);
                border-radius: 6px;
            }
        """
        )

        warn_label = BodyLabel(
            "⚠️ 严正声明：本工具仅供安全研究与技术交流，请勿用于非法用途。使用即代表您已同意免责声明。",
            self.disclaimer_banner,
        )
        warn_label.setStyleSheet("color: #d35400; font-weight: bold;")
        banner_layout.addWidget(warn_label, 1)

        self.btn_view_disclaimer = PushButton("查看详情", self.disclaimer_banner)
        self.btn_view_disclaimer.setFixedSize(80, 28)
        banner_layout.addWidget(self.btn_view_disclaimer)

        layout.addWidget(self.disclaimer_banner)

        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("公网 IP 查询", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.net_tag = CaptionLabel("需要网络", self)
        self.net_tag.setStyleSheet(
            "background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;"
        )
        header_layout.addWidget(self.net_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self.info_card = QWidget()
        self.info_card.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1);"
        )
        card_layout = QVBoxLayout(self.info_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        self.ip_info_display = TextEdit()
        self.ip_info_display.setReadOnly(True)
        self.ip_info_display.setPlaceholderText("点击下方按钮获取您的公网 IP 信息...")
        self.ip_info_display.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #e0e0e0;")
        card_layout.addWidget(self.ip_info_display)

        layout.addWidget(self.info_card)

        self.btn_query = PrimaryPushButton(FIF.GLOBE, "立即查询公网IP", self)
        self.btn_query.setFixedHeight(40)
        layout.addWidget(self.btn_query)

        layout.addStretch(1)

    def update_network_status(self, is_online):
        """ 更新网络状态相关的 UI """
        self.btn_query.setEnabled(is_online)

        from PyQt5.QtWidgets import QGraphicsOpacityEffect

        if not hasattr(self, "_net_tag_opacity"):
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
            self.net_tag.setStyleSheet(
                "background-color: rgba(232, 17, 35, 0.2); color: #e81123; padding: 2px 8px; border-radius: 4px;"
            )
        else:
            self.btn_query.setText("立即查询公网IP")
            self.ip_info_display.setPlaceholderText("点击下方按钮获取您的公网 IP 信息...")
            self.net_tag.setText("需要网络")
            self.net_tag.setStyleSheet(
                "background-color: rgba(0, 120, 212, 0.2); color: #0078d4; padding: 2px 8px; border-radius: 4px;"
            )

        self._ani2 = QPropertyAnimation(self._net_tag_opacity, b"opacity")
        self._ani2.setDuration(300)
        self._ani2.setStartValue(0.1)
        self._ani2.setEndValue(1.0)
        self._ani2.start()

    def query_ip(self):
        if not self.window().is_online:
            from qfluentwidgets import InfoBar
            InfoBar.warning("网络未连接", "请检查您的网络连接后再试", duration=3000, parent=self.window())
            return
        self.ip_info_display.setText("正在查询中，请稍候...")
        from ui.workers import IPWorker
        self.ip_worker = IPWorker()
        self.ip_worker.finished.connect(self.display_ip_info)
        self.ip_worker.start()

    def display_ip_info(self, info):
        from qfluentwidgets import InfoBar
        if info["status"] == "success":
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

            text = (
                f"公网IP: {info['ip']}\n"
                f"国家: {info['country']}\n"
                f"地区: {info['region']}\n"
                f"城市: {info['city']}\n"
                f"运营商: {raw_isp}\n"
                f"数据来源: {info.get('source', '未知')}"
            )
            self.ip_info_display.setText(text)

            # 更新速度测试界面的 IP 信息
            if hasattr(self.window(), "speed_interface"):
                speed_iface = self.window().speed_interface
                speed_iface.ip_value.setText(str(info["ip"]))
                speed_iface.isp_value.setText(isp)

                region = info.get("region", "")
                city = info.get("city", "")
                loc = f"{region} {city}".strip()
                speed_iface.loc_value.setText(loc if loc else "未知地区")

            InfoBar.success("查询成功", "公网IP信息已更新", duration=2000, parent=self.window())
        else:
            self.ip_info_display.setText(f"查询失败: {info['message']}")
            if hasattr(self.window(), "speed_interface"):
                speed_iface = self.window().speed_interface
                speed_iface.ip_value.setText("--")
                speed_iface.isp_value.setText("查询失败")
                speed_iface.loc_value.setText("--")
            InfoBar.error("查询失败", info["message"], duration=3000, parent=self.window())

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, text_color, card_bg = "#1d1d1d", "#e0e0e0", "rgba(255, 255, 255, 0.05)"
        else:
            bg_color, text_color, card_bg = "#f7f9fc", "#333333", "rgba(0, 0, 0, 0.05)"

        self.setStyleSheet(f"#IPInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.info_card.setStyleSheet(
            f"background-color: {card_bg}; border-radius: 10px; border: 1px solid {'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.1)'};"
        )
        self.ip_info_display.setStyleSheet(
            f"background: transparent; border: none; font-size: 14px; color: {text_color};"
        )

    def stop_worker(self):
        if hasattr(self, "ip_worker") and self.ip_worker.isRunning():
            self.ip_worker.quit()
