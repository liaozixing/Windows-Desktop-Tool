"""
更新日志管理模块
用于记录和管理软件更新日志
支持从 README.md 自动同步最近更新内容
"""
import os
import sys
import json
import re
from datetime import datetime
from modules.settings import _CONFIG_DIR

CHANGELOG_FILE = os.path.join(_CONFIG_DIR, "changelog.json")

def get_changelog_file():
    """获取更新日志文件路径"""
    return CHANGELOG_FILE

def ensure_changelog_dir():
    """确保更新日志目录存在"""
    os.makedirs(os.path.dirname(CHANGELOG_FILE), exist_ok=True)

def write_changelog_entry(version, changes, date=None):
    """
    写入更新日志条目
    
    Args:
        version: 版本号，如 "v1.2.0"
        changes: 更新内容列表，如 ["修复了bug", "新增功能"]
        date: 日期字符串，格式为 "YYYY-MM-DD"，如果为None则使用当前日期
    """
    ensure_changelog_dir()
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 读取现有日志
    changelog_data = []
    if os.path.exists(CHANGELOG_FILE):
        try:
            with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                changelog_data = json.load(f)
        except Exception:
            changelog_data = []
    
    # 检查版本是否已存在
    existing_index = None
    for i, entry in enumerate(changelog_data):
        if entry.get('version') == version:
            existing_index = i
            break
    
    # 创建新条目
    new_entry = {
        'version': version,
        'date': date,
        'changes': changes if isinstance(changes, list) else [changes]
    }
    
    # 如果版本已存在，更新它；否则添加到开头
    if existing_index is not None:
        changelog_data[existing_index] = new_entry
    else:
        changelog_data.insert(0, new_entry)
    
    # 限制日志条目数量（保留最近50条）
    changelog_data = changelog_data[:50]
    
    # 写入文件
    try:
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(changelog_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"写入更新日志失败: {e}")
        return False

def read_changelog(limit=10):
    """
    读取更新日志
    
    Args:
        limit: 返回的条目数量限制
    
    Returns:
        日志条目列表，按时间倒序排列
    """
    if not os.path.exists(CHANGELOG_FILE):
        return []
    
    try:
        with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
            changelog_data = json.load(f)
        return changelog_data[:limit]
    except Exception:
        return []

def format_changelog_text(entries=None, max_entries=10):
    """
    格式化更新日志为文本格式
    
    Args:
        entries: 日志条目列表，如果为None则自动读取
        max_entries: 最大条目数
    
    Returns:
        格式化后的文本字符串
    """
    if entries is None:
        entries = read_changelog(max_entries)
    
    if not entries:
        return "暂无更新日志"
    
    lines = []
    for entry in entries:
        version = entry.get('version', '未知版本')
        date = entry.get('date', '未知日期')
        changes = entry.get('changes', [])
        
        lines.append(f"{version} ({date})")
        if isinstance(changes, list):
            for change in changes:
                lines.append(f"  {change}")
        else:
            lines.append(f"  {changes}")
        lines.append("")
    
    return "\n".join(lines)

def get_latest_version():
    """获取最新版本号"""
    entries = read_changelog(1)
    if entries:
        return entries[0].get('version', 'v1.0.0')
    return 'v1.0.0'

def find_readme_path():
    """
    查找 README.md 文件路径
    支持多种可能的路径
    """
    possible_paths = [
        # 当前工作目录
        os.path.join(os.getcwd(), "README.md"),
        # 脚本所在目录的父目录（Windows Desktop Tool 的父目录）
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md"),
        # 当前脚本所在目录的上一级目录（针对 Windows Desktop Tool 目录内部的情况）
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md"),
        # 打包后的情况
        os.path.join(os.path.dirname(sys.executable), "README.md") if getattr(sys, 'frozen', False) else None,
        # 从当前文件位置向上查找
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md"),
    ]
    
    # 过滤掉None值
    possible_paths = [p for p in possible_paths if p]
    
    for readme_path in possible_paths:
        if os.path.exists(readme_path):
            return readme_path
    
    return None

def parse_recent_updates_from_readme():
    """
    从 README.md 中解析"最近更新"部分
    
    Returns:
        tuple: (version, changes_list, date) 或 (None, None, None) 如果解析失败
    """
    readme_path = find_readme_path()
    if not readme_path:
        return None, None, None
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找"最近更新"部分
        # 匹配模式：## 🛠️ 最近更新 (v1.2.0) 或类似格式
        pattern = r'##\s*🛠️\s*最近更新\s*\(([vV]?\d+\.\d+\.\d+)\)'
        match = re.search(pattern, content)
        
        if not match:
            return None, None, None
        
        version = match.group(1)
        if not version.lower().startswith('v'):
            version = 'v' + version
        
        # 提取更新日期（从 README 顶部）
        date_match = re.search(r'\*\*版本[：:]\s*[vV]?\d+\.\d+\.\d+\*\*\s*\(更新日期[：:]\s*(\d{4}-\d{2}-\d{2})\)', content)
        date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        # 提取"最近更新"部分的内容
        # 找到"最近更新"标题后的内容，直到下一个 ## 标题
        start_pos = match.end()
        next_section_match = re.search(r'\n##\s+', content[start_pos:])
        if next_section_match:
            updates_text = content[start_pos:start_pos + next_section_match.start()]
        else:
            updates_text = content[start_pos:]
        
        # 解析更新内容列表
        changes = []
        lines = updates_text.split('\n')
        current_main_item = None
        current_sub_items = []
        
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # 匹配主项（以 - ** 开头，且后面有冒号或直接换行）
            main_match = re.match(r'^-\s*\*\*(.+?)\*\*[：:]?\s*$', line)
            if main_match:
                # 如果有之前的主项，先保存
                if current_main_item:
                    if current_sub_items:
                        # 合并主项和子项
                        item_text = f"{current_main_item}：{'；'.join(current_sub_items)}"
                    else:
                        item_text = current_main_item
                    changes.append(item_text)
                    current_sub_items = []
                current_main_item = main_match.group(1).strip()
            # 匹配子项（以 - 开头，但不是 ** 开头，通常是缩进的）
            elif line.startswith('-') and not line.startswith('- **'):
                sub_item = line.lstrip('- ').strip()
                # 移除可能的 ** 标记
                sub_item = re.sub(r'\*\*([^*]+)\*\*', r'\1', sub_item)
                if current_main_item:
                    current_sub_items.append(sub_item)
                else:
                    # 如果没有主项，直接添加为独立项
                    changes.append(sub_item)
            # 匹配子项内容（以 - ** 开头，但缩进更多，表示是子项）
            elif re.match(r'^\s{2,}-\s*\*\*(.+?)\*\*[：:]?\s*$', line):
                sub_match = re.match(r'^\s{2,}-\s*\*\*(.+?)\*\*[：:]?\s*$', line)
                if sub_match:
                    sub_item = sub_match.group(1).strip()
                    if current_main_item:
                        current_sub_items.append(sub_item)
                    else:
                        changes.append(sub_item)
            # 匹配其他内容（可能是子项的继续，或者是普通文本）
            elif line and not line.startswith('#'):
                # 如果是主项的继续（没有 - 开头）
                if current_main_item and not line.startswith('-'):
                    # 检查是否是子项的详细说明
                    if current_sub_items:
                        # 添加到最后一个子项
                        current_sub_items[-1] += ' ' + line
                    else:
                        # 添加到主项
                        current_main_item += ' ' + line
        
        # 添加最后一个项
        if current_main_item:
            if current_sub_items:
                item_text = f"{current_main_item}：{'；'.join(current_sub_items)}"
            else:
                item_text = current_main_item
            changes.append(item_text)
        
        # 如果没有解析到内容，尝试简单模式
        if not changes:
            # 简单模式：提取所有以 - 开头的行
            for line in lines:
                line = line.strip()
                if line.startswith('-') and len(line) > 2:
                    # 移除 - 和可能的 ** 标记
                    clean_line = re.sub(r'^-\s*\*\*?', '', line)
                    clean_line = re.sub(r'\*\*?[：:]?\s*$', '', clean_line)
                    clean_line = clean_line.strip()
                    if clean_line:
                        changes.append(clean_line)
        
        return version, changes, date
    
    except Exception as e:
        print(f"解析 README.md 失败: {e}")
        return None, None, None

def sync_changelog_from_readme():
    """
    从 README.md 同步最近更新到更新日志
    如果 README.md 中的最近更新变化了，会自动更新 changelog.json
    当 README.md 更新到新版本时，会自动清理旧版本日志，只保留当前版本
    
    Returns:
        bool: 是否成功同步
    """
    version, changes, date = parse_recent_updates_from_readme()
    
    if not version or not changes:
        return False
    
    ensure_changelog_dir()
    
    # 读取现有日志
    changelog_data = []
    if os.path.exists(CHANGELOG_FILE):
        try:
            with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                changelog_data = json.load(f)
        except Exception:
            changelog_data = []
    
    # 检查是否已存在该版本的日志
    existing_entry = None
    existing_index = None
    for i, entry in enumerate(changelog_data):
        if entry.get('version') == version:
            existing_entry = entry
            existing_index = i
            break
    
    # 如果已存在，检查内容是否相同
    if existing_entry:
        existing_changes = existing_entry.get('changes', [])
        # 比较内容（转换为字符串列表进行比较，忽略顺序）
        if isinstance(existing_changes, list) and isinstance(changes, list):
            # 标准化字符串（去除多余空格）
            existing_normalized = [str(c).strip() for c in existing_changes]
            new_normalized = [str(c).strip() for c in changes]
            # 排序后比较
            existing_str = '\n'.join(sorted(existing_normalized))
            new_str = '\n'.join(sorted(new_normalized))
            if existing_str == new_str:
                # 内容相同，但需要清理旧版本
                # 只保留当前 README.md 中显示的版本
                changelog_data = [existing_entry]
                try:
                    with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(changelog_data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"清理旧版本日志失败: {e}")
                return True
    
    # 如果版本更新了（README.md 中的版本与现有日志中的最新版本不同）
    # 清理所有旧版本，只保留当前 README.md 中的版本
    new_entry = {
        'version': version,
        'date': date,
        'changes': changes if isinstance(changes, list) else [changes]
    }
    
    # 只保留当前版本（清理所有旧版本）
    changelog_data = [new_entry]
    
    # 写入文件
    try:
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(changelog_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"写入更新日志失败: {e}")
        return False

def _normalize_version_to_tuple(version_text):
    if version_text is None:
        return ()
    s = str(version_text).strip()
    s = re.sub(r'^[vV]\s*', '', s)
    s = re.sub(r'[^0-9.].*$', '', s)
    parts = [p for p in s.split('.') if p != '']
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except Exception:
            break
    while out and out[-1] == 0:
        out.pop()
    return tuple(out)

def compare_versions(a, b):
    va = _normalize_version_to_tuple(a)
    vb = _normalize_version_to_tuple(b)
    max_len = max(len(va), len(vb))
    va = va + (0,) * (max_len - len(va))
    vb = vb + (0,) * (max_len - len(vb))
    if va > vb:
        return 1
    if va < vb:
        return -1
    return 0

def fetch_latest_github_release(repo_full_name, timeout_sec=6):
    try:
        import requests
        url = f"https://api.github.com/repos/{repo_full_name}/releases/latest"
        r = requests.get(url, headers={"User-Agent": "Windows-Desktop-Tool"}, timeout=timeout_sec)
        if r.status_code != 200:
            return {"ok": False, "message": f"请求失败: HTTP {r.status_code}"}
        data = r.json() or {}
        tag = data.get("tag_name") or ""
        html_url = data.get("html_url") or f"https://github.com/{repo_full_name}/releases"
        name = data.get("name") or ""
        latest = tag.strip() or name.strip()
        if not latest:
            return {"ok": False, "message": "未获取到版本号"}
        return {"ok": True, "latest_version": latest, "url": html_url}
    except Exception as e:
        return {"ok": False, "message": str(e)}

if __name__ == "__main__":
    # 测试代码
    write_changelog_entry("v1.2.0", [
        "[重构] 格式转换界面：合并图片与文档转换，新增视频转换功能",
        "[优化] 配置保存：配置文件迁移至 %APPDATA% 目录",
        "[新增] 退出确认：新增退出确认对话框",
    ])
    print(format_changelog_text())
