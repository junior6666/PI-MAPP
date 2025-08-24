# Enhanced Object Detection System v2.0 🚀

一个全面优化的通用目标检测系统，基于YOLO，具有现代化渐变UI和强大功能。
[视频介绍](https://www.bilibili.com/video/BV1FVtwz8EZB/?vd_source=ea444bcb59e16e58cfdca990f3514384)

![Enhanced Detection System](https://img.shields.io/badge/Version-2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
## 👿 界面预览
![UI初始化界面.png](ui_predict_results/UI%E5%88%9D%E5%A7%8B%E5%8C%96%E7%95%8C%E9%9D%A2.png)
## ✨ 主要特性

### 🎨 现代化UI设计
- **渐变样式效果**: 采用现代化渐变背景和按钮设计
- **响应式布局**: 智能适应不同分辨率和屏幕尺寸
- **优化图标**: 重新设计的应用程序图标，支持多种尺寸
- **流畅动画**: 按钮悬停和点击动画效果

### 📊 增强的功能体验
- **详细日志显示**: 实时显示检测类别、置信度、数量统计
- **结果详情面板**: 表格化显示目标坐标、尺寸、置信度
- **颜色编码**: 根据置信度高低使用不同颜色标识
- **智能统计**: 自动统计各类别检测数量和平均置信度

### 📁 灵活的模型管理
- **多路径扫描**: 支持多个预设目录自动扫描模型文件
- **自定义路径**: 允许用户指定任意目录加载模型
- **模型信息**: 显示文件大小、修改时间等详细信息
- **高级选择器**: 提供专业的模型选择对话框

### 📹 强大的多摄像头支持
- **自动检测**: 智能扫描系统中所有可用摄像头
- **设备信息**: 显示分辨率、帧率等摄像头参数
- **多选支持**: 可同时选择多个摄像头进行监控
- **状态监控**: 实时显示每个摄像头的连接状态

### 🖥️ 专业监控系统
- **多路监控**: 同时监控多个摄像头的实时画面
- **网格布局**: 自动排列多个视频流的显示界面
- **独立控制**: 每个摄像头可独立开始/停止监控
- **状态反馈**: 实时显示检测结果和系统状态

### ⚡ 性能与稳定性优化
- **多线程架构**: 优化的线程管理，避免界面卡顿
- **内存优化**: 智能的内存使用和释放机制
- **异常处理**: 完善的错误处理和用户提示系统
- **资源管理**: 自动管理摄像头等硬件资源

## 🛠️ 系统要求

### 基础环境
- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 建议 4GB 以上
- **显卡**: 支持CUDA的NVIDIA显卡（可选，用于GPU加速）

### 依赖包
```bash
# 核心依赖
ultralytics>=8.0.0    # YOLO模型库
PySide6>=6.0.0       # Qt6界面框架
opencv-python>=4.5.0  # 图像处理
numpy>=1.21.0        # 数值计算

# 可选依赖
torch>=1.12.0        # PyTorch（如果需要GPU加速）
torchvision>=0.13.0  # 计算机视觉工具
```

## 📦 安装指南

### 方法一：使用 pip 安装
```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install ultralytics PySide6 opencv-python numpy
```

### 方法二：使用 conda 安装
```bash
# 创建conda环境
conda create -n detection python=3.9
conda activate detection

# 安装依赖
conda install pytorch torchvision -c pytorch
pip install ultralytics PySide6 opencv-python
```

### 方法三：从源码安装
```bash
# 克隆项目
git clone <repository-url>
cd enhanced-detection-system

# 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 准备模型文件
将YOLO模型文件（.pt格式）放置在以下任一目录：
```
pt_models/          # 项目根目录下
models/             # 通用模型目录
weights/            # 权重文件目录
~/yolo_models/      # 用户主目录
```

### 2. 启动应用程序
```bash
# 运行主程序
python enhanced_ui_main.py

# 或者运行其他版本
python enhanced_detection_main.py  # 基础版本
```

### 3. 基本使用流程
1. **选择模型**: 在"模型配置"中选择要使用的YOLO模型
2. **设置置信度**: 调整置信度阈值（默认0.25）
3. **选择检测源**: 
   - 📷 单张图片：选择图片文件进行检测
   - 🎬 视频文件：选择视频文件逐帧检测
   - 📹 摄像头：实时摄像头检测
   - 📂 文件夹批量：批量处理文件夹中的图片
4. **开始检测**: 点击"开始检测"按钮
5. **查看结果**: 在相应标签页查看检测结果

## 📖 详细功能说明

### 🎯 实时检测页面
- **原图显示**: 显示原始图像或视频帧
- **结果展示**: 显示带有检测框和标签的结果图像
- **详情面板**: 表格形式显示每个检测目标的详细信息
- **实时统计**: 显示检测数量、平均置信度等统计信息

### 📊 批量结果页面
- **结果导航**: 使用前进/后退按钮浏览批量检测结果
- **信息显示**: 显示当前图片的文件名、检测数量等信息
- **批量保存**: 一键保存所有检测结果图片和报告
- **进度跟踪**: 实时显示批量处理的进度

### 🖥️ 实时监控页面
- **多摄像头**: 同时连接和监控多个摄像头设备
- **网格显示**: 自动排列多个视频流的显示区域
- **独立控制**: 每个摄像头可以独立控制开始/停止
- **状态监控**: 显示连接状态、检测数量、处理速度等

### 📋 运行日志
- **时间戳**: 每条日志都带有精确的时间戳
- **分类标识**: 使用emoji图标区分不同类型的消息
- **详细信息**: 记录检测类别、数量、耗时等详细信息
- **自动清理**: 自动限制日志数量，避免内存溢出

## ⚙️ 高级配置

### 模型配置
```python
# 支持的模型路径
MODELS_PATHS = [
    "pt_models",                    # 项目目录
    "models",                       # 通用目录
    "weights",                      # 权重目录
    "~/yolo_models",               # 用户目录
    "/usr/local/share/yolo_models", # 系统目录 (Linux)
    "C:/yolo_models",              # 系统目录 (Windows)
]
```

### 摄像头配置
```python
# 摄像头参数设置
CAMERA_SETTINGS = {
    'width': 640,        # 图像宽度
    'height': 480,       # 图像高度
    'fps': 30,          # 帧率
    'detection_fps': 10, # 检测频率
}
```

### UI样式配置
```python
# 渐变颜色配置
UI_COLORS = {
    'primary_start': '#3498db',     # 主要渐变起始色
    'primary_end': '#2980b9',       # 主要渐变结束色
    'background_start': '#f8f9fa',   # 背景渐变起始色
    'background_end': '#e9ecef',     # 背景渐变结束色
}
```

## 🔧 自定义开发

### 添加新的检测源
```python
class CustomDetectionThread(QThread):
    def __init__(self, model, custom_source):
        super().__init__()
        self.model = model
        self.custom_source = custom_source
    
    def run(self):
        # 实现自定义检测逻辑
        pass
```

### 扩展UI组件
```python
class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # 自定义UI布局和样式
        pass
```

### 添加新的模型格式支持
```python
class ModelManager:
    def scan_models(self, custom_path=None):
        # 扩展支持的模型格式
        supported_formats = ['.pt', '.onnx', '.engine']
        # 实现扫描逻辑
```

## 🐛 故障排除

### 常见问题及解决方案

#### 1. 模型加载失败
```bash
错误: 模型加载失败
解决: 
- 确认模型文件完整且格式正确
- 检查文件路径是否存在
- 确认ultralytics版本兼容性
```

#### 2. 摄像头无法打开
```bash
错误: 无法打开摄像头
解决:
- 检查摄像头是否被其他程序占用
- 确认摄像头驱动程序正常
- 尝试更换摄像头索引号
```

#### 3. 界面显示异常
```bash
错误: UI渲染问题
解决:
- 更新PySide6到最新版本
- 检查系统显卡驱动
- 调整系统DPI设置
```

#### 4. 内存使用过高
```bash
错误: 内存占用持续增长
解决:
- 降低检测频率
- 减小图像处理尺寸
- 定期重启长时间运行的检测
```

## 📊 性能优化建议

### 1. 硬件优化
- **GPU加速**: 使用NVIDIA显卡配合CUDA加速推理
- **内存配置**: 推荐8GB以上内存用于批量处理
- **存储空间**: 确保足够空间保存检测结果

### 2. 软件优化
- **模型选择**: 根据需求选择合适大小的模型（nano/small/medium/large/x）
- **置信度设置**: 适当提高置信度阈值减少误检
- **检测频率**: 实时检测时适当降低处理频率

### 3. 系统配置
- **虚拟环境**: 使用独立的Python环境避免依赖冲突
- **定期清理**: 定期清理临时文件和日志文件
- **系统监控**: 监控CPU、内存、GPU使用情况

## 🤝 贡献指南

### 提交代码
1. Fork项目到个人仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交代码：`git commit -m "Add new feature"`
4. 推送分支：`git push origin feature/new-feature`
5. 提交Pull Request

### 报告问题
- 使用Issue模板提交问题报告
- 提供详细的错误信息和复现步骤
- 包含系统环境和依赖版本信息

### 功能建议
- 在Issue中详细描述新功能需求
- 说明功能的应用场景和预期效果
- 提供设计思路和实现建议

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - 提供优秀的YOLO实现
- [Qt Project](https://www.qt.io/) - 提供强大的UI框架
- [OpenCV](https://opencv.org/) - 提供图像处理功能
- 所有贡献者和用户的支持

## 📞 联系我们

- **项目主页**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **功能建议**: [GitHub Discussions]
- **邮箱**: 2642144249@qq.com
## 😄 预测效果

* 垃圾检测
![垃圾检测.png](ui_predict_results/%E5%9E%83%E5%9C%BE%E6%A3%80%E6%B5%8B.png)
* 头盔检测
![头盔检测.png](ui_predict_results/%E5%A4%B4%E7%9B%94%E6%A3%80%E6%B5%8B.png)
* 息肉诊断
![息肉诊断.png](ui_predict_results/%E6%81%AF%E8%82%89%E8%AF%8A%E6%96%AD.png)
* 文档分析
![文档分析.png](ui_predict_results/%E6%96%87%E6%A1%A3%E5%88%86%E6%9E%90.png)
* 火情诊断
![火情检测.png](ui_predict_results/%E7%81%AB%E6%83%85%E6%A3%80%E6%B5%8B.png)
---

**Enhanced Object Detection System v2.0** - 让目标检测更加简单、高效、美观！

🌟 如果这个项目对您有帮助，请给我们一个Star！
