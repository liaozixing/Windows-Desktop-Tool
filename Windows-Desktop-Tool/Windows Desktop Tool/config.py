# 全局配置与版本管理

# 应用版本号
APP_VERSION = "v1.4.3"

# 更新日期
UPDATE_DATE = "2026-01-31"

# 更新日志
CHANGELOG_TEXT = f"""{APP_VERSION} ({UPDATE_DATE})
1. [新增] 二维码工具：支持生成自定义二维码，可保存或复制图片。
2. [新增] 自动更新：支持启动时自动检查 GitHub Release 新版本。
3. [优化] 测速体验：重新设计测速界面，采用平滑曲线算法（Catmull-Rom），修复曲线“扭扭的”问题。
4. [优化] 测速功能：测速时自动获取 IP/归属地/运营商信息，修复设置按钮无法点击的问题。
5. [优化] UI 细节：统一蓝色主题风格，修复深色模式下二维码输入框背景异常。
6. [修复] 程序退出时偶尔卡顿的问题。
7. [修复] 移除自动清理 __pycache__ 功能（避免潜在的文件系统权限冲突）。"""

# GitHub 地址
GITHUB_URL = "https://github.com/liaozixing/Windows-Desktop-Tool"
