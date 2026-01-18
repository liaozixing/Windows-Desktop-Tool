import sys
import os
from PyQt5.QtCore import Qt, QTranslator, QLibraryInfo, QLocale
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme, FluentTranslator
from ui.main_window import MainWindow

def main():
    # 启用高 DPI 缩放支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 启用高 DPI 缩放策略
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # 确保当前目录在 sys.path 中，以便导入模块
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # 允许最小化到托盘而不退出

    # 加载中文翻译
    translator = QTranslator()
    if translator.load("qt_zh_CN", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    
    # 加载 qfluentwidgets 的翻译
    fluent_translator = FluentTranslator(QLocale(QLocale.Chinese, QLocale.China))
    app.installTranslator(fluent_translator)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
