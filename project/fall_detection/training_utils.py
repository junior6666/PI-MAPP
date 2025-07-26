"""
训练工具模块
用于数据准备和模型训练
"""

import os
import json
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from pose_detection import PoseDetector
from fall_detection_algorithms import TraditionalMLFallDetector, DeepLearningFallDetector

class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, pose_detector: PoseDetector):
        self.pose_detector = pose_detector
        self.processed_data = []
        
    def process_video_dataset(self, dataset_path: str, output_path: str = "processed_data"):
        """
        处理视频数据集
        
        Args:
            dataset_path: 数据集路径，包含fall和normal子文件夹
            output_path: 输出路径
        """
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 处理摔倒视频
        fall_path = os.path.join(dataset_path, "fall")
        if os.path.exists(fall_path):
            self._process_videos_in_folder(fall_path, output_path, label=1)
        
        # 处理正常视频
        normal_path = os.path.join(dataset_path, "normal")
        if os.path.exists(normal_path):
            self._process_videos_in_folder(normal_path, output_path, label=0)
        
        # 保存处理后的数据
        self.save_processed_data(output_path)
        
    def _process_videos_in_folder(self, folder_path: str, output_path: str, label: int):
        """处理文件夹中的视频"""
        video_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        
        for video_file in video_files:
            video_path = os.path.join(folder_path, video_file)
            print(f"处理视频: {video_file}")
            
            try:
                # 处理视频
                poses_sequence = self.pose_detector.process_video(video_path)
                
                # 保存处理结果
                output_file = os.path.join(output_path, f"{video_file[:-4]}_{label}.json")
                self._save_poses_sequence(poses_sequence, output_file, label)
                
            except Exception as e:
                print(f"处理视频 {video_file} 失败: {e}")
    
    def _save_poses_sequence(self, poses_sequence: List[List[Dict[str, Any]]], 
                           output_file: str, label: int):
        """保存姿势序列"""
        data = {
            'label': label,
            'frames': len(poses_sequence),
            'poses_sequence': poses_sequence,
            'processed_time': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_processed_data(self, output_path: str):
        """保存处理后的数据"""
        metadata = {
            'total_samples': len(self.processed_data),
            'processed_time': datetime.now().isoformat(),
            'data_files': []
        }
        
        # 收集所有数据文件
        for file in os.listdir(output_path):
            if file.endswith('.json'):
                metadata['data_files'].append(file)
        
        # 保存元数据
        metadata_file = os.path.join(output_path, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"数据处理完成，共处理 {metadata['total_samples']} 个样本")

class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self):
        self.feature_names = []
        
    def extract_features_from_poses(self, poses: List[Dict[str, Any]]) -> np.ndarray:
        """从姿势数据中提取特征"""
        if not poses:
            return np.array([])
        
        features = []
        for pose in poses:
            pose_features = self._extract_single_pose_features(pose)
            features.append(pose_features)
        
        return np.array(features)
    
    def _extract_single_pose_features(self, pose: Dict[str, Any]) -> List[float]:
        """提取单个姿势的特征"""
        keypoints = pose['keypoints']
        features = []
        
        # 基础关键点特征
        for name in ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 
                    'left_knee', 'right_knee', 'left_ankle', 'right_ankle']:
            if name in keypoints:
                kp = keypoints[name]
                features.extend([kp['x'], kp['y'], kp['confidence']])
            else:
                features.extend([0, 0, 0])
        
        # 几何特征
        geometric_features = self._calculate_geometric_features(keypoints)
        features.extend(list(geometric_features.values()))
        
        return features
    
    def _calculate_geometric_features(self, keypoints: Dict[str, Any]) -> Dict[str, float]:
        """计算几何特征"""
        features = {}
        
        # 躯干长度
        if 'left_shoulder' in keypoints and 'left_hip' in keypoints:
            trunk_length = np.sqrt(
                (keypoints['left_shoulder']['x'] - keypoints['left_hip']['x'])**2 +
                (keypoints['left_shoulder']['y'] - keypoints['left_hip']['y'])**2
            )
            features['trunk_length'] = trunk_length
        else:
            features['trunk_length'] = 0
        
        # 腿部长度
        if 'left_hip' in keypoints and 'left_knee' in keypoints:
            leg_length = np.sqrt(
                (keypoints['left_hip']['x'] - keypoints['left_knee']['x'])**2 +
                (keypoints['left_hip']['y'] - keypoints['left_knee']['y'])**2
            )
            features['leg_length'] = leg_length
        else:
            features['leg_length'] = 0
        
        # 躯干角度
        if all(k in keypoints for k in ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']):
            angle = self._calculate_trunk_angle(keypoints)
            features['trunk_angle'] = angle
        else:
            features['trunk_angle'] = 0
        
        # 高度比例
        if all(k in keypoints for k in ['left_shoulder', 'left_hip', 'left_knee']):
            shoulder_y = keypoints['left_shoulder']['y']
            hip_y = keypoints['left_hip']['y']
            knee_y = keypoints['left_knee']['y']
            
            trunk_height = abs(shoulder_y - hip_y)
            leg_height = abs(hip_y - knee_y)
            total_height = trunk_height + leg_height
            
            features['height_ratio'] = trunk_height / total_height if total_height > 0 else 0
        else:
            features['height_ratio'] = 0
        
        return features
    
    def _calculate_trunk_angle(self, keypoints: Dict[str, Any]) -> float:
        """计算躯干角度"""
        shoulder_center_x = (keypoints['left_shoulder']['x'] + keypoints['right_shoulder']['x']) / 2
        shoulder_center_y = (keypoints['left_shoulder']['y'] + keypoints['right_shoulder']['y']) / 2
        hip_center_x = (keypoints['left_hip']['x'] + keypoints['right_hip']['x']) / 2
        hip_center_y = (keypoints['left_hip']['y'] + keypoints['right_hip']['y']) / 2
        
        dx = hip_center_x - shoulder_center_x
        dy = hip_center_y - shoulder_center_y
        
        if dx == 0:
            return 0
        
        angle = np.arctan2(dx, dy) * 180 / np.pi
        return abs(angle)

class ModelTrainer:
    """模型训练器"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.training_history = []
        
    def prepare_training_data(self, data_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        features_list = []
        labels_list = []
        
        # 加载所有数据文件
        for file in os.listdir(data_path):
            if file.endswith('.json') and file != 'metadata.json':
                file_path = os.path.join(data_path, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    poses_sequence = data['poses_sequence']
                    label = data['label']
                    
                    # 提取特征
                    for poses in poses_sequence:
                        if poses:  # 确保有检测到姿势
                            features = self.feature_extractor.extract_features_from_poses(poses)
                            if len(features) > 0:
                                # 取第一个人的特征
                                features_list.append(features[0])
                                labels_list.append(label)
                
                except Exception as e:
                    print(f"加载数据文件 {file} 失败: {e}")
        
        return np.array(features_list), np.array(labels_list)
    
    def train_traditional_ml_models(self, X: np.ndarray, y: np.ndarray, 
                                  output_dir: str = "trained_models"):
        """训练传统机器学习模型"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 训练不同算法
        algorithms = ['knn', 'svm', 'rf']
        results = {}
        
        for algo in algorithms:
            print(f"训练 {algo.upper()} 模型...")
            
            model = TraditionalMLFallDetector(algo)
            model.train(X_train, y_train)
            
            # 评估模型
            predictions, probabilities = model.predict(X_test)
            accuracy = np.mean(predictions == y_test)
            
            # 保存模型
            model_path = os.path.join(output_dir, f"{algo}_model.pkl")
            model.save_model(model_path)
            
            results[algo] = {
                'accuracy': accuracy,
                'predictions': predictions,
                'probabilities': probabilities,
                'model_path': model_path
            }
            
            print(f"{algo.upper()} 模型准确率: {accuracy:.4f}")
        
        # 生成评估报告
        self._generate_evaluation_report(results, y_test, output_dir)
        
        return results
    
    def train_deep_learning_model(self, data_path: str, output_dir: str = "trained_models"):
        """训练深度学习模型"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 准备序列数据
        pose_sequences = []
        labels = []
        
        for file in os.listdir(data_path):
            if file.endswith('.json') and file != 'metadata.json':
                file_path = os.path.join(data_path, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    poses_sequence = data['poses_sequence']
                    label = data['label']
                    
                    # 只保留有足够帧数的序列
                    if len(poses_sequence) >= 10:
                        pose_sequences.append(poses_sequence)
                        labels.append(label)
                
                except Exception as e:
                    print(f"加载数据文件 {file} 失败: {e}")
        
        if len(pose_sequences) == 0:
            print("没有足够的数据进行深度学习训练")
            return None
        
        # 训练深度学习模型
        dl_model = DeepLearningFallDetector('lstm')
        
        try:
            dl_model.train(pose_sequences, labels, epochs=50, batch_size=32)
            
            # 保存模型
            model_path = os.path.join(output_dir, "lstm_model.pth")
            dl_model.save_model(model_path)
            
            print("深度学习模型训练完成")
            return model_path
            
        except Exception as e:
            print(f"深度学习模型训练失败: {e}")
            return None
    
    def _generate_evaluation_report(self, results: Dict[str, Any], y_test: np.ndarray, 
                                  output_dir: str):
        """生成评估报告"""
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 准确率对比
        algorithms = list(results.keys())
        accuracies = [results[algo]['accuracy'] for algo in algorithms]
        
        axes[0, 0].bar(algorithms, accuracies)
        axes[0, 0].set_title('模型准确率对比')
        axes[0, 0].set_ylabel('准确率')
        axes[0, 0].set_ylim(0, 1)
        
        # 混淆矩阵
        for i, algo in enumerate(algorithms):
            row = i // 2
            col = i % 2
            
            if row == 0 and col == 0:
                continue  # 跳过第一个位置（准确率图）
            
            cm = confusion_matrix(y_test, results[algo]['predictions'])
            sns.heatmap(cm, annot=True, fmt='d', ax=axes[row, col])
            axes[row, col].set_title(f'{algo.upper()} 混淆矩阵')
            axes[row, col].set_xlabel('预测标签')
            axes[row, col].set_ylabel('真实标签')
        
        plt.tight_layout()
        
        # 保存图表
        plot_path = os.path.join(output_dir, 'model_evaluation.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 生成文本报告
        report_path = os.path.join(output_dir, 'evaluation_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("模型评估报告\n")
            f.write("=" * 50 + "\n\n")
            
            for algo in algorithms:
                f.write(f"{algo.upper()} 模型:\n")
                f.write(f"准确率: {results[algo]['accuracy']:.4f}\n")
                
                # 详细分类报告
                report = classification_report(y_test, results[algo]['predictions'])
                f.write(f"分类报告:\n{report}\n")
                f.write("-" * 30 + "\n\n")
        
        print(f"评估报告已保存到: {output_dir}")

class DataVisualizer:
    """数据可视化器"""
    
    def __init__(self):
        pass
    
    def visualize_pose_data(self, poses_sequence: List[List[Dict[str, Any]]], 
                           output_path: str = "visualization"):
        """可视化姿势数据"""
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 提取关键点轨迹
        keypoint_trajectories = self._extract_keypoint_trajectories(poses_sequence)
        
        # 绘制轨迹图
        self._plot_trajectories(keypoint_trajectories, output_path)
        
        # 绘制特征变化图
        self._plot_feature_changes(poses_sequence, output_path)
    
    def _extract_keypoint_trajectories(self, poses_sequence: List[List[Dict[str, Any]]]) -> Dict[str, List[Tuple[float, float]]]:
        """提取关键点轨迹"""
        trajectories = {}
        keypoint_names = ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        
        for name in keypoint_names:
            trajectories[name] = []
        
        for poses in poses_sequence:
            if poses:
                pose = poses[0]  # 取第一个人的姿势
                keypoints = pose['keypoints']
                
                for name in keypoint_names:
                    if name in keypoints:
                        kp = keypoints[name]
                        trajectories[name].append((kp['x'], kp['y']))
                    else:
                        trajectories[name].append((0, 0))
            else:
                for name in keypoint_names:
                    trajectories[name].append((0, 0))
        
        return trajectories
    
    def _plot_trajectories(self, trajectories: Dict[str, List[Tuple[float, float]]], 
                          output_path: str):
        """绘制关键点轨迹"""
        plt.figure(figsize=(12, 8))
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        keypoint_names = list(trajectories.keys())
        
        for i, name in enumerate(keypoint_names):
            trajectory = trajectories[name]
            x_coords = [point[0] for point in trajectory]
            y_coords = [point[1] for point in trajectory]
            
            plt.plot(x_coords, y_coords, color=colors[i], label=name, alpha=0.7)
            plt.scatter(x_coords[0], y_coords[0], color=colors[i], s=50, marker='o')
            plt.scatter(x_coords[-1], y_coords[-1], color=colors[i], s=50, marker='s')
        
        plt.title('关键点轨迹图')
        plt.xlabel('X坐标')
        plt.ylabel('Y坐标')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 保存图片
        trajectory_path = os.path.join(output_path, 'keypoint_trajectories.png')
        plt.savefig(trajectory_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_feature_changes(self, poses_sequence: List[List[Dict[str, Any]]], 
                             output_path: str):
        """绘制特征变化图"""
        feature_extractor = FeatureExtractor()
        features_list = []
        
        for poses in poses_sequence:
            if poses:
                features = feature_extractor.extract_features_from_poses(poses)
                if len(features) > 0:
                    features_list.append(features[0])
                else:
                    features_list.append(np.zeros(51))  # 假设特征维度为51
            else:
                features_list.append(np.zeros(51))
        
        features_array = np.array(features_list)
        
        # 绘制关键特征的变化
        key_features = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # 选择一些关键特征
        feature_names = ['nose_x', 'nose_y', 'nose_conf', 'left_shoulder_x', 
                        'left_shoulder_y', 'left_shoulder_conf', 'right_shoulder_x',
                        'right_shoulder_y', 'right_shoulder_conf']
        
        fig, axes = plt.subplots(3, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, (feature_idx, feature_name) in enumerate(zip(key_features, feature_names)):
            axes[i].plot(features_array[:, feature_idx])
            axes[i].set_title(feature_name)
            axes[i].set_xlabel('帧数')
            axes[i].set_ylabel('值')
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        feature_path = os.path.join(output_path, 'feature_changes.png')
        plt.savefig(feature_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """主函数 - 用于测试和演示"""
    print("训练工具模块测试")
    
    # 创建组件
    pose_detector = PoseDetector()
    preprocessor = DataPreprocessor(pose_detector)
    trainer = ModelTrainer()
    visualizer = DataVisualizer()
    
    print("组件初始化完成")
    
    # 示例用法
    # 1. 处理数据集
    # preprocessor.process_video_dataset("path/to/dataset", "processed_data")
    
    # 2. 训练模型
    # X, y = trainer.prepare_training_data("processed_data")
    # results = trainer.train_traditional_ml_models(X, y)
    # trainer.train_deep_learning_model("processed_data")
    
    # 3. 可视化数据
    # visualizer.visualize_pose_data(poses_sequence, "visualization")
    
    print("训练工具模块测试完成")

if __name__ == "__main__":
    main() 