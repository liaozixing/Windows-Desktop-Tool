from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    CaptionLabel,
    FluentIcon as FIF,
    MessageBox,
    PushButton,
    SubtitleLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from modules.system_functions import (
    get_activation_status,
    open_cmd,
    open_environment_variables,
    open_explorer,
    open_group_policy,
    open_run_dialog,
    open_task_manager,
)
from modules.system_info import SystemInfoWorker


class SystemInterface(QWidget):
    """ 系统功能界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SystemInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("系统工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet(
            "background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;"
        )
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        tools_layout = QGridLayout()
        self.btn_cmd = PushButton(FIF.COMMAND_PROMPT, "命令行", self)
        self.btn_taskmgr = PushButton(FIF.BASKETBALL, "任务管理器", self)
        self.btn_explorer = PushButton(FIF.FOLDER, "资源管理器", self)
        self.btn_gpedit = PushButton(FIF.SETTING, "组策略", self)
        self.btn_run = PushButton(FIF.SEND, "运行框", self)
        self.btn_env = PushButton(FIF.SETTING, "环境变量", self)

        tools_layout.addWidget(self.btn_cmd, 0, 0)
        tools_layout.addWidget(self.btn_taskmgr, 0, 1)
        tools_layout.addWidget(self.btn_explorer, 0, 2)
        tools_layout.addWidget(self.btn_gpedit, 1, 0)
        tools_layout.addWidget(self.btn_run, 1, 1)
        tools_layout.addWidget(self.btn_env, 1, 2)
        layout.addLayout(tools_layout)

        layout.addSpacing(20)
        self.other_title = SubtitleLabel("其他工具", self)
        self.other_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(self.other_title)

        other_layout = QGridLayout()
        self.btn_activation = PushButton(FIF.ACCEPT, "系统激活状态", self)
        self.btn_sys_info = PushButton(FIF.INFO, "本机配置信息", self)
        other_layout.addWidget(self.btn_activation, 0, 0)
        other_layout.addWidget(self.btn_sys_info, 0, 1)
        other_layout.setColumnStretch(2, 1)
        layout.addLayout(other_layout)

        layout.addStretch(1)

        self.btn_cmd.clicked.connect(open_cmd)
        self.btn_taskmgr.clicked.connect(open_task_manager)
        self.btn_explorer.clicked.connect(lambda: open_explorer())
        self.btn_gpedit.clicked.connect(self.open_gpedit)
        self.btn_run.clicked.connect(open_run_dialog)
        self.btn_env.clicked.connect(open_environment_variables)
        self.btn_activation.clicked.connect(self.show_activation_status)
        self.btn_sys_info.clicked.connect(self.show_system_info)

        self._check_home_edition()

    def _check_home_edition(self):
        """ 检查 Windows 版本，如果是家庭版则禁用组策略按钮并添加提示 """
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            edition, _ = winreg.QueryValueEx(key, "EditionID")
            if "HOME" in edition.upper():
                self.btn_gpedit.setEnabled(False)
                self.btn_gpedit.setToolTip("此功能在 Windows 家庭版中不可用")
                self.btn_gpedit.installEventFilter(ToolTipFilter(self.btn_gpedit, 500, ToolTipPosition.TOP))
        except:
            pass

    def update_network_status(self, is_online):
        """ 更新网络状态 (系统工具大多数离线可用，不需要特殊处理) """
        pass

    def start_gp_fix(self):
        from qfluentwidgets import MessageBox
        self.gp_fix_mb = MessageBox("正在安装组策略", "正在初始化安装程序...", self.window())
        self.gp_fix_mb.yesButton.hide()
        self.gp_fix_mb.noButton.setText("后台运行")

        from ui.workers import GPFixWorker
        self.gp_worker = GPFixWorker()
        self.gp_worker.progress.connect(self.on_gp_fix_progress)
        self.gp_worker.finished.connect(self.on_gp_fix_finished)
        self.gp_worker.start()

        self.gp_fix_mb.exec_()

    def on_gp_fix_progress(self, msg):
        if hasattr(self, "gp_fix_mb") and self.gp_fix_mb.isVisible():
            self.gp_fix_mb.contentLabel.setText(msg)

    def on_gp_fix_finished(self, success, message):
        if hasattr(self, "gp_fix_mb") and self.gp_fix_mb.isVisible():
            self.gp_fix_mb.done(0)

        from qfluentwidgets import InfoBar
        if success:
            InfoBar.success("修复成功", message, duration=5000, parent=self.window())
            from modules.system_functions import open_group_policy
            open_group_policy()
        else:
            if "管理员权限" in message:
                message = "修复失败：需要管理员权限。请尝试右键以管理员身份运行本程序后再重试。"
            InfoBar.error("修复失败", message, duration=5000, parent=self.window())

    def open_gpedit(self):
        from modules.system_functions import open_group_policy
        if not open_group_policy():
            from qfluentwidgets import MessageBox
            mb = MessageBox(
                "组策略编辑器未找到",
                "系统中未找到组策略编辑器（gpedit.msc）。这通常是因为您使用的是 Windows 家庭版。\n\n是否要一键安装并启用组策略功能？",
                self.window(),
            )
            mb.yesButton.setText("立即安装")
            mb.noButton.setText("取消")
            if mb.exec_():
                self.start_gp_fix()

    def show_activation_status(self):
        status = get_activation_status()
        MessageBox("系统激活状态", status, self.window()).exec_()

    def show_system_info(self):
        self.sys_info_mb = MessageBox("请稍候", "正在深度扫描硬件配置，请稍候...", self.window())
        self.sys_info_mb.yesButton.hide()
        self.sys_info_mb.cancelButton.hide()

        self.sys_info_thread = QThread()
        self.sys_info_worker = SystemInfoWorker()
        self.sys_info_worker.moveToThread(self.sys_info_thread)
        self.sys_info_thread.started.connect(self.sys_info_worker.run)
        self.sys_info_worker.finished.connect(self._on_sys_info_finished)
        self.sys_info_worker.finished.connect(self.sys_info_thread.quit)
        self.sys_info_worker.finished.connect(self.sys_info_worker.deleteLater)
        self.sys_info_thread.finished.connect(self.sys_info_thread.deleteLater)

        self.sys_info_thread.start()
        self.sys_info_mb.exec_()

    def _on_sys_info_finished(self, info):
        if hasattr(self, "sys_info_mb"):
            self.sys_info_mb.accept()

        if "error" in info:
            MessageBox("获取信息失败", info["error"], self.window()).exec_()
            return

        info_str = (
            f"💻 计算机名称:  {info.get('node', '未知')}\n"
            f"💿 操作系统:    {info.get('os', '未知')}\n"
            f"🧠 处理器:      {info.get('processor', '未知')}\n"
            f"📟 内存总量:    {info.get('memory_total', '未知')}\n"
            f"🎨 显卡型号:    {info.get('gpu', '未知')}\n\n"
            f"💽 硬盘总容量:  {info.get('disk_summary', '未知')}\n"
            f"----------------------------------\n"
            f"{info.get('disk_details', '未知')}"
        )

        mb = MessageBox("本机配置信息", info_str, self.window())
        mb.yesButton.setText("确定")
        mb.cancelButton.hide()
        mb.exec_()

    def stop_worker(self):
        if hasattr(self, "gp_worker") and self.gp_worker.isRunning():
            self.gp_worker.quit()
        if hasattr(self, "sys_info_thread") and self.sys_info_thread.isRunning():
            self.sys_info_thread.quit()

    def show_network_details(self, is_online):
        """ 显示网络连接详情 """
        import socket
        import subprocess
        details = "正在获取网络信息..."
        if not is_online:
            details = "❌ 当前未连接到互联网"
        else:
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)

                ssid = "未知 (可能为有线连接)"
                signal = "未知"
                try:
                    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    result = subprocess.run(
                        ["netsh", "wlan", "show", "interfaces"],
                        capture_output=True,
                        text=True,
                        encoding="gbk",
                        errors="ignore",
                        creationflags=flags,
                    )
                    output = result.stdout

                    for line in output.split("\n"):
                        if " SSID" in line and "BSSID" not in line:
                            ssid = line.split(":")[1].strip()
                        if "信号" in line or "Signal" in line:
                            signal = line.split(":")[1].strip()
                except Exception:
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

        mb = MessageBox("网络连接详情", details, self.window())
        mb.yesButton.setText("确定")
        mb.cancelButton.hide()
        mb.exec_()
