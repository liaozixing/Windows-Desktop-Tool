使用该软件时请先阅读 `Windows Desktop Tool\disclaimer.py` 免责声明文件

#  Windows 桌面工具 ( Windows Desktop Tool)

**版本：v1.4.0** (更新日期: 2026-01-28)

一个基于 Python 和 PyQt-Fluent-Widgets 开发的现代化 Windows 桌面实用工具集。该工具集集成网络信息查询、网速测试、文件粉碎、万能格式转换、窗口定位工具、系统快捷工具等功能，并具备完善的**实时网络监控**与**离线支持**机制。

## 🛠️ 最近更新 (v1.4.3)
- **新功能**：
  - **二维码工具**：全新上线！支持自定义文本生成二维码，一键保存或复制到剪贴板。
  - **自动更新**：支持启动时自动检查 GitHub 最新版本，不错过任何新功能。
- **体验优化**：
  - **测速重构**：重新设计的网速测试界面，采用 Catmull-Rom 算法绘制平滑曲线，告别锯齿和扭曲；自动获取 IP 归属地信息。
  - **主题统一**：全线统一蓝色主题风格，修复深色模式下部分组件显示异常的问题。
- **性能与修复**：
  - **秒级关闭**：彻底解决了程序关闭时卡顿的问题。
  - **配置持久化**：修复了自动更新开关状态无法保存的问题。
  - **移除冗余**：移除了自动清理 `__pycache__` 的功能，避免潜在的文件权限问题。

## 🛠️ 环境要求

- **操作系统**: Windows 10/11 (推荐 Windows 11)
- **Python 版本**: Python 3.8 或更高版本
- **依赖库**:
  - `PyQt5`: 界面框架
  - `PyQt-Fluent-Widgets`: Fluent Design 风格组件库
  - `Pillow`: 图片处理与格式转换
  - `pdf2docx` / `docx2pdf`: PDF 与 Word 相互转换
  - `python-docx` / `pandas`: 文档表格提取与 Excel 处理
  - `psutil`: 系统进程信息获取
  - `speedtest-cli`: 网络测速核心

## 🚀 快速开始

### 1. 克隆或下载项目
将项目代码下载到本地目录。

### 2. 安装依赖
打开终端（CMD 或 PowerShell），进入项目根目录，运行以下命令安装所需依赖：

```bash
pip install -r requirements.txt
```

### 3. 启动程序
在项目根目录下运行以下命令即可启动：

```bash
python main.py
```

## 💡 功能说明

### 1. 🌐 网络信息查询
- **高精度定位**：自动获取当前公网 IP 地址。
- **详尽数据**：显示地理位置（省、市）、运营商信息及数据来源。
- **状态详情**：点击底部状态栏查看本地内网 IP、WiFi 名称及信号。

### 2. 🚀 可视化网速测试
- **动态仪表盘**：通过仪表盘实时展示下载与上传速度。
- **实时图表**：内置测速曲线图，直观反映网络波动。

### 3. 🧹 文件粉碎工具
- **强制删除**：支持粉碎被占用的文件或文件夹，自动尝试解除进程占用。
- **智能校验**：自动识别系统关键文件并保护，防止误删导致系统崩溃。
- **快捷操作**：支持右键复制路径、打开目录，支持长路径省略显示。

### 4. 🔍 窗口弹窗定位工具
- **实时识别**：拖动定位图标至任意窗口，实时显示窗口标题、句柄、PID 及所属进程路径。
- **进程管理**：支持一键定位文件、复制路径或**直接结束目标进程**。

### 5. 🛠️ 系统工具集成
- **快捷工具栏**：一键直达命令行、任务管理器、组策略（支持家庭版一键修复）、运行框、环境变量等。
- **配置看板**：清爽的硬件配置信息弹窗，涵盖 CPU、GPU、内存、SSD 状态等。

### 6. 🔄 万能格式转换
- **图片转换**：SVG 转 ICO/PNG，PNG/JPG/WebP/BMP 互转。
- **文档转换**：PDF 互转 Word，Excel 与 Word 数据互提。
- **视频转换**：支持 MP4/MKV/MOV/AVI 等常见格式。

## 📂 项目结构

```text
Windows-Desktop-Tool/
└── Windows Desktop Tool/       # 程序主目录
    ├── modules/                # 核心功能逻辑模块
    │   ├── changelog.py        # 更新日志处理
    │   ├── file_converter.py   # 格式转换逻辑
    │   ├── file_shredder.py    # 文件粉碎逻辑
    │   ├── ip_query.py         # IP 查询逻辑
    │   ├── network_monitor.py  # 网络监控逻辑
    │   ├── network_speed.py    # 网速测试逻辑
    │   ├── settings.py         # 配置管理逻辑
    │   ├── system_functions.py # 系统工具逻辑
    │   ├── system_info.py      # 本机信息逻辑
    │   └── window_tool.py      # 窗口定位逻辑
    ├── ui/                     # 用户界面实现模块
    │   ├── background_workers.py # 后台异步任务处理
    │   ├── components.py       # 自定义 Fluent UI 组件
    │   ├── converter_interface.py # 格式转换界面
    │   ├── disclaimer_dialog.py  # 免责声明对话框
    │   ├── ip_interface.py     # IP 查询界面
    │   ├── main_window.py      # 主窗口实现
    │   ├── settings_interface.py # 设置与更新日志界面
    │   ├── shredder_interface.py # 文件粉碎界面
    │   ├── speed_test_interface.py # 网速测试界面
    │   ├── system_interface.py   # 系统功能界面
    │   └── window_tool_interface.py # 窗口工具界面
    ├── utils/                  # 通用工具模块
    ├── app.ico                 # 程序图标
    ├── app.svg                 # 程序矢量图标
    ├── config.py               # 版本号与更新日志配置
    ├── disclaimer.py           # 免责声明内容
    ├── main.py                 # 程序入口
    ├── requirements.txt        # 依赖清单
    └── settings.json           # 用户配置文件
├── README.md                   # 项目说明文档
```

---

## 📜 开源协议说明

本项目采用 **GPL-3.0 开源协议** 发布。

这意味着：

1. 你可以自由使用、修改和分发本项目代码  
2. 如果你发布修改后的版本：
   - 必须 **公开源代码**
   - 必须 **继续使用 GPL-3.0 协议**
3. 可以用于商业用途  
4. 但仍需遵守 GPL 开源规则

*由 AI 辅助开发，致力于打造更便捷的 Windows 办公环境。*
