# 通用目标检测系统 - Universal Object Detection System

基于YOLO的通用目标检测系统，提供图形化界面，支持多种检测模式和高级功能。

## 📋 功能特性

### 🎯 核心功能
- **多模式检测**：支持单张图片、视频文件、摄像头实时检测、文件夹批量检测
- **动态模型加载**：支持运行时切换不同的YOLO模型权重
- **置信度调整**：实时调整检测置信度阈值（0.01-1.0）
- **批量处理**：支持文件夹遍历，批量处理大量图片

### 🎨 界面特性
- **双显示窗口**：同时显示原图和检测结果
- **标签页设计**：实时检测和批量结果分离显示
- **进度跟踪**：实时显示检测进度和状态
- **结果导航**：批量检测结果支持前后翻页浏览

### 💾 数据管理
- **结果保存**：批量检测结果可保存为图片和详细报告
- **日志记录**：完整的检测过程日志，支持清除和滚动
- **文件预览**：选择文件后立即预览，提升用户体验

## 🚀 快速开始

### 环境要求
```bash
Python 3.8+
PySide6
OpenCV (cv2)
ultralytics (YOLO)
numpy
```

### 安装依赖
```bash
pip install PySide6 opencv-python ultralytics numpy
```

### 模型准备
1. 在项目根目录创建 `pt_models` 文件夹
2. 将您的YOLO模型文件（.pt格式）放入该文件夹
3. 支持的模型格式：YOLOv8/YOLOv11等ultralytics兼容模型

### 运行程序
```bash
python universal_object_detection.py
```

## 📁 项目结构
```
universal_object_detection/
├── universal_object_detection.py  # 主程序文件
├── pt_models/                     # 模型权重文件夹
│   ├── yolov8n.pt                # 示例：YOLO模型文件
│   ├── yolov8s.pt                # 示例：YOLO模型文件
│   └── custom_model.pt           # 示例：自定义模型文件
└── README.md                     # 项目说明文档
```

## 🎮 使用指南

### 1. 模型配置
- **选择模型**：从下拉列表中选择要使用的YOLO模型
- **刷新模型**：点击🔄按钮重新扫描模型文件夹
- **置信度设置**：使用滑块或数值框调整检测置信度阈值

### 2. 检测模式

#### 📸 单张图片检测
1. 选择"单张图片"模式
2. 点击"选择文件"按钮选择图片
3. 点击"▶ 开始检测"进行检测

#### 🎬 视频文件检测
1. 选择"视频文件"模式
2. 选择视频文件（支持mp4、avi、mov等格式）
3. 开始检测，可暂停/继续/停止

#### 📹 摄像头实时检测
1. 选择"摄像头"模式
2. 直接点击"▶ 开始检测"开始实时检测
3. 支持暂停和停止功能

#### 📁 文件夹批量检测
1. 选择"文件夹批量"模式
2. 选择包含图片的文件夹
3. 开始批量检测，自动处理所有支持格式的图片
4. 在"批量结果"标签页查看和导航结果

### 3. 结果管理
- **结果浏览**：使用前后导航按钮浏览批量检测结果
- **保存结果**：将批量检测结果保存为图片和报告文件
- **清除结果**：清空当前批量检测结果

### 4. 日志监控
- **实时日志**：查看检测过程的详细信息
- **日志管理**：支持清除日志，自动限制日志行数

## 🔧 技术细节

### 支持的图片格式
- JPG/JPEG
- PNG
- BMP
- TIFF
- WebP

### 支持的视频格式
- MP4
- AVI
- MOV
- MKV
- WMV
- FLV

### 性能优化
- **多线程处理**：检测过程在后台线程运行，不阻塞UI
- **内存管理**：自动限制日志缓存，避免内存泄漏
- **帧率控制**：视频和摄像头检测支持帧率控制

## 🎨 界面说明

### 左侧控制面板
1. **模型配置区**：模型选择和置信度设置
2. **检测源配置区**：检测模式选择和文件选择
3. **检测控制区**：开始/暂停/停止按钮和进度条
4. **运行日志区**：实时显示检测日志信息

### 右侧显示区域
1. **实时检测标签页**：显示原图和检测结果
2. **批量结果标签页**：批量检测结果浏览和管理

## 🔍 故障排除

### 常见问题
1. **模型加载失败**
   - 检查模型文件是否存在于 `pt_models` 文件夹
   - 确保模型文件格式正确（.pt格式）
   - 检查ultralytics库是否正确安装

2. **摄像头无法打开**
   - 确保摄像头设备可用且未被其他程序占用
   - 检查摄像头权限设置

3. **检测速度慢**
   - 降低置信度阈值可能提高检测速度
   - 使用更小的模型（如YOLOv8n而不是YOLOv8x）
   - 确保GPU驱动和CUDA环境配置正确

### 日志信息
程序会记录详细的运行日志，包括：
- 模型加载状态
- 文件选择和处理信息
- 检测结果统计
- 错误和警告信息

## 📄 许可证

本项目基于MIT许可证开源。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📧 联系方式

如有问题或建议，请通过Issue联系我们2642144249@qq.com。

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
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt 
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11.pt 
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11.pt 
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11.pt 

```

### 使用Python下载

```python
from ultralytics import YOLO

# 下载并加载模型（首次运行会自动下载）
model = YOLO('pt_models/yolov8n.pt')  # nano版本
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
- **8以后的版本同样支持**
- **自定义模型**: 您训练的任何符合YOLO格式的.pt文件

## 🔧 自定义模型

如果您有自己训练的YOLO模型，只需将.pt文件复制到此文件夹，程序会自动识别。

### 训练自定义模型示例

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('pt_models/yolov8n.pt')

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