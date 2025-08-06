#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版测试应用 - 用于测试基本界面功能
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFileDialog,
                               QMessageBox, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

class SimpleMainWindow(QMainWindow):
    """简化主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("步态分析工具 - 测试版")
        self.setMinimumSize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 视频区域占位
        video_placeholder = QLabel("视频播放区域")
        video_placeholder.setAlignment(Qt.AlignCenter)
        video_placeholder.setStyleSheet("""
            QLabel {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: #2a2a2a;
                color: #888888;
                font-size: 14pt;
                font-weight: bold;
                min-height: 300px;
            }
        """)
        left_layout.addWidget(video_placeholder)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        
        open_btn = QPushButton("打开视频")
        open_btn.clicked.connect(self.open_video)
        controls_layout.addWidget(open_btn)
        
        play_btn = QPushButton("播放")
        controls_layout.addWidget(play_btn)
        
        stop_btn = QPushButton("停止")
        controls_layout.addWidget(stop_btn)
        
        left_layout.addLayout(controls_layout)
        
        # 右侧区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 图表区域占位
        chart_placeholder = QLabel("特征曲线显示区域")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet("""
            QLabel {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: #2a2a2a;
                color: #888888;
                font-size: 14pt;
                font-weight: bold;
                min-height: 300px;
            }
        """)
        right_layout.addWidget(chart_placeholder)
        
        # 参数区域占位
        params_placeholder = QLabel("步态参数显示区域")
        params_placeholder.setAlignment(Qt.AlignCenter)
        params_placeholder.setStyleSheet("""
            QLabel {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: #2a2a2a;
                color: #888888;
                font-size: 14pt;
                font-weight: bold;
                min-height: 200px;
            }
        """)
        right_layout.addWidget(params_placeholder)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])
        
        main_layout.addWidget(splitter)
    
    def open_video(self):
        """打开视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;所有文件 (*.*)"
        )
        
        if file_path:
            QMessageBox.information(self, "提示", f"已选择视频文件:\n{file_path}")

def setup_application_style(app):
    """设置应用程序样式"""
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
    """)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("步态分析工具测试版")
    
    # 设置样式
    setup_application_style(app)
    
    # 创建主窗口
    window = SimpleMainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()