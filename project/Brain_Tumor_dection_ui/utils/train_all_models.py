import torch
from ultralytics import YOLO
import os
from datetime import datetime

# 解决 OpenMP 冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 配置参数
DATA_CONFIG = r'data.yaml'  # 数据集配置文件
IMG_SIZE = 512                  # 输入图像尺寸
EPOCHS = 100                    # 总训练轮数
BATCH_SIZE = 16                 # 批量大小（根据 GPU 显存调整）

# 要训练的模型配置
MODELS_TO_TRAIN = [
    {
        'name': 'yolov8n',
        'model_file': 'yolov8n.pt',
        'train_name': 'train_yolov8n'
    },
    {
        'name': 'yolov9t',
        'model_file': 'yolov9t.pt',
        'train_name': 'train_yolov9t'
    },
    {
        'name': 'yolov10n',
        'model_file': 'yolov10n.pt',
        'train_name': 'train_yolov10n'
    },
    {
        'name': 'yolo11n',
        'model_file': 'yolo11n.pt',
        'train_name': 'train_yolo11n'
    },
    {
        'name': 'yolo26n',
        'model_file': 'yolo26n.pt',
        'train_name': 'train_yolo26n'
    }
]


def train_model(model_config):
    """
    训练单个模型
    
    Args:
        model_config: 模型配置字典
    """
    print("\n" + "=" * 60)
    print(f"开始训练：{model_config['name']}")
    print("=" * 60)
    print(f"模型文件：{model_config['model_file']}")
    print(f"训练名称：{model_config['train_name']}")
    print(f"数据集：{DATA_CONFIG}")
    print(f"图像尺寸：{IMG_SIZE}")
    print(f"训练轮数：{EPOCHS}")
    print(f"批量大小：{BATCH_SIZE}")
    print("=" * 60 + "\n")
    
    try:
        # 加载预训练模型
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在加载模型...")
        model = YOLO(model_config['model_file'])
        
        # 开始训练
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始训练...")
        results = model.train(
            data=DATA_CONFIG,
            imgsz=IMG_SIZE,
            name=model_config['train_name'],
            epochs=EPOCHS,
            batch=BATCH_SIZE,
            # resume=True  # 如果需要断点续训，取消注释
        )
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {model_config['name']} 训练完成！")
        print(f"训练结果保存在：runs/detect/{model_config['train_name']}/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ [{model_config['name']}] 训练失败：{str(e)}")
        return False


def main():
    """主训练流程"""
    print("\n" + "🚀" * 30)
    print("脑肿瘤检测模型批量训练 - 5 种 YOLO 架构")
    print("🚀" * 30 + "\n")
    
    # 显示训练计划
    print("📋 训练计划:")
    for i, model in enumerate(MODELS_TO_TRAIN, 1):
        print(f"  {i}. {model['name']} ({model['model_file']})")
    print()
    
    # 检查 CUDA 可用性
    if torch.cuda.is_available():
        print(f"✅ CUDA 可用：{torch.cuda.get_device_name(0)}")
        print(f"   显存：{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB\n")
    else:
        print("⚠️  未检测到 CUDA，将使用 CPU 训练（速度较慢）\n")
    
    # 统计训练结果
    success_count = 0
    failed_models = []
    
    # 依次训练每个模型
    for idx, model_config in enumerate(MODELS_TO_TRAIN, 1):
        print(f"\n{'='*60}")
        print(f"进度：{idx}/{len(MODELS_TO_TRAIN)}")
        print(f"{'='*60}")
        
        success = train_model(model_config)
        
        if success:
            success_count += 1
            print(f"✅ {model_config['name']} 训练成功！")
        else:
            failed_models.append(model_config['name'])
            print(f"❌ {model_config['name']} 训练失败！")
        
        # 训练间隔提示
        if idx < len(MODELS_TO_TRAIN):
            print(f"\n⏸️  准备训练下一个模型：{MODELS_TO_TRAIN[idx]['name']}")
            print("   建议等待 10 秒让 GPU 冷却...")
    
    # 训练总结
    print("\n" + "=" * 60)
    print("🎉 所有训练任务完成！")
    print("=" * 60)
    print(f"成功：{success_count}/{len(MODELS_TO_TRAIN)}")
    
    if failed_models:
        print(f"\n失败的模型:")
        for model_name in failed_models:
            print(f"  - {model_name}")
    
    print("\n训练权重保存位置:")
    for model in MODELS_TO_TRAIN:
        print(f"  runs/detect/{model['train_name']}/weights/best.pt")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
