"""
后台工作线程模块
"""
from PyQt5.QtCore import QThread, pyqtSignal
from modules.ip_query import get_public_ip_info
from modules.network_speed import run_speed_test
from modules.system_functions import fix_group_policy
from modules.changelog import fetch_latest_github_release, compare_versions

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

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, repo_full_name, current_version, parent=None):
        super().__init__(parent=parent)
        self.repo_full_name = repo_full_name
        self.current_version = current_version

    def run(self):
        result = fetch_latest_github_release(self.repo_full_name)
        if not result.get("ok"):
            self.finished.emit({
                "status": "error",
                "message": result.get("message", "检查更新失败"),
                "current_version": self.current_version,
                "repo": self.repo_full_name
            })
            return
        latest = result.get("latest_version")
        url = result.get("url")
        update_available = compare_versions(latest, self.current_version) > 0
        self.finished.emit({
            "status": "success",
            "current_version": self.current_version,
            "latest_version": latest,
            "update_available": bool(update_available),
            "url": url,
            "repo": self.repo_full_name
        })

