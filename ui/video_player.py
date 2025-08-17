#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频播放器组件
支持视频播放、骨骼点显示、播放控制等功能
"""

import cv2
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Signal, QThread, QSize, Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor


class VideoPlayerWidget(QWidget):
    """视频播放器组件"""
    
    # 信号定义
    frame_changed = Signal(int)  # 帧数变化
    playback_finished = Signal()  # 播放完成
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_capture = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.is_playing_flag = False
        self.playback_speed = 1.0
        self.keypoints_data = []
        self.video_loaded = False
        
        # 骨骼连接定义（COCO格式）
        self.skeleton_connections = [
            # 躯干
            (5, 6),   # 左肩-右肩
            (5, 11),  # 左肩-左髋
            (6, 12),  # 右肩-右髋
            (11, 12), # 左髋-右髋
            
            # 左臂
            (5, 7),   # 左肩-左肘
            (7, 9),   # 左肘-左腕
            
            # 右臂
            (6, 8),   # 右肩-右肘
            (8, 10),  # 右肘-右腕
            
            # 左腿
            (11, 13), # 左髋-左膝
            (13, 15), # 左膝-左踝
            
            # 右腿
            (12, 14), # 右髋-右膝
            (14, 16), # 右膝-右踝
            
            # 头部
            (0, 1),   # 鼻子-左眼
            (0, 2),   # 鼻子-右眼
            (1, 3),   # 左眼-左耳
            (2, 4),   # 右眼-右耳
        ]
        
        # 关键点颜色定义
        self.keypoint_colors = [
            (255, 0, 0),    # 0: 鼻子 - 红色
            (255, 85, 0),   # 1: 左眼 - 橙红
            (255, 170, 0),  # 2: 右眼 - 橙色
            (255, 255, 0),  # 3: 左耳 - 黄色
            (170, 255, 0),  # 4: 右耳 - 黄绿
            (85, 255, 0),   # 5: 左肩 - 绿色
            (0, 255, 0),    # 6: 右肩 - 纯绿
            (0, 255, 85),   # 7: 左肘 - 青绿
            (0, 255, 170),  # 8: 右肘 - 青色
            (0, 255, 255),  # 9: 左腕 - 青蓝
            (0, 170, 255),  # 10: 右腕 - 蓝色
            (0, 85, 255),   # 11: 左髋 - 深蓝
            (0, 0, 255),    # 12: 右髋 - 纯蓝
            (85, 0, 255),   # 13: 左膝 - 蓝紫
            (170, 0, 255),  # 14: 右膝 - 紫色
            (255, 0, 255),  # 15: 左踝 - 洋红
            (255, 0, 170),  # 16: 右踝 - 粉红
        ]
        
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:1 #2a2a2a);
                color: #888888;
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        self.video_label.setText("请选择视频文件")
        self.video_label.setMinimumSize(640, 480)
        layout.addWidget(self.video_label)
        
        # 视频信息标签
        self.info_label = QLabel("视频信息: 未加载")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10pt;
                padding: 5px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.info_label)
    
    def setup_timer(self):
        """设置播放定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
    
    def load_video(self, video_path):
        """加载视频文件"""
        try:
            # 释放之前的视频
            if self.video_capture:
                self.video_capture.release()
            
            # 打开新视频
            self.video_capture = cv2.VideoCapture(video_path)
            
            if not self.video_capture.isOpened():
                raise Exception("无法打开视频文件")
            
            # 获取视频信息
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 更新状态
            self.current_frame = 0
            self.video_loaded = True
            
            # 更新信息显示
            duration = self.total_frames / self.fps if self.fps > 0 else 0
            self.info_label.setText(
                f"视频信息: {width}x{height} | {self.total_frames}帧 | "
                f"{self.fps:.2f}fps | 时长: {duration:.2f}s"
            )
            
            # 显示第一帧
            self.seek_to_frame(0)
            
        except Exception as e:
            self.video_loaded = False
            self.video_label.setText(f"加载视频失败: {str(e)}")
            raise e
    
    def set_keypoints_data(self, keypoints_data):
        """设置关键点数据"""
        self.keypoints_data = keypoints_data
        # 重新显示当前帧
        if self.video_loaded:
            self.display_current_frame()
    
    def seek_to_frame(self, frame_number):
        """跳转到指定帧"""
        if not self.video_loaded:
            return
        
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        if frame_number != self.current_frame:
            self.current_frame = frame_number
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.display_current_frame()
            self.frame_changed.emit(frame_number)
    
    def display_current_frame(self):
        """显示当前帧"""
        if not self.video_loaded:
            return
        
        ret, frame = self.video_capture.read()
        if not ret:
            return
        
        # 绘制骨骼点
        if self.keypoints_data and self.current_frame < len(self.keypoints_data):
            frame = self.draw_keypoints(frame, self.keypoints_data[self.current_frame])
        
        # 转换为Qt格式并显示
        self.display_frame(frame)
    
    def draw_keypoints(self, frame, keypoints):
        """在帧上绘制骨骼点"""
        if not keypoints:
            return frame
        
        # 复制帧以避免修改原始数据
        result_frame = frame.copy()
        
        # 绘制骨骼连接线
        for connection in self.skeleton_connections:
            pt1_idx, pt2_idx = connection
            
            if (pt1_idx < len(keypoints) and pt2_idx < len(keypoints) and
                len(keypoints[pt1_idx]) >= 3 and len(keypoints[pt2_idx]) >= 3):
                
                x1, y1, conf1 = keypoints[pt1_idx][:3]
                x2, y2, conf2 = keypoints[pt2_idx][:3]
                
                # 只有当两个点的置信度都足够高时才绘制连接线
                if conf1 > 0.5 and conf2 > 0.5:
                    cv2.line(result_frame, (int(x1), int(y1)), (int(x2), int(y2)), 
                            (0, 255, 0), 2)
        
        # 绘制关键点
        for i, keypoint in enumerate(keypoints):
            if len(keypoint) >= 3:
                x, y, conf = keypoint[:3]
                
                if conf > 0.5:  # 只绘制置信度高的点
                    color = self.keypoint_colors[i % len(self.keypoint_colors)]
                    # 绘制外圆
                    cv2.circle(result_frame, (int(x), int(y)), 6, color, -1)
                    # 绘制内圆
                    cv2.circle(result_frame, (int(x), int(y)), 4, (255, 255, 255), -1)
                    # 绘制中心点
                    cv2.circle(result_frame, (int(x), int(y)), 2, color, -1)
        
        return result_frame
    
    def display_frame(self, frame):
        """显示帧到标签"""
        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 获取标签大小
        label_size = self.video_label.size()
        
        # 计算缩放比例，保持宽高比
        h, w, ch = rgb_frame.shape
        scale_w = label_size.width() / w
        scale_h = label_size.height() / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 缩放图像
        resized_frame = cv2.resize(rgb_frame, (new_w, new_h))
        
        # 转换为QImage
        bytes_per_line = 3 * new_w
        q_image = QImage(resized_frame.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
        
        # 转换为QPixmap并显示
        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)
    
    def play(self):
        """开始播放"""
        if self.video_loaded and not self.is_playing_flag:
            self.is_playing_flag = True
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.start(interval)
    
    def pause(self):
        """暂停播放"""
        if self.is_playing_flag:
            self.is_playing_flag = False
            self.timer.stop()
    
    def stop(self):
        """停止播放"""
        if self.timer.isActive():
            self.timer.stop()
        
        self.is_playing_flag = False
        self.seek_to_frame(0)
    
    def next_frame(self):
        """播放下一帧"""
        if not self.video_loaded:
            return
        
        if self.current_frame < self.total_frames - 1:
            self.seek_to_frame(self.current_frame + 1)
        else:
            # 播放完成
            self.pause()
            self.playback_finished.emit()
    
    def set_playback_speed(self, speed):
        """设置播放速度"""
        self.playback_speed = speed
        
        # 如果正在播放，更新定时器间隔
        if self.is_playing_flag:
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.setInterval(interval)
    
    def is_playing(self):
        """检查是否正在播放"""
        return self.is_playing_flag
    
    def get_frame_count(self):
        """获取总帧数"""
        return self.total_frames
    
    def get_fps(self):
        """获取帧率"""
        return self.fps
    
    def get_current_frame(self):
        """获取当前帧号"""
        return self.current_frame
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.video_capture:
            self.video_capture.release()
        event.accept()