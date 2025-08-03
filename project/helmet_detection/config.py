#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头盔检测系统配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 模型配置
MODEL_CONFIG = {
    'model_path': PROJECT_ROOT / 'pt_models' / 'helmet_best.pt',
    'confidence_threshold': 0.5,  # 置信度阈值
    'iou_threshold': 0.45,        # NMS IoU阈值
    'max_det': 300,               # 最大检测数量
}

# 界面配置
UI_CONFIG = {
    'window_title': '头盔检测系统',
    'window_width': 1400,
    'window_height': 900,
    'image_min_width': 600,
    'image_min_height': 400,
    'log_max_height': 150,
    'font_family': 'Consolas',
    'font_size': 9,
}

# 检测配置
DETECTION_CONFIG = {
    'video_fps': 30,              # 视频帧率
    'camera_fps': 30,             # 摄像头帧率
    'frame_delay': 0.03,          # 帧间延迟（秒）
    'max_video_frames': 1000,     # 最大视频帧数（测试用）
}

# 文件配置
FILE_CONFIG = {
    'supported_images': ['*.jpg', '*.jpeg', '*.png', '*.bmp'],
    'supported_videos': ['*.mp4', '*.avi', '*.mov', '*.mkv'],
    'output_dir': PROJECT_ROOT / 'runs' / 'detect',
}

# 日志配置
LOG_CONFIG = {
    'max_log_lines': 1000,        # 最大日志行数
    'timestamp_format': '%H:%M:%S',
    'log_level': 'INFO',
}

# 样式配置
STYLE_CONFIG = {
    'primary_color': '#4CAF50',
    'primary_hover': '#45a049',
    'disabled_color': '#cccccc',
    'disabled_text': '#666666',
    'border_color': 'gray',
    'background_color': 'black',
}

def get_model_path():
    """获取模型路径"""
    return str(MODEL_CONFIG['model_path'])

def get_supported_formats(file_type):
    """获取支持的文件格式"""
    if file_type == 'image':
        return ' '.join([f"({fmt})" for fmt in FILE_CONFIG['supported_images']])
    elif file_type == 'video':
        return ' '.join([f"({fmt})" for fmt in FILE_CONFIG['supported_videos']])
    return ""

def get_file_filter(file_type):
    """获取文件过滤器字符串"""
    if file_type == 'image':
        formats = FILE_CONFIG['supported_images']
        return f"图片文件 ({' '.join(formats)})"
    elif file_type == 'video':
        formats = FILE_CONFIG['supported_videos']
        return f"视频文件 ({' '.join(formats)})"
    return "所有文件 (*.*)"

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        PROJECT_ROOT / 'pt_models',
        PROJECT_ROOT / 'helmet_test_img',
        PROJECT_ROOT / 'runs' / 'detect',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def validate_model():
    """验证模型文件是否存在"""
    model_path = MODEL_CONFIG['model_path']
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    return True 