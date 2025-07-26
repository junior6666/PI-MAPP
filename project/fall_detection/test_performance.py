"""
性能测试脚本
测试优化后的摔倒检测系统性能
"""

import cv2
import time
import numpy as np
from pose_detection import PoseDetector
from fall_detection_algorithms import ThresholdFallDetector

def test_detection_speed():
    """测试检测速度"""
    print("开始性能测试...")
    
    # 初始化检测器
    pose_detector = PoseDetector()
    threshold_detector = ThresholdFallDetector()
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 测试不同分辨率的检测速度
    resolutions = [
        (320, 240),
        (480, 360), 
        (640, 480),
        (800, 600)
    ]
    
    print("\n检测速度测试结果:")
    print("-" * 50)
    
    for width, height in resolutions:
        # 调整图像大小
        resized_image = cv2.resize(test_image, (width, height))
        
        # 测试检测速度
        times = []
        for _ in range(10):  # 测试10次取平均值
            start_time = time.time()
            
            # 姿势检测
            poses = pose_detector.detect_pose(resized_image)
            
            # 摔倒检测
            if poses:
                for pose in poses:
                    is_fall, confidence, _ = threshold_detector.detect_fall(pose)
            
            # 绘制骨架
            if poses:
                processed = pose_detector.draw_pose(resized_image, poses)
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = np.mean(times)
        fps = 1.0 / avg_time
        
        print(f"分辨率 {width}x{height}: {avg_time*1000:.1f}ms ({fps:.1f} FPS)")
    
    print("-" * 50)

def test_draw_performance():
    """测试绘制性能"""
    print("\n绘制性能测试:")
    print("-" * 50)
    
    pose_detector = PoseDetector()
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 模拟检测结果
    mock_poses = [{
        'keypoints': {
            'nose': {'x': 320, 'y': 100, 'confidence': 0.9},
            'left_shoulder': {'x': 280, 'y': 150, 'confidence': 0.8},
            'right_shoulder': {'x': 360, 'y': 150, 'confidence': 0.8},
            'left_elbow': {'x': 250, 'y': 200, 'confidence': 0.7},
            'right_elbow': {'x': 390, 'y': 200, 'confidence': 0.7},
            'left_wrist': {'x': 220, 'y': 250, 'confidence': 0.6},
            'right_wrist': {'x': 420, 'y': 250, 'confidence': 0.6},
            'left_hip': {'x': 300, 'y': 300, 'confidence': 0.8},
            'right_hip': {'x': 340, 'y': 300, 'confidence': 0.8},
            'left_knee': {'x': 290, 'y': 400, 'confidence': 0.7},
            'right_knee': {'x': 350, 'y': 400, 'confidence': 0.7},
            'left_ankle': {'x': 280, 'y': 480, 'confidence': 0.6},
            'right_ankle': {'x': 360, 'y': 480, 'confidence': 0.6}
        },
        'bbox': [250, 80, 390, 500],
        'confidence': 0.85
    }]
    
    # 测试不同绘制选项的性能
    draw_options = [
        ("完整绘制", True, True, True),
        ("仅骨架", False, True, True),
        ("仅关键点", True, False, True),
        ("仅边框", False, False, True)
    ]
    
    for name, draw_kp, draw_skel, draw_bbox in draw_options:
        times = []
        for _ in range(20):  # 测试20次
            start_time = time.time()
            processed = pose_detector.draw_pose(
                test_image, mock_poses, 
                draw_keypoints=draw_kp, 
                draw_skeleton=draw_skel, 
                draw_bbox=draw_bbox
            )
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = np.mean(times)
        fps = 1.0 / avg_time
        print(f"{name}: {avg_time*1000:.1f}ms ({fps:.1f} FPS)")
    
    print("-" * 50)

def test_memory_usage():
    """测试内存使用情况"""
    print("\n内存使用测试:")
    print("-" * 50)
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"初始内存使用: {initial_memory:.1f} MB")
    
    # 创建检测器
    pose_detector = PoseDetector()
    threshold_detector = ThresholdFallDetector()
    
    after_init_memory = process.memory_info().rss / 1024 / 1024
    print(f"初始化后内存: {after_init_memory:.1f} MB")
    print(f"检测器占用: {after_init_memory - initial_memory:.1f} MB")
    
    # 模拟视频处理
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    for i in range(100):
        poses = pose_detector.detect_pose(test_image)
        if poses:
            processed = pose_detector.draw_pose(test_image, poses)
        
        if i % 20 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"处理 {i} 帧后内存: {current_memory:.1f} MB")
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"最终内存使用: {final_memory:.1f} MB")
    print(f"内存增长: {final_memory - after_init_memory:.1f} MB")
    
    print("-" * 50)

if __name__ == "__main__":
    print("摔倒检测系统性能测试")
    print("=" * 60)
    
    try:
        test_detection_speed()
        test_draw_performance()
        test_memory_usage()
        
        print("\n性能测试完成！")
        print("\n优化建议:")
        print("1. 使用较低分辨率进行检测 (640x480 或更低)")
        print("2. 调整检测间隔以平衡速度和准确性")
        print("3. 选择适当的显示质量设置")
        print("4. 使用GPU加速 (如果可用)")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        print("请确保已安装所有依赖包") 