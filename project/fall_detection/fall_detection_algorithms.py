"""
摔倒检测算法模块
包含多种检测方法：阈值法、传统机器学习、深度学习
"""

import numpy as np
import cv2
from typing import List, Dict, Any, Tuple
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import joblib
import os

class ThresholdFallDetector:
    """基于阈值的摔倒检测器"""
    
    def __init__(self):
        self.thresholds = {
            'height_ratio': 0.6,  # 高度比例阈值
            'width_ratio': 1.2,   # 宽度比例阈值
            'angle_threshold': 45  # 角度阈值
        }
    
    def calculate_pose_ratios(self, pose: Dict[str, Any]) -> Dict[str, float]:
        """计算姿势的各种比例"""
        keypoints = pose['keypoints']
        
        # 获取关键点坐标
        left_shoulder = keypoints.get('left_shoulder', {'x': 0, 'y': 0})
        right_shoulder = keypoints.get('right_shoulder', {'x': 0, 'y': 0})
        left_hip = keypoints.get('left_hip', {'x': 0, 'y': 0})
        right_hip = keypoints.get('right_hip', {'x': 0, 'y': 0})
        left_knee = keypoints.get('left_knee', {'x': 0, 'y': 0})
        right_knee = keypoints.get('right_knee', {'x': 0, 'y': 0})
        
        # 计算躯干高度（肩膀到臀部）
        shoulder_y = (left_shoulder['y'] + right_shoulder['y']) / 2
        hip_y = (left_hip['y'] + right_hip['y']) / 2
        trunk_height = abs(shoulder_y - hip_y)
        
        # 计算腿部高度（臀部到膝盖）
        knee_y = (left_knee['y'] + right_knee['y']) / 2
        leg_height = abs(hip_y - knee_y)
        
        # 计算总高度
        total_height = trunk_height + leg_height
        
        # 计算宽度（肩膀宽度）
        shoulder_width = abs(left_shoulder['x'] - right_shoulder['x'])
        
        # 计算比例
        height_ratio = trunk_height / total_height if total_height > 0 else 0
        width_ratio = shoulder_width / total_height if total_height > 0 else 0
        
        # 计算躯干角度
        trunk_angle = self._calculate_angle(
            (left_shoulder['x'], left_shoulder['y']),
            (right_shoulder['x'], right_shoulder['y']),
            (left_hip['x'], left_hip['y']),
            (right_hip['x'], right_hip['y'])
        )
        
        return {
            'height_ratio': height_ratio,
            'width_ratio': width_ratio,
            'trunk_angle': trunk_angle,
            'total_height': total_height
        }
    
    def _calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                        p3: Tuple[float, float], p4: Tuple[float, float]) -> float:
        """计算两条线段之间的角度"""
        # 计算向量
        vec1 = (p2[0] - p1[0], p2[1] - p1[1])
        vec2 = (p4[0] - p3[0], p4[1] - p3[1])
        
        # 计算角度
        dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
        mag1 = np.sqrt(vec1[0]**2 + vec1[1]**2)
        mag2 = np.sqrt(vec2[0]**2 + vec2[1]**2)
        
        if mag1 * mag2 == 0:
            return 0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = np.clip(cos_angle, -1, 1)
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        return angle
    
    def detect_fall(self, pose: dict) -> tuple:
        """
        优化后的阈值法：
        1. 主判据：头部和腰部/脚部高度差小于肩膀到手肘距离（骨骼点8和6的距离）。
        2. 备用判据：两肩膀中点与两髋关节中点连线与垂直线夹角，超过20度判为摔倒。
        """
        keypoints = pose.get('keypoints', {})
        # COCO骨骼点索引
        # 0:nose 5:left_shoulder 6:right_shoulder 11:left_hip 12:right_hip 8:left_elbow 10:right_elbow 15:left_ankle 16:right_ankle
        def get_xy(idx_name):
            kp = keypoints.get(idx_name)
            if kp and kp['confidence'] > 0.5:
                return kp['x'], kp['y']
            return None
        # 主判据
        nose = get_xy('nose')
        mid_hip = None
        if get_xy('left_hip') and get_xy('right_hip'):
            lx, ly = get_xy('left_hip')
            rx, ry = get_xy('right_hip')
            mid_hip = ((lx+rx)/2, (ly+ry)/2)
        left_ankle = get_xy('left_ankle')
        right_ankle = get_xy('right_ankle')
        # 肩膀到手肘距离（优先左侧）
        shoulder = get_xy('left_shoulder') or get_xy('right_shoulder')
        elbow = get_xy('left_elbow') or get_xy('right_elbow')
        if shoulder and elbow:
            ref_dist = ((shoulder[0]-elbow[0])**2 + (shoulder[1]-elbow[1])**2) ** 0.5
        else:
            ref_dist = 40  # 默认值
        # 头-腰高度差
        fall1 = False
        if nose and mid_hip:
            head_hip_dy = abs(nose[1] - mid_hip[1])
            if head_hip_dy < ref_dist:
                fall1 = True
        # 头-脚高度差
        fall2 = False
        if nose and left_ankle and right_ankle:
            foot_y = (left_ankle[1] + right_ankle[1]) / 2
            head_foot_dy = abs(nose[1] - foot_y)
            if head_foot_dy < ref_dist:
                fall2 = True
        # 备用判据：肩膀中点-髋关节中点连线与垂直线夹角
        angle_fall = False
        if get_xy('left_shoulder') and get_xy('right_shoulder') and get_xy('left_hip') and get_xy('right_hip'):
            sx, sy = get_xy('left_shoulder')
            sx2, sy2 = get_xy('right_shoulder')
            shoulder_mid = ((sx+sx2)/2, (sy+sy2)/2)
            hx, hy = get_xy('left_hip')
            hx2, hy2 = get_xy('right_hip')
            hip_mid = ((hx+hx2)/2, (hy+hy2)/2)
            dx = hip_mid[0] - shoulder_mid[0]
            dy = hip_mid[1] - shoulder_mid[1]
            if dy != 0:
                angle = abs(np.degrees(np.arctan2(dx, dy)))
                if angle > 20:
                    angle_fall = True
        # 综合判定
        is_fall = fall1 or fall2 or angle_fall
        confidence = 1.0 if is_fall else 0.0
        features = {
            'head_hip_dy': head_hip_dy if nose and mid_hip else -1,
            'head_foot_dy': head_foot_dy if nose and left_ankle and right_ankle else -1,
            'ref_dist': ref_dist,
            'angle': angle if 'angle' in locals() else -1
        }
        return is_fall, confidence, features

class TraditionalMLFallDetector:
    """传统机器学习摔倒检测器"""
    
    def __init__(self, model_type: str = 'svm'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def extract_features(self, poses: List[Dict[str, Any]]) -> np.ndarray:
        """提取特征向量"""
        features = []
        
        for pose in poses:
            pose_features = []
            keypoints = pose['keypoints']
            
            # 基础特征：关键点坐标和置信度
            for name in ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 
                        'left_knee', 'right_knee', 'left_ankle', 'right_ankle']:
                if name in keypoints:
                    kp = keypoints[name]
                    pose_features.extend([kp['x'], kp['y'], kp['confidence']])
                else:
                    pose_features.extend([0, 0, 0])
            
            # 几何特征
            ratios = self._calculate_geometric_features(pose)
            pose_features.extend(list(ratios.values()))
            
            features.append(pose_features)
        
        return np.array(features)
    
    def _calculate_geometric_features(self, pose: Dict[str, Any]) -> Dict[str, float]:
        """计算几何特征"""
        keypoints = pose['keypoints']
        
        # 计算各种比例和角度
        features = {}
        
        # 躯干长度比例
        if 'left_shoulder' in keypoints and 'left_hip' in keypoints:
            trunk_length = np.sqrt(
                (keypoints['left_shoulder']['x'] - keypoints['left_hip']['x'])**2 +
                (keypoints['left_shoulder']['y'] - keypoints['left_hip']['y'])**2
            )
            features['trunk_length'] = trunk_length
        else:
            features['trunk_length'] = 0
        
        # 腿部长度比例
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
        
        return features
    
    def _calculate_trunk_angle(self, keypoints: Dict[str, Any]) -> float:
        """计算躯干角度"""
        shoulder_center_x = (keypoints['left_shoulder']['x'] + keypoints['right_shoulder']['x']) / 2
        shoulder_center_y = (keypoints['left_shoulder']['y'] + keypoints['right_shoulder']['y']) / 2
        hip_center_x = (keypoints['left_hip']['x'] + keypoints['right_hip']['x']) / 2
        hip_center_y = (keypoints['left_hip']['y'] + keypoints['right_hip']['y']) / 2
        
        # 计算与垂直线的角度
        dx = hip_center_x - shoulder_center_x
        dy = hip_center_y - shoulder_center_y
        
        if dx == 0:
            return 0
        
        angle = np.arctan2(dx, dy) * 180 / np.pi
        return abs(angle)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """训练模型"""
        # 数据预处理
        X_scaled = self.scaler.fit_transform(X)
        
        # 选择模型
        if self.model_type == 'knn':
            self.model = KNeighborsClassifier(n_neighbors=5)
        elif self.model_type == 'svm':
            self.model = SVC(kernel='rbf', probability=True)
        elif self.model_type == 'rf':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        # 训练模型
        self.model.fit(X_scaled, y)
        self.is_trained = True
        print(f"{self.model_type.upper()} 模型训练完成")
    
    def predict(self, poses: List[Dict[str, Any]]) -> Tuple[List[bool], List[float]]:
        """预测摔倒"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        features = self.extract_features(poses)
        if len(features) == 0:
            return [], []
        
        X_scaled = self.scaler.transform(features)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]  # 摔倒的概率
        
        return predictions.tolist(), probabilities.tolist()
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.is_trained:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'model_type': self.model_type
            }
            joblib.dump(model_data, filepath)
            print(f"模型已保存到: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.model_type = model_data['model_type']
            self.is_trained = True
            print(f"模型已从 {filepath} 加载")

class PoseDataset(Dataset):
    """姿势数据集"""
    
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

class LSTMFallDetector(nn.Module):
    """LSTM摔倒检测器"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMFallDetector, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 2)  # 2类：正常/摔倒
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # 取最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        output = self.dropout(last_output)
        output = self.fc(output)
        return output

class DeepLearningFallDetector:
    """深度学习摔倒检测器"""
    
    def __init__(self, model_type: str = 'lstm', input_size: int = 51):
        self.model_type = model_type
        self.input_size = input_size
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_trained = False
        
    def create_model(self):
        """创建模型"""
        if self.model_type == 'lstm':
            self.model = LSTMFallDetector(self.input_size)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        self.model.to(self.device)
    
    def prepare_sequence_data(self, pose_sequences: List[List[Dict[str, Any]]], 
                            labels: List[int], sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """准备序列数据"""
        features_list = []
        labels_list = []
        
        for sequence, label in zip(pose_sequences, labels):
            if len(sequence) < sequence_length:
                continue
            
            # 提取特征序列
            sequence_features = []
            for poses in sequence[-sequence_length:]:  # 取最后sequence_length帧
                if poses:
                    pose_features = self._extract_pose_features(poses[0])  # 取第一个人的姿势
                else:
                    pose_features = np.zeros(self.input_size)
                sequence_features.append(pose_features)
            
            features_list.append(sequence_features)
            labels_list.append(label)
        
        return np.array(features_list), np.array(labels_list)
    
    def _extract_pose_features(self, pose: Dict[str, Any]) -> np.ndarray:
        """提取单个姿势的特征"""
        keypoints = pose['keypoints']
        features = []
        
        # 关键点坐标和置信度
        for name in ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 
                    'left_knee', 'right_knee', 'left_ankle', 'right_ankle']:
            if name in keypoints:
                kp = keypoints[name]
                features.extend([kp['x'], kp['y'], kp['confidence']])
            else:
                features.extend([0, 0, 0])
        
        # 几何特征
        geometric_features = self._calculate_geometric_features(pose)
        features.extend(list(geometric_features.values()))
        
        return np.array(features)
    
    def _calculate_geometric_features(self, pose: Dict[str, Any]) -> Dict[str, float]:
        """计算几何特征"""
        keypoints = pose['keypoints']
        features = {}
        
        # 计算躯干角度
        if all(k in keypoints for k in ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']):
            angle = self._calculate_trunk_angle(keypoints)
            features['trunk_angle'] = angle
        else:
            features['trunk_angle'] = 0
        
        # 计算高度比例
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
    
    def train(self, pose_sequences: List[List[Dict[str, Any]]], labels: List[int], 
              epochs: int = 50, batch_size: int = 32, learning_rate: float = 0.001):
        """训练模型"""
        if self.model is None:
            self.create_model()
        
        # 准备数据
        X, y = self.prepare_sequence_data(pose_sequences, labels)
        
        if len(X) == 0:
            print("没有足够的数据进行训练")
            return
        
        # 划分训练集和验证集
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 创建数据加载器
        train_dataset = PoseDataset(X_train, y_train)
        val_dataset = PoseDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 定义损失函数和优化器
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # 训练循环
        for epoch in range(epochs):
            self.model.train()
            train_loss = 0
            for batch_features, batch_labels in train_loader:
                batch_features = batch_features.to(self.device)
                batch_labels = batch_labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_features)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # 验证
            self.model.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch_features, batch_labels in val_loader:
                    batch_features = batch_features.to(self.device)
                    batch_labels = batch_labels.to(self.device)
                    
                    outputs = self.model(batch_features)
                    loss = criterion(outputs, batch_labels)
                    val_loss += loss.item()
                    
                    _, predicted = torch.max(outputs.data, 1)
                    total += batch_labels.size(0)
                    correct += (predicted == batch_labels).sum().item()
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Train Loss: {train_loss/len(train_loader):.4f}, '
                      f'Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {100*correct/total:.2f}%')
        
        self.is_trained = True
        print("深度学习模型训练完成")
    
    def predict(self, pose_sequence: List[Dict[str, Any]], sequence_length: int = 10) -> Tuple[bool, float]:
        """预测摔倒"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        if len(pose_sequence) < sequence_length:
            return False, 0.0
        
        # 准备输入数据
        sequence_features = []
        for poses in pose_sequence[-sequence_length:]:
            if poses:
                pose_features = self._extract_pose_features(poses[0])
            else:
                pose_features = np.zeros(self.input_size)
            sequence_features.append(pose_features)
        
        # 转换为tensor
        input_tensor = torch.FloatTensor([sequence_features]).to(self.device)
        
        # 预测
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            fall_probability = probabilities[0, 1].item()
            prediction = fall_probability > 0.5
        
        return prediction, fall_probability
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.is_trained:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'model_type': self.model_type,
                'input_size': self.input_size
            }, filepath)
            print(f"模型已保存到: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        if os.path.exists(filepath):
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model_type = checkpoint['model_type']
            self.input_size = checkpoint['input_size']
            self.create_model()
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.is_trained = True
            print(f"模型已从 {filepath} 加载")

if __name__ == "__main__":
    # 测试代码
    print("测试阈值检测器...")
    threshold_detector = ThresholdFallDetector()
    
    print("测试传统机器学习检测器...")
    ml_detector = TraditionalMLFallDetector('svm')
    
    print("测试深度学习检测器...")
    dl_detector = DeepLearningFallDetector('lstm') 