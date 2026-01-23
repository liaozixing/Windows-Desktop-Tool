import os
import subprocess

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

def _popen(args, show_console=False):
    flags = _CREATE_NEW_CONSOLE if show_console else _CREATE_NO_WINDOW
    try:
        return subprocess.Popen(args, shell=False, creationflags=flags)
    except Exception:
        try:
            return subprocess.Popen(args, shell=True, creationflags=flags)
        except Exception:
            return None

def get_activation_status():
    """获取系统激活状态"""
    try:
        result = subprocess.run(
            ["cscript", "//nologo", os.path.join(os.environ["SystemRoot"], "System32", "slmgr.vbs"), "/xpr"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="gbk",
            errors="ignore",
            creationflags=_CREATE_NO_WINDOW,
        )
        return (result.stdout or "").strip()
    except Exception as e:
        return f"获取失败: {str(e)}"

def open_cmd():
    """打开系统命令行窗口"""
    _popen(["cmd.exe"], show_console=True)

def open_task_manager():
    """打开系统任务管理器"""
    _popen(["taskmgr.exe"])

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
        os.startfile(gpedit_path)
        return True
    except:
        return False

def fix_group_policy(progress_callback=None):
    """
    一键修复/启用组策略编辑器 (针对家庭版 Windows)
    progress_callback: 用于回传进度信息的函数
    """
    try:
        if progress_callback:
            progress_callback("正在准备修复环境...")

        import glob

        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        packages_dir = os.path.join(system_root, "servicing", "Packages")

        patterns = [
            "Microsoft-Windows-GroupPolicy-ClientExtensions-Package~3*.mum",
            "Microsoft-Windows-GroupPolicy-ClientTools-Package~3*.mum",
        ]

        package_files = []
        for pattern in patterns:
            package_files.extend(glob.glob(os.path.join(packages_dir, pattern)))

        package_names = sorted({os.path.basename(p) for p in package_files if p})
        total = len(package_names)
        if total == 0:
            return False, "未找到可用的组策略修复包"

        for i, pkg in enumerate(package_names, start=1):
            if progress_callback:
                progress_callback(f"正在安装组件 ({i}/{total}): {pkg[:30]}...")

            package_path = os.path.join(packages_dir, pkg)
            result = subprocess.run(
                ["dism", "/online", "/norestart", "/add-package", f"/packagepath:{package_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="gbk",
                errors="ignore",
                creationflags=_CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout)

        return True, "修复完成！请尝试重新打开组策略。"
    except subprocess.CalledProcessError as e:
        return False, f"执行失败 (需管理员权限): {str(e)}"
    except Exception as e:
        return False, f"修复过程出现异常: {str(e)}"

def open_run_dialog():
    """打开运行对话框"""
    _popen(["rundll32.exe", "shell32.dll,#61"])

def open_environment_variables():
    """打开系统环境变量设置"""
    _popen(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"])

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
