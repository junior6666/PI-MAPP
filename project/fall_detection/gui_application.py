"""
摔倒检测GUI应用程序
集成所有功能模块的图形界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import os
from typing import Optional, Dict, Any
import json

# 导入自定义模块
from pose_detection import PoseDetector, resize_pose
from fall_detection_algorithms import (
    ThresholdFallDetector, 
    TraditionalMLFallDetector, 
    DeepLearningFallDetector
)
from alert_system import AlertManager, AlertConfig

class FallDetectionGUI:
    """摔倒检测GUI应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("摔倒检测系统")
        self.root.geometry("1300x900")
        self.root.configure(bg='#f0f0f0')
        
        # 新增：顶部信息栏变量
        self.source_type = tk.StringVar(value="未加载")
        self.frame_status = tk.StringVar(value="未检测")
        self.detect_speed = tk.StringVar(value="-")
        self.current_algorithm = tk.StringVar(value="阈值法")
        self.frame_index = 0
        self.total_frames = 0
        self.is_paused = False
        self.is_video_playing = False
        
        # 性能优化变量
        self.skip_frames = 0  # 跳帧计数
        self.last_detection_time = 0
        self.detection_interval = 0.05  # 检测间隔（秒）
        self.last_poses = None  # 缓存上一帧的检测结果
        
        # 显示质量设置
        self.max_display_width = 640
        self.max_display_height = 480
        
        # 初始化组件
        self.pose_detector = PoseDetector()
        self.threshold_detector = ThresholdFallDetector()
        self.ml_detector = TraditionalMLFallDetector('svm')
        self.dl_detector = DeepLearningFallDetector('lstm')
        self.alert_manager = AlertManager()
        self.alert_config = AlertConfig()
        
        self.video_capture = None
        self.current_frame = None
        self.current_processed_frame = None
        self.pose_sequence = []
        self.current_detection_results = {
            'threshold': {'is_fall': False, 'confidence': 0.0},
            'ml': {'is_fall': False, 'confidence': 0.0},
            'dl': {'is_fall': False, 'confidence': 0.0}
        }
        
        self.create_widgets()
        self.load_config()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 顶部信息栏 - 美化设计，一行显示
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 使用LabelFrame包装状态信息
        status_frame = ttk.LabelFrame(info_frame, text="系统状态", padding=8)
        status_frame.pack(fill=tk.X)
        
        # 一行显示所有状态信息
        status_row = ttk.Frame(status_frame)
        status_row.pack(fill=tk.X, pady=2)
        
        # 输入源
        source_frame = ttk.Frame(status_row)
        source_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(source_frame, text="📹 输入源:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        source_label = ttk.Label(source_frame, textvariable=self.source_type, 
                               font=('Arial', 9), foreground='#0066cc', width=8)
        source_label.pack(side=tk.LEFT, padx=5)
        
        # 检测状态
        status_frame_inner = ttk.Frame(status_row)
        status_frame_inner.pack(side=tk.LEFT, padx=10)
        ttk.Label(status_frame_inner, text="🔍 检测状态:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame_inner, textvariable=self.frame_status, 
                               font=('Arial', 9), foreground='#cc6600', width=8)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # 检测速率
        speed_frame = ttk.Frame(status_row)
        speed_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(speed_frame, text="⚡ 检测速率:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        speed_label = ttk.Label(speed_frame, textvariable=self.detect_speed, 
                              font=('Arial', 9), foreground='#009900', width=8)
        speed_label.pack(side=tk.LEFT, padx=5)
        
        # 算法
        algo_frame = ttk.Frame(status_row)
        algo_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(algo_frame, text="🧠 算法:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        algo_label = ttk.Label(algo_frame, textvariable=self.current_algorithm, 
                             font=('Arial', 9), foreground='#990099', width=8)
        algo_label.pack(side=tk.LEFT, padx=5)
        
        # 帧信息
        frame_frame = ttk.Frame(status_row)
        frame_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(frame_frame, text="📊 帧:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.frame_info_label = ttk.Label(frame_frame, text="0/0", 
                                        font=('Arial', 9), foreground='#666666', width=10)
        self.frame_info_label.pack(side=tk.LEFT, padx=5)
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        self.create_control_panel(main_frame)
        
        # 右侧显示面板
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 视频显示区域（双窗口）
        video_frame = ttk.LabelFrame(display_frame, text="视频显示", padding=5)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        video_inner_frame = ttk.Frame(video_frame)
        video_inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # 原图窗口
        original_frame = ttk.Frame(video_inner_frame)
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(original_frame, text="原图/原视频", font=('Arial', 10, 'bold')).pack()
        self.original_video_label = ttk.Label(original_frame, text="请加载图片或视频")
        self.original_video_label.pack(fill=tk.BOTH, expand=True)
        
        # 检测后窗口
        processed_frame = ttk.Frame(video_inner_frame)
        processed_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(processed_frame, text="检测后", font=('Arial', 10, 'bold')).pack()
        self.processed_video_label = ttk.Label(processed_frame, text="请加载图片或视频")
        self.processed_video_label.pack(fill=tk.BOTH, expand=True)
        
        # 进度条和暂停按钮
        progress_frame = ttk.Frame(video_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(progress_frame, variable=self.progress_var, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_progress_change)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.pause_button = ttk.Button(progress_frame, text="暂停", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # 系统日志区域（移到视频显示下方）
        log_frame = ttk.LabelFrame(display_frame, text="📝 系统日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志工具栏
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(log_toolbar, text="🗑️ 清空日志", command=self.clear_log, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_toolbar, text="💾 保存日志", command=self.save_log, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_toolbar, text="📋 复制日志", command=self.copy_log, width=10).pack(side=tk.LEFT, padx=2)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=50, 
                                                font=('Consolas', 9), 
                                                bg='#f8f8f8', fg='#333333')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置日志标签颜色
        self.log_text.tag_configure("INFO", foreground="#0066cc")
        self.log_text.tag_configure("SUCCESS", foreground="#009900")
        self.log_text.tag_configure("WARNING", foreground="#cc6600")
        self.log_text.tag_configure("ERROR", foreground="#cc0000")
        
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 输入源选择区域
        input_frame = ttk.LabelFrame(control_frame, text="📁 输入源选择", padding=5)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(input_frame, text="🖼️ 加载图片", command=self.load_image).pack(fill=tk.X, pady=2)
        ttk.Button(input_frame, text="🎬 加载视频", command=self.load_video).pack(fill=tk.X, pady=2)
        ttk.Button(input_frame, text="📹 打开摄像头", command=self.open_camera).pack(fill=tk.X, pady=2)
        
        # 检测算法选择
        algo_frame = ttk.LabelFrame(control_frame, text="🧠 检测算法", padding=5)
        algo_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.algorithm_var = tk.StringVar(value="threshold")
        ttk.Radiobutton(algo_frame, text="阈值法", variable=self.algorithm_var, 
                       value="threshold").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="机器学习", variable=self.algorithm_var, 
                       value="ml").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="深度学习", variable=self.algorithm_var, 
                       value="dl").pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="全部算法", variable=self.algorithm_var, 
                       value="all").pack(anchor=tk.W)
        
        # 检测控制
        detect_frame = ttk.LabelFrame(control_frame, text="⚙️ 检测控制", padding=5)
        detect_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(detect_frame, text="▶️ 开始检测", command=self.start_detection).pack(fill=tk.X, pady=2)
        ttk.Button(detect_frame, text="⏹️ 停止检测", command=self.stop_detection).pack(fill=tk.X, pady=2)
        ttk.Button(detect_frame, text="🔍 单帧检测", command=self.single_frame_detection).pack(fill=tk.X, pady=2)
        
        # 预警设置
        alert_frame = ttk.LabelFrame(control_frame, text="🚨 预警设置", padding=5)
        alert_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(alert_frame, text="⚙️ 配置预警", command=self.configure_alerts).pack(fill=tk.X, pady=2)
        ttk.Button(alert_frame, text="🧪 测试预警", command=self.test_alerts).pack(fill=tk.X, pady=2)
        ttk.Button(alert_frame, text="📋 查看历史", command=self.view_alert_history).pack(fill=tk.X, pady=2)
        
        # 模型管理
        model_frame = ttk.LabelFrame(control_frame, text="🤖 模型管理", padding=5)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(model_frame, text="🎯 训练模型", command=self.train_models).pack(fill=tk.X, pady=2)
        ttk.Button(model_frame, text="📂 加载模型", command=self.load_models).pack(fill=tk.X, pady=2)
        ttk.Button(model_frame, text="💾 保存模型", command=self.save_models).pack(fill=tk.X, pady=2)
        
        # 设置和保存
        settings_frame = ttk.LabelFrame(control_frame, text="⚙️ 系统设置", padding=5)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(settings_frame, text="🔧 参数设置", command=self.open_settings).pack(fill=tk.X, pady=2)
        ttk.Button(settings_frame, text="💾 保存配置", command=self.save_config).pack(fill=tk.X, pady=2)
        ttk.Button(settings_frame, text="📖 关于", command=self.show_about).pack(fill=tk.X, pady=2)
        
    def create_display_panel(self, parent):
        """创建右侧显示面板"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 视频显示区域
        video_frame = ttk.LabelFrame(display_frame, text="视频显示", padding=5)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.video_label = ttk.Label(video_frame, text="请加载图片或视频")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # 检测结果显示
        result_frame = ttk.LabelFrame(display_frame, text="检测结果", padding=5)
        result_frame.pack(fill=tk.X)
        
        # 创建结果显示区域
        # self.create_result_display(result_frame) # 删除此行
        

        
    def log_message(self, message: str, level: str = "INFO"):
        """添加日志消息 - 支持不同级别"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空", "INFO")
        
    def save_log(self):
        """保存日志到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                title="保存日志",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"日志已保存到: {filename}", "SUCCESS")
        except Exception as e:
            self.log_message(f"保存日志失败: {e}", "ERROR")
            
    def copy_log(self):
        """复制日志到剪贴板"""
        try:
            log_content = self.log_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.log_message("日志已复制到剪贴板", "SUCCESS")
        except Exception as e:
            self.log_message(f"复制日志失败: {e}", "ERROR")

    def display_frame(self, frame, processed_frame=None, poses=None):
        """显示原始帧和检测后帧 - 支持最大尺寸限制和骨骼点坐标同步缩放"""
        if frame is None:
            return
        max_width = self.max_display_width
        max_height = self.max_display_height
        height, width = frame.shape[:2]
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame_display = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            poses_display = resize_pose(poses, scale, scale) if poses is not None else None
            if poses_display is not None:
                processed_display = self.pose_detector.draw_pose(frame_display, poses_display, draw_keypoints=True, draw_skeleton=True, draw_bbox=True)
            elif processed_frame is not None:
                processed_display = cv2.resize(processed_frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            else:
                processed_display = None
        else:
            frame_display = frame
            poses_display = poses
            if poses_display is not None:
                processed_display = self.pose_detector.draw_pose(frame_display, poses_display, draw_keypoints=True, draw_skeleton=True, draw_bbox=True)
            else:
                processed_display = processed_frame
        # 原图
        frame_rgb = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(pil_image)
        self.original_video_label.configure(image=photo, text="")
        self.original_video_label.image = photo
        # 检测后图
        if processed_display is not None:
            processed_rgb = cv2.cvtColor(processed_display, cv2.COLOR_BGR2RGB)
            pil_processed = Image.fromarray(processed_rgb)
            photo2 = ImageTk.PhotoImage(pil_processed)
            self.processed_video_label.configure(image=photo2, text="")
            self.processed_video_label.image = photo2
        else:
            self.processed_video_label.configure(image="", text="无检测结果")
            self.processed_video_label.image = None

    def play_video(self):
        """播放视频，支持暂停/进度条/检测显示"""
        if self.video_capture is None:
            return
        
        self.is_video_playing = True
        self.is_paused = False
        self.pause_button.config(text="暂停")
        self.frame_index = 0
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progress_bar.config(to=max(1, self.total_frames-1))
        self.frame_info_label.config(text=f"0/{self.total_frames}")
        self.source_type.set("视频")
        
        def video_loop():
            frame_count = 0
            fps_start_time = time.time()
            last_detection_time = 0
            
            while self.is_video_playing:
                if self.is_paused:
                    time.sleep(0.01)
                    continue
                
                ret, frame = self.video_capture.read()
                if not ret:
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.frame_index = 0
                    frame_count = 0
                    fps_start_time = time.time()
                    last_detection_time = 0
                    continue
                
                self.frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                self.frame_info_label.config(text=f"{self.frame_index}/{self.total_frames}")
                self.progress_var.set(self.frame_index)
                self.current_frame = frame
                
                current_time = time.time()
                
                # 智能检测：每隔一定时间进行一次完整检测
                if current_time - last_detection_time > self.detection_interval:
                    # 完整检测
                    t0 = time.time()
                    processed, status, poses = self.detect_and_draw(frame, return_poses=True)
                    t1 = time.time()
                    last_detection_time = current_time
                    
                    # 计算FPS（每30帧更新一次）
                    frame_count += 1
                    if frame_count % 30 == 0:
                        current_fps_time = time.time()
                        fps = 30.0 / (current_fps_time - fps_start_time)
                        self.detect_speed.set(f"{fps:.1f} fps")
                        fps_start_time = current_fps_time
                    
                    self.frame_status.set(status)
                    self.display_frame(frame, None, poses=poses)
                else:
                    # 使用缓存的检测结果，只更新显示
                    if self.last_poses is not None:
                        self.display_frame(frame, None, poses=self.last_poses)
                    else:
                        self.display_frame(frame, frame)
                
                # 控制帧率 - 目标25fps
                elapsed = time.time() - current_time
                target_delay = 1.0 / 25.0
                if elapsed < target_delay:
                    time.sleep(target_delay - elapsed)
        
        threading.Thread(target=video_loop, daemon=True).start()

    def detect_and_draw(self, frame, return_poses=False):
        """检测并返回检测后图像和状态"""
        # 降低检测分辨率以提高速度
        height, width = frame.shape[:2]
        if width > 640:  # 限制检测分辨率
            scale = 640.0 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            detect_frame = cv2.resize(frame, (new_width, new_height))
        else:
            detect_frame = frame.copy()
        
        poses = self.pose_detector.detect_pose(detect_frame)
        
        # 缓存检测结果
        self.last_poses = poses
        
        if not poses:
            return frame, "未识别到骨骼点"
        
        # 选择算法
        algo = self.algorithm_var.get()
        self.current_algorithm.set({"threshold":"阈值法","ml":"机器学习","dl":"深度学习","all":"全部"}.get(algo, algo))
        
        status = "正常"
        
        # 快速检测逻辑
        if algo in ["threshold", "all"]:
            for pose in poses:
                is_fall, confidence, _ = self.threshold_detector.detect_fall(pose)
                if is_fall:
                    status = "摔倒"
                    break  # 找到摔倒就停止
        
        # 绘制骨架（使用原始分辨率）
        processed = self.pose_detector.draw_pose(frame, poses, draw_keypoints=True, draw_skeleton=True, draw_bbox=True)
        
        if return_poses:
            return processed, status, poses
        return processed, status

    def update_detection_interval(self, value):
        """更新检测间隔"""
        self.detection_interval = float(value)
        self.log_message(f"检测间隔已更新为: {self.detection_interval:.3f}秒")

    def update_display_quality(self, event=None):
        """更新显示质量"""
        quality = self.display_quality_var.get()
        if quality == "低":
            self.max_display_width = 240
            self.max_display_height = 180
        elif quality == "中等":
            self.max_display_width = 320
            self.max_display_height = 240
        else:  # 高
            self.max_display_width = 480
            self.max_display_height = 360
        
        self.log_message(f"显示质量已更新为: {quality}")

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="继续" if self.is_paused else "暂停")

    def on_progress_change(self, val):
        if self.video_capture is not None and self.total_frames>0:
            idx = int(float(val))
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, idx)
            self.frame_index = idx

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.source_type.set("图片")
            self.current_frame = cv2.imread(file_path)
            t0 = time.time()
            processed, status, poses = self.detect_and_draw(self.current_frame, return_poses=True)
            t1 = time.time()
            self.detect_speed.set(f"{(t1-t0)*1000:.1f} ms")
            self.frame_status.set(status)
            self.display_frame(self.current_frame, None, poses=poses)
            self.frame_info_label.config(text="1/1")
            self.progress_var.set(0)
            self.log_message(f"已加载图片: {file_path}", "SUCCESS")

    def load_video(self):
        file_path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv")]
        )
        if file_path:
            if self.video_capture is not None:
                self.video_capture.release()
            self.video_capture = cv2.VideoCapture(file_path)
            self.source_type.set("视频")
            self.play_video()
            self.log_message(f"已加载视频: {file_path}", "SUCCESS")

    def open_camera(self):
        if self.video_capture is not None:
            self.video_capture.release()
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            self.log_message("无法打开摄像头，请检查设备连接", "ERROR")
            return
        self.source_type.set("摄像头")
        self.play_video()
        self.log_message("摄像头已启动", "SUCCESS")
        
    def stop_detection(self):
        """停止检测"""
        self.is_video_playing = False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        
        # 清空视频窗口显示
        self.original_video_label.configure(image="", text="请加载图片或视频")
        self.original_video_label.image = None
        self.processed_video_label.configure(image="", text="请加载图片或视频")
        self.processed_video_label.image = None
        
        # 重置状态信息
        self.source_type.set("未加载")
        self.frame_status.set("未检测")
        self.detect_speed.set("-")
        self.frame_info_label.config(text="0/0")
        self.progress_var.set(0)
        
        # 清空当前帧
        self.current_frame = None
        self.current_processed_frame = None
        self.last_poses = None
        
        self.log_message("已停止检测", "INFO")
        
    def start_detection(self):
        """开始检测"""
        if self.current_frame is None:
            messagebox.showwarning("警告", "请先加载图片或视频")
            return
        
        self.log_message("开始检测...")
        
        # 在新线程中运行检测
        def detection_thread():
            try:
                # 姿势检测
                poses = self.pose_detector.detect_pose(self.current_frame)
                
                if not poses:
                    self.log_message("未检测到人体姿势")
                    return
                
                # 更新姿势序列（用于深度学习）
                self.pose_sequence.append(poses)
                if len(self.pose_sequence) > 10:  # 保持最近10帧
                    self.pose_sequence.pop(0)
                
                # 根据选择的算法进行检测
                algorithm = self.algorithm_var.get()
                
                if algorithm in ["threshold", "all"]:
                    # 阈值法检测
                    for pose in poses:
                        is_fall, confidence, features = self.threshold_detector.detect_fall(pose)
                        self.current_detection_results['threshold'] = {
                            'is_fall': is_fall,
                            'confidence': confidence
                        }
                
                if algorithm in ["ml", "all"]:
                    # 机器学习检测
                    if self.ml_detector.is_trained:
                        predictions, probabilities = self.ml_detector.predict(poses)
                        if predictions:
                            self.current_detection_results['ml'] = {
                                'is_fall': predictions[0],
                                'confidence': probabilities[0]
                            }
                
                if algorithm in ["dl", "all"]:
                    # 深度学习检测
                    if self.dl_detector.is_trained and len(self.pose_sequence) >= 10:
                        is_fall, confidence = self.dl_detector.predict(self.pose_sequence)
                        self.current_detection_results['dl'] = {
                            'is_fall': is_fall,
                            'confidence': confidence
                        }
                
                # 更新显示
                # self.update_result_display() # 删除此行
                
                # 检查是否需要发送预警
                self.check_and_send_alert()
                
                self.log_message("检测完成")
                
            except Exception as e:
                self.log_message(f"检测失败: {e}")
        
        detection_thread = threading.Thread(target=detection_thread, daemon=True)
        detection_thread.start()
        
    def single_frame_detection(self):
        """单帧检测"""
        if self.current_frame is None:
            messagebox.showwarning("警告", "请先加载图片或视频")
            return
        
        self.start_detection()
        
    # def update_result_display(self): # 删除此行
    #     """更新结果显示""" # 删除此行
    #     # 更新阈值法结果 # 删除此行
    #     threshold_result = self.current_detection_results['threshold'] # 删除此行
    #     status_text = "摔倒" if threshold_result['is_fall'] else "正常" # 删除此行
    #     color = "red" if threshold_result['is_fall'] else "green" # 删除此行
        
    #     self.threshold_result_label.configure( # 删除此行
    #         text=status_text, # 删除此行
    #         foreground=color # 删除此行
    #     ) # 删除此行
    #     self.threshold_confidence_label.configure( # 删除此行
    #         text=f"置信度: {threshold_result['confidence']:.2f}" # 删除此行
    #     ) # 删除此行
        
    #     # 更新机器学习结果 # 删除此行
    #     ml_result = self.current_detection_results['ml'] # 删除此行
    #     status_text = "摔倒" if ml_result['is_fall'] else "正常" # 删除此行
    #     color = "red" if ml_result['is_fall'] else "green" # 删除此行
        
    #     self.ml_result_label.configure( # 删除此行
    #         text=status_text, # 删除此行
    #         foreground=color # 删除此行
    #     ) # 删除此行
    #     self.ml_confidence_label.configure( # 删除此行
    #         text=f"置信度: {ml_result['confidence']:.2f}" # 删除此行
    #     ) # 删除此行
        
    #     # 更新深度学习结果 # 删除此行
    #     dl_result = self.current_detection_results['dl'] # 删除此行
    #     status_text = "摔倒" if dl_result['is_fall'] else "正常" # 删除此行
    #     color = "red" if dl_result['is_fall'] else "green" # 删除此行
        
    #     self.dl_result_label.configure( # 删除此行
    #         text=status_text, # 删除此行
    #         foreground=color # 删除此行
    #     ) # 删除此行
    #     self.dl_confidence_label.configure( # 删除此行
    #         text=f"置信度: {dl_result['confidence']:.2f}" # 删除此行
    #     ) # 删除此行
        
    def check_and_send_alert(self):
        """检查并发送预警"""
        # 检查是否有任何算法检测到摔倒
        any_fall_detected = any(
            result['is_fall'] for result in self.current_detection_results.values()
        )
        
        if any_fall_detected:
            # 计算平均置信度
            confidences = [
                result['confidence'] for result in self.current_detection_results.values()
                if result['is_fall']
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # 发送预警
            self.alert_manager.send_fall_alert(avg_confidence, self.current_frame)
            self.log_message(f"检测到摔倒！已发送预警，置信度: {avg_confidence:.2f}")
            
    def configure_alerts(self):
        """配置预警"""
        # 创建预警配置窗口
        config_window = tk.Toplevel(self.root)
        config_window.title("预警配置")
        config_window.geometry("500x400")
        
        # 邮箱配置
        email_frame = ttk.LabelFrame(config_window, text="邮箱配置", padding=10)
        email_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(email_frame, text="SMTP服务器:").grid(row=0, column=0, sticky=tk.W)
        smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        ttk.Entry(email_frame, textvariable=smtp_server_var).grid(row=0, column=1, sticky=tk.EW)
        
        ttk.Label(email_frame, text="端口:").grid(row=1, column=0, sticky=tk.W)
        smtp_port_var = tk.StringVar(value="587")
        ttk.Entry(email_frame, textvariable=smtp_port_var).grid(row=1, column=1, sticky=tk.EW)
        
        ttk.Label(email_frame, text="发送邮箱:").grid(row=2, column=0, sticky=tk.W)
        sender_email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=sender_email_var).grid(row=2, column=1, sticky=tk.EW)
        
        ttk.Label(email_frame, text="密码:").grid(row=3, column=0, sticky=tk.W)
        sender_password_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=sender_password_var, show="*").grid(row=3, column=1, sticky=tk.EW)
        
        ttk.Label(email_frame, text="接收邮箱:").grid(row=4, column=0, sticky=tk.W)
        recipient_email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=recipient_email_var).grid(row=4, column=1, sticky=tk.EW)
        
        # 保存按钮
        def save_email_config():
            try:
                self.alert_manager.add_email_alert(
                    sender_email_var.get(),
                    sender_password_var.get(),
                    [recipient_email_var.get()]
                )
                messagebox.showinfo("成功", "邮箱配置已保存")
                config_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {e}")
        
        ttk.Button(config_window, text="保存邮箱配置", command=save_email_config).pack(pady=10)
        
    def test_alerts(self):
        """测试预警"""
        try:
            results = self.alert_manager.test_all_connections()
            if results:
                message = "预警测试结果:\n"
                for method, success in results.items():
                    status = "成功" if success else "失败"
                    message += f"{method}: {status}\n"
                messagebox.showinfo("测试结果", message)
            else:
                messagebox.showwarning("警告", "未配置任何预警方式")
        except Exception as e:
            messagebox.showerror("错误", f"测试失败: {e}")
            
    def view_alert_history(self):
        """查看预警历史"""
        history = self.alert_manager.get_all_alert_history()
        
        if not history:
            messagebox.showinfo("历史记录", "暂无预警历史")
            return
        
        # 创建历史记录窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("预警历史")
        history_window.geometry("600x400")
        
        # 创建表格
        columns = ("时间", "类型", "消息", "状态")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # 添加数据
        for record in history:
            status = "成功" if record['success'] else "失败"
            tree.insert("", tk.END, values=(
                record['timestamp'][:19],  # 只显示到秒
                record['type'],
                record['message'][:30] + "..." if len(record['message']) > 30 else record['message'],
                status
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def train_models(self):
        """训练模型"""
        messagebox.showinfo("训练模型", "模型训练功能需要训练数据，请准备数据集后使用")
        
    def load_models(self):
        """加载模型"""
        try:
            # 加载机器学习模型
            if os.path.exists("ml_model.pkl"):
                self.ml_detector.load_model("ml_model.pkl")
                self.log_message("机器学习模型加载成功")
            
            # 加载深度学习模型
            if os.path.exists("dl_model.pth"):
                self.dl_detector.load_model("dl_model.pth")
                self.log_message("深度学习模型加载成功")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载模型失败: {e}")
            
    def save_models(self):
        """保存模型"""
        try:
            if self.ml_detector.is_trained:
                self.ml_detector.save_model("ml_model.pkl")
                self.log_message("机器学习模型保存成功")
            
            if self.dl_detector.is_trained:
                self.dl_detector.save_model("dl_model.pth")
                self.log_message("深度学习模型保存成功")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存模型失败: {e}")
            
    def save_config(self):
        """保存当前配置"""
        try:
            config = {
                'algorithm': self.algorithm_var.get(),
                'detection_interval': self.detection_interval,
                'display_quality': self.display_quality_var.get() if hasattr(self, 'display_quality_var') else '中等',
                'alert_settings': {
                    'email_enabled': True,
                    'sms_enabled': False
                }
            }
            
            filename = filedialog.asksaveasfilename(
                title="保存配置",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self.log_message(f"配置已保存到: {filename}", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"保存配置失败: {e}", "ERROR")

    def open_settings(self):
        """打开设置窗口 - 优化设计，增加阈值法参数和YOLO权重选择"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("系统设置")
        settings_window.geometry("520x700")
        settings_window.resizable(False, False)
        
        # 设置主框架
        main_settings_frame = ttk.Frame(settings_window, padding=10)
        main_settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # 检测设置
        detect_settings = ttk.LabelFrame(main_settings_frame, text="🔍 检测设置", padding=10)
        detect_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 检测间隔设置
        ttk.Label(detect_settings, text="检测间隔 (秒):").grid(row=0, column=0, sticky=tk.W)
        interval_var = tk.DoubleVar(value=self.detection_interval)
        interval_scale = ttk.Scale(detect_settings, variable=interval_var, from_=0.01, to=0.2, orient=tk.HORIZONTAL)
        interval_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(detect_settings, textvariable=interval_var, width=6).grid(row=0, column=2, sticky=tk.W)
        
        # YOLO骨骼检测模型权重选择
        ttk.Label(detect_settings, text="YOLO骨骼模型权重:").grid(row=1, column=0, sticky=tk.W)
        yolo_weights = ["yolov8n-pose.pt", "yolo11x-pose.pt"]
        yolo_weight_var = tk.StringVar(value=self.pose_detector.model_path if hasattr(self.pose_detector, 'model_path') else yolo_weights[0])
        yolo_combo = ttk.Combobox(detect_settings, textvariable=yolo_weight_var, values=yolo_weights, state="readonly")
        yolo_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(detect_settings, textvariable=yolo_weight_var, width=16).grid(row=1, column=2, sticky=tk.W)
        
        # 阈值法参数
        threshold_settings = ttk.LabelFrame(main_settings_frame, text="📏 阈值法参数", padding=10)
        threshold_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 高度比例
        ttk.Label(threshold_settings, text="高度比例阈值:").grid(row=0, column=0, sticky=tk.W)
        height_ratio_var = tk.DoubleVar(value=getattr(self.threshold_detector, 'height_ratio', 0.5))
        height_ratio_scale = ttk.Scale(threshold_settings, variable=height_ratio_var, from_=0.1, to=1.0, orient=tk.HORIZONTAL, resolution=0.01)
        height_ratio_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(threshold_settings, textvariable=height_ratio_var, width=6).grid(row=0, column=2, sticky=tk.W)
        
        # 宽度比例
        ttk.Label(threshold_settings, text="宽度比例阈值:").grid(row=1, column=0, sticky=tk.W)
        width_ratio_var = tk.DoubleVar(value=getattr(self.threshold_detector, 'width_ratio', 0.5))
        width_ratio_scale = ttk.Scale(threshold_settings, variable=width_ratio_var, from_=0.1, to=1.0, orient=tk.HORIZONTAL, resolution=0.01)
        width_ratio_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(threshold_settings, textvariable=width_ratio_var, width=6).grid(row=1, column=2, sticky=tk.W)
        
        # 角度阈值
        ttk.Label(threshold_settings, text="角度阈值(°):").grid(row=2, column=0, sticky=tk.W)
        angle_var = tk.DoubleVar(value=getattr(self.threshold_detector, 'angle_threshold', 45))
        angle_scale = ttk.Scale(threshold_settings, variable=angle_var, from_=10, to=90, orient=tk.HORIZONTAL, resolution=1)
        angle_scale.grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(threshold_settings, textvariable=angle_var, width=6).grid(row=2, column=2, sticky=tk.W)
        
        # 显示设置
        display_settings = ttk.LabelFrame(main_settings_frame, text="🖥️ 显示设置", padding=10)
        display_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 最大显示尺寸设置
        ttk.Label(display_settings, text="最大显示宽度:").grid(row=0, column=0, sticky=tk.W)
        max_width_var = tk.IntVar(value=640)
        max_width_scale = ttk.Scale(display_settings, variable=max_width_var, from_=320, to=1280, orient=tk.HORIZONTAL)
        max_width_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(display_settings, textvariable=max_width_var, width=6).grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(display_settings, text="最大显示高度:").grid(row=1, column=0, sticky=tk.W)
        max_height_var = tk.IntVar(value=480)
        max_height_scale = ttk.Scale(display_settings, variable=max_height_var, from_=240, to=960, orient=tk.HORIZONTAL)
        max_height_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(display_settings, textvariable=max_height_var, width=6).grid(row=1, column=2, sticky=tk.W)
        
        # 显示质量
        ttk.Label(display_settings, text="显示质量:").grid(row=2, column=0, sticky=tk.W)
        quality_var = tk.StringVar(value="原始画质")
        quality_combo = ttk.Combobox(display_settings, textvariable=quality_var, 
                                   values=["原始画质", "高质量", "中等质量", "低质量"], 
                                   state="readonly")
        quality_combo.grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        # 日志设置
        log_settings = ttk.LabelFrame(main_settings_frame, text="📝 日志设置", padding=10)
        log_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 日志级别
        ttk.Label(log_settings, text="日志级别:").pack(anchor=tk.W)
        log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_settings, textvariable=log_level_var, 
                                     values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                     state="readonly")
        log_level_combo.pack(fill=tk.X, pady=5)
        
        # 自动保存日志
        auto_save_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(log_settings, text="自动保存日志", variable=auto_save_var).pack(anchor=tk.W, pady=5)
        
        # 预警设置
        alert_settings = ttk.LabelFrame(main_settings_frame, text="🚨 预警设置", padding=10)
        alert_settings.pack(fill=tk.X, pady=(0, 10))
        
        # 预警冷却时间
        ttk.Label(alert_settings, text="预警冷却时间 (秒):").pack(anchor=tk.W)
        cooldown_var = tk.IntVar(value=60)
        cooldown_scale = ttk.Scale(alert_settings, variable=cooldown_var, from_=10, to=300, 
                                 orient=tk.HORIZONTAL)
        cooldown_scale.pack(fill=tk.X, pady=5)
        
        # 启用预警
        enable_alert_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(alert_settings, text="启用预警功能", variable=enable_alert_var).pack(anchor=tk.W, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(main_settings_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def apply_settings():
            try:
                self.detection_interval = interval_var.get()
                # 更新阈值法参数
                self.threshold_detector.height_ratio = height_ratio_var.get()
                self.threshold_detector.width_ratio = width_ratio_var.get()
                self.threshold_detector.angle_threshold = angle_var.get()
                # 更新显示设置
                self.max_display_width = max_width_var.get()
                self.max_display_height = max_height_var.get()
                # 切换YOLO权重
                if hasattr(self.pose_detector, 'model_path') and self.pose_detector.model_path != yolo_weight_var.get():
                    self.pose_detector.load_model(yolo_weight_var.get())
                    self.log_message(f"已切换YOLO骨骼模型权重: {yolo_weight_var.get()}", "SUCCESS")
                self.log_message("设置已应用", "SUCCESS")
                settings_window.destroy()
            except Exception as e:
                self.log_message(f"应用设置失败: {e}", "ERROR")
        
        def reset_settings():
            interval_var.set(0.05)
            height_ratio_var.set(0.5)
            width_ratio_var.set(0.5)
            angle_var.set(45)
            yolo_weight_var.set(yolo_weights[0])
            max_width_var.set(640)
            max_height_var.set(480)
            quality_var.set("原始画质")
            self.log_message("设置已重置", "INFO")
        
        ttk.Button(button_frame, text="✅ 应用", command=apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 重置", command=reset_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ 取消", command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def show_about(self):
        """显示关于信息"""
        about_text = """
摔倒检测系统 v1.0

功能特性:
- 基于YOLO的人体姿势检测
- 多种摔倒检测算法（阈值法、机器学习、深度学习）
- 实时视频检测
- 邮箱和短信预警功能
- 图形化用户界面

技术栈:
- Python 3.8+
- PyTorch
- OpenCV
- scikit-learn
- tkinter

作者: AI Assistant
        """
        messagebox.showinfo("关于", about_text)
        
    def load_config(self):
        """加载配置"""
        try:
            # 加载预警配置
            config = self.alert_config.config
            
            if config['email']['enabled']:
                self.alert_manager.add_email_alert(
                    config['email']['sender_email'],
                    config['email']['sender_password'],
                    config['email']['recipient_emails']
                )
            
            if config['sms']['enabled']:
                self.alert_manager.add_sms_alert(
                    config['sms']['api_key'],
                    config['sms']['api_secret'],
                    config['sms']['phone_numbers']
                )
            
            self.log_message("配置加载完成")
            
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
            
    def on_closing(self):
        """程序关闭时的清理工作"""
        self.stop_detection()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = FallDetectionGUI(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 启动应用
    root.mainloop()

if __name__ == "__main__":
    main() 