import ctypes
import ctypes.wintypes
import psutil
import os
import subprocess

# Windows API 定义
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def get_window_info_at(x, y):
    """获取指定坐标处的窗口信息"""
    point = ctypes.wintypes.POINT(x, y)
    hwnd = user32.WindowFromPoint(point)
    
    if not hwnd:
        return None
    
    # 获取顶层窗口 (如果当前是子窗口)
    root_hwnd = user32.GetAncestor(hwnd, 2) # GA_ROOT
    if root_hwnd:
        hwnd = root_hwnd

    # 获取窗口标题
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value

    # 获取进程 ID
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid = pid.value

    # 获取进程信息
    process_name = "未知"
    process_path = "未知"
    try:
        proc = psutil.Process(pid)
        process_name = proc.name()
        process_path = proc.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    return {
        "hwnd": hwnd,
        "title": title,
        "pid": pid,
        "process_name": process_name,
        "process_path": process_path,
        "rect": get_window_rect(hwnd)
    }

def get_window_rect(hwnd):
    """获取窗口矩形坐标"""
    rect = ctypes.wintypes.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    return None

def open_file_location(path):
    """打开文件所在位置并选中文件"""
    if not path or path == "未知" or not os.path.exists(path):
        return False
    
    try:
        # 使用 explorer /select, "path" 选中文件
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        return True
    except Exception:
        return False
