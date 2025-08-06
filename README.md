# 步态分析可视化GUI应用

基于PySide6和深度学习的现代化步态分析工具，支持实时视频播放、骨骼点显示、关节角度分析和步态参数计算。

![App Screenshot](screenshots/main_interface.png)

## 主要功能

### 📹 视频播放与控制
- **实时视频播放**: 支持多种视频格式 (MP4, AVI, MOV, MKV, WMV)
- **骨骼点叠加显示**: 实时显示17个COCO格式关键点
- **播放控制**: 播放、暂停、停止、帧跳转
- **速度控制**: 0.25x - 3.0x 可调节播放速度
- **帧精确控制**: 支持单帧前进/后退

### 📊 特征曲线分析
- **关节角度曲线**: 实时显示髋、膝、踝关节角度变化
- **躯干摆动分析**: 分析躯干相对垂直线的摆动角度
- **数据类型切换**: 原始数据与平滑数据对比
- **多标签页显示**: 关节角度、步态周期、支撑相分析
- **当前帧指示**: 图表中显示当前播放帧位置

### 🦵 步态参数计算
- **步态周期检测**: 自动识别左右脚步态周期
- **支撑相分析**: 计算支撑相和摆动相比例
- **对称性评估**: 左右脚对称性分析
- **时间参数**: 步频、周期时长、相位时间
- **空间参数**: 步长、步宽估算

### 🔧 参数控制面板
- **关节显示控制**: 可选择显示/隐藏特定关节数据
- **平滑参数调节**: 可调节数据平滑强度
- **检测阈值设置**: 自定义关键点检测置信度阈值
- **显示选项**: 支撑相标记、步态周期显示

### 🤖 YOLO模型集成
- **自动关键点生成**: 使用YOLO11/YOLOv8姿态估计模型
- **多模型支持**: 支持不同精度的YOLO模型
- **批量处理**: 支持批量视频处理
- **进度显示**: 实时显示处理进度

### 💾 数据保存与导出
- **多格式支持**: JSON、Excel格式保存
- **图表导出**: PNG、PDF格式图表导出
- **分析报告**: 详细的步态分析报告
- **支撑相报告**: 专门的支撑相和摆动相分析报告

## 安装指南

### 系统要求
- Python 3.8 或更高版本
- Windows 10/11, macOS 10.14+, 或 Linux
- 8GB+ RAM (推荐)
- 支持CUDA的显卡 (可选，用于加速YOLO模型)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/gait-analysis-gui.git
   cd gait-analysis-gui
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **下载YOLO模型** (可选)
   ```bash
   # 创建模型目录
   mkdir models
   cd models
   
   # 下载YOLO模型文件 (选择其中一个)
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11n-pose.pt  # 轻量级
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11s-pose.pt  # 小型
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11m-pose.pt  # 中型
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11l-pose.pt  # 大型
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11x-pose.pt  # 超大型
   ```

## 使用指南

### 启动应用
```bash
python main.py
```

### 基本工作流程

1. **加载视频文件**
   - 点击菜单 "文件" → "打开视频文件"
   - 选择要分析的步态视频

2. **生成关键点数据** (如果没有现有数据)
   - 点击菜单 "分析" → "生成关键点数据" 
   - 等待YOLO模型处理完成

3. **开始步态分析**
   - 点击菜单 "分析" → "开始分析"
   - 等待分析完成

4. **查看分析结果**
   - 在右侧图表区域查看关节角度曲线
   - 在下方参数面板查看步态参数
   - 切换不同标签页查看详细分析

5. **保存结果**
   - 点击菜单 "文件" → "保存分析结果"
   - 选择保存格式 (JSON/Excel)

### 界面说明

#### 主界面布局
```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│    视频播放区域     │    特征曲线显示     │
│   (骨骼点叠加)      │   (关节角度分析)    │
│                     │                     │
├─────────────────────┼─────────────────────┤
│                     │                     │
│    控制面板         │    参数显示面板     │
│   (播放控制等)      │   (步态参数等)      │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

#### 控制面板功能
- **播放控制**: 播放/暂停、停止、速度调节
- **帧控制**: 帧滑块、精确帧跳转
- **显示选项**: 关节显示开关、数据类型选择
- **分析选项**: 平滑强度、检测阈值调节

#### 图表显示
- **关节角度**: 显示各关节的角度变化曲线
- **步态周期**: 显示归一化的步态周期对比
- **支撑相分析**: 显示支撑相和摆动相的时序分析

### 高级功能

#### 批量处理
使用命令行工具进行批量处理：
```bash
python -m core.keypoint_generator --video path/to/video.mp4 --output path/to/output/
```

#### 自定义模型
如果有自己训练的YOLO模型，可以：
1. 将模型文件放在 `models/` 目录下
2. 在生成关键点时选择自定义模型路径

#### 数据格式
支持的关键点数据格式为COCO 17点格式：
```json
{
  "metadata": {
    "format": "COCO",
    "keypoint_names": ["nose", "left_eye", "right_eye", ...]
  },
  "keypoints": [
    [[x1, y1, conf1], [x2, y2, conf2], ...],  // 第1帧
    [[x1, y1, conf1], [x2, y2, conf2], ...],  // 第2帧
    ...
  ]
}
```

## 技术架构

### 核心组件
- **UI层**: PySide6 现代化界面
- **显示层**: OpenCV视频处理 + PyQtGraph图表
- **分析层**: SciPy信号处理 + NumPy数值计算
- **AI层**: Ultralytics YOLO模型

### 关键算法
- **关节角度计算**: 基于向量夹角的几何计算
- **数据平滑**: Savitzky-Golay滤波器
- **步态周期检测**: 基于峰值检测的周期识别
- **支撑相分析**: 基于关节角度变化率的相位分割

### 文件结构
```
gait-analysis-gui/
├── main.py                 # 应用程序入口
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
├── ui/                    # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   ├── video_player.py    # 视频播放器
│   ├── chart_display.py   # 图表显示
│   ├── control_panel.py   # 控制面板
│   ├── parameter_display.py # 参数显示
│   └── phase_analysis_dialog.py # 支撑相分析对话框
├── core/                  # 核心分析模块
│   ├── __init__.py
│   ├── gait_analyzer.py   # 步态分析器
│   └── keypoint_generator.py # 关键点生成器
└── models/                # YOLO模型文件目录
    └── (YOLO model files)
```

## 故障排除

### 常见问题

1. **无法启动应用程序**
   - 检查Python版本是否为3.8+
   - 确认所有依赖包已正确安装
   - 检查是否有权限问题

2. **YOLO模型加载失败**
   - 确认模型文件存在于 `models/` 目录
   - 检查网络连接（首次使用会自动下载）
   - 尝试手动下载模型文件

3. **视频无法播放**
   - 检查视频文件格式是否支持
   - 确认OpenCV正确安装
   - 尝试转换视频格式

4. **分析结果不准确**
   - 检查关键点检测质量
   - 调整检测置信度阈值
   - 确认视频中人物清晰可见

5. **界面显示异常**
   - 检查显示器分辨率和缩放设置
   - 尝试重启应用程序
   - 更新显卡驱动程序

### 性能优化

1. **提高处理速度**
   - 使用GPU加速 (安装CUDA版本的PyTorch)
   - 选择较小的YOLO模型 (yolo11n-pose.pt)
   - 降低视频分辨率

2. **减少内存使用**
   - 处理较短的视频片段
   - 关闭不需要的图表显示
   - 定期清理临时文件

## 开发说明

### 代码风格
- 遵循PEP 8规范
- 使用类型提示
- 添加详细的文档字符串

### 测试
```bash
# 运行单元测试
python -m pytest tests/

# 生成测试覆盖率报告
python -m pytest --cov=core tests/
```

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页: https://github.com/your-repo/gait-analysis-gui
- 问题反馈: https://github.com/your-repo/gait-analysis-gui/issues
- 邮箱: your-email@example.com

## 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLO模型
- [PySide6](https://doc.qt.io/qtforpython/) - GUI框架
- [PyQtGraph](https://pyqtgraph.readthedocs.io/) - 图表显示
- [OpenCV](https://opencv.org/) - 计算机视觉库
