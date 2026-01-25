"""
后台工作线程模块
"""
from PyQt5.QtCore import QThread, pyqtSignal
from modules.ip_query import get_public_ip_info
from modules.network_speed import run_speed_test
from modules.system_functions import fix_group_policy

class IPWorker(QThread):
    """IP查询工作线程"""
    finished = pyqtSignal(dict)

    def run(self):
        result = get_public_ip_info()
        self.finished.emit(result)

class SpeedTestWorker(QThread):
    """网速测试工作线程"""
    progress = pyqtSignal(str)
    metric = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(self, provider="auto", parent=None):
        super().__init__(parent=parent)
        self.provider = provider

    def run(self):
        result = run_speed_test(self.progress.emit, provider=self.provider, metric_callback=self.metric.emit)
        self.finished.emit(result)

class GPFixWorker(QThread):
    """组策略修复线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def run(self):
        success, message = fix_group_policy(self.progress.emit)
        self.finished.emit(success, message)

