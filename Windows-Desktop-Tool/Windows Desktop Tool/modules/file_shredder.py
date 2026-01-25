import os
import shutil
import stat
import psutil
from PyQt5.QtCore import QThread, pyqtSignal

def is_system_path(path, check_processes=False):
    """
    检查路径是否为系统关键文件路径
    check_processes: 是否检查进程占用（耗时操作，默认关闭以提高性能）
    """
    try:
        path = os.path.abspath(path).lower()
        system_drive = os.environ.get('SystemDrive', 'C:').lower()
        
        # 关键目录列表
        critical_dirs = [
            os.path.join(system_drive, "\\windows").lower(),
            os.path.join(system_drive, "\\program files").lower(),
            os.path.join(system_drive, "\\program files (x86)").lower(),
            os.path.join(system_drive, "\\users\\default").lower(),
            # 补充一些极其关键的
            os.path.join(system_drive, "\\boot").lower(),
            os.path.join(system_drive, "\\recovery").lower(),
            os.path.join(system_drive, "\\pagefile.sys").lower(),
            os.path.join(system_drive, "\\swapfile.sys").lower(),
            os.path.join(system_drive, "\\hiberfil.sys").lower(),
            os.path.join(system_drive, "\\msocache").lower(),
            os.path.join(system_drive, "\\system volume information").lower(),
        ]
        
        # 注册表相关系统文件 (通常在 System32\config)
        reg_files_dir = os.path.join(system_drive, "\\windows\\system32\\config").lower()
        critical_dirs.append(reg_files_dir)
        
        # 白名单增强建议：禁止粉碎系统盘根目录下的文件
        if path == system_drive + "\\" or path == system_drive:
            return True, "禁止对系统盘根目录进行粉碎操作"

        for critical in critical_dirs:
            if path.startswith(critical):
                return True, "检测到系统关键文件，为防止系统损坏，已禁止操作"

        # 检查是否被系统关键进程占用 (仅在 check_processes=True 时执行)
        if check_processes:
            abs_path = os.path.abspath(path)
            for proc in psutil.process_iter(['pid', 'open_files']):
                try:
                    if proc.info['pid'] <= 1000:
                        for file in proc.info.get('open_files') or []:
                            if os.path.abspath(file.path) == abs_path:
                                return True, "此文件正在被系统关键进程占用，禁止操作"
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
    except Exception:
        pass

    return False, ""

def try_kill_locking_processes(path):
    """尝试终止占用该文件的进程"""
    try:
        abs_path = os.path.abspath(path)
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                for file in proc.info.get('open_files') or []:
                    if os.path.abspath(file.path) == abs_path:
                        proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass

def force_delete(path):
    """
    尝试强制删除文件或文件夹
    """
    try:
        if not os.path.exists(path):
            return True, "文件已不存在"

        # 先尝试普通删除
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
                return True, "成功粉碎"
            elif os.path.isdir(path):
                shutil.rmtree(path, onerror=remove_readonly)
                return True, "成功粉碎"
        except (PermissionError, OSError):
            # 如果失败（可能是被占用），尝试解除占用后重试
            try_kill_locking_processes(path)
            
            # 再次尝试删除
            if os.path.isfile(path) or os.path.islink(path):
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
            elif os.path.isdir(path):
                # 递归处理只读属性并删除
                for root, dirs, files in os.walk(path):
                    for momo in dirs:
                        try: os.chmod(os.path.join(root, momo), stat.S_IWRITE)
                        except: pass
                    for momo in files:
                        try: os.chmod(os.path.join(root, momo), stat.S_IWRITE)
                        except: pass
                shutil.rmtree(path, onerror=remove_readonly)
            return True, "成功粉碎"
            
    except Exception as e:
        return False, str(e)

def remove_readonly(func, path, _):
    """清除只读属性并重新尝试删除"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

class ValidationWorker(QThread):
    """
    后台校验文件占用情况（性能优化版：仅执行快速路径校验）
    """
    finished = pyqtSignal(str, bool, str) # 路径, 是否是系统文件, 原因

    def __init__(self, paths):
        super().__init__()
        self.paths = [os.path.abspath(p).lower() for p in paths]
        self.path_map = {os.path.abspath(p).lower(): p for p in paths}

    def run(self):
        # 批量匹配路径，跳过耗时的进程扫描
        for abs_path_lower in self.paths:
            original_path = self.path_map[abs_path_lower]
            
            # 执行快速路径检查
            is_sys, reason = is_system_path(original_path, check_processes=False)
            if is_sys:
                self.finished.emit(original_path, True, reason)
            else:
                self.finished.emit(original_path, False, "")

class ShredderWorker(QThread):
    progress = pyqtSignal(int, str)
    file_finished = pyqtSignal(str, bool, str) # 路径, 是否成功, 消息
    finished = pyqtSignal(int, int, list) # 成功数, 失败数, 错误列表

    def __init__(self, paths):
        super().__init__()
        self.paths = paths

    def run(self):
        success_count = 0
        fail_count = 0
        errors = []
        total = len(self.paths)

        for i, path in enumerate(self.paths):
            # 最后的安全检查
            is_sys, _ = is_system_path(path)
            if is_sys:
                fail_count += 1
                msg = "系统关键文件，禁止操作"
                errors.append(f"{path}: {msg}")
                self.file_finished.emit(path, False, msg)
                continue

            if not os.path.exists(path):
                fail_count += 1
                msg = "文件不存在"
                errors.append(f"{path}: {msg}")
                self.file_finished.emit(path, False, msg)
                continue
            
            self.progress.emit(int(i / total * 100), f"正在粉碎: {os.path.basename(path)}")
            
            # 尝试解除占用
            success, msg = force_delete(path)
            if success:
                success_count += 1
                self.file_finished.emit(path, True, "已粉碎")
            else:
                fail_count += 1
                errors.append(f"{path}: {msg}")
                self.file_finished.emit(path, False, msg)
        
        self.finished.emit(success_count, fail_count, errors)
