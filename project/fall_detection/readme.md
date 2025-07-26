# 摔倒检测系统

这是一个基于人体骨骼点进行摔倒检测的完整项目，集成了多种检测算法和预警功能。

## 功能特性

### 🎯 核心功能
- **人体姿势检测**: 基于YOLO的人体骨骼点提取
- **多种检测算法**: 
  - 阈值法：基于几何特征的快速检测
  - 传统机器学习：KNN、SVM、随机森林
  - 深度学习：LSTM序列模型
- **实时检测**: 支持图片、视频和摄像头实时检测
- **预警系统**: 邮箱和短信预警功能

### 🖥️ 用户界面
- **图形化界面**: 基于tkinter的现代化GUI
- **实时显示**: 视频播放和检测结果实时显示
- **结果可视化**: 多种算法的检测结果对比
- **系统日志**: 详细的操作和检测日志

### 🔧 技术特性
- **模块化设计**: 清晰的代码结构和模块分离
- **配置管理**: 灵活的配置文件和参数设置
- **模型管理**: 模型训练、保存和加载功能
- **数据可视化**: 训练数据和检测结果的可视化

## 项目结构

```
fall_detection/
├── README.md                 # 项目说明文档
├── requirements.txt          # 依赖包列表
├── main.py                   # 主程序入口
├── pose_detection.py         # 人体姿势检测模块
├── fall_detection_algorithms.py  # 摔倒检测算法模块
├── alert_system.py           # 预警系统模块
├── gui_application.py        # GUI应用程序
├── training_utils.py         # 训练工具模块
├── models/                   # 模型文件目录
├── data/                     # 数据文件目录
└── config/                   # 配置文件目录
```

## 安装说明

### 环境要求
- Python 3.8+
- Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd fall_detection
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **下载YOLO模型**（可选）
```bash
# 程序会自动下载默认模型，也可以手动下载
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-pose.pt
```

## 使用指南

### 🚀 快速开始

1. **启动GUI应用程序**
```bash
python main.py
# 或者
python main.py --mode gui
```

2. **使用命令行检测**
```bash
# 检测视频文件
python main.py --mode detect --video path/to/video.mp4 --output result.json

# 训练模型
python main.py --mode train --data path/to/dataset --model-output trained_models
```

### 📱 GUI使用说明

#### 基本操作
1. **加载媒体**: 点击"加载图片"、"加载视频"或"打开摄像头"
2. **选择算法**: 在"检测算法"区域选择检测方法
3. **开始检测**: 点击"开始检测"或"单帧检测"
4. **查看结果**: 在右侧面板查看检测结果和置信度

#### 预警配置
1. **配置邮箱**: 点击"配置预警"设置邮箱参数
2. **测试连接**: 点击"测试预警"验证配置
3. **查看历史**: 点击"查看历史"查看预警记录

#### 模型管理
1. **训练模型**: 准备数据集后点击"训练模型"
2. **加载模型**: 点击"加载模型"加载已训练的模型
3. **保存模型**: 点击"保存模型"保存当前模型

### 🔧 高级配置

#### 预警系统配置
```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "recipient_emails": ["recipient@example.com"]
  },
  "sms": {
    "enabled": false,
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "phone_numbers": ["+8613800138000"]
  },
  "general": {
    "alert_cooldown": 60,
    "enable_alerts": true
  }
}
```

#### 算法参数调整
- **阈值法**: 在`ThresholdFallDetector`类中调整阈值参数
- **机器学习**: 在`TraditionalMLFallDetector`类中调整模型参数
- **深度学习**: 在`DeepLearningFallDetector`类中调整网络结构

## 算法说明

### 1. 阈值法 (Threshold Method)
基于人体几何特征的快速检测方法：
- **高度比例**: 躯干高度与总高度的比例
- **宽度比例**: 肩膀宽度与总高度的比例  
- **躯干角度**: 躯干与垂直线的夹角

### 2. 传统机器学习 (Traditional ML)
使用经典机器学习算法：
- **KNN**: K近邻分类器
- **SVM**: 支持向量机
- **随机森林**: 集成学习方法

### 3. 深度学习 (Deep Learning)
基于LSTM的序列模型：
- **输入**: 连续帧的姿势特征序列
- **网络**: LSTM + 全连接层
- **输出**: 摔倒概率

## 数据格式

### 训练数据格式
```
dataset/
├── fall/           # 摔倒视频
│   ├── video1.mp4
│   ├── video2.mp4
│   └── ...
└── normal/         # 正常视频
    ├── video1.mp4
    ├── video2.mp4
    └── ...
```

### 处理后的数据格式
```json
{
  "label": 1,
  "frames": 150,
  "poses_sequence": [
    [
      {
        "person_id": 0,
        "keypoints": {
          "nose": {"x": 100, "y": 50, "confidence": 0.9},
          "left_shoulder": {"x": 80, "y": 80, "confidence": 0.8},
          ...
        },
        "bbox": [70, 40, 130, 200],
        "confidence": 0.85
      }
    ],
    ...
  ],
  "processed_time": "2024-01-01T12:00:00"
}
```

## 性能优化

### 检测速度优化
- 使用GPU加速（CUDA）
- 降低视频分辨率
- 调整检测频率

### 准确率优化
- 增加训练数据
- 调整算法参数
- 使用集成方法

### 内存优化
- 批量处理
- 及时释放资源
- 使用生成器处理大数据

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径
   - 确认PyTorch版本兼容性

2. **摄像头无法打开**
   - 检查摄像头权限
   - 确认摄像头未被其他程序占用

3. **预警发送失败**
   - 检查网络连接
   - 验证邮箱/短信配置
   - 确认API密钥有效性

4. **检测效果不佳**
   - 调整算法参数
   - 增加训练数据
   - 检查数据质量

### 调试模式
```bash
# 启用详细日志
python main.py --debug

# 测试单个模块
python -c "from pose_detection import PoseDetector; print('测试成功')"
```

## 开发指南

### 添加新算法
1. 在`fall_detection_algorithms.py`中创建新类
2. 实现`detect_fall`方法
3. 在GUI中添加算法选项
4. 更新配置和文档

### 扩展预警方式
1. 在`alert_system.py`中创建新的预警类
2. 继承`AlertSystem`基类
3. 实现`_send_alert_impl`方法
4. 在GUI中添加配置选项

### 自定义特征提取
1. 修改`FeatureExtractor`类
2. 添加新的特征计算方法
3. 更新训练和检测流程

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范
- 遵循PEP 8规范
- 添加类型注解
- 编写文档字符串
- 添加单元测试

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮箱: [your-email@example.com]

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持多种检测算法
- 集成GUI界面
- 实现预警功能

---

**注意**: 本项目仅供学习和研究使用，实际部署时请根据具体需求调整参数和配置。