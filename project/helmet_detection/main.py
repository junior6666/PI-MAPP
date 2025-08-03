import sys
import cv2
import time
import threading
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                               QProgressBar, QFileDialog, QComboBox, QGroupBox)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap, QImage, QFont
from ultralytics import YOLO
import numpy as np


class DetectionThread(QThread):
    """检测线程"""
    result_ready = Signal(object, object, float, list, list, list)  # 原图, 结果图, 耗时, 置信度, xyxy, xyxyn
    progress_updated = Signal(int)
    finished = Signal()
    
    def __init__(self, model, source_type, source_path=None):
        super().__init__()
        self.model = model
        self.source_type = source_type  # 'image', 'video', 'camera'
        self.source_path = source_path
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
        results = self.model(self.source_path)
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
            results = self.model(frame)
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
            results = self.model(frame)
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


class HelmetDetectionUI(QMainWindow):
    """头盔检测UI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.detection_thread = None
        self.current_source_type = 'image'
        self.current_source_path = None
        self.detection_completed = False  # 添加检测完成状态标记
        
        self.init_ui()
        self.load_model()
        
        # 设置窗口图标
        self.setWindowIcon(self.create_icon())
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("头盔检测系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 图像显示区域
        image_group = QGroupBox("检测结果")
        image_layout = QHBoxLayout(image_group)
        
        # 原图显示
        self.original_label = QLabel("原图")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setMinimumSize(600, 400)
        self.original_label.setStyleSheet("""
            border: 1px solid #bdc3c7; 
            background-color: #f8f9fa; 
            color: #7f8c8d; 
            font-weight: bold; 
            font-size: 12px;
            border-radius: 4px;
        """)
        
        # 结果图显示
        self.result_label = QLabel("检测结果")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(600, 400)
        self.result_label.setStyleSheet("""
            border: 1px solid #bdc3c7; 
            background-color: #f8f9fa; 
            color: #7f8c8d; 
            font-weight: bold; 
            font-size: 12px;
            border-radius: 4px;
        """)
        
        image_layout.addWidget(self.original_label)
        image_layout.addWidget(self.result_label)
        
        # 控制区域
        control_group = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_group)
        
        # 第一行：源选择和检测控制按钮并排显示
        control_row = QHBoxLayout()
        
        # 左侧：源选择
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("选择源:"))
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["图片", "视频", "摄像头"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        source_layout.addWidget(self.source_combo)
        
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.clicked.connect(self.select_file)
        self.select_file_btn.setEnabled(True)
        source_layout.addWidget(self.select_file_btn)
        
        control_row.addLayout(source_layout)
        control_row.addStretch()
        
        # 右侧：检测控制按钮
        detect_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ 开始检测")
        self.start_btn.clicked.connect(self.start_detection)
        self.start_btn.setEnabled(False)
        detect_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ 暂停检测")
        self.pause_btn.clicked.connect(self.pause_detection)
        self.pause_btn.setEnabled(False)
        detect_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ 停止检测")
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        detect_layout.addWidget(self.stop_btn)
        
        control_row.addLayout(detect_layout)
        control_layout.addLayout(control_row)
        
        # 第二行：进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("检测进度:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        control_layout.addLayout(progress_layout)
        
        # 日志区域
        log_group = QGroupBox("检测日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 6))
        log_layout.addWidget(self.log_text)
        
        # 清除日志按钮放在右下角
        log_bottom_layout = QHBoxLayout()
        log_bottom_layout.addStretch()
        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMaximumWidth(80)
        self.clear_log_btn.setMaximumHeight(40)
        log_bottom_layout.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_bottom_layout)
        
        # 添加到主布局
        main_layout.addWidget(image_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(log_group)
        
        # 添加状态栏
        self.statusBar().showMessage("就绪 - 请选择检测源")
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 8px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px 0 6px;
                color: #333333;
            }
            QPushButton {
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #3498db;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                min-width: 90px;
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
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                max-height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
            }
        """)
        
    def load_model(self):
        """加载模型"""
        try:
            model_path = Path("pt_models/helmet_best.pt")
            if model_path.exists():
                self.model = YOLO(str(model_path))
                self.log_message("模型加载成功")
                # 根据当前选择的源类型启用相应按钮
                if self.current_source_type == "camera":
                    self.start_btn.setEnabled(True)
                elif self.current_source_type in ["image", "video"]:
                    self.select_file_btn.setEnabled(True)
            else:
                self.log_message("错误: 模型文件不存在")
        except Exception as e:
            self.log_message(f"错误: 模型加载失败 - {str(e)}")
    
    def on_source_changed(self, source_text):
        """源选择改变"""
        source_map = {"图片": "image", "视频": "video", "摄像头": "camera"}
        self.current_source_type = source_map.get(source_text)
        
        # 重置文件路径
        self.current_source_path = None
        
        # 清空显示窗口
        self.clear_display_windows()
        
        if self.current_source_type in ["image", "video"]:
            self.select_file_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            self.statusBar().showMessage(f"已选择{source_text}模式 - 请选择文件")
        else:
            self.select_file_btn.setEnabled(False)
            # 摄像头模式直接启用开始按钮
            if self.model:
                self.start_btn.setEnabled(True)
                self.statusBar().showMessage("已选择摄像头模式 - 可以开始检测")
    
    def clear_display_windows(self):
        """清空显示窗口"""
        self.original_label.clear()
        self.original_label.setText("原图")
        self.result_label.clear()
        self.result_label.setText("检测结果")
    
    def select_file(self):
        """选择文件"""
        if self.current_source_type == "image":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)"
            )
        elif self.current_source_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)"
            )
        else:
            return
            
        if file_path:
            self.current_source_path = file_path
            self.log_message(f"已选择文件: {file_path}")
            self.start_btn.setEnabled(True)
            self.statusBar().showMessage(f"已选择文件 - 可以开始检测")
            
            # 立即显示所选文件
            self.display_selected_file(file_path)
    
    def display_selected_file(self, file_path):
        """立即显示所选文件"""
        try:
            if self.current_source_type == "image":
                # 显示图片
                img = cv2.imread(file_path)
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    self.display_image(img_rgb, self.original_label)
                    # 清空结果图显示
                    self.result_label.clear()
                    self.result_label.setText("检测结果")
                    self.log_message("图片已加载，可以开始检测")
                else:
                    self.log_message("错误: 无法读取图片文件")
                    
            elif self.current_source_type == "video":
                # 显示视频第一帧
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        self.display_image(frame_rgb, self.original_label)
                        # 清空结果图显示
                        self.result_label.clear()
                        self.result_label.setText("检测结果")
                        self.log_message("视频已加载，可以开始检测")
                    else:
                        self.log_message("错误: 无法读取视频第一帧")
                    cap.release()
                else:
                    self.log_message("错误: 无法打开视频文件")
                    
        except Exception as e:
            self.log_message(f"错误: 显示文件失败 - {str(e)}")
    
    def start_detection(self):
        """开始检测"""
        if not self.model:
            self.log_message("错误: 模型未加载")
            return
            
        if not self.current_source_type:
            self.log_message("错误: 请选择检测源")
            return
            
        if self.current_source_type in ["image", "video"] and not self.current_source_path:
            self.log_message("错误: 请选择文件")
            return
        
        # 重置检测完成状态
        self.detection_completed = False
        self._frame_count = 0  # 重置帧计数器
        
        # 创建检测线程
        self.detection_thread = DetectionThread(
            self.model, self.current_source_type, self.current_source_path
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
        
        # 开始检测
        self.detection_thread.start()
        self.log_message("开始检测...")
        self.statusBar().showMessage("正在检测中...")
    
    def pause_detection(self):
        """暂停检测"""
        if self.detection_thread and self.detection_thread.is_running:
            if self.detection_thread.is_paused:
                self.detection_thread.resume()
                self.pause_btn.setText("⏸ 暂停检测")
                self.log_message("检测已恢复")
            else:
                self.detection_thread.pause()
                self.pause_btn.setText("▶ 继续检测")
                self.log_message("检测已暂停")
    
    def stop_detection(self):
        """停止检测"""
        if self.detection_thread and self.detection_thread.is_running:
            self.detection_thread.stop()
            self.detection_thread.wait()
            self.on_detection_finished()
    
    def on_detection_result(self, original_img, result_img, inference_time, 
                           confidences, xyxy_coords, xyxyn_coords):
        """检测结果回调"""
        # 显示图像
        self.display_image(original_img, self.original_label)
        self.display_image(result_img, self.result_label)
        
        # 更新日志 - 优化输出格式
        if self.current_source_type == 'image':
            # 图片检测只输出一次详细信息
            self.log_message(f"推理耗时: {inference_time:.3f}秒")
            if confidences:
                self.log_message(f"检测到 {len(confidences)} 个目标")
                for i, (conf, xyxy, xyxyn) in enumerate(zip(confidences, xyxy_coords, xyxyn_coords)):
                    self.log_message(f"目标 {i+1}: 置信度={conf:.3f}, xyxy={xyxy}, xyxyn={xyxyn}")
            else:
                self.log_message("未检测到目标")
        else:
            # 视频/摄像头检测减少日志输出频率
            # 只在检测到目标或每30帧输出一次日志
            if not hasattr(self, '_frame_count'):
                self._frame_count = 0
            self._frame_count += 1
            
            if confidences or self._frame_count % 30 == 0:
                if confidences:
                    self.log_message(f"检测到 {len(confidences)} 个目标 (耗时: {inference_time:.3f}秒)")
                else:
                    self.log_message(f"未检测到目标 (耗时: {inference_time:.3f}秒)")
    
    def on_detection_finished(self):
        """检测完成回调"""
        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ 暂停检测")
        self.stop_btn.setEnabled(False)
        self.source_combo.setEnabled(True)
        self.select_file_btn.setEnabled(self.current_source_type in ["image", "video"])
        
        # 重置进度条
        self.progress_bar.setValue(0)
        
        # 避免重复输出检测完成消息
        if not self.detection_completed:
            self.detection_completed = True
            self.log_message("检测完成")
            self.statusBar().showMessage("检测完成")
            
            # # 检测完成后清空显示窗口，准备下一次检测
            # if self.current_source_type in ["image", "video"]:
            #     self.clear_display_windows()
    
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
        
        # 限制日志行数，避免内存占用过多
        max_lines = 1000
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > max_lines:
            # 保留最后500行
            keep_lines = lines[-500:]
            self.log_text.setPlainText('\n'.join(keep_lines))
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.log_message("日志已清除")
    
    def create_icon(self):
        """创建应用图标"""
        from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
        
        # 创建一个简单的头盔图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 255, 255))  # 背景
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制头盔形状 - 更圆润的设计
        painter.setPen(QColor(255, 193, 7))  # 黄色边框
        painter.setBrush(QColor(255, 193, 7))  # 黄色填充
        
        # 头盔主体（更圆润的椭圆形）
        painter.drawEllipse(10, 18, 44, 32)
        
        # 头盔底部（圆角矩形）
        painter.drawRoundedRect(12, 42, 40, 10, 5, 5)
        
        # 添加文字 - 白色且更大
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))  # 白色文字
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "HD")
        
        painter.end()
        
        return QIcon(pixmap)


def main():
    app = QApplication(sys.argv)
    window = HelmetDetectionUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 