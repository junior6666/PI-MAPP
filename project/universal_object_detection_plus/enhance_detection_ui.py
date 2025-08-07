import sys
import os
import cv2
import time
import threading
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QProgressBar, QFileDialog, QComboBox, QGroupBox,
                               QSlider, QSpinBox, QCheckBox, QTabWidget,
                               QScrollArea, QGridLayout, QSplitter, QDoubleSpinBox,
                               QListWidget, QListWidgetItem, QMessageBox, QDialog,
                               QDialogButtonBox, QLineEdit, QFormLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QFrame, QStackedWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import (QPixmap, QImage, QFont, QIcon, QPainter, QColor,
                           QLinearGradient, QBrush, QPen, QPolygonF, QRadialGradient)
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 请安装ultralytics库: pip install ultralytics")
    sys.exit(1)

# 检测摄像头（通常前4个索引）
MAX_PROBE = 10  # 最多探测到 /dev/video9
MISS_TOLERANCE = 2  # 连续打不开 2 个就停
class CameraManager:
    """摄像头管理器"""

    def __init__(self):
        self.cameras = []
        self.scan_cameras()

    def scan_cameras(self):
        """扫描可用摄像头"""
        self.cameras = []

        miss = 0
        for idx in range(MAX_PROBE):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # Windows 可加 cv2.CAP_DSHOW 加速
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)

                    self.cameras.append({
                        'id': idx,
                        'name': f'摄像头 {idx}',
                        'resolution': f'{w}x{h}',
                        'fps': fps,
                        'available': True
                    })
                    miss = 0  # 只要成功一次就重置 miss
                cap.release()
            else:
                miss += 1
                if miss >= MISS_TOLERANCE:
                    break

        # 如果没有摄像头，添加虚拟摄像头用于测试
        if not self.cameras:
            self.cameras.append({
                'id': -1,
                'name': "虚拟摄像头 (用于测试)",
                'resolution': "640x480",
                'fps': 30,
                'available': False
            })

    def get_available_cameras(self):
        """获取可用摄像头列表"""
        return [cam for cam in self.cameras if cam['available']]

    def get_camera_info(self, camera_id):
        """获取摄像头信息"""
        for cam in self.cameras:
            if cam['id'] == camera_id:
                return cam
        return None


class ModelManager:
    """模型管理器"""

    def __init__(self):
        self.models_paths = [
            Path("pt_models"),
            Path("models"),
            Path("weights"),
            Path.home() / "yolo_models"
        ]
        self.current_model = None
        self.class_names = []

    def scan_models(self, custom_path=None):
        """扫描模型文件"""
        models = []
        search_paths = self.models_paths.copy()

        if custom_path and Path(custom_path).exists():
            search_paths.insert(0, Path(custom_path))

        for model_dir in search_paths:
            if model_dir.exists():
                pt_files = sorted(model_dir.glob("*.pt"))
                for pt_file in pt_files:
                    models.append({
                        'name': pt_file.name,
                        'path': str(pt_file),
                        'size': self._get_file_size(pt_file),
                        'modified': self._get_modification_time(pt_file)
                    })

        return models

    def load_model(self, model_path):
        """加载模型"""
        try:
            self.current_model = YOLO(model_path)
            self.class_names = list(self.current_model.names.values())
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def get_class_names(self):
        """获取类别名称"""
        return self.class_names

    def _get_file_size(self, file_path):
        """获取文件大小"""
        try:
            size = file_path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown"

    def _get_modification_time(self, file_path):
        """获取修改时间"""
        try:
            timestamp = file_path.stat().st_mtime
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except:
            return "Unknown"


class GradientWidget(QWidget):
    """渐变背景组件"""

    def __init__(self, start_color="#3498db", end_color="#2c3e50", direction="vertical"):
        super().__init__()
        self.start_color = QColor(start_color)
        self.end_color = QColor(end_color)
        self.direction = direction

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient()
        if self.direction == "vertical":
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, self.height())
        else:
            gradient.setStart(0, 0)
            gradient.setFinalStop(self.width(), 0)

        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)

        painter.fillRect(self.rect(), QBrush(gradient))


class AnimatedButton(QPushButton):
    """带动画效果的按钮"""

    def __init__(self, text="", icon=None):
        super().__init__(text)
        if icon:
            self.setIcon(icon)

        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
                color: white;
                padding: 2px 8px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
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
        """)


class ModelSelectionDialog(QDialog):
    """模型选择对话框"""

    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.selected_model = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("选择模型")
        self.setModal(True)
        self.resize(800, 300)

        layout = QVBoxLayout(self)

        # 自定义路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("自定义模型路径:"))

        self.path_edit = QLineEdit()
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_models)
        path_layout.addWidget(refresh_btn)

        layout.addLayout(path_layout)

        # 模型列表
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(4)
        self.model_table.setHorizontalHeaderLabels(["模型名称", "大小", "修改时间", "路径"])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


        self.model_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.model_table.doubleClicked.connect(self.accept)

        layout.addWidget(self.model_table)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.refresh_models()

    def browse_path(self):
        """浏览自定义路径"""
        path = QFileDialog.getExistingDirectory(self, "选择模型目录")
        if path:
            self.path_edit.setText(path)
            self.refresh_models()

    def refresh_models(self):
        """刷新模型列表"""
        custom_path = self.path_edit.text() if self.path_edit.text() else None
        models = self.model_manager.scan_models(custom_path)

        self.model_table.setRowCount(len(models))

        for i, model in enumerate(models):
            self.model_table.setItem(i, 0, QTableWidgetItem(model['name']))
            self.model_table.setItem(i, 1, QTableWidgetItem(model['size']))
            self.model_table.setItem(i, 2, QTableWidgetItem(model['modified']))
            self.model_table.setItem(i, 3, QTableWidgetItem(model['path']))

    def accept(self):
        """确认选择"""
        current_row = self.model_table.currentRow()
        if current_row >= 0:
            self.selected_model = self.model_table.item(current_row, 3).text()
        super().accept()


class DetectionResultWidget(QWidget):
    """检测结果显示组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("检测结果详情")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["类别", "置信度", "坐标", "大小"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setMaximumHeight(100)

        layout.addWidget(self.result_table)

        # 统计信息
        self.stats_label = QLabel("等待检测结果...")
        self.stats_label.setStyleSheet("background-color: #ecf0f1; padding: 2px; border-radius: 4px;")
        layout.addWidget(self.stats_label)

    def update_results(self, results, class_names, inference_time):
        """更新检测结果"""
        if not results or not results[0].boxes:
            self.result_table.setRowCount(0)
            self.stats_label.setText("未检测到目标")
            return

        boxes = results[0].boxes
        confidences = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy()

        # 更新表格
        self.result_table.setRowCount(len(confidences))

        class_counts = {}
        for i, (conf, cls, box) in enumerate(zip(confidences, classes, xyxy)):
            class_name = class_names[cls] if cls < len(class_names) else f"类别{cls}"

            # 统计类别数量
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            self.result_table.setItem(i, 0, QTableWidgetItem(class_name))
            self.result_table.setItem(i, 1, QTableWidgetItem(f"{conf:.3f}"))
            self.result_table.setItem(i, 2, QTableWidgetItem(f"({box[0]:.0f},{box[1]:.0f})"))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{box[2] - box[0]:.0f}×{box[3] - box[1]:.0f}"))

        # 更新统计信息
        total_objects = len(confidences)
        avg_confidence = np.mean(confidences)

        stats_text = f"检测到 {total_objects} 个目标 | 平均置信度: {avg_confidence:.3f} | 耗时: {inference_time:.3f}秒\n"
        stats_text += "类别统计: " + " | ".join([f"{name}: {count}" for name, count in class_counts.items()])

        self.stats_label.setText(stats_text)

# 继续下一部分...