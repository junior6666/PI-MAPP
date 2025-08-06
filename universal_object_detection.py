import sys
import os
import cv2
import time
import threading
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                               QProgressBar, QFileDialog, QComboBox, QGroupBox,
                               QSlider, QSpinBox, QCheckBox, QTabWidget,
                               QScrollArea, QGridLayout, QSplitter, QDoubleSpinBox)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon, QPainter, QColor
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 请安装ultralytics库: pip install ultralytics")
    sys.exit(1)


class BatchDetectionThread(QThread):
    """批量检测线程（文件夹遍历）"""
    result_ready = Signal(str, object, object, float, list, list, list)  # 文件路径, 原图, 结果图, 耗时, 置信度, xyxy, xyxyn
    progress_updated = Signal(int)
    current_file_changed = Signal(str)  # 当前处理的文件
    finished = Signal()
    
    def __init__(self, model, folder_path, confidence_threshold=0.25, supported_formats=None):
        super().__init__()
        self.model = model
        self.folder_path = folder_path
        self.confidence_threshold = confidence_threshold
        self.supported_formats = supported_formats or ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.is_running = False
        
    def run(self):
        self.is_running = True
        
        # 收集所有支持的图片文件
        image_files = []
        for fmt in self.supported_formats:
            image_files.extend(Path(self.folder_path).rglob(f'*{fmt}'))
            image_files.extend(Path(self.folder_path).rglob(f'*{fmt.upper()}'))
        
        total_files = len(image_files)
        if total_files == 0:
            self.finished.emit()
            return
            
        for i, img_path in enumerate(image_files):
            if not self.is_running:
                break
                
            self.current_file_changed.emit(str(img_path))
            
            try:
                # 处理单个图片
                start_time = time.time()
                results = self.model(str(img_path), conf=self.confidence_threshold)
                end_time = time.time()
                
                # 获取原图
                original_img = cv2.imread(str(img_path))
                if original_img is not None:
                    original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
                    
                    # 获取结果图
                    result_img = results[0].plot()
                    result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
                    
                    # 提取检测信息
                    confidences = []
                    xyxy_coords = []
                    xyxyn_coords = []
                    
                    for result in results:
                        if result.boxes is not None:
                            confidences = result.boxes.conf.cpu().numpy().tolist()
                            xyxy_coords = result.boxes.xyxy.cpu().numpy().tolist()
                            xyxyn_coords = result.boxes.xyxyn.cpu().numpy().tolist()
                    
                    self.result_ready.emit(str(img_path), original_img, result_img, 
                                         end_time - start_time, confidences, xyxy_coords, xyxyn_coords)
                
            except Exception as e:
                print(f"处理文件 {img_path} 时发生错误: {e}")
            
            # 更新进度
            progress = int(((i + 1) / total_files) * 100)
            self.progress_updated.emit(progress)
            
        self.is_running = False
        self.finished.emit()
    
    def stop(self):
        self.is_running = False


class DetectionThread(QThread):
    """检测线程"""
    result_ready = Signal(object, object, float, list, list, list)  # 原图, 结果图, 耗时, 置信度, xyxy, xyxyn
    progress_updated = Signal(int)
    finished = Signal()
    
    def __init__(self, model, source_type, source_path=None, confidence_threshold=0.25):
        super().__init__()
        self.model = model
        self.source_type = source_type  # 'image', 'video', 'camera'
        self.source_path = source_path
        self.confidence_threshold = confidence_threshold
        self.is_running = False
        self.is_paused = False
        
    def run(self):
        self.is_running = True
        
        if self.source_type == 'image':
            self._process_image()
        elif self.source_type == 'video':
            self._process_video()
        elif self.source_type == 'camera':
            self._process_camera()
            
        self.is_running = False
        self.finished.emit()
    
    def _process_image(self):
        """处理单张图片"""
        if not self.source_path:
            return
            
        start_time = time.time()
        results = self.model(self.source_path, conf=self.confidence_threshold)
        end_time = time.time()
        
        # 获取原图
        original_img = cv2.imread(self.source_path)
        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        
        # 获取结果图
        result_img = results[0].plot()
        result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        
        # 提取检测信息
        confidences = []
        xyxy_coords = []
        xyxyn_coords = []
        
        for result in results:
            if result.boxes is not None:
                confidences = result.boxes.conf.cpu().numpy().tolist()
                xyxy_coords = result.boxes.xyxy.cpu().numpy().tolist()
                xyxyn_coords = result.boxes.xyxyn.cpu().numpy().tolist()
        
        self.result_ready.emit(original_img, result_img, end_time - start_time, 
                              confidences, xyxy_coords, xyxyn_coords)
    
    def _process_video(self):
        """处理视频"""
        if not self.source_path:
            return
            
        cap = cv2.VideoCapture(self.source_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        
        while cap.isOpened() and self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            ret, frame = cap.read()
            if not ret:
                break
                
            start_time = time.time()
            results = self.model(frame, conf=self.confidence_threshold)
            end_time = time.time()
            
            # 获取原图
            original_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 获取结果图
            result_img = results[0].plot()
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            
            # 提取检测信息
            confidences = []
            xyxy_coords = []
            xyxyn_coords = []
            
            for result in results:
                if result.boxes is not None:
                    confidences = result.boxes.conf.cpu().numpy().tolist()
                    xyxy_coords = result.boxes.xyxy.cpu().numpy().tolist()
                    xyxyn_coords = result.boxes.xyxyn.cpu().numpy().tolist()
            
            self.result_ready.emit(original_img, result_img, end_time - start_time, 
                                  confidences, xyxy_coords, xyxyn_coords)
            
            frame_count += 1
            if total_frames > 0:
                progress = int((frame_count / total_frames) * 100)
                self.progress_updated.emit(progress)
            
            # 控制帧率
            time.sleep(0.03)  # 约30fps
            
        cap.release()
    
    def _process_camera(self):
        """处理摄像头"""
        cap = cv2.VideoCapture(0)
        
        while cap.isOpened() and self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            ret, frame = cap.read()
            if not ret:
                break
                
            start_time = time.time()
            results = self.model(frame, conf=self.confidence_threshold)
            end_time = time.time()
            
            # 获取原图
            original_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 获取结果图
            result_img = results[0].plot()
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            
            # 提取检测信息
            confidences = []
            xyxy_coords = []
            xyxyn_coords = []
            
            for result in results:
                if result.boxes is not None:
                    confidences = result.boxes.conf.cpu().numpy().tolist()
                    xyxy_coords = result.boxes.xyxy.cpu().numpy().tolist()
                    xyxyn_coords = result.boxes.xyxyn.cpu().numpy().tolist()
            
            self.result_ready.emit(original_img, result_img, end_time - start_time, 
                                  confidences, xyxy_coords, xyxyn_coords)
            
            # 控制帧率
            time.sleep(0.03)  # 约30fps
            
        cap.release()
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_running = False


class UniversalObjectDetectionUI(QMainWindow):
    """通用目标检测UI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.detection_thread = None
        self.batch_detection_thread = None
        self.current_source_type = 'image'
        self.current_source_path = None
        self.detection_completed = False
        self.confidence_threshold = 0.25
        self.batch_results = []  # 存储批量检测结果
        
        self.init_ui()
        self.load_default_model()
        
        # 设置窗口图标
        self.setWindowIcon(self.create_icon())

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("通用目标检测系统 - Universal Object Detection System")
        self.setGeometry(100, 100, 1600, 900)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分割器用于调整布局
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：控制面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setMaximumWidth(400)
        left_widget.setMinimumWidth(350)
        
        # 模型配置区域
        model_group = QGroupBox("模型配置")
        model_layout = QVBoxLayout(model_group)
        
        # 模型选择
        model_select_layout = QHBoxLayout()
        model_select_layout.addWidget(QLabel("选择模型:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.init_model_combo()
        model_select_layout.addWidget(self.model_combo)
        
        # 刷新模型按钮
        self.refresh_models_btn = QPushButton("🔄")
        self.refresh_models_btn.setMaximumWidth(30)
        self.refresh_models_btn.clicked.connect(self.refresh_models)
        self.refresh_models_btn.setToolTip("刷新模型列表")
        model_select_layout.addWidget(self.refresh_models_btn)
        
        model_layout.addLayout(model_select_layout)
        
        # 置信度配置
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度阈值:"))
        
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setMinimum(1)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(self.on_confidence_changed)
        conf_layout.addWidget(self.conf_slider)
        
        self.conf_spinbox = QDoubleSpinBox()
        self.conf_spinbox.setRange(0.01, 1.0)
        self.conf_spinbox.setSingleStep(0.01)
        self.conf_spinbox.setValue(0.25)
        self.conf_spinbox.setDecimals(2)
        self.conf_spinbox.valueChanged.connect(self.on_confidence_spinbox_changed)
        conf_layout.addWidget(self.conf_spinbox)
        
        model_layout.addLayout(conf_layout)
        
        # 检测源配置区域
        source_group = QGroupBox("检测源配置")
        source_layout = QVBoxLayout(source_group)
        
        # 检测模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("检测模式:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["单张图片", "视频文件", "摄像头", "文件夹批量"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        mode_layout.addWidget(self.source_combo)
        source_layout.addLayout(mode_layout)
        
        # 文件选择
        file_layout = QHBoxLayout()
        self.select_file_btn = QPushButton("选择文件/文件夹")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        source_layout.addLayout(file_layout)
        
        # 当前文件显示
        self.current_file_label = QLabel("未选择文件")
        self.current_file_label.setWordWrap(True)
        self.current_file_label.setStyleSheet("color: #666; font-size: 10px;")
        source_layout.addWidget(self.current_file_label)
        
        # 检测控制区域
        control_group = QGroupBox("检测控制")
        control_layout = QVBoxLayout(control_group)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ 开始检测")
        self.start_btn.clicked.connect(self.start_detection)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.clicked.connect(self.pause_detection)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(btn_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        control_layout.addLayout(progress_layout)
        
        # 批量检测结果控制
        batch_control_layout = QHBoxLayout()
        self.save_results_btn = QPushButton("保存结果")
        self.save_results_btn.clicked.connect(self.save_batch_results)
        self.save_results_btn.setEnabled(False)
        batch_control_layout.addWidget(self.save_results_btn)
        
        self.clear_results_btn = QPushButton("清除结果")
        self.clear_results_btn.clicked.connect(self.clear_batch_results)
        self.clear_results_btn.setEnabled(False)
        batch_control_layout.addWidget(self.clear_results_btn)
        
        control_layout.addLayout(batch_control_layout)
        
        # 日志区域
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMaximumWidth(80)
        log_btn_layout.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_btn_layout)
        
        # 添加到左侧布局
        left_layout.addWidget(model_group)
        left_layout.addWidget(source_group)
        left_layout.addWidget(control_group)
        left_layout.addWidget(log_group)
        left_layout.addStretch()
        
        # 右侧：图像显示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 实时检测标签页
        realtime_tab = QWidget()
        realtime_layout = QHBoxLayout(realtime_tab)
        
        # 原图显示
        original_container = QWidget()
        original_container_layout = QVBoxLayout(original_container)
        original_container_layout.addWidget(QLabel("原图"))
        self.original_label = QLabel("等待加载图片...")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setMinimumSize(500, 400)
        self.original_label.setStyleSheet(self._get_image_label_style())
        original_container_layout.addWidget(self.original_label)
        
        # 结果图显示
        result_container = QWidget()
        result_container_layout = QVBoxLayout(result_container)
        result_container_layout.addWidget(QLabel("检测结果"))
        self.result_label = QLabel("等待检测结果...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(500, 400)
        self.result_label.setStyleSheet(self._get_image_label_style())
        result_container_layout.addWidget(self.result_label)
        
        realtime_layout.addWidget(original_container)
        realtime_layout.addWidget(result_container)
        
        # 批量检测结果标签页
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        # 批量结果控制栏
        batch_control_bar = QHBoxLayout()
        batch_control_bar.addWidget(QLabel("批量检测结果:"))
        batch_control_bar.addStretch()
        
        # 结果导航
        self.prev_result_btn = QPushButton("⬅ 上一个")
        self.prev_result_btn.clicked.connect(self.show_prev_result)
        self.prev_result_btn.setEnabled(False)
        batch_control_bar.addWidget(self.prev_result_btn)
        
        self.result_index_label = QLabel("0/0")
        batch_control_bar.addWidget(self.result_index_label)
        
        self.next_result_btn = QPushButton("下一个 ➡")
        self.next_result_btn.clicked.connect(self.show_next_result)
        self.next_result_btn.setEnabled(False)
        batch_control_bar.addWidget(self.next_result_btn)
        
        batch_layout.addLayout(batch_control_bar)
        
        # 批量结果显示
        batch_image_layout = QHBoxLayout()
        
        self.batch_original_label = QLabel("批量检测: 原图")
        self.batch_original_label.setAlignment(Qt.AlignCenter)
        self.batch_original_label.setMinimumSize(500, 400)
        self.batch_original_label.setStyleSheet(self._get_image_label_style())
        
        self.batch_result_label = QLabel("批量检测: 结果图")
        self.batch_result_label.setAlignment(Qt.AlignCenter)
        self.batch_result_label.setMinimumSize(500, 400)
        self.batch_result_label.setStyleSheet(self._get_image_label_style())
        
        batch_image_layout.addWidget(self.batch_original_label)
        batch_image_layout.addWidget(self.batch_result_label)
        batch_layout.addLayout(batch_image_layout)
        
        # 当前结果信息
        self.batch_info_label = QLabel("选择文件夹开始批量检测")
        self.batch_info_label.setWordWrap(True)
        self.batch_info_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        batch_layout.addWidget(self.batch_info_label)
        
        # 添加标签页
        self.tab_widget.addTab(realtime_tab, "实时检测")
        self.tab_widget.addTab(batch_tab, "批量结果")
        
        right_layout.addWidget(self.tab_widget)
        
        # 添加到分割器
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([400, 1200])  # 设置初始比例
        
        main_layout.addWidget(main_splitter)
        
        # 添加状态栏
        self.statusBar().showMessage("就绪 - 请选择模型和检测源")
        
        # 设置样式
        self.setStyleSheet(self._get_app_stylesheet())
        
        # 初始化批量检测变量
        self.current_batch_index = 0

    def _get_image_label_style(self):
        """获取图片标签样式"""
        return """
            border: 2px solid #e0e0e0; 
            background-color: #f8f9fa; 
            color: #7f8c8d; 
            font-weight: bold; 
            font-size: 12px;
            border-radius: 6px;
            padding: 10px;
        """

    def _get_app_stylesheet(self):
        """获取应用程序样式表"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 11px;
            }
            QPushButton {
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: #3498db;
                color: white;
                min-width: 80px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #ecf0f1;
                border-color: #bdc3c7;
                color: #95a5a6;
            }
            QComboBox {
                padding: 6px 10px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                font-size: 11px;
                min-width: 120px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                max-height: 22px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                padding: 5px;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 6px;
                background: #ecf0f1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
            QSpinBox, QDoubleSpinBox {
                padding: 4px 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                min-width: 60px;
            }
            QTabWidget::pane {
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 20px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-color: #d0d0d0;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """

    def load_default_model(self):
        """加载默认模型"""
        # 尝试加载第一个可用的模型
        if self.model_combo.count() > 0 and self.model_combo.itemText(0) != "无可用模型":
            first_model = self.model_combo.itemText(0)
            self.load_model(first_model)

    def init_model_combo(self):
        """初始化模型选择下拉框"""
        self.model_combo.clear()
        
        # 扫描 pt_models 目录
        model_dir = Path("pt_models")
        model_dir.mkdir(exist_ok=True)
        pt_files = sorted(model_dir.glob("*.pt"))
        
        if not pt_files:
            self.model_combo.addItem("无可用模型")
            self.model_combo.setEnabled(False)
        else:
            self.model_combo.addItems([f.name for f in pt_files])
            self.model_combo.setEnabled(True)
    
    def refresh_models(self):
        """刷新模型列表"""
        current_model = self.model_combo.currentText()
        self.init_model_combo()
        
        # 尝试保持之前选择的模型
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        self.log_message("已刷新模型列表")

    def load_model(self, model_name):
        """加载模型"""
        if model_name == "无可用模型":
            self.model = None
            return
            
        model_path = Path("pt_models") / model_name
        
        if not model_path.exists():
            self.log_message(f"错误: 模型文件不存在 - {model_path}")
            self.model = None
            return
        
        try:
            # 停止当前检测
            if self.detection_thread and self.detection_thread.is_running:
                self.detection_thread.stop()
                self.detection_thread.wait()
            
            if self.batch_detection_thread and self.batch_detection_thread.is_running:
                self.batch_detection_thread.stop()
                self.batch_detection_thread.wait()
            
            # 加载新模型
            self.model = YOLO(str(model_path))
            self.log_message(f"模型加载成功: {model_name}")
            
            # 更新按钮状态
            self.update_button_states()
            
        except Exception as e:
            self.log_message(f"错误: 模型加载失败 - {str(e)}")
            self.model = None

    def on_model_changed(self, model_text):
        """模型选择改变"""
        self.load_model(model_text)
        
        # 清空显示
        self.clear_display_windows()
        self.current_source_path = None
        self.current_file_label.setText("未选择文件")

    def on_confidence_changed(self, value):
        """置信度滑块改变"""
        conf_value = value / 100.0
        self.confidence_threshold = conf_value
        self.conf_spinbox.blockSignals(True)
        self.conf_spinbox.setValue(conf_value)
        self.conf_spinbox.blockSignals(False)
        
    def on_confidence_spinbox_changed(self, value):
        """置信度数值框改变"""
        self.confidence_threshold = value
        self.conf_slider.blockSignals(True)
        self.conf_slider.setValue(int(value * 100))
        self.conf_slider.blockSignals(False)

    def on_source_changed(self, source_text):
        """检测源改变"""
        source_map = {
            "单张图片": "image", 
            "视频文件": "video", 
            "摄像头": "camera",
            "文件夹批量": "batch"
        }
        self.current_source_type = source_map.get(source_text)
        
        # 重置状态
        self.current_source_path = None
        self.current_file_label.setText("未选择文件")
        self.clear_display_windows()
        self.clear_batch_results()
        
        # 更新按钮状态
        self.update_button_states()
        
        # 更新状态栏
        if self.current_source_type == "camera":
            self.statusBar().showMessage("摄像头模式 - 可直接开始检测")
        elif self.current_source_type == "batch":
            self.statusBar().showMessage("批量检测模式 - 请选择文件夹")
        else:
            self.statusBar().showMessage(f"{source_text}模式 - 请选择文件")

    def update_button_states(self):
        """更新按钮状态"""
        has_model = self.model is not None
        has_source = self.current_source_path is not None or self.current_source_type == "camera"
        
        if self.current_source_type == "camera":
            self.start_btn.setEnabled(has_model)
            self.select_file_btn.setText("选择文件/文件夹")
            self.select_file_btn.setEnabled(False)
        elif self.current_source_type == "batch":
            self.start_btn.setEnabled(has_model and has_source)
            self.select_file_btn.setText("选择文件夹")
            self.select_file_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(has_model and has_source)
            self.select_file_btn.setText("选择文件")
            self.select_file_btn.setEnabled(True)

    def select_file(self):
        """选择文件或文件夹"""
        if self.current_source_type == "image":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "", 
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;所有文件 (*)"
            )
        elif self.current_source_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频", "", 
                "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
            )
        elif self.current_source_type == "batch":
            file_path = QFileDialog.getExistingDirectory(
                self, "选择包含图片的文件夹"
            )
        else:
            return
        
        if file_path:
            self.current_source_path = file_path
            self.current_file_label.setText(f"已选择: {Path(file_path).name}")
            self.log_message(f"已选择: {file_path}")
            
            # 更新按钮状态
            self.update_button_states()
            
            # 预览文件（如果是图片或视频）
            if self.current_source_type in ["image", "video"]:
                self.preview_file(file_path)
            elif self.current_source_type == "batch":
                # 扫描文件夹统计图片数量
                self.scan_folder_info(file_path)

    def preview_file(self, file_path):
        """预览选中的文件"""
        try:
            if self.current_source_type == "image":
                img = cv2.imread(file_path)
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    self.display_image(img_rgb, self.original_label)
                    self.result_label.clear()
                    self.result_label.setText("等待检测结果...")
                    
            elif self.current_source_type == "video":
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        self.display_image(frame_rgb, self.original_label)
                        self.result_label.clear()
                        self.result_label.setText("等待检测结果...")
                    cap.release()
        except Exception as e:
            self.log_message(f"预览文件失败: {str(e)}")

    def scan_folder_info(self, folder_path):
        """扫描文件夹信息"""
        try:
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            image_files = []
            
            for fmt in supported_formats:
                image_files.extend(Path(folder_path).rglob(f'*{fmt}'))
                image_files.extend(Path(folder_path).rglob(f'*{fmt.upper()}'))
            
            count = len(image_files)
            self.log_message(f"文件夹扫描完成: 找到 {count} 张图片")
            
            if count > 0:
                self.statusBar().showMessage(f"已选择文件夹 - 包含 {count} 张图片")
            else:
                self.statusBar().showMessage("选择的文件夹中没有找到支持的图片格式")
                
        except Exception as e:
            self.log_message(f"扫描文件夹失败: {str(e)}")

    def start_detection(self):
        """开始检测"""
        if not self.model:
            self.log_message("错误: 模型未加载")
            return
        
        # 重置状态
        self.detection_completed = False
        self._frame_count = 0
        
        if self.current_source_type == "batch":
            self.start_batch_detection()
        else:
            self.start_single_detection()

    def start_single_detection(self):
        """开始单个检测"""
        if self.current_source_type in ["image", "video"] and not self.current_source_path:
            self.log_message("错误: 请选择文件")
            return
        
        # 创建检测线程
        self.detection_thread = DetectionThread(
            self.model, self.current_source_type, self.current_source_path, self.confidence_threshold
        )
        self.detection_thread.result_ready.connect(self.on_detection_result)
        self.detection_thread.progress_updated.connect(self.progress_bar.setValue)
        self.detection_thread.finished.connect(self.on_detection_finished)
        
        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.source_combo.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        self.model_combo.setEnabled(False)
        
        # 切换到实时检测标签页
        self.tab_widget.setCurrentIndex(0)
        
        # 开始检测
        self.detection_thread.start()
        self.log_message(f"开始{self.current_source_type}检测...")
        self.statusBar().showMessage("正在检测中...")

    def start_batch_detection(self):
        """开始批量检测"""
        if not self.current_source_path:
            self.log_message("错误: 请选择文件夹")
            return
        
        # 清空之前的结果
        self.clear_batch_results()
        
        # 创建批量检测线程
        self.batch_detection_thread = BatchDetectionThread(
            self.model, self.current_source_path, self.confidence_threshold
        )
        self.batch_detection_thread.result_ready.connect(self.on_batch_result)
        self.batch_detection_thread.progress_updated.connect(self.progress_bar.setValue)
        self.batch_detection_thread.current_file_changed.connect(self.on_current_file_changed)
        self.batch_detection_thread.finished.connect(self.on_batch_finished)
        
        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)  # 批量检测不支持暂停
        self.stop_btn.setEnabled(True)
        self.source_combo.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        self.model_combo.setEnabled(False)
        
        # 切换到批量检测标签页
        self.tab_widget.setCurrentIndex(1)
        
        # 开始检测
        self.batch_detection_thread.start()
        self.log_message("开始批量检测...")
        self.statusBar().showMessage("正在批量检测中...")

    def pause_detection(self):
        """暂停检测"""
        if self.detection_thread and self.detection_thread.is_running:
            if self.detection_thread.is_paused:
                self.detection_thread.resume()
                self.pause_btn.setText("⏸ 暂停")
                self.log_message("检测已恢复")
            else:
                self.detection_thread.pause()
                self.pause_btn.setText("▶ 继续")
                self.log_message("检测已暂停")

    def stop_detection(self):
        """停止检测"""
        if self.detection_thread and self.detection_thread.is_running:
            self.detection_thread.stop()
            self.detection_thread.wait()
        
        if self.batch_detection_thread and self.batch_detection_thread.is_running:
            self.batch_detection_thread.stop()
            self.batch_detection_thread.wait()
        
        self.on_detection_finished()

    def on_detection_result(self, original_img, result_img, inference_time, 
                           confidences, xyxy_coords, xyxyn_coords):
        """单个检测结果回调"""
        # 显示图像
        self.display_image(original_img, self.original_label)
        self.display_image(result_img, self.result_label)
        
        # 更新日志
        if self.current_source_type == 'image':
            self.log_detection_details(inference_time, confidences, xyxy_coords, xyxyn_coords)
        else:
            # 视频/摄像头检测减少日志输出
            if not hasattr(self, '_frame_count'):
                self._frame_count = 0
            self._frame_count += 1
            
            if confidences or self._frame_count % 30 == 0:
                object_count = len(confidences) if confidences else 0
                self.log_message(f"检测到 {object_count} 个目标 (耗时: {inference_time:.3f}秒)")

    def on_batch_result(self, file_path, original_img, result_img, inference_time, 
                       confidences, xyxy_coords, xyxyn_coords):
        """批量检测结果回调"""
        # 保存结果
        result_data = {
            'file_path': file_path,
            'original_img': original_img,
            'result_img': result_img,
            'inference_time': inference_time,
            'confidences': confidences,
            'xyxy_coords': xyxy_coords,
            'xyxyn_coords': xyxyn_coords,
            'object_count': len(confidences) if confidences else 0
        }
        
        self.batch_results.append(result_data)
        
        # 如果是第一个结果，立即显示
        if len(self.batch_results) == 1:
            self.current_batch_index = 0
            self.show_batch_result(0)
            
        # 更新导航按钮
        self.update_batch_navigation()
        
        # 记录日志
        object_count = len(confidences) if confidences else 0
        self.log_message(f"完成: {Path(file_path).name} - {object_count} 个目标 ({inference_time:.3f}秒)")

    def on_current_file_changed(self, file_path):
        """当前处理文件改变"""
        self.statusBar().showMessage(f"正在处理: {Path(file_path).name}")

    def on_batch_finished(self):
        """批量检测完成"""
        total_count = len(self.batch_results)
        total_objects = sum(result['object_count'] for result in self.batch_results)
        
        self.log_message(f"批量检测完成! 处理了 {total_count} 张图片，检测到 {total_objects} 个目标")
        self.statusBar().showMessage(f"批量检测完成 - {total_count} 张图片，{total_objects} 个目标")
        
        # 启用保存和清除按钮
        self.save_results_btn.setEnabled(True)
        self.clear_results_btn.setEnabled(True)
        
        self.on_detection_finished()

    def on_detection_finished(self):
        """检测完成回调"""
        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ 暂停")
        self.stop_btn.setEnabled(False)
        self.source_combo.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        self.model_combo.setEnabled(True)
        
        # 重置进度条
        self.progress_bar.setValue(0)
        
        if not self.detection_completed:
            self.detection_completed = True
            if self.current_source_type != "batch":
                self.log_message("检测完成")

    def show_batch_result(self, index):
        """显示指定索引的批量检测结果"""
        if 0 <= index < len(self.batch_results):
            result = self.batch_results[index]
            
            # 显示图像
            self.display_image(result['original_img'], self.batch_original_label)
            self.display_image(result['result_img'], self.batch_result_label)
            
            # 更新信息
            file_name = Path(result['file_path']).name
            object_count = result['object_count']
            inference_time = result['inference_time']
            
            info_text = f"文件: {file_name}\n"
            info_text += f"检测目标: {object_count} 个\n"
            info_text += f"推理耗时: {inference_time:.3f} 秒\n"
            
            if result['confidences']:
                info_text += "置信度: " + ", ".join([f"{conf:.3f}" for conf in result['confidences'][:5]])
                if len(result['confidences']) > 5:
                    info_text += f" (共{len(result['confidences'])}个)"
            
            self.batch_info_label.setText(info_text)
            
            # 更新索引显示
            self.result_index_label.setText(f"{index + 1}/{len(self.batch_results)}")

    def show_prev_result(self):
        """显示上一个结果"""
        if self.current_batch_index > 0:
            self.current_batch_index -= 1
            self.show_batch_result(self.current_batch_index)
            self.update_batch_navigation()

    def show_next_result(self):
        """显示下一个结果"""
        if self.current_batch_index < len(self.batch_results) - 1:
            self.current_batch_index += 1
            self.show_batch_result(self.current_batch_index)
            self.update_batch_navigation()

    def update_batch_navigation(self):
        """更新批量结果导航按钮状态"""
        has_results = len(self.batch_results) > 0
        self.prev_result_btn.setEnabled(has_results and self.current_batch_index > 0)
        self.next_result_btn.setEnabled(has_results and self.current_batch_index < len(self.batch_results) - 1)

    def save_batch_results(self):
        """保存批量检测结果"""
        if not self.batch_results:
            self.log_message("没有可保存的结果")
            return
        
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_dir:
            return
        
        try:
            save_path = Path(save_dir)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            result_dir = save_path / f"detection_results_{timestamp}"
            result_dir.mkdir(exist_ok=True)
            
            # 保存检测结果图片
            for i, result in enumerate(self.batch_results):
                file_name = Path(result['file_path']).stem
                
                # 保存结果图
                result_img = cv2.cvtColor(result['result_img'], cv2.COLOR_RGB2BGR)
                result_save_path = result_dir / f"{file_name}_result.jpg"
                cv2.imwrite(str(result_save_path), result_img)
            
            # 保存检测报告
            report_path = result_dir / "detection_report.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("目标检测批量处理报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"置信度阈值: {self.confidence_threshold}\n")
                f.write(f"处理图片数量: {len(self.batch_results)}\n")
                f.write(f"总检测目标数: {sum(r['object_count'] for r in self.batch_results)}\n")
                f.write("\n详细结果:\n")
                f.write("-" * 50 + "\n")
                
                for i, result in enumerate(self.batch_results, 1):
                    f.write(f"{i}. {Path(result['file_path']).name}\n")
                    f.write(f"   检测目标: {result['object_count']} 个\n")
                    f.write(f"   推理耗时: {result['inference_time']:.3f} 秒\n")
                    if result['confidences']:
                        f.write(f"   置信度: {', '.join([f'{c:.3f}' for c in result['confidences']])}\n")
                    f.write("\n")
            
            self.log_message(f"结果已保存到: {result_dir}")
            
        except Exception as e:
            self.log_message(f"保存失败: {str(e)}")

    def clear_batch_results(self):
        """清除批量检测结果"""
        self.batch_results.clear()
        self.current_batch_index = 0
        
        # 清空显示
        self.batch_original_label.clear()
        self.batch_original_label.setText("批量检测: 原图")
        self.batch_result_label.clear()
        self.batch_result_label.setText("批量检测: 结果图")
        self.batch_info_label.setText("选择文件夹开始批量检测")
        self.result_index_label.setText("0/0")
        
        # 禁用按钮
        self.prev_result_btn.setEnabled(False)
        self.next_result_btn.setEnabled(False)
        self.save_results_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(False)

    def log_detection_details(self, inference_time, confidences, xyxy_coords, xyxyn_coords):
        """记录详细检测信息"""
        self.log_message(f"推理耗时: {inference_time:.3f}秒")
        if confidences:
            self.log_message(f"检测到 {len(confidences)} 个目标")
            for i, (conf, xyxy, xyxyn) in enumerate(zip(confidences, xyxy_coords, xyxyn_coords)):
                self.log_message(f"目标 {i+1}: 置信度={conf:.3f}")
        else:
            self.log_message("未检测到目标")

    def clear_display_windows(self):
        """清空显示窗口"""
        self.original_label.clear()
        self.original_label.setText("等待加载图片...")
        self.result_label.clear()
        self.result_label.setText("等待检测结果...")

    def display_image(self, img_array, label):
        """在标签中显示图像"""
        if img_array is None:
            return
        
        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        
        # 转换为QImage
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # 缩放图像以适应标签
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        label.setPixmap(scaled_pixmap)

    def log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 限制日志行数
        max_lines = 1000
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > max_lines:
            keep_lines = lines[-500:]
            self.log_text.setPlainText('\n'.join(keep_lines))
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.log_message("日志已清除")

    def create_icon(self, size=64):
        """创建应用图标"""
        from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt, QRectF
        
        standard_sizes = (16, 32, 48, 64, 128, 256)
        icon = QIcon()
        
        for s in standard_sizes:
            px = QPixmap(s, s)
            px.fill(QColor("#ffffff"))
            
            painter = QPainter(px)
            painter.setRenderHint(QPainter.Antialiasing)
            
            margin = max(3, s // 10)
            side = s - 2 * margin
            rect = QRectF(margin, margin, side, side)
            
            # 外框
            painter.setPen(QColor("#3498db"))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, side * 0.2, side * 0.2)
            
            # 十字准星
            center = s / 2
            arm_len = side * 0.30
            painter.setPen(QColor("#3498db"))
            painter.drawLine(center - arm_len, center, center + arm_len, center)
            painter.drawLine(center, center - arm_len, center, center + arm_len)
            
            # 中心点
            r = max(1, s // 64)
            painter.setBrush(QColor("#3498db"))
            painter.drawEllipse(center - r, center - r, 2 * r, 2 * r)
            
            painter.end()
            icon.addPixmap(px)
        
        return icon


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Universal Object Detection System")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("AI Vision Lab")
    
    window = UniversalObjectDetectionUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()