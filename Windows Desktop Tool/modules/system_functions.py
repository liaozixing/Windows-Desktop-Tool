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

if __name__ == "__main__":
    pass
