import os
import platform
import psutil
import subprocess
import ctypes
from PyQt5.QtCore import QObject, pyqtSignal

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_gpu_info():
    try:
        # 获取具体的显卡型号
        command = "wmic path win32_VideoController get name"
        output = subprocess.check_output(command, shell=True).decode('utf-8', errors='ignore')
        lines = [line.strip() for line in output.split('\n') if line.strip() and "Name" not in line]
        gpu_name = ", ".join(lines)
        return gpu_name if gpu_name else "未知"
    except:
        return "未知"

def get_disk_type(drive_letter):
    """根据盘符判断磁盘类型 (SSD/HDD)"""
    try:
        # 优化：通过更快的命令或逻辑，或者只针对物理磁盘号查询一次
        # 这里为了速度，如果 powershell 太慢，可以考虑缓存
        cmd = f"powershell \"Get-PhysicalDisk | Where-Object {{ (Get-Partition -DriveLetter {drive_letter}).DiskNumber -eq $_.DeviceId }} | Select-Object -ExpandProperty MediaType\""
        output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
        if "SSD" in output.upper():
            return "SSD"
        elif "HDD" in output.upper():
            return "HDD"
        return "本地磁盘"
    except:
        return "本地磁盘"

class SystemInfoWorker(QObject):
    """异步获取系统信息的 Worker"""
    finished = pyqtSignal(dict)

    def run(self):
        info = get_system_info()
        self.finished.emit(info)

def get_system_info():
    info = {}
    try:
        # 操作系统信息优化
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_name, _ = winreg.QueryValueEx(key, "ProductName")
            display_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
            build_number, _ = winreg.QueryValueEx(key, "CurrentBuild")
            
            # 修正 Windows 11 显示问题 (Win11 注册表中 ProductName 可能仍显示为 Win10)
            if int(build_number) >= 22000:
                product_name = product_name.replace("Windows 10", "Windows 11")
            
            # 简化名称
            product_name = product_name.replace("Microsoft ", "")
            info['os'] = f"{product_name} ({display_version})"
        except:
            uname = platform.uname()
            info['os'] = f"{uname.system} {uname.release}"
        
        # 核心硬件 (处理器)
        # 尝试通过 wmic 获取更准确的 CPU 名称
        try:
            cpu_cmd = "wmic cpu get name"
            cpu_output = subprocess.check_output(cpu_cmd, shell=True).decode('utf-8', errors='ignore')
            cpu_name = cpu_output.split('\n')[1].strip()
            info['processor'] = cpu_name
        except:
            info['processor'] = platform.processor().split(',')[0].strip()
            
        svmem = psutil.virtual_memory()
        info['memory_total'] = get_size(svmem.total)
        
        # 显卡
        info['gpu'] = get_gpu_info()
        
        # 磁盘信息优化
        partitions = psutil.disk_partitions()
        total_size = 0
        total_free = 0
        disk_details = []
        
        # 缓存磁盘类型以减少 PowerShell 调用次数
        disk_type_cache = {}
        
        for partition in partitions:
            if 'fixed' in partition.opts:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_size += usage.total
                    total_free += usage.free
                    
                    drive_letter = partition.device.split(":")[0]
                    if drive_letter not in disk_type_cache:
                        disk_type_cache[drive_letter] = get_disk_type(drive_letter)
                    
                    dtype = disk_type_cache[drive_letter]
                    disk_details.append(f"• {partition.device} [{dtype}]: {get_size(usage.total)} (剩余 {get_size(usage.free)})")
                except:
                    continue
        
        info['disk_summary'] = f"{get_size(total_size)} (可用 {get_size(total_free)})"
        info['disk_details'] = "\n".join(disk_details)
        info['node'] = platform.node()
        
    except Exception as e:
        info['error'] = str(e)
    
    return info
