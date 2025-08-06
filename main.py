#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步态分析可视化GUI应用
基于PySide6的现代化界面设计
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QFont, QPalette, QColor

from ui.main_window import MainWindow

def setup_application_style(app):
    """设置应用程序样式"""
    # 设置暗色主题
    app.setStyle("Fusion")
    
    # 创建暗色调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(palette)
    
    # 设置全局样式表
    app.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #2b2b2b, stop:1 #3c3c3c);
        }
        
        QWidget {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 9pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #5a5a5a;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #ffffff;
        }
        
        QPushButton {
            border: 2px solid #5a5a5a;
            border-radius: 6px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6a6a6a, stop:1 #4a4a4a);
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #7a7a7a, stop:1 #5a5a5a);
            border: 2px solid #6a6a6a;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a4a4a, stop:1 #6a6a6a);
        }
        
        QPushButton:disabled {
            background: #3a3a3a;
            color: #666666;
            border: 2px solid #3a3a3a;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: white;
            height: 10px;
            border-radius: 4px;
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #66bb6a, stop:1 #43a047);
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        
        QSlider::add-page:horizontal {
            background: #fff;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 18px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: 3px;
        }
        
        QCheckBox {
            spacing: 5px;
            color: white;
        }
        
        QCheckBox::indicator {
            width: 13px;
            height: 13px;
        }
        
        QCheckBox::indicator:unchecked {
            background: #2b2b2b;
            border: 2px solid #5a5a5a;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #66bb6a, stop:1 #43a047);
            border: 2px solid #43a047;
            border-radius: 3px;
        }
        
        QComboBox {
            border: 2px solid #5a5a5a;
            border-radius: 4px;
            padding: 5px;
            min-width: 6em;
            background: #2b2b2b;
            color: white;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left-width: 1px;
            border-left-color: #5a5a5a;
            border-left-style: solid;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }
        
        QProgressBar {
            border: 2px solid #5a5a5a;
            border-radius: 5px;
            text-align: center;
            background: #2b2b2b;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #66bb6a, stop:1 #43a047);
            border-radius: 3px;
        }
        
        QStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3c3c3c, stop:1 #2b2b2b);
            border-top: 1px solid #5a5a5a;
        }
        
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3c3c3c, stop:1 #2b2b2b);
            border-bottom: 1px solid #5a5a5a;
        }
        
        QMenuBar::item {
            spacing: 3px;
            padding: 5px 10px;
            background: transparent;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5a5a5a, stop:1 #4a4a4a);
        }
    """)

def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("步态分析可视化工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("GaitAnalysis")
    
    # 设置应用程序图标和样式
    setup_application_style(app)
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()