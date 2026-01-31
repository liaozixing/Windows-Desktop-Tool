import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFileDialog
from PyQt5.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, BodyLabel, CaptionLabel, PrimaryPushButton, 
                            PushButton, FluentIcon as FIF, InfoBar, ComboBox, 
                            StrongBodyLabel, SearchLineEdit)

class ConverterInterface(QWidget):
    """ 综合格式转换界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ConverterInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 头部布局
        header_layout = QHBoxLayout()
        self.title = SubtitleLabel("万能格式转换", self)
        self.title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title)
        
        # 离线标识
        self.offline_tag = CaptionLabel("离线可用", self)
        self.offline_tag.setStyleSheet("background-color: rgba(39, 174, 96, 0.2); color: #27ae60; padding: 2px 8px; border-radius: 4px;")
        header_layout.addWidget(self.offline_tag)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(StrongBodyLabel("转换类型", self))
        self.type_box = ComboBox(self)
        self.type_box.addItems(["图片转换", "文档转换", "视频转换"])
        self.type_box.setFixedWidth(200)
        type_layout.addWidget(self.type_box)
        type_layout.addStretch(1)
        layout.addLayout(type_layout)

        # 堆栈布局处理不同分类
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        # --- 图片转换面板 ---
        self.img_panel = QWidget()
        img_layout = QVBoxLayout(self.img_panel)
        img_layout.setContentsMargins(0, 10, 0, 0)
        img_layout.setSpacing(15)

        self.img_card = QWidget()
        self.img_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        img_card_layout = QVBoxLayout(self.img_card)
        
        img_card_layout.addWidget(StrongBodyLabel("1. 选择源文件"))
        self.img_path_edit = SearchLineEdit()
        self.img_path_edit.setPlaceholderText("选择源图片文件...")
        self.img_path_edit.setReadOnly(True)
        self.img_path_edit.searchButton.hide()
        self.btn_img_browse = PushButton("选择文件")
        
        row = QHBoxLayout()
        row.addWidget(self.img_path_edit)
        row.addWidget(self.btn_img_browse)
        img_card_layout.addLayout(row)

        img_card_layout.addSpacing(10)
        img_card_layout.addWidget(StrongBodyLabel("2. 选择目标格式"))
        
        self.img_format_group = QHBoxLayout()
        self.img_btn_png = PushButton("PNG", self)
        self.img_btn_jpg = PushButton("JPG", self)
        self.img_btn_webp = PushButton("WebP", self)
        self.img_btn_bmp = PushButton("BMP", self)
        self.img_btn_ico = PushButton("ICO", self)
        
        self.img_format_btns = [self.img_btn_png, self.img_btn_jpg, self.img_btn_webp, self.img_btn_bmp, self.img_btn_ico]
        for btn in self.img_format_btns:
            btn.setCheckable(True)
            btn.clicked.connect(self.on_img_format_clicked)
            self.img_format_group.addWidget(btn)
        self.img_format_group.addStretch(1)
        img_card_layout.addLayout(self.img_format_group)

        img_card_layout.addSpacing(10)
        self.btn_img_convert = PrimaryPushButton(FIF.SYNC, "开始转换图片")
        self.btn_img_convert.setEnabled(False)
        img_card_layout.addWidget(self.btn_img_convert)
        img_layout.addWidget(self.img_card)
        img_layout.addStretch(1)

        # --- 文档转换面板 ---
        self.doc_panel = QWidget()
        doc_layout = QVBoxLayout(self.doc_panel)
        doc_layout.setContentsMargins(0, 10, 0, 0)
        doc_layout.setSpacing(15)

        self.doc_card = QWidget()
        self.doc_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        doc_card_layout = QVBoxLayout(self.doc_card)

        doc_card_layout.addWidget(StrongBodyLabel("1. 选择源文档"))
        self.doc_path_edit = SearchLineEdit()
        self.doc_path_edit.setPlaceholderText("选择源文档文件...")
        self.doc_path_edit.setReadOnly(True)
        self.doc_path_edit.searchButton.hide()
        self.btn_doc_browse = PushButton("选择文件")
        
        row2 = QHBoxLayout()
        row2.addWidget(self.doc_path_edit)
        row2.addWidget(self.btn_doc_browse)
        doc_card_layout.addLayout(row2)

        doc_card_layout.addSpacing(10)
        doc_card_layout.addWidget(StrongBodyLabel("2. 选择目标格式"))
        self.doc_target_box = ComboBox(self)
        self.doc_target_box.addItem("Word 文档 (*.docx)", "docx")
        self.doc_target_box.addItem("PDF 文档 (*.pdf)", "pdf")
        self.doc_target_box.addItem("Excel 表格 (*.xlsx)", "xlsx")
        self.doc_target_box.setFixedWidth(260)
        doc_card_layout.addWidget(self.doc_target_box)

        doc_card_layout.addSpacing(10)
        self.btn_doc_convert = PrimaryPushButton(FIF.SYNC, "开始转换文档")
        self.btn_doc_convert.setEnabled(False)
        doc_card_layout.addWidget(self.btn_doc_convert)
        doc_layout.addWidget(self.doc_card)
        doc_layout.addStretch(1)

        self.video_panel = QWidget()
        video_layout = QVBoxLayout(self.video_panel)
        video_layout.setContentsMargins(0, 10, 0, 0)
        video_layout.setSpacing(15)

        self.video_card = QWidget()
        self.video_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        video_card_layout = QVBoxLayout(self.video_card)

        video_card_layout.addWidget(StrongBodyLabel("1. 选择源视频"))
        self.video_path_edit = SearchLineEdit()
        self.video_path_edit.setPlaceholderText("选择源视频文件...")
        self.video_path_edit.setReadOnly(True)
        self.video_path_edit.searchButton.hide()
        self.btn_video_browse = PushButton("选择文件")

        row3 = QHBoxLayout()
        row3.addWidget(self.video_path_edit)
        row3.addWidget(self.btn_video_browse)
        video_card_layout.addLayout(row3)

        video_card_layout.addSpacing(10)
        video_card_layout.addWidget(StrongBodyLabel("2. 选择目标格式"))
        self.video_format_box = ComboBox(self)
        self.video_format_box.addItems(["MP4", "MKV", "MOV", "AVI"])
        self.video_format_box.setFixedWidth(200)
        video_card_layout.addWidget(self.video_format_box)

        video_card_layout.addSpacing(10)
        self.btn_video_convert = PrimaryPushButton(FIF.SYNC, "开始转换视频")
        self.btn_video_convert.setEnabled(False)
        video_card_layout.addWidget(self.btn_video_convert)
        video_layout.addWidget(self.video_card)
        video_layout.addStretch(1)

        self.stack.addWidget(self.img_panel)
        self.stack.addWidget(self.doc_panel)
        self.stack.addWidget(self.video_panel)

        self.type_box.currentIndexChanged.connect(self.stack.setCurrentIndex)

        self.btn_img_browse.clicked.connect(self.select_img_file)
        self.btn_doc_browse.clicked.connect(self.select_doc_file)
        self.btn_video_browse.clicked.connect(self.select_video_file)
        
        self.btn_img_convert.clicked.connect(self.do_img_convert)
        self.btn_doc_convert.clicked.connect(self.do_doc_convert)
        self.btn_video_convert.clicked.connect(self.do_video_convert)

    def on_img_format_clicked(self):
        btn = self.sender()
        for b in self.img_format_btns:
            if b != btn:
                b.setChecked(False)
        self.update_img_convert_btn()

    def update_img_convert_btn(self):
        has_file = bool(self.img_path_edit.text())
        has_format = any(b.isChecked() for b in self.img_format_btns)
        self.btn_img_convert.setEnabled(has_file and has_format)

    def update_doc_convert_btn(self):
        has_file = bool(self.doc_path_edit.text())
        self.btn_doc_convert.setEnabled(has_file)

    def update_video_convert_btn(self):
        has_file = bool(self.video_path_edit.text())
        self.btn_video_convert.setEnabled(has_file)

    def select_img_file(self):
        # 允许选择所有支持的图片格式
        filter_str = "图片文件 (*.svg *.png *.jpg *.jpeg *.webp *.bmp)"
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", filter_str)
        if path:
            self.img_path_edit.setText(path)
            self.update_img_convert_btn()

    def select_doc_file(self):
        # 允许选择所有支持的文档格式
        filter_str = "文档文件 (*.pdf *.docx *.xlsx *.xls)"
        path, _ = QFileDialog.getOpenFileName(self, "选择文档", "", filter_str)
        if path:
            self.doc_path_edit.setText(path)
            self.update_doc_convert_btn()

    def select_video_file(self):
        filter_str = "视频文件 (*.mp4 *.mkv *.mov *.avi *.flv *.wmv)"
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", filter_str)
        if path:
            self.video_path_edit.setText(path)
            self.update_video_convert_btn()

    def do_img_convert(self):
        input_path = self.img_path_edit.text()
        target_fmt = ""
        for b in self.img_format_btns:
            if b.isChecked():
                target_fmt = b.text()
                break
        
        if not target_fmt: return

        # 延迟导入文件转换模块
        from modules.file_converter import svg_to_ico, image_convert
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtGui import QImage, QPainter
        
        is_svg = input_path.lower().endswith(".svg")
        success, msg = False, "转换失败"
        save_path = None

        if is_svg:
            if target_fmt == "ICO":
                default_name = os.path.splitext(os.path.basename(input_path))[0] + ".ico"
                save_path, _ = QFileDialog.getSaveFileName(self, "保存 ICO", default_name, "ICO 图标 (*.ico)")
                if save_path:
                    success, msg = svg_to_ico(input_path, save_path)
            else:
                save_path, _ = QFileDialog.getSaveFileName(self, f"保存 {target_fmt}", f"output.{target_fmt.lower()}", f"{target_fmt} 图片 (*.{target_fmt.lower()})")
                if save_path:
                    try:
                        renderer = QSvgRenderer(input_path)
                        image = QImage(1024, 1024, QImage.Format_ARGB32)
                        image.fill(Qt.transparent)
                        painter = QPainter(image)
                        renderer.render(painter)
                        painter.end()
                        success = image.save(save_path, target_fmt)
                        msg = "成功" if success else "保存失败"
                    except Exception as e:
                        msg = str(e)
        else:
            save_path, _ = QFileDialog.getSaveFileName(self, f"保存 {target_fmt}", f"output.{target_fmt.lower()}", f"{target_fmt} 图片 (*.{target_fmt.lower()})")
            if save_path:
                success, msg = image_convert(input_path, save_path, target_fmt)

        if save_path:
            if success: InfoBar.success("转换成功", "文件已保存", duration=3000, parent=self.window())
            else: InfoBar.error("转换失败", msg, duration=5000, parent=self.window())

    def do_doc_convert(self):
        input_path = self.doc_path_edit.text()
        if not input_path:
            return
        # 延迟导入文件转换模块
        from modules.file_converter import pdf_to_word, word_to_pdf, word_to_excel, excel_to_word
        
        target = self.doc_target_box.currentData()
        ext = os.path.splitext(input_path)[1].lower()
        success, msg = False, "未执行"
        save_path = None
        if ext == ".pdf" and target == "docx":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Word", "output.docx", "Word 文档 (*.docx)")
            if save_path:
                success, msg = pdf_to_word(input_path, save_path)
        elif ext == ".docx" and target == "pdf":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 PDF", "output.pdf", "PDF 文档 (*.pdf)")
            if save_path:
                success, msg = word_to_pdf(input_path, save_path)
        elif ext == ".docx" and target == "xlsx":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Excel", "output.xlsx", "Excel 表格 (*.xlsx)")
            if save_path:
                success, msg = word_to_excel(input_path, save_path)
        elif ext == ".xlsx" and target == "docx":
            save_path, _ = QFileDialog.getSaveFileName(self, "保存 Word", "output.docx", "Word 文档 (*.docx)")
            if save_path:
                success, msg = excel_to_word(input_path, save_path)

        if save_path:
            if success: InfoBar.success("转换成功", "文件已保存", duration=3000, parent=self.window())
            else: InfoBar.error("转换失败", msg, duration=5000, parent=self.window())

    def do_video_convert(self):
        input_path = self.video_path_edit.text()
        if not input_path:
            return
        # 延迟导入文件转换模块
        from modules.file_converter import video_convert
        
        target_fmt = self.video_format_box.currentText().lower()
        base = os.path.splitext(os.path.basename(input_path))[0]
        default_name = f"{base}.{target_fmt}"
        filter_str = f"{target_fmt.upper()} 视频 (*.{target_fmt})"
        save_path, _ = QFileDialog.getSaveFileName(self, "保存视频", default_name, filter_str)
        if not save_path:
            return
        success, msg = video_convert(input_path, save_path, target_fmt)
        if success:
            InfoBar.success("转换成功", "视频已保存", duration=3000, parent=self.window())
        else:
            InfoBar.error("转换失败", msg, duration=5000, parent=self.window())

    def update_network_status(self, is_online):
        """ 更新网络状态 """
        pass

    def set_theme(self, is_dark):
        if is_dark:
            bg_color, text_color, sub_text, card_bg = "#1d1d1d", "#e0e0e0", "#a0a0a0", "rgba(255, 255, 255, 0.05)"
        else:
            bg_color, text_color, sub_text, card_bg = "#f7f9fc", "#333333", "#666666", "rgba(0, 0, 0, 0.05)"

        self.setStyleSheet(f"#ConverterInterface{{background-color:{bg_color};}}")
        self.title.setStyleSheet(f"color:{text_color}; font-size: 16px; font-weight: 600;")
        self.img_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px;")
        self.doc_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px;")
        if hasattr(self, "video_card"):
            self.video_card.setStyleSheet(f"background-color: {card_bg}; border-radius: 10px;")
