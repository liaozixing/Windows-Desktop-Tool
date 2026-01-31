import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtCore import QThread
from qfluentwidgets import (SubtitleLabel, PushButton, MessageBox, CaptionLabel, 
                            ToolTipFilter, ToolTipPosition, FluentIcon as FIF)

from modules.system_functions import (open_cmd, open_task_manager, open_explorer, 
                                     open_group_policy, get_activation_status)
from modules.system_info import SystemInfoWorker

class SystemInterface(QWidget):
    """ 系统功能界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SystemInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("系统工具", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 网络需求标识 (离线可用)
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 快捷工具栏 (还原原来的布局)
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

        # 绑定信号
        from modules.system_functions import open_run_dialog
        self.btn_cmd.clicked.connect(open_cmd)
        self.btn_taskmgr.clicked.connect(open_task_manager)
        self.btn_explorer.clicked.connect(lambda: open_explorer())
        self.btn_gpedit.clicked.connect(self.open_gpedit)
        self.btn_run.clicked.connect(open_run_dialog)
        self.btn_env.clicked.connect(lambda: os.system("rundll32.exe sysdm.cpl,EditEnvironmentVariables"))
        self.btn_activation.clicked.connect(self.show_activation_status)
        self.btn_sys_info.clicked.connect(self.show_system_info)

        # 检查是否为家庭版并禁用组策略按钮
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
                # 安装 ToolTipFilter 以支持 Fluent UI 样式的提示
                self.btn_gpedit.installEventFilter(ToolTipFilter(self.btn_gpedit, 500, ToolTipPosition.TOP))
        except:
            pass

    def update_network_status(self, is_online):
        """ 更新网络状态 (系统工具大多数离线可用，不需要特殊处理) """
        pass

    def open_gpedit(self):
        if not open_group_policy():
            # 如果找不到组策略，提示用户修复
            mb = MessageBox(
                "组策略编辑器未找到", 
                "系统中未找到组策略编辑器（gpedit.msc）。这通常是因为您使用的是 Windows 家庭版。\n\n是否要一键安装并启用组策略功能？", 
                self.window()
            )
            mb.yesButton.setText("立即安装")
            mb.noButton.setText("取消")
            if mb.exec_():
                # 调用主窗口的修复方法
                if hasattr(self.window(), 'start_gp_fix'):
                    self.window().start_gp_fix()

    def show_activation_status(self):
        status = get_activation_status()
        MessageBox("系统激活状态", status, self.window()).exec_()

    def show_system_info(self):
        # 创建加载提示
        self.sys_info_mb = MessageBox("请稍候", "正在深度扫描硬件配置，请稍候...", self.window())
        self.sys_info_mb.yesButton.hide()
        self.sys_info_mb.cancelButton.hide()
        
        # 启动后台线程获取信息
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
        if hasattr(self, 'sys_info_mb'):
            self.sys_info_mb.accept()
            
        if 'error' in info:
            MessageBox("获取信息失败", info['error'], self.window()).exec_()
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
