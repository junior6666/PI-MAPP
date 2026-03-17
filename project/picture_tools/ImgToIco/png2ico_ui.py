#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG to ICO Converter UI
使用PySide6实现的PNG转ICO格式转换工具
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QGroupBox, QProgressBar,
    QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QIcon
from PIL import Image


class StyleManager:
    """样式管理器 - 提供现代化UI样式"""

    @staticmethod
    def get_main_stylesheet():
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }

            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid rgba(52, 152, 219, 0.7);
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(245, 245, 245, 0.9));
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                color: white;
                min-width: 80px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                transform: translateY(-1px);
            }

            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }

            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
                color: #7f8c8d;
            }

            QLineEdit {
                padding: 8px 10px;
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 6px;
                background: white;
                font-size: 12px;
            }

            QLineEdit:focus {
                border-color: #3498db;
                background: white;
            }

            QProgressBar {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 11px;
                max-height: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                border-radius: 6px;
                margin: 1px;
            }

            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """


class ConvertThread(QThread):
    """转换线程 - 用于在后台执行PNG到ICO的转换"""
    progress_updated = Signal(int)
    conversion_finished = Signal(bool, str)

    def __init__(self, png_path, ico_path, sizes=None):
        super().__init__()
        self.png_path = png_path
        self.ico_path = ico_path
        self.sizes = sizes or [ (64, 64), (128, 128), (256, 256)]

    def run(self):
        try:
            # 打开PNG文件
            self.progress_updated.emit(10)
            with Image.open(self.png_path) as img:
                # 确保图像是RGBA模式
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                self.progress_updated.emit(30)

                # 创建临时图像列表
                ico_images = []
                for size in self.sizes:
                    # 调整图像大小
                    resized_img = img.resize(size, Image.Resampling.LANCZOS)
                    ico_images.append(resized_img)
                    self.progress_updated.emit(30 + (size[0] / 256) * 50)

                # 保存为ICO文件
                self.progress_updated.emit(90)
                ico_images[0].save(self.ico_path, format='ICO', 
                                  sizes=self.sizes, append_images=ico_images[1:])
                self.progress_updated.emit(100)

                self.conversion_finished.emit(True, f"转换成功: {self.ico_path}")
        except Exception as e:
            self.conversion_finished.emit(False, f"转换失败: {str(e)}")


class PNGtoICOConverter(QMainWindow):
    """PNG转ICO转换器主窗口"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.png_path = ""
        self.ico_path = ""
        self.convert_thread = None

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("PNG to ICO Converter")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowIcon(QIcon.fromTheme("image"))

        # 设置样式
        self.setStyleSheet(StyleManager.get_main_stylesheet())

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 文件选择区域
        file_group = QGroupBox("📁 文件选择")
        file_layout = QVBoxLayout(file_group)

        # PNG文件选择
        png_layout = QHBoxLayout()
        self.png_line_edit = QLineEdit()
        self.png_line_edit.setPlaceholderText("选择PNG文件...")
        self.png_line_edit.setReadOnly(True)
        png_browse_btn = QPushButton("📂 浏览PNG")
        png_browse_btn.clicked.connect(self.browse_png)
        png_layout.addWidget(self.png_line_edit)
        png_layout.addWidget(png_browse_btn)
        file_layout.addLayout(png_layout)

        # ICO输出路径选择
        ico_layout = QHBoxLayout()
        self.ico_line_edit = QLineEdit()
        self.ico_line_edit.setPlaceholderText("选择ICO输出路径...")
        self.ico_line_edit.setReadOnly(True)
        ico_browse_btn = QPushButton("📂 浏览输出")
        ico_browse_btn.clicked.connect(self.browse_ico)
        ico_layout.addWidget(self.ico_line_edit)
        ico_layout.addWidget(ico_browse_btn)
        file_layout.addLayout(ico_layout)

        main_layout.addWidget(file_group)

        # 预览区域
        preview_group = QGroupBox("🖼️ 预览")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setSpacing(20)

        # PNG预览
        png_preview_container = QWidget()
        png_preview_layout = QVBoxLayout(png_preview_container)
        png_title = QLabel("PNG 预览")
        png_title.setAlignment(Qt.AlignCenter)
        png_title.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        png_preview_layout.addWidget(png_title)
        
        self.png_preview_label = QLabel("PNG预览")
        self.png_preview_label.setAlignment(Qt.AlignCenter)
        self.png_preview_label.setStyleSheet("""
            border: 2px dashed rgba(52, 152, 219, 0.3);
            border-radius: 8px;
            min-height: 200px;
            background: rgba(248, 249, 250, 0.9);
        """)
        png_preview_layout.addWidget(self.png_preview_label)

        # ICO预览
        ico_preview_container = QWidget()
        ico_preview_layout = QVBoxLayout(ico_preview_container)
        ico_title = QLabel("ICO 预览")
        ico_title.setAlignment(Qt.AlignCenter)
        ico_title.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        ico_preview_layout.addWidget(ico_title)
        
        self.ico_preview_label = QLabel("转换后显示ICO预览")
        self.ico_preview_label.setAlignment(Qt.AlignCenter)
        self.ico_preview_label.setStyleSheet("""
            border: 2px dashed rgba(52, 152, 219, 0.3);
            border-radius: 8px;
            min-height: 200px;
            background: rgba(248, 249, 250, 0.9);
        """)
        ico_preview_layout.addWidget(self.ico_preview_label)

        # 添加到水平布局
        preview_layout.addWidget(png_preview_container)
        preview_layout.addWidget(ico_preview_container)

        main_layout.addWidget(preview_group)

        # 控制区域
        control_group = QGroupBox("⚙️ 控制")
        control_layout = QVBoxLayout(control_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(self.status_label)

        # 转换按钮
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("🚀 开始转换")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.clear_btn)
        control_layout.addLayout(button_layout)

        main_layout.addWidget(control_group)

        # 添加垂直间距
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def browse_png(self):
        """浏览并选择PNG文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PNG文件", "", "PNG Files (*.png);;All Files (*.*)"
        )
        if file_path:
            self.png_path = file_path
            self.png_line_edit.setText(file_path)
            self.update_preview()
            
            # 自动生成ICO输出路径
            if not self.ico_path:
                ico_path = Path(file_path).with_suffix('.ico')
                self.ico_path = str(ico_path)
                self.ico_line_edit.setText(self.ico_path)
            
            # 启用转换按钮
            if self.ico_path:
                self.convert_btn.setEnabled(True)

    def browse_ico(self):
        """浏览并选择ICO输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存ICO文件", "", "ICO Files (*.ico);;All Files (*.*)"
        )
        if file_path:
            self.ico_path = file_path
            self.ico_line_edit.setText(file_path)
            
            # 启用转换按钮
            if self.png_path:
                self.convert_btn.setEnabled(True)

    def update_preview(self):
        """更新PNG预览"""
        try:
            pixmap = QPixmap(self.png_path)
            if not pixmap.isNull():
                # 缩放预览图像以适应标签
                max_size = 200
                scaled_pixmap = pixmap.scaled(
                    max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.png_preview_label.setPixmap(scaled_pixmap)
                self.png_preview_label.setText("")
            else:
                self.png_preview_label.setText("无法预览图像")
        except Exception as e:
            self.png_preview_label.setText(f"预览错误: {str(e)}")

    def update_ico_preview(self):
        """更新ICO预览"""
        try:
            # 使用PIL打开ICO文件并选择64x64尺寸
            with Image.open(self.ico_path) as img:
                # 获取所有可用尺寸
                sizes = img.info.get('sizes', [])
                
                # 查找64x64尺寸
                if sizes:
                    # 尝试找到64x64尺寸
                    ico_image = None
                    for i, size in enumerate(sizes):
                        if size == (64, 64):
                            # 选择该尺寸
                            img.seek(i)
                            ico_image = img.copy()
                            break
                    
                    # 如果没有找到64x64，选择最大的尺寸
                    if not ico_image:
                        max_size = max(sizes, key=lambda s: s[0] * s[1])
                        for i, size in enumerate(sizes):
                            if size == max_size:
                                img.seek(i)
                                ico_image = img.copy()
                                break
                else:
                    # 如果没有尺寸信息，使用默认图像
                    ico_image = img.copy()
                
                # 将PIL图像转换为QPixmap
                if ico_image:
                    # 转换为RGB模式（如果需要）
                    if ico_image.mode == 'RGBA':
                        # 处理透明通道
                        img_data = ico_image.tobytes('raw', 'RGBA')
                        q_image = QImage(img_data, ico_image.size[0], ico_image.size[1], QImage.Format_RGBA8888)
                    else:
                        ico_image = ico_image.convert('RGB')
                        img_data = ico_image.tobytes('raw', 'RGB')
                        q_image = QImage(img_data, ico_image.size[0], ico_image.size[1], QImage.Format_RGB888)
                    
                    pixmap = QPixmap.fromImage(q_image)
                    
                    # 缩放预览图像以适应标签
                    max_size = 200
                    scaled_pixmap = pixmap.scaled(
                        max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    
                    self.ico_preview_label.setPixmap(scaled_pixmap)
                    self.ico_preview_label.setText("")
                else:
                    self.ico_preview_label.setText("无法获取ICO图像")
        except Exception as e:
            self.ico_preview_label.setText(f"ICO预览错误: {str(e)}")

    def start_conversion(self):
        """开始PNG到ICO的转换"""
        if not self.png_path or not self.ico_path:
            QMessageBox.warning(self, "警告", "请选择PNG文件和ICO输出路径")
            return

        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在转换...")

        # 创建转换线程
        self.convert_thread = ConvertThread(self.png_path, self.ico_path)
        self.convert_thread.progress_updated.connect(self.progress_bar.setValue)
        self.convert_thread.conversion_finished.connect(self.on_conversion_finished)
        self.convert_thread.start()

    def on_conversion_finished(self, success, message):
        """转换完成后的处理"""
        self.status_label.setText(message)
        
        if success:
            QMessageBox.information(self, "成功", message)
            # 显示ICO预览
            self.update_ico_preview()
        else:
            QMessageBox.critical(self, "错误", message)

        # 启用按钮
        self.convert_btn.setEnabled(True)

    def clear_all(self):
        """清空所有选择和预览"""
        self.png_path = ""
        self.ico_path = ""
        self.png_line_edit.clear()
        self.ico_line_edit.clear()
        
        # 清除PNG预览
        self.png_preview_label.clear()
        self.png_preview_label.setText("PNG预览")
        
        # 清除ICO预览
        self.ico_preview_label.clear()
        self.ico_preview_label.setText("转换后显示ICO预览")
        
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.convert_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PNGtoICOConverter()
    window.show()
    sys.exit(app.exec())
