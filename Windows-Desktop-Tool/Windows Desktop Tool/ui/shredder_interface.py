import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem, QMenu, QAction, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qfluentwidgets import (SubtitleLabel, BodyLabel, CaptionLabel, PrimaryPushButton, 
                            PushButton, FluentIcon as FIF, InfoBar, MessageBox, 
                            TableWidget, ProgressBar)

from modules.file_shredder import ShredderWorker, is_system_path, ValidationWorker
from modules.window_tool import open_file_location

class ShredderInterface(QWidget):
    """ 文件粉碎界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ShredderInterface")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("文件粉碎", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 离线标识
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self.desc = BodyLabel("将需要销毁的文件或文件夹拖入此处，或点击下方按钮添加。", self)
        layout.addWidget(self.desc)

        # 文件列表
        self.file_list = TableWidget(self)
        self.file_list.setColumnCount(3)
        self.file_list.setHorizontalHeaderLabels(["路径", "类型", "当前状态"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.file_list.setColumnWidth(1, 100)
        self.file_list.setColumnWidth(2, 120)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.file_list)

        # 按钮栏
        btn_layout = QHBoxLayout()
        self.btn_add_file = PushButton(FIF.ADD, "添加文件", self)
        self.btn_add_folder = PushButton(FIF.FOLDER, "添加文件夹", self)
        self.btn_remove = PushButton(FIF.REMOVE, "移除选中", self)
        self.btn_clear = PushButton(FIF.DELETE, "清空列表", self)
        self.btn_shred = PrimaryPushButton(FIF.BROOM, "立即粉碎", self)
        
        btn_layout.addWidget(self.btn_add_file)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_shred)
        layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = CaptionLabel("", self)
        layout.addWidget(self.status_label)

        # 绑定信号
        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_shred.clicked.connect(self.start_shredding)

        self.paths = set()
        self.system_paths = set() # 新增：记录系统文件路径
        self.update_desc()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_paths(files)

    def add_files(self):
        from PyQt5.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*.*)")
        if files:
            self.add_paths(files)

    def add_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths):
        to_validate = []
        for path in paths:
            path = os.path.normpath(path)
            if path in self.paths or path in self.system_paths:
                continue

            # 快速路径校验（不检查进程占用，防止 UI 卡死）
            is_sys, reason = is_system_path(path, check_processes=False)
            
            row = self.file_list.rowCount()
            self.file_list.insertRow(row)
            
            # 路径列：使用中间省略
            fm = self.file_list.fontMetrics()
            elided_path = fm.elidedText(path, Qt.ElideMiddle, 400) # 初始宽度
            path_item = QTableWidgetItem(elided_path)
            path_item.setData(Qt.UserRole, path)
            path_item.setToolTip(path)
            self.file_list.setItem(row, 0, path_item)
            
            if is_sys:
                self.system_paths.add(path)
                # 类型列
                type_item = QTableWidgetItem("【系统文件】")
                type_item.setForeground(QColor("#ff4d4f"))
                self.file_list.setItem(row, 1, type_item)
                
                # 状态列
                status_item = QTableWidgetItem("禁止粉碎 (系统文件)")
                status_item.setForeground(QColor("#ff4d4f"))
                self.file_list.setItem(row, 2, status_item)
                
                InfoBar.warning(
                    "安全提示",
                    f"检测到系统关键文件：{os.path.basename(path)}\n已自动标记为禁止粉碎，如需移除请手动清空列表。",
                    duration=5000,
                    parent=self.window()
                )
            else:
                self.paths.add(path)
                # 更准确的类型显示
                if os.path.isdir(path):
                    file_type = "文件夹"
                else:
                    ext = os.path.splitext(path)[1].lower()
                    type_map = {
                        '.py': 'Python 脚本',
                        '.html': 'HTML 文档',
                        '.htm': 'HTML 文档',
                        '.txt': '文本文件',
                        '.pdf': 'PDF 文档',
                        '.docx': 'Word 文档',
                        '.xlsx': 'Excel 表格',
                        '.jpg': 'JPEG 图片',
                        '.png': 'PNG 图片',
                        '.exe': '可执行程序',
                        '.zip': '压缩文件',
                        '.rar': '压缩文件'
                    }
                    file_type = type_map.get(ext, f"{ext[1:].upper() if ext else '未知'} 文件")
                
                self.file_list.setItem(row, 1, QTableWidgetItem(file_type))
                self.file_list.setItem(row, 2, QTableWidgetItem("待粉碎"))
                to_validate.append(path)
        
        # 启动后台校验 worker 检查占用情况
        if to_validate:
            self.status_label.setText("正在执行深度安全检查...")
            self.validator = ValidationWorker(to_validate)
            self.validator.finished.connect(self.on_validation_finished)
            self.validator.start()
            
        self.update_desc()

    def show_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        path = self.file_list.item(row, 0).data(Qt.UserRole)
        
        menu = QMenu(self)
        copy_path_action = QAction(FIF.COPY.icon(), "复制路径", self)
        open_loc_action = QAction(FIF.FOLDER.icon(), "打开文件位置", self)
        remove_action = QAction(FIF.REMOVE.icon(), "从列表中移除", self)
        
        copy_path_action.triggered.connect(lambda: QApplication.clipboard().setText(path))
        open_loc_action.triggered.connect(lambda: open_file_location(path))
        remove_action.triggered.connect(self.remove_selected)
        
        menu.addAction(copy_path_action)
        menu.addAction(open_loc_action)
        menu.addSeparator()
        menu.addAction(remove_action)
        
        menu.exec_(self.file_list.viewport().mapToGlobal(pos))

    def on_validation_finished(self, path, is_sys, reason):
        """ 后台深度校验回调 """
        self.status_label.setText("")
        if is_sys:
            # 发现是被系统占用的文件，将其转入系统文件列表
            if path in self.paths:
                self.paths.remove(path)
            self.system_paths.add(path)
            
            # 更新 UI 状态
            for row in range(self.file_list.rowCount()):
                if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                    # 更新类型列
                    type_item = QTableWidgetItem("【系统占用】")
                    type_item.setForeground(QColor("#ff4d4f"))
                    self.file_list.setItem(row, 1, type_item)
                    
                    # 更新状态列
                    status_item = QTableWidgetItem("禁止粉碎 (系统占用)")
                    status_item.setForeground(QColor("#ff4d4f"))
                    self.file_list.setItem(row, 2, status_item)
                    break
            
            InfoBar.warning(
                "安全提示",
                f"文件被系统关键进程占用：{os.path.basename(path)}\n已标记为禁止操作。",
                duration=3000,
                parent=self.window()
            )
            self.update_desc()

    def remove_path(self, path):
        """ 移除指定路径的文件 """
        for row in range(self.file_list.rowCount()):
            if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                self.file_list.removeRow(row)
                break
        if path in self.paths:
            self.paths.remove(path)
        if path in self.system_paths:
            self.system_paths.remove(path)
        self.update_desc()

    def remove_selected(self):
        selected_ranges = self.file_list.selectedRanges()
        if not selected_ranges:
            return
        
        # 从后往前删，避免索引偏移
        rows_to_remove = []
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows_to_remove.append(row)
        
        rows_to_remove = sorted(list(set(rows_to_remove)), reverse=True)
        for row in rows_to_remove:
            path = self.file_list.item(row, 0).data(Qt.UserRole)
            if path in self.paths:
                self.paths.remove(path)
            if path in self.system_paths:
                self.system_paths.remove(path)
            self.file_list.removeRow(row)
        self.update_desc()

    def clear_list(self):
        self.paths.clear()
        self.system_paths.clear()
        self.file_list.setRowCount(0)
        self.update_desc()

    def update_desc(self):
        if not self.paths and not self.system_paths:
            self.desc.setText("当前没有待粉碎文件，请拖入需要处理的文件。")
            self.btn_shred.setEnabled(False)
        elif self.system_paths and not self.paths:
            self.desc.setText("列表仅包含系统关键文件，已禁止粉碎操作。")
            self.btn_shred.setEnabled(False)
        elif self.system_paths and self.paths:
            self.desc.setText(f"已选择 {len(self.paths)} 个项目，包含系统文件（已跳过）。")
            self.btn_shred.setEnabled(True)
        else:
            self.desc.setText(f"已选择 {len(self.paths)} 个项目，准备粉碎。")
            self.btn_shred.setEnabled(True)

    def start_shredding(self):
        if not self.paths:
            InfoBar.warning("提示", "请先添加需要粉碎的文件或文件夹", duration=2000, parent=self.window())
            return

        msg_box = MessageBox(
            "确认粉碎",
            "确定要粉碎选中的文件吗？粉碎后数据将无法恢复，且会尝试解除占用强制删除！",
            self.window()
        )
        msg_box.yesButton.setText("确定粉碎")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec_():
            self.set_controls_enabled(False)
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            
            self.worker = ShredderWorker(list(self.paths))
            self.worker.progress.connect(self.on_progress)
            self.worker.file_finished.connect(self.on_file_finished)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

    def on_file_finished(self, path, success, msg):
        """ 单个文件处理完成的回调 """
        for row in range(self.file_list.rowCount()):
            if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                status_item = QTableWidgetItem(msg)
                if success:
                    status_item.setForeground(QColor("#27ae60")) # 绿色
                else:
                    status_item.setForeground(QColor("#ff4d4f")) # 红色
                self.file_list.setItem(row, 2, status_item)
                break

    def set_controls_enabled(self, enabled):
        """ 控制界面按钮的可操作性 """
        self.btn_shred.setEnabled(enabled)
        self.btn_add_file.setEnabled(enabled)
        self.btn_add_folder.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.btn_remove.setEnabled(enabled)
        self.file_list.setEnabled(enabled)

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def on_finished(self, success, fail, errors):
        self.set_controls_enabled(True)
        self.progress_bar.hide()
        self.status_label.setText("")
        
        if fail == 0:
            InfoBar.success("粉碎完成", "文件已彻底粉碎，无法恢复", duration=3000, parent=self.window())
        else:
            msg = f"成功: {success}, 失败: {fail}"
            if errors:
                msg += "\n部分错误: " + "\n".join(errors[:3])
            InfoBar.error("部分项目粉碎失败", msg, duration=5000, parent=self.window())
        
        # 粉碎完成后移除已成功粉碎的路径记录，但保留在列表中显示
        paths_to_remove = []
        for path in self.paths:
            # 检查列表中该路径的状态
            for row in range(self.file_list.rowCount()):
                if self.file_list.item(row, 0).data(Qt.UserRole) == path:
                    if self.file_list.item(row, 2).text() == "已粉碎":
                        paths_to_remove.append(path)
                    break
        
        for p in paths_to_remove:
            self.paths.remove(p)
            
        self.update_desc()

    def set_theme(self, is_dark):
        if is_dark:
            bg_color = "#1d1d1d"
            text_color = "#e0e0e0"
            sub_text = "#a0a0a0"
        else:
            bg_color = "#f7f9fc"
            text_color = "#333333"
            sub_text = "#666666"

        self.setStyleSheet(f"#ShredderInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.desc.setStyleSheet(f"color:{sub_text};")
        self.status_label.setStyleSheet(f"color:{sub_text};")
