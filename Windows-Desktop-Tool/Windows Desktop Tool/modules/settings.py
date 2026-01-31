import os
import sys
import winreg
import json

APP_NAME = "UniversalWindowsDesktopTool"
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

_CONFIG_ROOT = os.getenv("APPDATA") or _BASE_DIR
_CONFIG_DIR = os.path.join(_CONFIG_ROOT, APP_NAME)
CONFIG_FILE = os.path.join(_CONFIG_DIR, "settings.json")

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
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def load_settings():
    """从 JSON 文件加载配置"""
    defaults = {
        "auto_start": False,
        "minimize_to_tray": True,
        "theme": "深色",
        "accent_color": "#1677ff",
        "language": "简体中文",
        "disclaimer_accepted": False,
        "auto_check_updates": True
    }

    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception as e:
            print(f"加载配置失败: {e}")
    legacy_file = os.path.join(_BASE_DIR, "settings.json")
    if not data and os.path.exists(legacy_file):
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception as e:
            print(f"迁移旧配置失败: {e}")

    if isinstance(data, dict):
        if "auto_check_update" in data and "auto_check_updates" not in data:
            data["auto_check_updates"] = bool(data.get("auto_check_update"))
            data.pop("auto_check_update", None)

    merged = defaults.copy()
    if isinstance(data, dict):
        merged.update(data)

    save_settings(merged)
    return merged

if __name__ == "__main__":
    # set_auto_start(True)
    pass
