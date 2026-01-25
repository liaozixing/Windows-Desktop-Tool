import socket
from PyQt5.QtCore import QThread, pyqtSignal

class NetworkMonitor(QThread):
    """
    网络连接监控线程
    """
    status_changed = pyqtSignal(bool)

    def __init__(self, parent=None, interval=5000):
        super().__init__(parent)
        self.interval = interval
        self.is_running = True
        self.last_status = None

    def check_connection(self):
        """
        检查网络连接
        """
        try:
            # 尝试连接常用的 DNS 服务器 (Google 或 Cloudflare)
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            return False

    def run(self):
        while self.is_running:
            current_status = self.check_connection()
            if current_status != self.last_status:
                self.status_changed.emit(current_status)
                self.last_status = current_status
            self.msleep(self.interval)

    def stop(self):
        self.is_running = False
        self.wait()
