"""
人体骨骼点检测模块
使用YOLO进行姿势估计
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
from typing import List, Tuple, Dict, Any
import json

def resize_pose(poses, scale_x, scale_y):
    """
    对一组pose结果进行坐标缩放，返回新pose列表
    """
    new_poses = []
    for pose in poses:
        new_pose = dict(pose)
        new_kps = {}
        for name, kp in pose['keypoints'].items():
            new_kps[name] = {
                'x': kp['x'] * scale_x,
                'y': kp['y'] * scale_y,
                'confidence': kp['confidence']
            }
        new_pose['keypoints'] = new_kps
        if 'bbox' in pose and pose['bbox'] is not None:
            x1, y1, x2, y2 = pose['bbox']
            new_pose['bbox'] = [x1*scale_x, y1*scale_y, x2*scale_x, y2*scale_y]
        new_poses.append(new_pose)
    return new_poses

class PoseDetector:
    def __init__(self, model_path: str = "yolov8n-pose.pt", conf_threshold: float = 0.7, device: str = 'cuda'):
        """
        初始化姿势检测器
        
        Args:
            model_path: YOLO模型路径
            conf_threshold: 置信度阈值
            device: 设备类型 ('cpu' 或 'cuda')
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.device = device
        self.model = None
        self.load_model()
        
        # COCO关键点定义
        self.keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
    def load_model(self):
        """加载YOLO模型"""
        try:
            print(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            print("模型加载成功!")
        except Exception as e:
            print(f"模型加载失败: {e}")
            # 如果指定模型不存在，使用默认模型
            print("使用默认模型 yolo11x-pose.pt")
            self.model = YOLO("yolo11x-pose.pt")
    
    def detect_pose(self, image) -> List[Dict[str, Any]]:
        """
        检测图像中的人体姿势
        
        Args:
            image: 输入图像 (numpy array 或 文件路径)
            
        Returns:
            包含关键点信息的列表
        """
        if self.model is None:
            raise ValueError("模型未加载")
        
        # 运行推理
        results = self.model(image, conf=self.conf_threshold, device=self.device)
        
        poses = []
        for result in results:
            if result.keypoints is not None:
                keypoints = result.keypoints.data.cpu().numpy()
                confidences = result.keypoints.conf.cpu().numpy()
                
                for i, (kp, conf) in enumerate(zip(keypoints, confidences)):
                    pose_data = {
                        'person_id': i,
                        'keypoints': {},
                        'bbox': result.boxes.xyxy[i].cpu().numpy().tolist() if result.boxes is not None else None,
                        'confidence': float(result.boxes.conf[i].cpu().numpy()) if result.boxes is not None else 0.0
                    }
                    
                    # 提取关键点坐标和置信度
                    for j, (name, point, conf_val) in enumerate(zip(self.keypoint_names, kp, conf)):
                        pose_data['keypoints'][name] = {
                            'x': float(point[0]),
                            'y': float(point[1]),
                            'confidence': float(conf_val)
                        }
                    
                    poses.append(pose_data)
        
        return poses
    
    def process_video(self, video_path: str, output_path: str = None, save_frames: bool = False) -> List[List[Dict[str, Any]]]:
        """
        处理视频文件
        
        Args:
            video_path: 视频文件路径
            output_path: 输出视频路径 (可选)
            save_frames: 是否保存帧数据
            
        Returns:
            每帧的姿势检测结果
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        frame_poses = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检测当前帧的姿势
            poses = self.detect_pose(frame)
            frame_poses.append(poses)
            
            frame_count += 1
            if frame_count % 30 == 0:  # 每30帧打印一次进度
                print(f"已处理 {frame_count} 帧")
        
        cap.release()
        print(f"视频处理完成，共处理 {frame_count} 帧")
        
        return frame_poses
    
    def draw_pose(self, image, poses, draw_keypoints=True, draw_skeleton=True, draw_bbox=True):
        """
        在图像上绘制检测到的姿势（假定输入坐标已与图像分辨率一致）
        优化版本：使用不同颜色的圆点美化关节点和线条
        """
        image_copy = image.copy()
        
        # 定义关键点颜色映射 - 按身体部位分组
        keypoint_colors = {
            # 头部关键点 - 蓝色系
            'nose': (255, 100, 100),      # 浅蓝色
            'left_eye': (255, 150, 150),  # 蓝色
            'right_eye': (255, 150, 150), # 蓝色
            'left_ear': (255, 200, 200),  # 浅蓝色
            'right_ear': (255, 200, 200), # 浅蓝色
            
            # 上肢关键点 - 绿色系
            'left_shoulder': (100, 255, 100),  # 浅绿色
            'right_shoulder': (100, 255, 100), # 浅绿色
            'left_elbow': (150, 255, 150),     # 绿色
            'right_elbow': (150, 255, 150),    # 绿色
            'left_wrist': (200, 255, 200),     # 浅绿色
            'right_wrist': (200, 255, 200),    # 浅绿色
            
            # 躯干关键点 - 红色系
            'left_hip': (100, 100, 255),   # 浅红色
            'right_hip': (100, 100, 255),  # 浅红色
            
            # 下肢关键点 - 黄色系
            'left_knee': (100, 255, 255),  # 浅黄色
            'right_knee': (100, 255, 255), # 浅黄色
            'left_ankle': (150, 255, 255), # 黄色
            'right_ankle': (150, 255, 255) # 黄色
        }
        
        # 定义骨架连接和对应的线条颜色
        skeleton_connections = [
            # 头部连接 - 蓝色线条
            ('left_eye', 'right_eye'),
            ('left_eye', 'left_ear'),
            ('right_eye', 'right_ear'),
            ('nose', 'left_eye'),
            ('nose', 'right_eye'),
            
            # 躯干连接 - 红色线条
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            
            # 上肢连接 - 绿色线条
            ('left_shoulder', 'left_elbow'),
            ('right_shoulder', 'right_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_elbow', 'right_wrist'),
            
            # 下肢连接 - 黄色线条
            ('left_hip', 'left_knee'),
            ('right_hip', 'right_knee'),
            ('left_knee', 'left_ankle'),
            ('right_knee', 'right_ankle')
        ]
        
        # 线条颜色映射
        line_colors = {
            # 头部线条 - 蓝色
            ('left_eye', 'right_eye'): (255, 100, 100),
            ('left_eye', 'left_ear'): (255, 100, 100),
            ('right_eye', 'right_ear'): (255, 100, 100),
            ('nose', 'left_eye'): (255, 100, 100),
            ('nose', 'right_eye'): (255, 100, 100),
            
            # 躯干线条 - 红色
            ('left_shoulder', 'right_shoulder'): (100, 100, 255),
            ('left_shoulder', 'left_hip'): (100, 100, 255),
            ('right_shoulder', 'right_hip'): (100, 100, 255),
            ('left_hip', 'right_hip'): (100, 100, 255),
            
            # 上肢线条 - 绿色
            ('left_shoulder', 'left_elbow'): (100, 255, 100),
            ('right_shoulder', 'right_elbow'): (100, 255, 100),
            ('left_elbow', 'left_wrist'): (100, 255, 100),
            ('right_elbow', 'right_wrist'): (100, 255, 100),
            
            # 下肢线条 - 黄色
            ('left_hip', 'left_knee'): (100, 255, 255),
            ('right_hip', 'right_knee'): (100, 255, 255),
            ('left_knee', 'left_ankle'): (100, 255, 255),
            ('right_knee', 'right_ankle'): (100, 255, 255)
        }
        
        for pose in poses:
            keypoints = pose['keypoints']
            
            # 绘制人物边框
            if draw_bbox and pose.get('bbox') is not None:
                bbox = pose['bbox']
                if len(bbox) == 4:
                    x1, y1, x2, y2 = map(int, bbox)
                    # 使用白色边框，更清晰
                    cv2.rectangle(image_copy, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # 绘制关键点 - 使用不同颜色和大小的圆点
            if draw_keypoints:
                for name, kp in keypoints.items():
                    if kp['confidence'] > 0.5:
                        x, y = int(kp['x']), int(kp['y'])
                        color = keypoint_colors.get(name, (0, 255, 0))  # 默认绿色
                        
                        # 根据关键点重要性调整圆点大小
                        radius = 4 if name in ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip'] else 3
                        
                        # 绘制外圈（白色边框）
                        cv2.circle(image_copy, (x, y), radius + 1, (255, 255, 255), -1)
                        # 绘制内圈（彩色填充）
                        cv2.circle(image_copy, (x, y), radius, color, -1)
                        # 绘制中心点（黑色）
                        cv2.circle(image_copy, (x, y), 1, (0, 0, 0), -1)
            
            # 绘制骨架线条 - 使用不同颜色和粗细
            if draw_skeleton:
                for connection in skeleton_connections:
                    kp1_name, kp2_name = connection
                    if kp1_name in keypoints and kp2_name in keypoints:
                        kp1 = keypoints[kp1_name]
                        kp2 = keypoints[kp2_name]
                        if kp1['confidence'] > 0.5 and kp2['confidence'] > 0.5:
                            pt1 = (int(kp1['x']), int(kp1['y']))
                            pt2 = (int(kp2['x']), int(kp2['y']))
                            
                            # 获取线条颜色
                            line_color = line_colors.get(connection, (255, 0, 0))
                            
                            # 绘制线条（稍微粗一些，更清晰）
                            cv2.line(image_copy, pt1, pt2, line_color, 3)
        
        return image_copy
    
    def extract_features(self, poses: List[Dict[str, Any]]) -> np.ndarray:
        """
        从姿势数据中提取特征
        
        Args:
            poses: 姿势检测结果
            
        Returns:
            特征向量
        """
        if not poses:
            return np.array([])
        
        features = []
        for pose in poses:
            pose_features = []
            keypoints = pose['keypoints']
            
            # 计算关键点之间的角度和距离
            # 这里可以添加更多特征提取逻辑
            for name in self.keypoint_names:
                if name in keypoints:
                    kp = keypoints[name]
                    pose_features.extend([kp['x'], kp['y'], kp['confidence']])
                else:
                    pose_features.extend([0, 0, 0])  # 缺失关键点用0填充
            
            features.append(pose_features)
        
        return np.array(features)

if __name__ == "__main__":
    # 测试代码
    detector = PoseDetector()
    
    # 测试图像检测
    test_image_path = "test_image.jpg"
    if os.path.exists(test_image_path):
        image = cv2.imread(test_image_path)
        poses = detector.detect_pose(image)
        print(f"检测到 {len(poses)} 个人体姿势")
        
        # 绘制结果
        result_image = detector.draw_pose(image, poses)
        cv2.imshow("Pose Detection", result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows() 