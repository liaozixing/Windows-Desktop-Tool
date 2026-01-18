import os
import subprocess

def get_activation_status():
    """获取系统激活状态"""
    try:
        # 使用 slmgr.vbs /xpr 获取激活过期日期
        result = subprocess.check_output(['cscript', '//nologo', os.path.join(os.environ['SystemRoot'], 'System32', 'slmgr.vbs'), '/xpr'], 
                                        stderr=subprocess.STDOUT, 
                                        universal_newlines=True,
                                        encoding='gbk')
        return result.strip()
    except Exception as e:
        return f"获取失败: {str(e)}"

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
    """打开组策略编辑器，如果不存在则返回 False"""
    try:
        # 检查 gpedit.msc 是否存在
        gpedit_path = os.path.join(os.environ['SystemRoot'], 'System32', 'gpedit.msc')
        if not os.path.exists(gpedit_path):
            return False
        os.system("start gpedit.msc")
        return True
    except:
        return False

def fix_group_policy(progress_callback=None):
    """
    一键修复/启用组策略编辑器 (针对家庭版 Windows)
    progress_callback: 用于回传进度信息的函数
    """
    try:
        if progress_callback: progress_callback("正在准备修复环境...")
        
        # 构造批处理指令
        # 1. 查找软件包并生成列表
        # 2. 使用 DISM 安装软件包
        commands = [
            f'dir /b %systemroot%\\servicing\\Packages\\Microsoft-Windows-GroupPolicy-ClientExtensions-Package~3*.mum > "{os.environ["TEMP"]}\\gp.txt"',
            f'dir /b %systemroot%\\servicing\\Packages\\Microsoft-Windows-GroupPolicy-ClientTools-Package~3*.mum >> "{os.environ["TEMP"]}\\gp.txt"',
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, check=True)
            
        # 读取生成的列表并安装
        list_path = os.path.join(os.environ["TEMP"], "gp.txt")
        if not os.path.exists(list_path):
            return False, "未能生成修复包列表"
            
        with open(list_path, 'r') as f:
            packages = f.readlines()
            
        total = len(packages)
        if total == 0:
            return False, "未找到可用的组策略修复包"
            
        for i, pkg in enumerate(packages):
            pkg = pkg.strip()
            if not pkg: continue
            if progress_callback: progress_callback(f"正在安装组件 ({i+1}/{total}): {pkg[:30]}...")
            
            install_cmd = f'dism /online /norestart /add-package:"%systemroot%\\servicing\\Packages\\{pkg}"'
            subprocess.run(install_cmd, shell=True, check=True)
            
        # 清理临时文件
        if os.path.exists(list_path):
            os.remove(list_path)
            
        return True, "修复完成！请尝试重新打开组策略。"
    except subprocess.CalledProcessError as e:
        return False, f"执行失败 (需管理员权限): {str(e)}"
    except Exception as e:
        return False, f"修复过程出现异常: {str(e)}"

def open_run_dialog():
    """打开运行对话框"""
    # 使用 powershell 调用 COM 对象打开运行框
    cmd = '(New-Object -ComObject Shell.Application).FileRun()'
    subprocess.Popen(['powershell', '-Command', cmd], shell=True)

def open_environment_variables():
    """打开系统环境变量设置"""
    os.system("rundll32.exe sysdm.cpl,EditEnvironmentVariables")

def clean_cache(root_dir="."):
    """递归清理 __pycache__ 文件夹"""
    count = 0
    import shutil
    for root, dirs, files in os.walk(root_dir):
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_path)
                count += 1
            except:
                continue
    return count

if __name__ == "__main__":
    pass
