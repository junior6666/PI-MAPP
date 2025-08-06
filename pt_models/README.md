# YOLO模型文件夹

## 📁 模型存放说明

将您的YOLO模型权重文件（.pt格式）放入此文件夹，程序将自动扫描并在界面中显示可用模型。

## 🔽 获取预训练模型

### 官方预训练模型
您可以从 [Ultralytics官方](https://github.com/ultralytics/ultralytics) 下载官方预训练模型：

```bash
# 下载YOLOv8模型
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt
```

### 使用Python下载
```python
from ultralytics import YOLO

# 下载并加载模型（首次运行会自动下载）
model = YOLO('yolov8n.pt')  # nano版本
model = YOLO('yolov8s.pt')  # small版本  
model = YOLO('yolov8m.pt')  # medium版本
model = YOLO('yolov8l.pt')  # large版本
model = YOLO('yolov8x.pt')  # extra large版本
```

## 🎯 模型规格对比

| 模型 | 大小 | mAP | 速度 | 参数 | FLOPs |
|------|------|-----|------|------|-------|
| YOLOv8n | ~6MB | 37.3 | 最快 | 3.2M | 8.7B |
| YOLOv8s | ~22MB | 44.9 | 快 | 11.2M | 28.6B |
| YOLOv8m | ~50MB | 50.2 | 中等 | 25.9M | 78.9B |
| YOLOv8l | ~87MB | 52.9 | 慢 | 43.7M | 165.2B |
| YOLOv8x | ~136MB | 53.9 | 最慢 | 68.2M | 257.8B |

## 📋 支持的模型类型

- **目标检测**: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
- **实例分割**: yolov8n-seg.pt, yolov8s-seg.pt, yolov8m-seg.pt, yolov8l-seg.pt, yolov8x-seg.pt
- **姿态估计**: yolov8n-pose.pt, yolov8s-pose.pt, yolov8m-pose.pt, yolov8l-pose.pt, yolov8x-pose.pt
- **分类**: yolov8n-cls.pt, yolov8s-cls.pt, yolov8m-cls.pt, yolov8l-cls.pt, yolov8x-cls.pt
- **自定义模型**: 您训练的任何符合YOLOv8格式的.pt文件

## 🔧 自定义模型

如果您有自己训练的YOLO模型，只需将.pt文件复制到此文件夹，程序会自动识别。

### 训练自定义模型示例
```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 训练模型
model.train(data='path/to/your/dataset.yaml', epochs=100, imgsz=640)

# 保存模型到此文件夹
model.save('pt_models/custom_model.pt')
```

## 📝 注意事项

1. **文件格式**: 仅支持.pt格式的模型文件
2. **文件命名**: 文件名会在界面中显示，建议使用有意义的名称
3. **模型大小**: 较大的模型精度更高但速度更慢，请根据需要选择
4. **更新模型**: 添加新模型后，点击界面中的刷新按钮🔄即可更新列表

## 🚀 快速开始

1. 将模型文件放入此文件夹
2. 启动程序：`python universal_object_detection.py`
3. 在界面中选择模型
4. 开始检测！