"""
摔倒检测系统测试脚本
用于验证各个模块的功能
"""

import sys
import os
import numpy as np
import cv2
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from pose_detection import PoseDetector
        print("✓ PoseDetector 导入成功")
    except Exception as e:
        print(f"✗ PoseDetector 导入失败: {e}")
        return False
    
    try:
        from fall_detection_algorithms import ThresholdFallDetector, TraditionalMLFallDetector, DeepLearningFallDetector
        print("✓ 摔倒检测算法模块导入成功")
    except Exception as e:
        print(f"✗ 摔倒检测算法模块导入失败: {e}")
        return False
    
    try:
        from alert_system import AlertManager, AlertConfig
        print("✓ 预警系统模块导入成功")
    except Exception as e:
        print(f"✗ 预警系统模块导入失败: {e}")
        return False
    
    try:
        from training_utils import DataPreprocessor, ModelTrainer, FeatureExtractor
        print("✓ 训练工具模块导入成功")
    except Exception as e:
        print(f"✗ 训练工具模块导入失败: {e}")
        return False
    
    return True

def test_pose_detector():
    """测试姿势检测器"""
    print("\n测试姿势检测器...")
    
    try:
        detector = PoseDetector()
        print("✓ PoseDetector 初始化成功")
        
        # 创建测试图像
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        test_image[:] = (128, 128, 128)  # 灰色背景
        
        # 测试检测
        poses = detector.detect_pose(test_image)
        print(f"✓ 姿势检测完成，检测到 {len(poses)} 个姿势")
        
        return True
    except Exception as e:
        print(f"✗ 姿势检测器测试失败: {e}")
        return False

def test_fall_detectors():
    """测试摔倒检测器"""
    print("\n测试摔倒检测器...")
    
    try:
        # 测试阈值检测器
        threshold_detector = ThresholdFallDetector()
        print("✓ ThresholdFallDetector 初始化成功")
        
        # 测试机器学习检测器
        ml_detector = TraditionalMLFallDetector('svm')
        print("✓ TraditionalMLFallDetector 初始化成功")
        
        # 测试深度学习检测器
        dl_detector = DeepLearningFallDetector('lstm')
        print("✓ DeepLearningFallDetector 初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ 摔倒检测器测试失败: {e}")
        return False

def test_alert_system():
    """测试预警系统"""
    print("\n测试预警系统...")
    
    try:
        alert_manager = AlertManager()
        print("✓ AlertManager 初始化成功")
        
        alert_config = AlertConfig()
        print("✓ AlertConfig 初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ 预警系统测试失败: {e}")
        return False

def test_training_utils():
    """测试训练工具"""
    print("\n测试训练工具...")
    
    try:
        from training_utils import FeatureExtractor, ModelTrainer
        
        feature_extractor = FeatureExtractor()
        print("✓ FeatureExtractor 初始化成功")
        
        model_trainer = ModelTrainer()
        print("✓ ModelTrainer 初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ 训练工具测试失败: {e}")
        return False

def test_gui_components():
    """测试GUI组件"""
    print("\n测试GUI组件...")
    
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 测试图像处理
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:] = (255, 0, 0)  # 红色
        
        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(pil_image)
        
        print("✓ GUI组件测试成功")
        root.destroy()
        
        return True
    except Exception as e:
        print(f"✗ GUI组件测试失败: {e}")
        return False

def create_test_data():
    """创建测试数据"""
    print("\n创建测试数据...")
    
    try:
        # 创建测试目录
        test_dir = "test_data"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        # 创建测试图像
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        test_image[:] = (128, 128, 128)
        
        # 保存测试图像
        test_image_path = os.path.join(test_dir, "test_image.jpg")
        cv2.imwrite(test_image_path, test_image)
        print(f"✓ 测试图像已创建: {test_image_path}")
        
        # 创建测试配置
        test_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": []
            },
            "sms": {
                "enabled": False,
                "api_key": "",
                "api_secret": "",
                "phone_numbers": []
            },
            "general": {
                "alert_cooldown": 60,
                "enable_alerts": True
            }
        }
        
        import json
        config_path = os.path.join(test_dir, "test_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        print(f"✓ 测试配置已创建: {config_path}")
        
        return True
    except Exception as e:
        print(f"✗ 创建测试数据失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("摔倒检测系统测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("姿势检测器", test_pose_detector),
        ("摔倒检测器", test_fall_detectors),
        ("预警系统", test_alert_system),
        ("训练工具", test_training_utils),
        ("GUI组件", test_gui_components),
        ("测试数据", create_test_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 测试通过")
        else:
            print(f"✗ {test_name} 测试失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常运行。")
        print("\n下一步:")
        print("1. 运行 python main.py 启动GUI")
        print("2. 或运行 python main.py --mode detect --video your_video.mp4")
    else:
        print("⚠️  部分测试失败，请检查依赖安装。")
        print("\n建议:")
        print("1. 运行 pip install -r requirements.txt")
        print("2. 检查Python版本是否为3.8+")
        print("3. 检查CUDA环境（如果使用GPU）")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 