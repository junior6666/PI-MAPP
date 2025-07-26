"""
摔倒检测系统主程序
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目路径到系统路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui_application import main as gui_main
from pose_detection import PoseDetector
from fall_detection_algorithms import ThresholdFallDetector
from alert_system import AlertManager

def run_gui():
    """运行GUI应用程序"""
    print("启动摔倒检测系统GUI...")
    gui_main()

def run_command_line_detection(video_path: str, output_path: str = None):
    """运行命令行检测"""
    print(f"开始处理视频: {video_path}")
    
    # 初始化检测器
    pose_detector = PoseDetector()
    fall_detector = ThresholdFallDetector()
    
    try:
        # 处理视频
        poses_sequence = pose_detector.process_video(video_path)
        
        print(f"视频处理完成，共 {len(poses_sequence)} 帧")
        
        # 检测摔倒
        fall_detections = []
        for i, poses in enumerate(poses_sequence):
            if poses:
                for pose in poses:
                    is_fall, confidence, features = fall_detector.detect_fall(pose)
                    if is_fall:
                        fall_detections.append({
                            'frame': i,
                            'confidence': confidence,
                            'features': features
                        })
        
        # 输出结果
        if fall_detections:
            print(f"检测到 {len(fall_detections)} 个摔倒事件:")
            for detection in fall_detections:
                print(f"  帧 {detection['frame']}: 置信度 {detection['confidence']:.2f}")
        else:
            print("未检测到摔倒事件")
        
        # 保存结果
        if output_path:
            import json
            result = {
                'video_path': video_path,
                'total_frames': len(poses_sequence),
                'fall_detections': fall_detections,
                'processing_time': 'completed'
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"处理失败: {e}")

def run_training(data_path: str, output_path: str = "trained_models"):
    """运行模型训练"""
    print(f"开始训练模型，数据路径: {data_path}")
    
    try:
        from training_utils import ModelTrainer
        
        trainer = ModelTrainer()
        
        # 准备数据
        print("准备训练数据...")
        X, y = trainer.prepare_training_data(data_path)
        print(f"数据准备完成，特征维度: {X.shape}, 标签数量: {len(y)}")
        
        # 训练传统机器学习模型
        print("训练传统机器学习模型...")
        ml_results = trainer.train_traditional_ml_models(X, y, output_path)
        
        # 训练深度学习模型
        print("训练深度学习模型...")
        dl_model_path = trainer.train_deep_learning_model(data_path, output_path)
        
        print("模型训练完成!")
        
    except Exception as e:
        print(f"训练失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="摔倒检测系统")
    parser.add_argument('--mode', choices=['gui', 'detect', 'train'], 
                       default='gui', help='运行模式')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--data', type=str, help='训练数据路径')
    parser.add_argument('--model-output', type=str, default='trained_models',
                       help='模型输出路径')
    
    args = parser.parse_args()
    
    if args.mode == 'gui':
        run_gui()
    elif args.mode == 'detect':
        if not args.video:
            print("错误: 检测模式需要指定视频文件路径 (--video)")
            return
        run_command_line_detection(args.video, args.output)
    elif args.mode == 'train':
        if not args.data:
            print("错误: 训练模式需要指定数据路径 (--data)")
            return
        run_training(args.data, args.model_output)

if __name__ == "__main__":
    main() 