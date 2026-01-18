import os
import sys
import winreg
import json

CONFIG_FILE = "settings.json"

def set_auto_start(enabled=True):
    """设置或取消开机自启动 (通过注册表)"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "UniversalWindowsDesktopTool"
    # 获取当前执行文件的路径
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = os.path.abspath(sys.argv[0])
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"设置自启动失败: {e}")
        return False

def save_settings(settings):
    """保存配置到 JSON 文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def load_settings():
    """从 JSON 文件加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    # 默认配置
    return {
        "auto_start": False,
        "minimize_to_tray": True,
        "theme": "深色",
        "accent_color": "#1677ff",
        "language": "简体中文",
        "disclaimer_accepted": False
    }

if __name__ == "__main__":
    # set_auto_start(True)
    pass
