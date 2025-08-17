#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键点生成器
使用YOLO模型从视频中自动生成人体关键点数据
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path


class KeypointGenerator:
    """关键点生成器"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        
        # 支持的模型文件
        self.model_names = [
            'yolo11x-pose.pt',
            'yolo11l-pose.pt',
            'yolo11n-pose.pt',
            'yolo11m-pose.pt',
            'yolo11s-pose.pt',
            'yolov8x-pose.pt',
            'yolov8l-pose.pt',
            'yolov8n-pose.pt',
            'yolov8m-pose.pt',
            'yolov8s-pose.pt'
        ]
    
    def load_model(self, model_path=None):
        """加载YOLO模型"""
        try:
            # 动态导入ultralytics，避免在没有安装时崩溃
            try:
                from ultralytics import YOLO
            except ImportError:
                raise ImportError("请安装ultralytics库: pip install ultralytics")
            
            if model_path is None:
                model_path = self.find_model_file()
            
            if not model_path or not os.path.exists(model_path):
                raise FileNotFoundError("未找到YOLO模型文件")
            
            print(f"加载YOLO模型: {model_path}")
            self.model = YOLO(model_path)
            self.model_loaded = True
            
            return True
            
        except Exception as e:
            print(f"加载YOLO模型失败: {str(e)}")
            return False
    
    def find_model_file(self):
        """查找可用的模型文件"""
        # 搜索路径
        search_paths = []
        
        # 如果是打包后的可执行文件
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            search_paths.extend([
                os.path.join(base_path, "models"),
                os.path.join(base_path, "weights"),
                base_path
            ])
        
        # 常规搜索路径
        search_paths.extend([
            ".",
            "models",
            "weights",
            os.path.expanduser("~/.cache/torch/hub/ultralytics_yolov5_master"),
            os.path.expanduser("~/.ultralytics"),
        ])
        
        # 在每个路径中搜索模型文件
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for model_name in self.model_names:
                model_path = os.path.join(search_path, model_name)
                if os.path.exists(model_path):
                    return model_path
        
        return None
    
    def generate_from_video(self, video_path, output_dir=None, progress_callback=None):
        """从视频生成关键点数据"""
        try:
            # 加载模型
            if not self.model_loaded:
                if not self.load_model():
                    raise Exception("无法加载YOLO模型")
            
            # 确定输出目录
            if output_dir is None:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                video_dir = os.path.dirname(video_path)
                output_dir = os.path.join(video_dir, "output", video_name)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频文件: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"处理视频: {video_path}")
            print(f"总帧数: {total_frames}, 帧率: {fps}")
            
            # 存储所有帧的关键点数据
            all_keypoints = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 使用YOLO模型检测关键点
                results = self.model(frame, verbose=False)
                
                # 提取关键点数据
                frame_keypoints = self.extract_keypoints_from_results(results)
                all_keypoints.append(frame_keypoints)
                
                frame_count += 1
                
                # 更新进度
                if progress_callback and frame_count % 10 == 0:
                    progress = (frame_count / total_frames) * 100
                    progress_callback(progress)
                
                # 可选：显示处理进度
                if frame_count % 30 == 0:
                    print(f"已处理 {frame_count}/{total_frames} 帧 ({frame_count/total_frames*100:.1f}%)")
            
            cap.release()
            
            # 保存关键点数据
            keypoints_file = os.path.join(output_dir, "keypoints.json")
            self.save_keypoints_data(all_keypoints, keypoints_file, fps)
            
            print(f"关键点数据已保存到: {keypoints_file}")
            return keypoints_file
            
        except Exception as e:
            if 'cap' in locals():
                cap.release()
            raise Exception(f"生成关键点数据失败: {str(e)}")
    
    def extract_keypoints_from_results(self, results):
        """从YOLO结果中提取关键点数据"""
        keypoints_list = []
        
        try:
            for result in results:
                if hasattr(result, 'keypoints') and result.keypoints is not None:
                    # 获取关键点数据
                    keypoints_data = result.keypoints
                    
                    if hasattr(keypoints_data, 'data'):
                        # YOLOv8/v11格式
                        kpts = keypoints_data.data.cpu().numpy()
                        
                        # 处理每个检测到的人
                        for person_kpts in kpts:
                            # person_kpts shape: (17, 3) for COCO format
                            # 每个关键点包含 [x, y, confidence]
                            person_keypoints = []
                            
                            for point in person_kpts:
                                x, y, conf = float(point[0]), float(point[1]), float(point[2])
                                person_keypoints.append([x, y, conf])
                            
                            keypoints_list.append(person_keypoints)
                    
                    elif hasattr(keypoints_data, 'xy'):
                        # 其他格式
                        xy = keypoints_data.xy.cpu().numpy()
                        conf = keypoints_data.conf.cpu().numpy() if hasattr(keypoints_data, 'conf') else None
                        
                        for i, points in enumerate(xy):
                            person_keypoints = []
                            for j, (x, y) in enumerate(points):
                                confidence = conf[i][j] if conf is not None else 1.0
                                person_keypoints.append([float(x), float(y), float(confidence)])
                            keypoints_list.append(person_keypoints)
            
            # 如果检测到多个人，选择置信度最高的
            if len(keypoints_list) > 1:
                # 计算每个人的平均置信度
                avg_confidences = []
                for person_kpts in keypoints_list:
                    confidences = [kpt[2] for kpt in person_kpts if len(kpt) >= 3]
                    avg_conf = np.mean(confidences) if confidences else 0
                    avg_confidences.append(avg_conf)
                
                # 选择置信度最高的人
                best_person_idx = np.argmax(avg_confidences)
                return keypoints_list[best_person_idx]
            
            elif len(keypoints_list) == 1:
                return keypoints_list[0]
            
            else:
                # 没有检测到人，返回空的关键点数据
                return self.get_empty_keypoints()
                
        except Exception as e:
            print(f"提取关键点数据时出错: {str(e)}")
            return self.get_empty_keypoints()
    
    def get_empty_keypoints(self):
        """获取空的关键点数据（COCO格式，17个关键点）"""
        return [[0.0, 0.0, 0.0] for _ in range(17)]
    
    def save_keypoints_data(self, keypoints_data, output_file, fps=30):
        """保存关键点数据到JSON文件"""
        try:
            # 创建输出数据结构
            output_data = {
                'metadata': {
                    'format': 'COCO',
                    'total_frames': len(keypoints_data),
                    'fps': fps,
                    'keypoint_names': [
                        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
                        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                        'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                        'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
                    ],
                    'keypoint_skeleton': [
                        [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
                        [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
                        [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
                        [2, 4], [3, 5], [4, 6], [5, 7]
                    ]
                },
                'keypoints': keypoints_data
            }
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"关键点数据已保存: {output_file}")
            
        except Exception as e:
            raise Exception(f"保存关键点数据失败: {str(e)}")
    
    def validate_keypoints_data(self, keypoints_data):
        """验证关键点数据的有效性"""
        if not keypoints_data:
            return False, "关键点数据为空"
        
        valid_frames = 0
        total_frames = len(keypoints_data)
        
        for frame_idx, frame_keypoints in enumerate(keypoints_data):
            if not frame_keypoints:
                continue
            
            # 检查关键点数量
            if len(frame_keypoints) != 17:
                print(f"警告: 第{frame_idx}帧关键点数量不正确: {len(frame_keypoints)}")
                continue
            
            # 检查每个关键点的格式
            valid_points = 0
            for point in frame_keypoints:
                if len(point) >= 3 and point[2] > 0.1:  # 置信度阈值
                    valid_points += 1
            
            if valid_points >= 5:  # 至少5个有效关键点
                valid_frames += 1
        
        validity_ratio = valid_frames / total_frames if total_frames > 0 else 0
        
        if validity_ratio < 0.3:
            return False, f"有效帧比例过低: {validity_ratio:.2%}"
        
        return True, f"数据有效，有效帧比例: {validity_ratio:.2%}"
    
    def process_batch_videos(self, video_dir, output_base_dir=None, progress_callback=None):
        """批量处理视频文件"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        video_files = []
        
        # 查找视频文件
        for ext in video_extensions:
            video_files.extend(Path(video_dir).glob(f"*{ext}"))
            video_files.extend(Path(video_dir).glob(f"*{ext.upper()}"))
        
        if not video_files:
            raise Exception(f"在目录 {video_dir} 中未找到视频文件")
        
        results = []
        
        for i, video_file in enumerate(video_files):
            try:
                print(f"处理视频 {i+1}/{len(video_files)}: {video_file.name}")
                
                # 确定输出目录
                if output_base_dir:
                    output_dir = os.path.join(output_base_dir, video_file.stem)
                else:
                    output_dir = os.path.join(video_file.parent, "output", video_file.stem)
                
                # 生成关键点数据
                keypoints_file = self.generate_from_video(
                    str(video_file), 
                    output_dir,
                    progress_callback
                )
                
                results.append({
                    'video_file': str(video_file),
                    'keypoints_file': keypoints_file,
                    'status': 'success'
                })
                
            except Exception as e:
                print(f"处理视频 {video_file.name} 时出错: {str(e)}")
                results.append({
                    'video_file': str(video_file),
                    'keypoints_file': None,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


def save_keypoints_data(yolo_results, output_dir):
    """
    兼容函数：从YOLO结果保存关键点数据
    这个函数用于兼容原始代码中的调用
    """
    generator = KeypointGenerator()
    
    # 从YOLO结果提取关键点数据
    all_keypoints = []
    for result in yolo_results:
        frame_keypoints = generator.extract_keypoints_from_results([result])
        all_keypoints.append(frame_keypoints)
    
    # 保存数据
    keypoints_file = os.path.join(output_dir, "keypoints.json")
    generator.save_keypoints_data(all_keypoints, keypoints_file)
    
    return keypoints_file


if __name__ == "__main__":
    # 测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description="生成人体关键点数据")
    parser.add_argument("--video", "-v", required=True, help="输入视频文件路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--model", "-m", help="YOLO模型文件路径")
    
    args = parser.parse_args()
    
    generator = KeypointGenerator()
    
    try:
        keypoints_file = generator.generate_from_video(
            args.video, 
            args.output,
            lambda p: print(f"进度: {p:.1f}%")
        )
        print(f"成功生成关键点数据: {keypoints_file}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)