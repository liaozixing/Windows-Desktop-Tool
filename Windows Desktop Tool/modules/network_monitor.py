import socket
import time
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class NetworkMonitor(QThread):
    """
    网络连接监控线程
    """
    status_changed = pyqtSignal(bool)

    def __init__(
        self,
        parent=None,
        interval=5000,
        startup_interval=300,
        startup_grace_ms=2500,
        startup_offline_threshold=3,
        runtime_offline_threshold=2,
    ):
        super().__init__(parent)
        self.interval = int(interval)
        self.startup_interval = int(startup_interval)
        self.startup_grace_ms = int(startup_grace_ms)
        self.startup_offline_threshold = int(startup_offline_threshold)
        self.runtime_offline_threshold = int(runtime_offline_threshold)
        self.is_running = True
        self.last_status = None
        self._fail_count = 0
        self._startup_deadline = None

    def check_connection(self):
        """
        检查网络连接
        """
        tcp_targets = [
            ("223.5.5.5", 53),
            ("114.114.114.114", 53),
            ("1.1.1.1", 53),
        ]
        try:
            for host, port in tcp_targets:
                try:
                    conn = socket.create_connection((host, port), timeout=0.3)
                    conn.close()
                    return True
                except OSError:
                    continue

            try:
                r = requests.get(
                    "http://whois.pconline.com.cn/ipJson.jsp?json=true",
                    timeout=(0.5, 0.5),
                    headers={"User-Agent": "Windows-Desktop-Tool/1.0"},
                )
                return r.status_code == 200
            except Exception:
                return False
        except Exception:
            return False

    def run(self):
        self._startup_deadline = time.monotonic() + (self.startup_grace_ms / 1000.0)
        while self.is_running:
            current_status = self.check_connection()
            now = time.monotonic()

            if current_status:
                self._fail_count = 0
                if current_status != self.last_status:
                    self.status_changed.emit(True)
                    self.last_status = True
            else:
                self._fail_count += 1
                threshold = (
                    self.startup_offline_threshold
                    if now < self._startup_deadline
                    else self.runtime_offline_threshold
                )
                if self._fail_count >= threshold and current_status != self.last_status:
                    self.status_changed.emit(False)
                    self.last_status = False

            sleep_ms = self.startup_interval if now < self._startup_deadline else self.interval
            self.msleep(sleep_ms)

    def stop(self):
        self.is_running = False
        self.wait()
