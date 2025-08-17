#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步态分析器核心类
实现关节角度计算、步态周期分析、支撑相检测等功能
"""

import json
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
import cv2
import os


class GaitAnalyzer:
    """步态分析器"""
    
    def __init__(self):
        self.keypoints_data = None
        self.video_fps = 30
        self.results = {}
        
        # COCO关键点索引定义
        self.keypoint_indices = {
            'nose': 0,
            'left_eye': 1, 'right_eye': 2,
            'left_ear': 3, 'right_ear': 4,
            'left_shoulder': 5, 'right_shoulder': 6,
            'left_elbow': 7, 'right_elbow': 8,
            'left_wrist': 9, 'right_wrist': 10,
            'left_hip': 11, 'right_hip': 12,
            'left_knee': 13, 'right_knee': 14,
            'left_ankle': 15, 'right_ankle': 16
        }
    
    def analyze(self, video_path, keypoints_path, progress_callback=None):
        """执行完整的步态分析"""
        try:
            # 加载数据
            if progress_callback:
                progress_callback(10)
            
            self.load_keypoints_data(keypoints_path)
            self.load_video_info(video_path)
            
            # 计算关节角度
            if progress_callback:
                progress_callback(30)
            
            raw_angles = self.calculate_joint_angles()
            smoothed_angles = self.smooth_angles(raw_angles)
            
            # 步态周期分析
            if progress_callback:
                progress_callback(60)
            
            gait_cycles = self.detect_gait_cycles(smoothed_angles)
            
            # 支撑相分析
            if progress_callback:
                progress_callback(80)
            
            phase_analysis = self.analyze_stance_swing_phases(smoothed_angles)
            
            # 计算步态参数
            gait_params = self.calculate_gait_parameters(gait_cycles, phase_analysis)
            
            # 数据质量评估
            quality_info = self.assess_data_quality()
            
            if progress_callback:
                progress_callback(100)
            
            # 组装结果
            self.results = {
                'raw_angles': raw_angles,
                'smoothed_angles': smoothed_angles,
                'gait_cycles': gait_cycles,
                'phase_analysis': phase_analysis,
                'gait_params': gait_params,
                'quality_info': quality_info,
                'keypoints': self.keypoints_data,
                'video_fps': self.video_fps
            }
            
            return self.results
            
        except Exception as e:
            raise Exception(f"步态分析失败: {str(e)}")
    
    def load_keypoints_data(self, keypoints_path):
        """加载关键点数据"""
        try:
            with open(keypoints_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同格式的关键点数据
            if isinstance(data, list):
                self.keypoints_data = data
            elif isinstance(data, dict) and 'keypoints' in data:
                self.keypoints_data = data['keypoints']
            else:
                raise ValueError("不支持的关键点数据格式")
                
        except Exception as e:
            raise Exception(f"加载关键点数据失败: {str(e)}")
    
    def load_video_info(self, video_path):
        """加载视频信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            self.video_fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        except Exception as e:
            print(f"警告: 无法获取视频帧率，使用默认值30fps: {str(e)}")
            self.video_fps = 30
    
    def calculate_joint_angles(self):
        """计算关节角度"""
        angles = {
            'left_hip': [],
            'right_hip': [],
            'left_knee': [],
            'right_knee': [],
            'left_ankle': [],
            'right_ankle': [],
            'trunk_sway': [],
            'left_shoulder': [],
            'right_shoulder': []
        }
        
        for frame_keypoints in self.keypoints_data:
            if not frame_keypoints:
                # 添加空值
                for key in angles:
                    angles[key].append(np.nan)
                continue
            
            # 髋关节角度 (躯干与大腿的角度)
            left_hip_angle = self.calculate_hip_angle(frame_keypoints, 'left')
            right_hip_angle = self.calculate_hip_angle(frame_keypoints, 'right')
            angles['left_hip'].append(left_hip_angle)
            angles['right_hip'].append(right_hip_angle)
            
            # 膝关节角度 (大腿与小腿的角度)
            left_knee_angle = self.calculate_knee_angle(frame_keypoints, 'left')
            right_knee_angle = self.calculate_knee_angle(frame_keypoints, 'right')
            angles['left_knee'].append(left_knee_angle)
            angles['right_knee'].append(right_knee_angle)
            
            # 踝关节角度 (小腿与足部的角度)
            left_ankle_angle = self.calculate_ankle_angle(frame_keypoints, 'left')
            right_ankle_angle = self.calculate_ankle_angle(frame_keypoints, 'right')
            angles['left_ankle'].append(left_ankle_angle)
            angles['right_ankle'].append(right_ankle_angle)
            
            # 躯干摆动角度 (相对于垂直线的角度)
            trunk_angle = self.calculate_trunk_sway(frame_keypoints)
            angles['trunk_sway'].append(trunk_angle)
            
            # 肩关节角度
            left_shoulder_angle = self.calculate_shoulder_angle(frame_keypoints, 'left')
            right_shoulder_angle = self.calculate_shoulder_angle(frame_keypoints, 'right')
            angles['left_shoulder'].append(left_shoulder_angle)
            angles['right_shoulder'].append(right_shoulder_angle)
        
        return angles
    
    def calculate_hip_angle(self, keypoints, side):
        """计算髋关节角度"""
        try:
            # 获取关键点
            shoulder_idx = self.keypoint_indices[f'{side}_shoulder']
            hip_idx = self.keypoint_indices[f'{side}_hip']
            knee_idx = self.keypoint_indices[f'{side}_knee']
            
            shoulder = keypoints[shoulder_idx][:2]
            hip = keypoints[hip_idx][:2]
            knee = keypoints[knee_idx][:2]
            
            # 计算向量
            trunk_vector = np.array(shoulder) - np.array(hip)
            thigh_vector = np.array(knee) - np.array(hip)
            
            # 计算角度
            angle = self.calculate_angle_between_vectors(trunk_vector, thigh_vector)
            return angle
            
        except (IndexError, ValueError):
            return np.nan
    
    def calculate_knee_angle(self, keypoints, side):
        """计算膝关节角度"""
        try:
            # 获取关键点
            hip_idx = self.keypoint_indices[f'{side}_hip']
            knee_idx = self.keypoint_indices[f'{side}_knee']
            ankle_idx = self.keypoint_indices[f'{side}_ankle']
            
            hip = keypoints[hip_idx][:2]
            knee = keypoints[knee_idx][:2]
            ankle = keypoints[ankle_idx][:2]
            
            # 计算向量
            thigh_vector = np.array(hip) - np.array(knee)
            shin_vector = np.array(ankle) - np.array(knee)
            
            # 计算角度
            angle = self.calculate_angle_between_vectors(thigh_vector, shin_vector)
            return angle
            
        except (IndexError, ValueError):
            return np.nan
    
    def calculate_ankle_angle(self, keypoints, side):
        """计算踝关节角度"""
        try:
            # 获取关键点
            knee_idx = self.keypoint_indices[f'{side}_knee']
            ankle_idx = self.keypoint_indices[f'{side}_ankle']
            
            knee = keypoints[knee_idx][:2]
            ankle = keypoints[ankle_idx][:2]
            
            # 计算小腿向量
            shin_vector = np.array(ankle) - np.array(knee)
            
            # 垂直向量（代表足部）
            vertical_vector = np.array([0, 1])
            
            # 计算角度
            angle = self.calculate_angle_between_vectors(shin_vector, vertical_vector)
            return angle
            
        except (IndexError, ValueError):
            return np.nan
    
    def calculate_trunk_sway(self, keypoints):
        """计算躯干摆动角度"""
        try:
            # 获取肩部中点和髋部中点
            left_shoulder = keypoints[self.keypoint_indices['left_shoulder']][:2]
            right_shoulder = keypoints[self.keypoint_indices['right_shoulder']][:2]
            left_hip = keypoints[self.keypoint_indices['left_hip']][:2]
            right_hip = keypoints[self.keypoint_indices['right_hip']][:2]
            
            shoulder_center = np.array([(left_shoulder[0] + right_shoulder[0]) / 2,
                                      (left_shoulder[1] + right_shoulder[1]) / 2])
            hip_center = np.array([(left_hip[0] + right_hip[0]) / 2,
                                  (left_hip[1] + right_hip[1]) / 2])
            
            # 计算躯干向量
            trunk_vector = shoulder_center - hip_center
            
            # 垂直向量
            vertical_vector = np.array([0, -1])  # 向上
            
            # 计算角度
            angle = self.calculate_angle_between_vectors(trunk_vector, vertical_vector)
            return angle
            
        except (IndexError, ValueError):
            return np.nan
    
    def calculate_shoulder_angle(self, keypoints, side):
        """计算肩关节角度"""
        try:
            # 获取关键点
            shoulder_idx = self.keypoint_indices[f'{side}_shoulder']
            elbow_idx = self.keypoint_indices[f'{side}_elbow']
            
            shoulder = keypoints[shoulder_idx][:2]
            elbow = keypoints[elbow_idx][:2]
            
            # 计算手臂向量
            arm_vector = np.array(elbow) - np.array(shoulder)
            
            # 垂直向量
            vertical_vector = np.array([0, 1])
            
            # 计算角度
            angle = self.calculate_angle_between_vectors(arm_vector, vertical_vector)
            return angle
            
        except (IndexError, ValueError):
            return np.nan
    
    def calculate_angle_between_vectors(self, v1, v2):
        """计算两个向量之间的角度"""
        try:
            # 标准化向量
            v1_norm = v1 / np.linalg.norm(v1)
            v2_norm = v2 / np.linalg.norm(v2)
            
            # 计算点积
            dot_product = np.dot(v1_norm, v2_norm)
            
            # 确保点积在有效范围内
            dot_product = np.clip(dot_product, -1.0, 1.0)
            
            # 计算角度（弧度转度数）
            angle = np.arccos(dot_product) * 180 / np.pi
            
            return angle
            
        except (ValueError, ZeroDivisionError):
            return np.nan
    
    def smooth_angles(self, raw_angles, window_length=15, polyorder=3):
        """平滑角度数据"""
        smoothed_angles = {}
        
        for joint, angles in raw_angles.items():
            # 转换为numpy数组
            angles_array = np.array(angles)
            
            # 处理NaN值
            valid_indices = ~np.isnan(angles_array)
            
            if np.sum(valid_indices) < window_length:
                # 数据点太少，使用简单的插值
                smoothed_angles[joint] = self.interpolate_missing_values(angles_array)
            else:
                # 使用Savitzky-Golay滤波器
                try:
                    # 先插值填补缺失值
                    interpolated = self.interpolate_missing_values(angles_array)
                    
                    # 确保窗口长度为奇数且不超过数据长度
                    window_len = min(window_length, len(interpolated))
                    if window_len % 2 == 0:
                        window_len -= 1
                    window_len = max(3, window_len)
                    
                    # 应用Savitzky-Golay滤波器
                    smoothed = signal.savgol_filter(interpolated, window_len, polyorder)
                    smoothed_angles[joint] = smoothed.tolist()
                    
                except Exception:
                    # 如果平滑失败，使用插值结果
                    smoothed_angles[joint] = self.interpolate_missing_values(angles_array)
        
        return smoothed_angles
    
    def interpolate_missing_values(self, angles_array):
        """插值填补缺失值"""
        valid_indices = ~np.isnan(angles_array)
        
        if np.sum(valid_indices) < 2:
            # 有效数据点太少，用均值填充
            mean_val = np.nanmean(angles_array)
            if np.isnan(mean_val):
                mean_val = 0
            return np.full_like(angles_array, mean_val, dtype=float)
        
        # 使用线性插值
        valid_x = np.where(valid_indices)[0]
        valid_y = angles_array[valid_indices]
        
        if len(valid_x) >= 2:
            # 创建插值函数
            f = interp1d(valid_x, valid_y, kind='linear', 
                        bounds_error=False, fill_value='extrapolate')
            
            # 插值所有位置
            all_x = np.arange(len(angles_array))
            interpolated = f(all_x)
            
            return interpolated
        else:
            return angles_array
    
    def detect_gait_cycles(self, smoothed_angles):
        """检测步态周期"""
        cycles = []
        
        # 使用膝关节角度检测步态周期
        for side in ['left', 'right']:
            knee_angles = smoothed_angles[f'{side}_knee']
            side_cycles = self.detect_cycles_from_angles(knee_angles, side)
            cycles.extend(side_cycles)
        
        # 按时间排序
        cycles.sort(key=lambda x: x['start_frame'])
        
        return cycles
    
    def detect_cycles_from_angles(self, angles, side):
        """从角度数据中检测周期"""
        cycles = []
        
        try:
            # 找到峰值（代表步态周期的特征点）
            angles_array = np.array(angles)
            
            # 使用scipy找峰值
            peaks, _ = signal.find_peaks(angles_array, 
                                       height=np.nanmean(angles_array),
                                       distance=int(self.video_fps * 0.8))  # 最小间隔0.8秒
            
            # 从峰值确定周期
            for i in range(len(peaks) - 1):
                start_frame = peaks[i]
                end_frame = peaks[i + 1]
                
                cycle = {
                    'side': side,
                    'start_frame': int(start_frame),
                    'end_frame': int(end_frame),
                    'duration': (end_frame - start_frame) / self.video_fps,
                    'peak_angle': float(angles_array[peaks[i]]),
                    'angles': angles_array[start_frame:end_frame].tolist()
                }
                
                cycles.append(cycle)
                
        except Exception as e:
            print(f"检测{side}侧步态周期时出错: {str(e)}")
        
        return cycles
    
    def analyze_stance_swing_phases(self, smoothed_angles):
        """分析支撑相和摆动相"""
        phase_analysis = {
            'left_phases': [],
            'right_phases': [],
            'timeline': []
        }
        
        for side in ['left', 'right']:
            ankle_angles = smoothed_angles[f'{side}_ankle']
            knee_angles = smoothed_angles[f'{side}_knee']
            
            phases = self.detect_stance_swing_phases(ankle_angles, knee_angles, side)
            phase_analysis[f'{side}_phases'] = phases
            
            # 添加到时间线
            for phase in phases:
                phase_analysis['timeline'].append({
                    'side': side,
                    'type': phase['type'],
                    'start': phase['start_frame'],
                    'end': phase['end_frame']
                })
        
        # 按时间排序时间线
        phase_analysis['timeline'].sort(key=lambda x: x['start'])
        
        return phase_analysis
    
    def detect_stance_swing_phases(self, ankle_angles, knee_angles, side):
        """检测支撑相和摆动相"""
        phases = []
        
        try:
            # 结合踝关节和膝关节角度信息
            ankle_array = np.array(ankle_angles)
            knee_array = np.array(knee_angles)
            
            # 简化的相位检测：基于膝关节角度变化
            # 膝关节弯曲增加时通常是摆动相
            knee_velocity = np.gradient(knee_array)
            
            # 找到相位转换点
            threshold = np.nanstd(knee_velocity) * 0.5
            
            is_swing = knee_velocity > threshold
            phase_changes = np.diff(is_swing.astype(int))
            
            swing_starts = np.where(phase_changes == 1)[0] + 1
            swing_ends = np.where(phase_changes == -1)[0] + 1
            
            # 确保有配对的开始和结束
            if len(swing_starts) > 0 and len(swing_ends) > 0:
                if swing_starts[0] > swing_ends[0]:
                    swing_ends = swing_ends[1:]
                if len(swing_starts) > len(swing_ends):
                    swing_starts = swing_starts[:-1]
                
                # 生成相位信息
                for i, (start, end) in enumerate(zip(swing_starts, swing_ends)):
                    # 摆动相
                    phases.append({
                        'type': 'swing',
                        'start_frame': int(start),
                        'end_frame': int(end),
                        'duration': (end - start) / self.video_fps
                    })
                    
                    # 支撑相（下一个摆动相开始前）
                    if i < len(swing_ends) - 1:
                        next_start = swing_starts[i + 1]
                        phases.append({
                            'type': 'stance',
                            'start_frame': int(end),
                            'end_frame': int(next_start),
                            'duration': (next_start - end) / self.video_fps
                        })
                        
        except Exception as e:
            print(f"检测{side}侧支撑相和摆动相时出错: {str(e)}")
        
        return phases
    
    def calculate_gait_parameters(self, gait_cycles, phase_analysis):
        """计算步态参数"""
        params = {}
        
        # 基本步态参数
        if gait_cycles:
            cycle_durations = [cycle['duration'] for cycle in gait_cycles]
            params['avg_cycle_duration'] = np.mean(cycle_durations)
            params['cycle_duration_std'] = np.std(cycle_durations)
            
            # 步频（步/分钟）
            params['step_frequency'] = 60 / np.mean(cycle_durations) if cycle_durations else 0
            
            # 简化的步长估算（基于图像像素，需要实际标定）
            params['avg_stride_length'] = 120  # 示例值，需要实际计算
            params['avg_step_width'] = 15     # 示例值，需要实际计算
            
        # 相位分析参数
        left_phases = phase_analysis.get('left_phases', [])
        right_phases = phase_analysis.get('right_phases', [])
        
        # 支撑相和摆动相比例
        left_stance_phases = [p for p in left_phases if p['type'] == 'stance']
        left_swing_phases = [p for p in left_phases if p['type'] == 'swing']
        
        if left_stance_phases and left_swing_phases:
            total_left_time = sum(p['duration'] for p in left_phases)
            stance_time = sum(p['duration'] for p in left_stance_phases)
            swing_time = sum(p['duration'] for p in left_swing_phases)
            
            params['left_support_ratio'] = stance_time / total_left_time if total_left_time > 0 else 0
            params['left_swing_ratio'] = swing_time / total_left_time if total_left_time > 0 else 0
            params['avg_stance_time'] = stance_time / len(left_stance_phases) if left_stance_phases else 0
            params['avg_swing_time'] = swing_time / len(left_swing_phases) if left_swing_phases else 0
        
        # 右侧类似计算
        right_stance_phases = [p for p in right_phases if p['type'] == 'stance']
        right_swing_phases = [p for p in right_phases if p['type'] == 'swing']
        
        if right_stance_phases and right_swing_phases:
            total_right_time = sum(p['duration'] for p in right_phases)
            stance_time = sum(p['duration'] for p in right_stance_phases)
            swing_time = sum(p['duration'] for p in right_swing_phases)
            
            params['right_support_ratio'] = stance_time / total_right_time if total_right_time > 0 else 0
            params['right_swing_ratio'] = swing_time / total_right_time if total_right_time > 0 else 0
        
        # 对称性参数
        left_support = params.get('left_support_ratio', 0)
        right_support = params.get('right_support_ratio', 0)
        
        if left_support > 0 and right_support > 0:
            params['left_right_symmetry'] = (1 - abs(left_support - right_support) / max(left_support, right_support)) * 100
        else:
            params['left_right_symmetry'] = 0
        
        # 示例对称性参数
        params['temporal_symmetry'] = 85.0  # 需要实际计算
        params['spatial_symmetry'] = 82.0   # 需要实际计算
        params['double_support_ratio'] = 0.12  # 需要实际计算
        
        return params
    
    def assess_data_quality(self):
        """评估数据质量"""
        quality_info = {}
        
        if not self.keypoints_data:
            return {
                'data_completeness': 0.0,
                'detection_confidence': 0.0,
                'smoothing_quality': 0.0
            }
        
        # 数据完整性
        total_frames = len(self.keypoints_data)
        valid_frames = sum(1 for frame in self.keypoints_data if frame and len(frame) > 0)
        quality_info['data_completeness'] = valid_frames / total_frames if total_frames > 0 else 0
        
        # 检测置信度（基于关键点的置信度）
        confidence_scores = []
        for frame in self.keypoints_data:
            if frame:
                for keypoint in frame:
                    if len(keypoint) >= 3:  # 包含置信度
                        confidence_scores.append(keypoint[2])
        
        quality_info['detection_confidence'] = np.mean(confidence_scores) if confidence_scores else 0
        
        # 平滑质量（基于数据的连续性）
        quality_info['smoothing_quality'] = 0.85  # 示例值，需要实际计算
        
        return quality_info
    
    def save_results(self, file_path):
        """保存分析结果"""
        try:
            if file_path.endswith('.json'):
                # 保存为JSON格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
            elif file_path.endswith('.xlsx'):
                # 保存为Excel格式
                self.save_to_excel(file_path)
            
            else:
                raise ValueError("不支持的文件格式，请使用.json或.xlsx")
                
        except Exception as e:
            raise Exception(f"保存结果失败: {str(e)}")
    
    def save_to_excel(self, file_path):
        """保存为Excel格式"""
        try:
            import pandas as pd
            
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                # 保存基本参数
                if 'gait_params' in self.results:
                    params_df = pd.DataFrame([self.results['gait_params']])
                    params_df.to_excel(writer, sheet_name='步态参数', index=False)
                
                # 保存角度数据
                if 'smoothed_angles' in self.results:
                    angles_df = pd.DataFrame(self.results['smoothed_angles'])
                    angles_df.to_excel(writer, sheet_name='关节角度', index=False)
                
                # 保存步态周期
                if 'gait_cycles' in self.results:
                    cycles_df = pd.DataFrame(self.results['gait_cycles'])
                    cycles_df.to_excel(writer, sheet_name='步态周期', index=False)
                    
        except ImportError:
            raise Exception("需要安装pandas和xlsxwriter库来保存Excel文件")
        except Exception as e:
            raise Exception(f"保存Excel文件失败: {str(e)}")