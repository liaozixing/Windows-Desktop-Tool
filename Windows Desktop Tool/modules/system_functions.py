import os
import subprocess
import psutil
import win32api
import win32con
import shutil
import ctypes
from pathlib import Path

def open_cmd():
    """打开系统命令行窗口"""
    os.system("start cmd")

def open_task_manager():
    """打开系统任务管理器"""
    os.system("start taskmgr")

def open_explorer(path="."):
    """打开文件资源管理器到指定目录"""
    os.startfile(path)

def open_group_policy():
    """打开组策略编辑器"""
    os.system("start gpedit.msc")

def open_run_dialog():
    """打开运行对话框"""
    # 使用 powershell 调用 COM 对象打开运行框
    cmd = '(New-Object -ComObject Shell.Application).FileRun()'
    subprocess.Popen(['powershell', '-Command', cmd], shell=True)

def open_environment_variables():
    """打开系统环境变量设置"""
    os.system("rundll32.exe sysdm.cpl,EditEnvironmentVariables")

def get_cleanup_paths():
    """获取待清理的目录列表"""
    paths = {
        "系统临时文件": [
            os.environ.get('SystemRoot', 'C:\\Windows') + '\\Temp',
            os.environ.get('SystemRoot', 'C:\\Windows') + '\\Prefetch'
        ],
        "用户缓存文件": [
            os.environ.get('TEMP'),
            os.environ.get('LOCALAPPDATA') + '\\Temp',
            os.environ.get('LOCALAPPDATA') + '\\Microsoft\\Windows\\Explorer\\thumbcache_*.db'
        ],
        "回收站": ["RecycleBin"]
    }
    return paths

def scan_cleanable_files():
    """扫描可清理的文件并返回详细信息和总大小"""
    cleanup_items = []
    total_size = 0
    
    paths_config = get_cleanup_paths()
    
    for category, paths in paths_config.items():
        category_size = 0
        file_count = 0
        
        for path_str in paths:
            if path_str == "RecycleBin":
                # 获取回收站大小
                try:
                    class SHQUERYRBINFO(ctypes.Structure):
                        _fields_ = [("cbSize", ctypes.c_ulong),
                                    ("i64Size", ctypes.c_longlong),
                                    ("i64NumItems", ctypes.c_longlong)]
                    
                    rb_info = SHQUERYRBINFO()
                    rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
                    ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rb_info))
                    category_size += rb_info.i64Size
                    file_count += rb_info.i64NumItems
                except:
                    pass
                continue
                
            # 处理通配符和普通路径
            if '*' in path_str:
                base_dir = os.path.dirname(path_str)
                pattern = os.path.basename(path_str)
                if os.path.exists(base_dir):
                    for p in Path(base_dir).glob(pattern):
                        if p.is_file():
                            try:
                                s = p.stat().st_size
                                category_size += s
                                file_count += 1
                            except: pass
            else:
                if os.path.exists(path_str):
                    for root, dirs, files in os.walk(path_str):
                        for name in files:
                            try:
                                file_path = os.path.join(root, name)
                                category_size += os.path.getsize(file_path)
                                file_count += 1
                            except: pass
        
        if category_size > 0:
            cleanup_items.append({
                "category": category,
                "size": category_size,
                "count": file_count,
                "formatted_size": format_size(category_size)
            })
            total_size += category_size
            
    return cleanup_items, total_size

def format_size(size_bytes):
    """格式化字节数为可读单位"""
    if size_bytes == 0: return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

def execute_cleanup(categories, progress_callback=None):
    """执行清理操作"""
    cleaned_size = 0
    paths_config = get_cleanup_paths()
    
    total_categories = len(categories)
    for idx, category in enumerate(categories):
        if progress_callback:
            progress_callback(int((idx / total_categories) * 100), f"正在清理: {category}...")
            
        paths = paths_config.get(category, [])
        for path_str in paths:
            if path_str == "RecycleBin":
                try:
                    # 清空回收站
                    # 0x01: SHERB_NOCONFIRMATION, 0x02: SHERB_NOPROGRESSUI, 0x04: SHERB_NOSOUND
                    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
                except: pass
                continue
                
            if '*' in path_str:
                base_dir = os.path.dirname(path_str)
                pattern = os.path.basename(path_str)
                if os.path.exists(base_dir):
                    for p in Path(base_dir).glob(pattern):
                        try:
                            if p.is_file():
                                cleaned_size += p.stat().st_size
                                p.unlink()
                        except: pass
            else:
                if os.path.exists(path_str):
                    for root, dirs, files in os.walk(path_str, topdown=False):
                        for name in files:
                            try:
                                file_path = os.path.join(root, name)
                                cleaned_size += os.path.getsize(file_path)
                                os.remove(file_path)
                            except: pass
                        for name in dirs:
                            try:
                                os.rmdir(os.path.join(root, name))
                            except: pass
                            
    if progress_callback:
        progress_callback(100, "清理完成")
        
    return cleaned_size

if __name__ == "__main__":
    pass
