#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片布局管理工具 - PySide6 实现
功能：多张图片网格布局、实时预览、导出为单张图片
author : Jing
"""

import os
import sys
import copy
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from PySide6.QtCore import (
    Qt, QThread, Signal, QMimeData, QPoint, QStandardPaths, 
    QRect, QSize, QPointF, QPropertyAnimation, QEasingCurve, QObject, QEvent
)
from PySide6.QtGui import (
    QPixmap, QIcon, QDragEnterEvent, QDragMoveEvent, QDropEvent, QResizeEvent, 
    QPainter, QColor, QBrush, QPen, QAction, QKeySequence,
    QDrag, QPixmapCache
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit, QDialog, 
    QScrollArea, QFrame, QSlider, QSpinBox, QComboBox, QDoubleSpinBox,
    QGridLayout, QSizePolicy, QToolBar, QStatusBar, QSplitter,
    QColorDialog, QFormLayout, QRadioButton, QButtonGroup
)

def resource_path(relative_path):
    """获取资源的绝对路径，支持开发和打包后两种模式"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# -------------------- Style --------------------
class StyleManager:
    @staticmethod
    def get_main_stylesheet():
        return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
        }
        QGroupBox {
            font-weight: bold;
            font-size: 10px;
            border: 1px solid rgba(52, 152, 219, 0.7);
            border-radius: 6px;
            margin-top: 1ex;
            padding-top: 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(245, 245, 245, 0.9));
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2c3e50;
            font-size: 11px;
            font-weight: bold;
        }
        QPushButton {
            padding: 8px;
            font-size: 11px;
            font-weight: bold;
            border: none;
            border-radius: 4px;
            color: white;
            min-width: 50px;
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
        QListWidget {
            border: 1px solid rgba(189, 195, 199, 0.5);
            border-radius: 6px;
            background: white;
            selection-background-color: rgba(52, 152, 219, 0.2);
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid rgba(189, 195, 199, 0.2);
        }
        QListWidget::item:selected {
            background: rgba(52, 152, 219, 0.3);
            color: #2c3e50;
        }
        QProgressBar {
            border: 1px solid rgba(189, 195, 199, 0.5);
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            font-size: 9px;
            max-height: 16px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ecf0f1, stop:1 #d5dbdb);
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2ecc71, stop:1 #27ae60);
            border-radius: 4px;
            margin: 1px;
        }
        QTextEdit {
            border: 1px solid rgba(189, 195, 199, 0.5);
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.95);
            font-family: Consolas, Monaco, monospace;
            font-size: 9px;
            padding: 5px;
            selection-background-color: #3498db;
        }
        QSlider::groove:horizontal {
            border: 1px solid #bdc3c7;
            height: 6px;
            background: #ecf0f1;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3498db, stop:1 #2980b9);
            border: 1px solid #2980b9;
            width: 12px;
            margin: -3px 0;
            border-radius: 6px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5dade2, stop:1 #3498db);
        }
        QDoubleSpinBox, QSpinBox {
            border: 1px solid rgba(189, 195, 199, 0.5);
            border-radius: 4px;
            padding: 3px 6px;
            background: white;
            min-width: 50px;
            font-size: 10px;
        }
        QDoubleSpinBox:focus, QSpinBox:focus {
            border: 1px solid #3498db;
        }
        QComboBox {
            border: 1px solid rgba(189, 195, 199, 0.5);
            border-radius: 4px;
            padding: 3px 6px;
            background: white;
            min-width: 50px;
            font-size: 10px;
        }
        QComboBox:focus {
            border: 1px solid #3498db;
        }
        QComboBox::drop-down {
            width: 16px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #2c3e50;
            margin-right: 4px;
        }
        QLabel {
            color: #2c3e50;
            font-size: 10px;
        }
        QRadioButton {
            spacing: 5px;
            font-size: 10px;
        }
        QRadioButton::indicator {
            width: 14px;
            height: 14px;
            border-radius: 7px;
            border: 1px solid #bdc3c7;
            background: white;
        }
        QRadioButton::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3498db, stop:1 #2980b9);
            border: 1px solid #2980b9;
        }
        """


# -------------------- Model --------------------
class ImageItem:
    """图片数据模型"""
    def __init__(self, path: str):
        self.path = path
        self.pixmap = QPixmap(path)
        self.original_size = self.pixmap.size()
        self.display_size = self.original_size.scaled(
            QSize(150, 150), Qt.KeepAspectRatio
        )
        self.thumbnail = self.pixmap.scaled(
            self.display_size, Qt.KeepAspectRatio
        )
        self.position = (0, 0)  # 在网格中的位置 (row, col)
        self.selected = False


class LayoutConfig:
    """布局配置模型"""
    def __init__(self):
        self.rows = 3
        self.columns = 3
        self.horizontal_gap = 10
        self.vertical_gap = 10
        self.padding_top = 20
        self.padding_bottom = 20
        self.padding_left = 20
        self.padding_right = 20
        self.alignment = 'center'  # left, center, right, top, bottom
        self.layout_mode = 'auto_fill'  # fixed, auto_fill (默认为自动填充)
        self.canvas_width = 800
        self.canvas_height = 600
        self.auto_fit_content = True  # 默认自适应内容大小
        self.background_color = QColor(255, 255, 255, 255)  # 白色背景
        self.transparent_background = False
        
    def copy(self) -> 'LayoutConfig':
        """创建配置的深拷贝"""
        new_config = LayoutConfig()
        new_config.rows = self.rows
        new_config.columns = self.columns
        new_config.horizontal_gap = self.horizontal_gap
        new_config.vertical_gap = self.vertical_gap
        new_config.padding_top = self.padding_top
        new_config.padding_bottom = self.padding_bottom
        new_config.padding_left = self.padding_left
        new_config.padding_right = self.padding_right
        new_config.alignment = self.alignment
        new_config.layout_mode = self.layout_mode
        new_config.canvas_width = self.canvas_width
        new_config.canvas_height = self.canvas_height
        new_config.auto_fit_content = self.auto_fit_content
        new_config.background_color = QColor(self.background_color)
        new_config.transparent_background = self.transparent_background
        return new_config


class UndoStack:
    """撤销/重做栈"""
    def __init__(self, max_size: int = 20):
        self.undo_stack: List[LayoutConfig] = []
        self.redo_stack: List[LayoutConfig] = []
        self.max_size = max_size
        
    def push(self, config: LayoutConfig):
        self.undo_stack.append(config.copy())
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
    def undo(self) -> Optional[LayoutConfig]:
        if not self.undo_stack:
            return None
        self.redo_stack.append(self.undo_stack[-1].copy())
        self.undo_stack.pop()
        if self.undo_stack:
            return self.undo_stack[-1].copy()
        return None
        
    def redo(self) -> Optional[LayoutConfig]:
        if not self.redo_stack:
            return None
        config = self.redo_stack.pop()
        self.undo_stack.append(config.copy())
        return config
        
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 1
        
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0


# -------------------- View - Canvas --------------------
class ImageCanvas(QFrame):
    """图片画布组件，支持拖拽和实时预览"""
    images_dropped = Signal(list)
    layout_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self.setFrameStyle(QFrame.StyledPanel)
        self.layout_config = LayoutConfig()
        self.image_items: List[ImageItem] = []
        self.drag_start_pos = None
        self.dragged_item = None
        
        # 缩放和平移相关
        self.zoom_scale = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.pan_offset = QPointF(0, 0)
        self.is_panning = False
        self.pan_start_pos = None
        self.setMouseTracking(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
            
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        image_paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                image_paths.append(path)
        
        if image_paths:
            self.images_dropped.emit(image_paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
            
    def set_images(self, image_items: List[ImageItem]):
        self.image_items = image_items
        self.update()
        
    def set_layout_config(self, config: LayoutConfig):
        self.layout_config = config
        self.update()
        
    def reset_zoom_pan(self):
        """重置缩放和平移"""
        self.zoom_scale = 1.0
        self.pan_offset = QPointF(0, 0)
        self.update()
        
    def wheelEvent(self, event):
        """处理鼠标滚轮事件（Ctrl+ 滚轮缩放）"""
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl+ 滚轮实现缩放
            delta = event.angleDelta().y()
            if delta > 0:
                # 向上滚动，放大
                self.zoom_scale = min(self.zoom_scale * 1.1, self.max_zoom)
            else:
                # 向下滚动，缩小
                self.zoom_scale = max(self.zoom_scale / 1.1, self.min_zoom)
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        """处理鼠标按下事件（左右键拖动画布）"""
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if event.modifiers() == Qt.ControlModifier or event.button() == Qt.RightButton:
                # Ctrl+ 左键 或 右键拖动画布
                self.is_panning = True
                self.pan_start_pos = event.position()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件（拖动画布）"""
        if self.is_panning and self.pan_start_pos is not None:
            # 计算偏移量
            delta = event.position() - self.pan_start_pos
            self.pan_offset += QPointF(delta)
            self.pan_start_pos = event.position()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if self.is_panning:
                self.is_panning = False
                self.pan_start_pos = None
                self.setCursor(Qt.ArrowCursor)
                event.accept()
            else:
                super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 应用缩放和平移
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.zoom_scale, self.zoom_scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.translate(self.pan_offset)
        
        # 绘制背景
        if self.layout_config.transparent_background:
            painter.fillRect(self.rect(), Qt.transparent)
        else:
            painter.fillRect(self.rect(), self.layout_config.background_color)
        
        if not self.image_items:
            # 显示提示文字（不受缩放影响）
            painter.resetTransform()
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "拖拽图片到此处或点击'添加图片'按钮\n按住 Ctrl+ 滚轮缩放 | Ctrl/右键拖动画布")
            return
        
        # 计算布局
        self._calculate_layout(painter)
        
    def _calculate_layout(self, painter: QPainter):
        """计算并绘制图片网格布局"""
        config = self.layout_config
        images = self.image_items
        
        # 计算画布可用区域
        canvas_rect = self.rect()
        
        # 如果是自适应内容模式，计算实际需要的画布大小
        if config.auto_fit_content:
            total_width = sum([img.original_size.width() for img in images[:config.columns]])
            total_height = sum([img.original_size.height() for img in images[:config.rows]])
            canvas_width = (config.padding_left + config.padding_right + 
                          total_width + (config.columns - 1) * config.horizontal_gap)
            canvas_height = (config.padding_top + config.padding_bottom + 
                           total_height + (config.rows - 1) * config.vertical_gap)
        else:
            canvas_width = config.canvas_width
            canvas_height = config.canvas_height
        
        # 计算每个图片的平均尺寸
        available_width = canvas_width - config.padding_left - config.padding_right
        available_height = canvas_height - config.padding_top - config.padding_bottom
        
        if config.columns > 0 and config.rows > 0:
            cell_width = (available_width - (config.columns - 1) * config.horizontal_gap) / config.columns
            cell_height = (available_height - (config.rows - 1) * config.vertical_gap) / config.rows
        else:
            cell_width = 100
            cell_height = 100
        
        # 绘制图片
        start_x = config.padding_left
        start_y = config.padding_top
        
        for idx, image_item in enumerate(images):
            row = idx // config.columns
            col = idx % config.columns
            
            # 计算图片位置
            x = start_x + col * (cell_width + config.horizontal_gap)
            y = start_y + row * (cell_height + config.vertical_gap)
            
            # 对齐处理
            if config.alignment in ['center', 'top', 'bottom']:
                if config.alignment == 'center':
                    x_offset = (canvas_width - (config.columns * cell_width + 
                              (config.columns - 1) * config.horizontal_gap)) / 2
                    x += x_offset
                elif config.alignment == 'right':
                    x_offset = canvas_width - (config.columns * cell_width + 
                              (config.columns - 1) * config.horizontal_gap) - config.padding_right
                    x = x_offset
            
            # 缩放图片以适应单元格
            scaled_pixmap = image_item.pixmap.scaled(
                int(cell_width), int(cell_height),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # 绘制图片
            painter.drawPixmap(int(x), int(y), scaled_pixmap)
            
            # 如果选中，绘制边框
            if image_item.selected:
                pen = QPen(QColor(52, 152, 219), 3)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(int(x), int(y), scaled_pixmap.width(), scaled_pixmap.height())


# -------------------- View - Control Panel --------------------
class LayoutControlPanel(QWidget):
    """布局控制面板"""
    config_changed = Signal(LayoutConfig)
    export_requested = Signal()
    add_images_requested = Signal()
    clear_requested = Signal()
    reset_view_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.layout_config = LayoutConfig()
        self.undo_stack = UndoStack()
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # 图片管理组
        image_group = self._create_image_group()
        main_layout.addWidget(image_group)
        
        # 高级设置（可折叠抽屉）- 包含布局模式、图片间距、对齐方式
        advanced_group = self._create_advanced_settings_group()
        main_layout.addWidget(advanced_group)
        
        # 画布设置组
        canvas_group = self._create_canvas_group()
        main_layout.addWidget(canvas_group)
        
        # 操作按钮组
        action_group = self._create_action_group()
        main_layout.addWidget(action_group)
        
        main_layout.addStretch()
        
    def _create_image_group(self) -> QGroupBox:
        group = QGroupBox("图片管理")
        layout = QHBoxLayout()
        
        self.add_btn = QPushButton("📁 添加图片")
        self.add_btn.clicked.connect(self.add_images_requested.emit)
        layout.addWidget(self.add_btn,stretch=4)
        
        self.clear_btn = QPushButton("🗑️ 清空所有")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_btn,stretch=4)
        
        self.image_count_label = QLabel("图片数量：0")
        layout.addWidget(self.image_count_label,stretch=1)
        
        group.setLayout(layout)
        return group
        
    def _create_advanced_settings_group(self) -> QWidget:
        """创建高级设置组（可折叠抽屉）"""
        # 主容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题栏（可点击折叠）
        header_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("⚙️ 高级设置（布局/间距/对齐）")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)  # 默认收起
        self.toggle_btn.toggled.connect(self._on_toggle_advanced)
        header_layout.addWidget(self.toggle_btn)
        layout.addLayout(header_layout)
        
        # 可折叠内容区域
        self.advanced_content = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_content)
        advanced_layout.setContentsMargins(0, 10, 0, 0)
        advanced_layout.setSpacing(15)
        
        # 1. 布局模式
        layout_group = self._create_layout_group()
        advanced_layout.addWidget(layout_group)
        
        # 2. 图片间距
        gap_group = self._create_gap_group()
        advanced_layout.addWidget(gap_group)
        
        # 3. 对齐与内边距
        align_group = self._create_alignment_group()
        advanced_layout.addWidget(align_group)
        
        layout.addWidget(self.advanced_content)
        
        # 初始状态：收起
        self.advanced_content.setVisible(False)
        
        return container
        
    def _on_toggle_advanced(self, checked):
        """切换高级设置的显示/隐藏"""
        self.advanced_content.setVisible(checked)
        if checked:
            self.toggle_btn.setText("⚙️ 高级设置（点击收起）")
        else:
            self.toggle_btn.setText("⚙️ 高级设置（布局/间距/对齐）")
            
    def _create_layout_group(self) -> QGroupBox:
        group = QGroupBox("布局模式")
        layout = QFormLayout()
        
        # 布局模式选择
        mode_layout = QHBoxLayout()
        self.fixed_mode_radio = QRadioButton("固定行列")
        self.auto_fill_radio = QRadioButton("自动填充")
        self.auto_fill_radio.setChecked(True)  # 默认自动填充
        self.fixed_mode_radio.toggled.connect(self._on_layout_mode_changed)
        mode_layout.addWidget(self.fixed_mode_radio)
        mode_layout.addWidget(self.auto_fill_radio)
        mode_layout.addStretch()
        layout.addRow(mode_layout)
        
        # 行数和列数在同一行
        rc_layout = QHBoxLayout()
        
        # 行数
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 100)
        self.row_spin.setValue(3)
        self.row_spin.setFixedWidth(60)
        self.row_spin.valueChanged.connect(self._on_config_changed)
        rc_layout.addWidget(QLabel("行数:"))
        rc_layout.addWidget(self.row_spin)
        
        rc_layout.addSpacing(20)
        
        # 列数
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 100)
        self.col_spin.setValue(3)
        self.col_spin.setFixedWidth(60)
        self.col_spin.valueChanged.connect(self._on_config_changed)
        rc_layout.addWidget(QLabel("列数:"))
        rc_layout.addWidget(self.col_spin)
        
        rc_layout.addStretch()
        layout.addRow(rc_layout)
        
        group.setLayout(layout)
        return group
        
    def _create_gap_group(self) -> QGroupBox:
        group = QGroupBox("图片间距")
        layout = QFormLayout()
        
        # 水平间距
        h_gap_layout = QHBoxLayout()
        self.h_gap_slider = QSlider(Qt.Horizontal)
        self.h_gap_slider.setRange(0, 100)
        self.h_gap_slider.setValue(10)
        self.h_gap_slider.valueChanged.connect(self._on_h_gap_slider_changed)
        h_gap_layout.addWidget(self.h_gap_slider)
        
        self.h_gap_spin = QSpinBox()
        self.h_gap_spin.setRange(0, 500)
        self.h_gap_spin.setValue(10)
        self.h_gap_spin.setSuffix(" px")
        self.h_gap_spin.valueChanged.connect(self._on_h_gap_spin_changed)
        h_gap_layout.addWidget(self.h_gap_spin)
        
        layout.addRow("水平间距:", h_gap_layout)
        
        # 垂直间距
        v_gap_layout = QHBoxLayout()
        self.v_gap_slider = QSlider(Qt.Horizontal)
        self.v_gap_slider.setRange(0, 100)
        self.v_gap_slider.setValue(10)
        self.v_gap_slider.valueChanged.connect(self._on_v_gap_slider_changed)
        v_gap_layout.addWidget(self.v_gap_slider)
        
        self.v_gap_spin = QSpinBox()
        self.v_gap_spin.setRange(0, 500)
        self.v_gap_spin.setValue(10)
        self.v_gap_spin.setSuffix(" px")
        self.v_gap_spin.valueChanged.connect(self._on_v_gap_spin_changed)
        v_gap_layout.addWidget(self.v_gap_spin)
        
        layout.addRow("垂直间距:", v_gap_layout)
        
        group.setLayout(layout)
        return group
        
    def _create_alignment_group(self) -> QGroupBox:
        group = QGroupBox("对齐方式")
        layout = QVBoxLayout()
        
        # 对齐按钮组
        align_layout = QHBoxLayout()
        self.align_button_group = QButtonGroup(self)
        
        align_buttons = [
            ("左对齐", "left"),
            ("居中", "center"),
            ("右对齐", "right"),
        ]
        
        for text, align_type in align_buttons:
            btn = QRadioButton(text)
            btn.setProperty("align_type", align_type)
            self.align_button_group.addButton(btn)
            align_layout.addWidget(btn)
            
        align_layout.addStretch()
        layout.addLayout(align_layout)
        
        self.align_button_group.buttons()[1].setChecked(True)  # 默认居中
        self.align_button_group.buttonClicked.connect(self._on_alignment_changed)
        
        # 内边距设置
        padding_layout = QGridLayout()
        labels = ["上:", "下:", "左:", "右:"]
        self.padding_spins = []
        
        for i, label in enumerate(labels):
            spin = QSpinBox()
            spin.setRange(0, 200)
            spin.setValue(20 if i < 2 else 20)
            spin.setSuffix(" px")
            spin.valueChanged.connect(self._on_config_changed)
            self.padding_spins.append(spin)
            padding_layout.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            padding_layout.addWidget(spin, i // 2, (i % 2) * 2 + 1)
            
        layout.addLayout(padding_layout)
        
        group.setLayout(layout)
        return group
        
    def _create_canvas_group(self) -> QGroupBox:
        group = QGroupBox("画布设置")
        layout = QFormLayout()
        
        # 自适应内容 - 使用复选框而不是单选按钮，这样可以取消
        self.auto_fit_check = QPushButton("自适应内容大小")
        self.auto_fit_check.setCheckable(True)
        self.auto_fit_check.setChecked(True)  # 默认自适应
        self.auto_fit_check.toggled.connect(self._on_auto_fit_changed)

        # 初始化按钮文本
        self.auto_fit_check.setText("✓ 自适应内容大小 (点击关闭)")
        layout.addRow(self.auto_fit_check)
        
        # 画布尺寸（默认禁用，因为自适应模式已启用）
        canvas_layout = QHBoxLayout()
        self.canvas_width_spin = QSpinBox()
        self.canvas_width_spin.setRange(100, 5000)
        self.canvas_width_spin.setValue(800)
        self.canvas_width_spin.setSuffix(" px")
        self.canvas_width_spin.setEnabled(False)  # 默认禁用
        self.canvas_width_spin.valueChanged.connect(self._on_config_changed)
        
        self.canvas_height_spin = QSpinBox()
        self.canvas_height_spin.setRange(100, 5000)
        self.canvas_height_spin.setValue(600)
        self.canvas_height_spin.setSuffix(" px")
        self.canvas_height_spin.setEnabled(False)  # 默认禁用
        self.canvas_height_spin.valueChanged.connect(self._on_config_changed)
        
        canvas_layout.addWidget(QLabel("宽:"))
        canvas_layout.addWidget(self.canvas_width_spin)
        canvas_layout.addWidget(QLabel("高:"))
        canvas_layout.addWidget(self.canvas_height_spin)
        
        layout.addRow(canvas_layout)
        
        # 背景颜色
        bg_layout = QHBoxLayout()
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(20, 15)
        self.bg_color_btn.setStyleSheet("background-color: white; border: 1px solid #bdc3c7;")
        self.bg_color_btn.clicked.connect(self._on_bg_color_clicked)
        bg_layout.addWidget(self.bg_color_btn)
        bg_layout.addWidget(QLabel("背景颜色"))
        
        self.transparent_check = QRadioButton("透明背景")
        self.transparent_check.toggled.connect(self._on_transparent_changed)
        bg_layout.addWidget(self.transparent_check)
        bg_layout.addStretch()
        
        layout.addRow(bg_layout)
        
        group.setLayout(layout)
        return group
        
    def _create_action_group(self) -> QGroupBox:
        group = QGroupBox("操作")
        layout = QVBoxLayout()
        
        # 视图控制按钮
        view_layout = QHBoxLayout()
        self.reset_view_btn = QPushButton("🔄 重置视图")
        self.reset_view_btn.clicked.connect(self.reset_view_requested.emit)
        view_layout.addWidget(self.reset_view_btn)
        layout.addLayout(view_layout)
        
        # 撤销/重做按钮
        undo_layout = QHBoxLayout()
        self.undo_btn = QPushButton("↶ 撤销")
        self.undo_btn.clicked.connect(self._on_undo_clicked)
        self.undo_btn.setEnabled(False)
        undo_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↷ 重做")
        self.redo_btn.clicked.connect(self._on_redo_clicked)
        self.redo_btn.setEnabled(False)
        undo_layout.addWidget(self.redo_btn)
        layout.addLayout(undo_layout)
        
        # 导出按钮
        self.export_btn = QPushButton("💾 导出图片")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #58d68d, stop:1 #2ecc71);
            }
        """)
        self.export_btn.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
        
    def _on_config_changed(self):
        """配置变更处理"""
        self._update_config_from_ui()
        self.config_changed.emit(self.layout_config)
        
    def _update_config_from_ui(self):
        """从 UI 更新配置"""
        self.layout_config.rows = self.row_spin.value()
        self.layout_config.columns = self.col_spin.value()
        self.layout_config.horizontal_gap = self.h_gap_spin.value()
        self.layout_config.vertical_gap = self.v_gap_spin.value()
        self.layout_config.padding_top = self.padding_spins[0].value()
        self.layout_config.padding_bottom = self.padding_spins[1].value()
        self.layout_config.padding_left = self.padding_spins[2].value()
        self.layout_config.padding_right = self.padding_spins[3].value()
        self.layout_config.canvas_width = self.canvas_width_spin.value()
        self.layout_config.canvas_height = self.canvas_height_spin.value()
        
    def _on_layout_mode_changed(self):
        """布局模式切换"""
        is_fixed = self.fixed_mode_radio.isChecked()
        self.row_spin.setEnabled(is_fixed)
        self.col_spin.setEnabled(is_fixed)
        self._on_config_changed()
        
    def _on_h_gap_slider_changed(self, value):
        self.h_gap_spin.setValue(value)
        self._on_config_changed()
        
    def _on_h_gap_spin_changed(self, value):
        self.h_gap_slider.setValue(min(value, 100))
        self._on_config_changed()
        
    def _on_v_gap_slider_changed(self, value):
        self.v_gap_spin.setValue(value)
        self._on_config_changed()
        
    def _on_v_gap_spin_changed(self, value):
        self.v_gap_slider.setValue(min(value, 100))
        self._on_config_changed()
        
    def _on_alignment_changed(self, button):
        align_type = button.property("align_type")
        self.layout_config.alignment = align_type
        self.config_changed.emit(self.layout_config)
        
    def _on_auto_fit_changed(self, checked):
        self.layout_config.auto_fit_content = checked
        # 根据是否自适应来启用/禁用画布尺寸输入
        self.canvas_width_spin.setEnabled(not checked)
        self.canvas_height_spin.setEnabled(not checked)
        
        # 如果启用自适应，更新按钮样式
        if checked:
            self.auto_fit_check.setText("✓ 自适应内容大小 (点击关闭)")
        else:
            self.auto_fit_check.setText("自适应内容大小")
            
        self._on_config_changed()
        
    def _on_transparent_changed(self, checked):
        self.layout_config.transparent_background = checked
        self.bg_color_btn.setEnabled(not checked)
        self._on_config_changed()
        
    def _on_bg_color_clicked(self):
        color = QColorDialog.getColor(self.layout_config.background_color, self, "选择背景颜色")
        if color.isValid():
            self.layout_config.background_color = color
            self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #bdc3c7;")
            self.config_changed.emit(self.layout_config)
            
    def _on_undo_clicked(self):
        config = self.undo_stack.undo()
        if config:
            self._update_ui_from_config(config)
            self.config_changed.emit(config)
            
    def _on_redo_clicked(self):
        config = self.undo_stack.redo()
        if config:
            self._update_ui_from_config(config)
            self.config_changed.emit(config)
            
    def _update_ui_from_config(self, config: LayoutConfig):
        """从配置更新 UI"""
        self.row_spin.setValue(config.rows)
        self.col_spin.setValue(config.columns)
        self.h_gap_spin.setValue(config.horizontal_gap)
        self.v_gap_spin.setValue(config.vertical_gap)
        self.padding_spins[0].setValue(config.padding_top)
        self.padding_spins[1].setValue(config.padding_bottom)
        self.padding_spins[2].setValue(config.padding_left)
        self.padding_spins[3].setValue(config.padding_right)
        self.canvas_width_spin.setValue(config.canvas_width)
        self.canvas_height_spin.setValue(config.canvas_height)
        self.auto_fit_check.setChecked(config.auto_fit_content)
        self.transparent_check.setChecked(config.transparent_background)
        
    def _on_clear_clicked(self):
        """清空所有图片"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, '确认', '确定要清空所有图片吗？',
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_requested.emit()
            
    def update_image_count(self, count: int):
        """更新图片数量显示"""
        self.image_count_label.setText(f"图片数量：{count}")
        
    def save_state(self):
        """保存当前状态到撤销栈"""
        self.undo_stack.push(self.layout_config)
        self.undo_btn.setEnabled(self.undo_stack.can_undo())
        self.redo_btn.setEnabled(self.undo_stack.can_redo())


# -------------------- Main Window --------------------
class PicLayouterWindow(QMainWindow):
    """图片布局管理器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.image_items: List[ImageItem] = []
        self.layout_config = LayoutConfig()
        self._init_ui()
        self._setup_connections()
        
    def _init_ui(self):
        self.setWindowTitle("图片布局管理器 - PicLayouter")
        self.setMinimumSize(1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧画布区域
        canvas_frame = QFrame()
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(10, 10, 10, 10)
        
        self.canvas = ImageCanvas()
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout.addWidget(self.canvas)
        
        splitter.addWidget(canvas_frame)
        
        # 右侧控制面板
        control_scroll = QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setMinimumWidth(320)
        control_scroll.setMaximumWidth(450)
        
        self.control_panel = LayoutControlPanel()
        control_scroll.setWidget(self.control_panel)
        
        splitter.addWidget(control_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 应用样式
        self.setStyleSheet(StyleManager.get_main_stylesheet())
        
    def _setup_connections(self):
        """设置信号槽连接"""
        # 添加图片
        self.control_panel.add_images_requested.connect(self._on_add_images)
        
        # 清空图片
        self.control_panel.clear_requested.connect(self._on_clear_images)
        
        # 重置视图
        self.control_panel.reset_view_requested.connect(self._on_reset_view)
        
        # 配置变更
        self.control_panel.config_changed.connect(self._on_config_changed)
        
        # 导出
        self.control_panel.export_requested.connect(self._on_export)
        
        # 画布图片放置
        self.canvas.images_dropped.connect(self._on_images_dropped)
        
    def _on_add_images(self):
        """添加图片"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        
        if paths:
            self._add_images(paths)
            
    def _on_images_dropped(self, paths: List[str]):
        """处理拖拽放置的图片"""
        self._add_images(paths)
        
    def _on_clear_images(self):
        """清空所有图片"""
        self.image_items.clear()
        self.control_panel.update_image_count(0)
        self.canvas.set_images(self.image_items)
        self.canvas.reset_zoom_pan()
        self.status_bar.showMessage("已清空所有图片")
        self.control_panel.save_state()
        
    def _on_reset_view(self):
        """重置视图（缩放和平移）"""
        self.canvas.reset_zoom_pan()
        self.status_bar.showMessage("视图已重置")
        
    def _add_images(self, paths: List[str]):
        """添加图片到列表"""
        for path in paths:
            if os.path.isfile(path):
                try:
                    image_item = ImageItem(path)
                    self.image_items.append(image_item)
                except Exception as e:
                    print(f"加载图片失败 {path}: {e}")
                    
        self.control_panel.update_image_count(len(self.image_items))
        self.canvas.set_images(self.image_items)
        self.status_bar.showMessage(f"已添加 {len(paths)} 张图片")
        self.control_panel.save_state()
        
    def _on_config_changed(self, config: LayoutConfig):
        """配置变更处理"""
        self.layout_config = config
        self.canvas.set_layout_config(config)
        
    def _on_export(self):
        """导出图片"""
        if not self.image_items:
            QMessageBox.warning(self, "警告", "没有图片可导出！")
            return
            
        # 生成智能文件名：PicLayouter_YYYYMMDD_HHMMSS.png
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"PicLayouter_{timestamp}.png"
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出图片", default_name,
            "PNG 文件 (*.png);;JPG 文件 (*.jpg);;BMP 文件 (*.bmp)"
        )
        
        if file_path:
            self._export_image(file_path)
            
    def _export_image(self, file_path: str):
        """将画布导出为图片"""
        config = self.layout_config
        images = self.image_items
        
        # 计算实际需要的画布尺寸
        if config.auto_fit_content and images:
            # 自适应内容模式：根据图片和间距计算实际尺寸
            total_images_width = 0
            total_images_height = 0
            
            # 计算第一行图片的总宽度
            first_row_images = images[:config.columns]
            for img in first_row_images:
                total_images_width += img.original_size.width()
            
            # 计算第一列图片的总高度
            first_col_images = [images[i] for i in range(0, len(images), config.columns)]
            for img in first_col_images:
                total_images_height += img.original_size.height()
            
            # 计算总尺寸（包含间距和内边距）
            total_width = (config.padding_left + config.padding_right + 
                          total_images_width + (config.columns - 1) * config.horizontal_gap)
            total_height = (config.padding_top + config.padding_bottom + 
                           total_images_height + (config.rows - 1) * config.vertical_gap)
        else:
            # 固定画布模式
            total_width = config.canvas_width
            total_height = config.canvas_height
        
        # 确保最小尺寸
        total_width = max(total_width, 100)
        total_height = max(total_height, 100)
        
        # 创建导出 pixmap
        export_pixmap = QPixmap(total_width, total_height)
        
        # 绘制背景
        if config.transparent_background:
            export_pixmap.fill(Qt.transparent)
        else:
            export_pixmap.fill(config.background_color)
            
        # 使用 QPainter 绘制
        painter = QPainter(export_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算并绘制图片布局
        self._draw_export_layout_with_size(painter, total_width, total_height)
        
        painter.end()
        
        # 保存
        if export_pixmap.save(file_path):
            self.status_bar.showMessage(f"已导出到：{file_path} ({total_width}x{total_height})")
            # 创建查看图片按钮
            view_btn = QPushButton("👁️ 查看图片")
            view_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #9b59b6, stop:1 #8e44ad);
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a569bd, stop:1 #9b59b6);
                }
            """)
            view_btn.clicked.connect(lambda: self._view_exported_image(file_path))
            
            # 显示带查看按钮的对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("导出成功")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(f"图片已导出到:\n{file_path}")
            msg_box.setInformativeText(f"尺寸：{total_width}x{total_height} px")
            msg_box.addButton(QMessageBox.Ok)
            msg_box.addButton(view_btn, QMessageBox.ActionRole)
            msg_box.exec()
        else:
            QMessageBox.critical(self, "错误", "导出失败！")
            
    def _view_exported_image(self, file_path: str):
        """查看导出的图片"""
        import subprocess
        import sys
        
        try:
            if sys.platform == 'win32':
                # Windows: 使用默认图片查看器打开
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                # macOS: 使用默认图片查看器打开
                subprocess.run(['open', file_path])
            else:
                # Linux: 使用默认图片查看器打开
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法打开图片查看器：{e}")
            
    def _draw_export_layout(self, painter: QPainter):
        """绘制导出布局（使用配置的画布尺寸）"""
        self._draw_export_layout_with_size(painter, 
                                          self.layout_config.canvas_width, 
                                          self.layout_config.canvas_height)
        
    def _draw_export_layout_with_size(self, painter: QPainter, canvas_width: int, canvas_height: int):
        """绘制导出布局（指定画布尺寸）"""
        config = self.layout_config
        images = self.image_items
        
        if not images:
            return
            
        # 如果是自适应模式，使用图片原始尺寸
        if config.auto_fit_content:
            start_x = config.padding_left
            start_y = config.padding_top
            
            for idx, image_item in enumerate(images):
                row = idx // config.columns
                col = idx % config.columns
                
                # 计算位置
                x = start_x + col * (image_item.original_size.width() + config.horizontal_gap)
                y = start_y + row * (image_item.original_size.height() + config.vertical_gap)
                
                # 使用原始尺寸绘制
                painter.drawPixmap(int(x), int(y), image_item.pixmap)
        else:
            # 固定画布模式，缩放图片以适应
            cell_width = (canvas_width - config.padding_left - config.padding_right - 
                         (config.columns - 1) * config.horizontal_gap) / config.columns
            cell_height = (canvas_height - config.padding_top - config.padding_bottom - 
                          (config.rows - 1) * config.vertical_gap) / config.rows
            
            start_x = config.padding_left
            start_y = config.padding_top
            
            for idx, image_item in enumerate(images):
                row = idx // config.columns
                col = idx % config.columns
                
                x = start_x + col * (cell_width + config.horizontal_gap)
                y = start_y + row * (cell_height + config.vertical_gap)
                
                # 缩放图片
                scaled_pixmap = image_item.pixmap.scaled(
                    int(cell_width), int(cell_height),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                
                painter.drawPixmap(int(x), int(y), scaled_pixmap)


# -------------------- Application Entry --------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PicLayouter")
    app.setOrganizationName("PI-MAPP")
    
    window = PicLayouterWindow()
    window.setWindowIcon(QIcon(resource_path("app.ico")))
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
