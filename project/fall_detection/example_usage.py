"""
摔倒检测系统使用示例
演示如何使用各个模块进行摔倒检测
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def example_pose_detection():
    """示例：人体姿势检测"""
    print("=" * 50)
    print("示例1: 人体姿势检测")
    print("=" * 50)
    
    from pose_detection import PoseDetector
    
    # 初始化检测器
    detector = PoseDetector()
    
    # 创建测试图像（模拟摄像头输入）
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:] = (128, 128, 128)  # 灰色背景
    
    # 检测姿势
    poses = detector.detect_pose(test_image)
    
    print(f"检测到 {len(poses)} 个人体姿势")
    
    if poses:
        pose = poses[0]
        keypoints = pose['keypoints']
        print("关键点信息:")
        for name, kp in keypoints.items():
            if kp['confidence'] > 0.5:
                print(f"  {name}: ({kp['x']:.1f}, {kp['y']:.1f}), 置信度: {kp['confidence']:.2f}")
    
    return poses

def example_threshold_detection():
    """示例：阈值法摔倒检测"""
    print("\n" + "=" * 50)
    print("示例2: 阈值法摔倒检测")
    print("=" * 50)
    
    from fall_detection_algorithms import ThresholdFallDetector
    
    # 初始化检测器
    detector = ThresholdFallDetector()
    
    # 模拟姿势数据（摔倒状态）
    fall_pose = {
        'keypoints': {
            'left_shoulder': {'x': 100, 'y': 80, 'confidence': 0.9},
            'right_shoulder': {'x': 120, 'y': 80, 'confidence': 0.9},
            'left_hip': {'x': 100, 'y': 150, 'confidence': 0.8},
            'right_hip': {'x': 120, 'y': 150, 'confidence': 0.8},
            'left_knee': {'x': 100, 'y': 200, 'confidence': 0.7},
            'right_knee': {'x': 120, 'y': 200, 'confidence': 0.7}
        }
    }
    
    # 检测摔倒
    is_fall, confidence, features = detector.detect_fall(fall_pose)
    
    print(f"检测结果: {'摔倒' if is_fall else '正常'}")
    print(f"置信度: {confidence:.2f}")
    print("特征值:")
    for name, value in features.items():
        print(f"  {name}: {value:.2f}")

def example_ml_detection():
    """示例：机器学习摔倒检测"""
    print("\n" + "=" * 50)
    print("示例3: 机器学习摔倒检测")
    print("=" * 50)
    
    from fall_detection_algorithms import TraditionalMLFallDetector
    
    # 初始化检测器
    detector = TraditionalMLFallDetector('svm')
    
    # 模拟训练数据
    print("注意: 机器学习模型需要训练数据才能正常工作")
    print("这里只是演示如何初始化和使用")
    
    # 模拟姿势数据
    poses = [{
        'keypoints': {
            'nose': {'x': 110, 'y': 60, 'confidence': 0.9},
            'left_shoulder': {'x': 100, 'y': 80, 'confidence': 0.9},
            'right_shoulder': {'x': 120, 'y': 80, 'confidence': 0.9},
            'left_hip': {'x': 100, 'y': 150, 'confidence': 0.8},
            'right_hip': {'x': 120, 'y': 150, 'confidence': 0.8},
            'left_knee': {'x': 100, 'y': 200, 'confidence': 0.7},
            'right_knee': {'x': 120, 'y': 200, 'confidence': 0.7},
            'left_ankle': {'x': 100, 'y': 250, 'confidence': 0.6},
            'right_ankle': {'x': 120, 'y': 250, 'confidence': 0.6}
        }
    }]
    
    print("姿势数据已准备")
    print("要使用机器学习检测，需要先训练模型")

def example_alert_system():
    """示例：预警系统"""
    print("\n" + "=" * 50)
    print("示例4: 预警系统")
    print("=" * 50)
    
    from alert_system import AlertManager
    
    # 初始化预警管理器
    alert_manager = AlertManager()
    
    # 配置邮箱预警（示例配置，需要真实邮箱信息）
    print("配置邮箱预警...")
    print("注意: 需要真实的邮箱配置才能发送预警")
    
    # 模拟预警
    print("模拟发送摔倒预警...")
    alert_manager.send_fall_alert(0.85, None, "客厅")
    
    print("预警系统演示完成")

def example_gui_components():
    """示例：GUI组件"""
    print("\n" + "=" * 50)
    print("示例5: GUI组件")
    print("=" * 50)
    
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
        
        # 创建测试窗口
        root = tk.Tk()
        root.title("GUI组件测试")
        root.geometry("400x300")
        
        # 创建标签
        label = tk.Label(root, text="摔倒检测系统GUI组件测试", font=("Arial", 14))
        label.pack(pady=20)
        
        # 创建按钮
        def test_button():
            print("按钮点击测试成功")
        
        button = tk.Button(root, text="测试按钮", command=test_button)
        button.pack(pady=10)
        
        # 创建图像显示区域
        # 创建测试图像
        test_image = np.zeros((200, 300, 3), dtype=np.uint8)
        test_image[:] = (0, 255, 0)  # 绿色背景
        
        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(pil_image)
        
        # 显示图像
        image_label = tk.Label(root, image=photo)
        image_label.image = photo  # 保持引用
        image_label.pack(pady=10)
        
        print("GUI组件测试窗口已创建")
        print("点击窗口中的按钮进行测试")
        print("关闭窗口继续...")
        
        # 运行GUI（非阻塞）
        root.after(5000, root.destroy)  # 5秒后自动关闭
        root.mainloop()
        
    except Exception as e:
        print(f"GUI组件测试失败: {e}")

def example_complete_pipeline():
    """示例：完整检测流程"""
    print("\n" + "=" * 50)
    print("示例6: 完整检测流程")
    print("=" * 50)
    
    from pose_detection import PoseDetector
    from fall_detection_algorithms import ThresholdFallDetector
    from alert_system import AlertManager
    
    print("初始化检测组件...")
    
    # 初始化所有组件
    pose_detector = PoseDetector()
    fall_detector = ThresholdFallDetector()
    alert_manager = AlertManager()
    
    print("组件初始化完成")
    
    # 模拟视频帧处理
    print("模拟处理视频帧...")
    
    for frame_num in range(5):
        print(f"\n处理第 {frame_num + 1} 帧:")
        
        # 1. 姿势检测
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        test_image[:] = (128, 128, 128)
        
        poses = pose_detector.detect_pose(test_image)
        print(f"  检测到 {len(poses)} 个姿势")
        
        # 2. 摔倒检测
        if poses:
            for i, pose in enumerate(poses):
                is_fall, confidence, features = fall_detector.detect_fall(pose)
                print(f"  人员 {i+1}: {'摔倒' if is_fall else '正常'} (置信度: {confidence:.2f})")
                
                # 3. 预警处理
                if is_fall and confidence > 0.7:
                    print(f"  ⚠️  检测到摔倒！发送预警...")
                    alert_manager.send_fall_alert(confidence, test_image, f"第{frame_num+1}帧")
        
        else:
            print("  未检测到人体姿势")
    
    print("\n完整检测流程演示完成")

def main():
    """主函数"""
    print("摔倒检测系统使用示例")
    print("本示例演示如何使用各个模块进行摔倒检测")
    
    # 运行各个示例
    try:
        example_pose_detection()
        example_threshold_detection()
        example_ml_detection()
        example_alert_system()
        example_gui_components()
        example_complete_pipeline()
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)
        
        print("\n下一步:")
        print("1. 运行 python main.py 启动完整GUI")
        print("2. 运行 python T_test_system.py 进行系统测试")
        print("3. 查看 README.md 了解详细使用方法")
        
    except Exception as e:
        print(f"\n示例运行出错: {e}")
        print("请检查依赖安装和模块导入")

if __name__ == "__main__":
    main() 