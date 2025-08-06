#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Universal Object Detection System v2.0
优化的通用目标检测系统

新功能特性:
✨ 渐变UI样式效果  
📱 优化的响应式布局
📊 增强的日志显示（类别识别信息）
📁 支持自定义模型目录加载  
📹 多摄像头支持和选择
🖥️ 实时监控页面
🎨 优化的图标设计
⚡ 性能优化和错误处理
"""

import sys
import os
import cv2
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 请安装ultralytics库: pip install ultralytics")
    sys.exit(1)


class StyleManager:
    """样式管理器 - 提供渐变和现代化UI样式"""
    
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
                border: 2px solid rgba(52, 152, 219, 0.3);
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
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                color: white;
                min-width: 100px;
                min-height: 35px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
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
            
            QComboBox {
                padding: 8px 15px;
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #f8f9fa);
                font-size: 12px;
                min-width: 150px;
                min-height: 25px;
            }
            
            QProgressBar {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 11px;
                max-height: 25px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                border-radius: 6px;
                margin: 1px;
            }
            
            QTextEdit {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.95);
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                selection-background-color: #3498db;
            }
            
            QTabWidget::pane {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(245, 245, 245, 0.95));
                margin-top: 5px;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 12px 25px;
                margin-right: 3px;
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-color: rgba(52, 152, 219, 0.7);
            }
            
            QTableWidget {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: white;
                gridline-color: rgba(189, 195, 199, 0.3);
                selection-background-color: rgba(52, 152, 219, 0.2);
            }
            
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """

    @staticmethod 
    def get_image_label_style():
        return """
            border: 3px solid rgba(52, 152, 219, 0.3);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(248, 249, 250, 0.9), stop:1 rgba(233, 236, 239, 0.9));
            color: #7f8c8d;
            font-weight: bold;
            font-size: 14px;
            border-radius: 10px;
            padding: 15px;
        """


print("✅ Enhanced Detection System - 样式管理器已加载")
