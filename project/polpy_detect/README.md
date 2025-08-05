# 息肉智能检测系统

基于PySide6和MySQL的医疗息肉目标检测系统，采用Fluent Design设计风格，支持实时检测、历史记录管理和PDF报告生成。
[UI视频介绍](https://www.bilibili.com/video/BV1VNtHzqE5Z/?vd_source=ea444bcb59e16e58cfdca990f3514384)
## 功能特性

### 🎯 核心功能
- **实时检测**: 支持图片、视频和摄像头实时检测
- **双类别识别**: 增生性息肉（Hyperplastic_polyps）和腺瘤息肉（Adenoma polyps）
- **Fluent Design UI**: 现代化的微软设计风格界面
- **数据库管理**: MySQL数据库存储患者信息和检测记录
- **PDF报告**: 自动生成专业的医疗检测报告

### 📊 系统功能
- **参数设置**: IOU阈值、置信度阈值、模型权重配置
- **历史记录**: 完整的检测历史查询和管理
- **患者信息**: 详细的患者信息录入和管理
- **统计报告**: 检测数据统计和分析
- **导出功能**: 支持PDF报告导出

## 系统架构

### 数据库设计
```
patients (患者信息表)
├── id (主键)
├── name (患者姓名)
├── gender (性别)
├── age (年龄)
├── medical_record_number (病历号)
├── phone (联系电话)
└── created_at (创建时间)

doctors (医生信息表)
├── id (主键)
├── name (医生姓名)
├── department (科室)
├── title (职称)
└── created_at (创建时间)

detection_records (检测记录表)
├── id (主键)
├── patient_id (患者ID，外键)
├── doctor_id (医生ID，外键)
├── source_file_path (源文件路径)
├── result_file_path (结果文件路径)
├── detection_type (检测类型：图片/视频/摄像头)
├── processing_time_ms (处理时间)
├── detection_date (检测日期)
└── notes (备注)

detection_details (检测详情表)
├── id (主键)
├── record_id (记录ID，外键)
├── polyp_type (息肉类型)
├── confidence (置信度)
├── coordinates_x1, y1, x2, y2 (坐标)
└── detection_time_ms (检测时间)

system_config (系统配置表)
├── id (主键)
├── config_key (配置键)
├── config_value (配置值)
└── description (描述)
```

## 安装说明

### 环境要求
- Python 3.8 或更高版本
- MySQL 5.7 或更高版本
- Windows 10/11

### 快速安装

1. **克隆项目**
```bash
git clone <repository-url>
cd polpy_detect
```

2. **运行安装脚本**
```bash
install.bat
```

3. **启动应用程序**
```bash
run.bat
```

### 手动安装

1. **安装Python依赖**
```bash
pip install -r requirements.txt
```

2. **配置MySQL数据库**
- 确保MySQL服务正在运行
- 创建数据库：`CREATE DATABASE polyp_detection;`
- 修改 `database_setup.py` 中的数据库连接参数

3. **初始化数据库**
```bash
python database_setup.py
```

4. **启动应用程序**
```bash
python main_ui.py
```

## 使用指南

### 主界面操作

1. **选择文件检测**
   - 点击"📁 选择文件"按钮
   - 选择图片或视频文件
   - 点击"▶️ 开始检测"

2. **摄像头检测**
   - 点击"📹 加载摄像头"按钮
   - 系统将打开摄像头
   - 点击"▶️ 开始检测"进行实时检测

3. **参数设置**
   - 点击右上角"⚙️ 参数设置"按钮
   - 调整IOU阈值和置信度阈值
   - 配置数据库连接参数

### 历史记录管理

1. **查看历史记录**
   - 切换到"历史记录"标签页
   - 系统自动加载最近的检测记录

2. **搜索记录**
   - 在搜索框输入关键词
   - 选择搜索字段（患者信息/医生信息/类别）
   - 设置日期范围
   - 点击"🔍 查询"按钮

3. **查看详情**
   - 点击记录行的"查看"按钮
   - 查看患者信息和检测详情

### 保存和导出

1. **保存检测结果**
   - 完成检测后点击"💾 保存结果"
   - 填写患者信息表单
   - 系统自动保存到数据库

2. **导出PDF报告**
   - 点击"📄 导出报告"按钮
   - 系统生成包含检测结果的PDF报告
   - 报告包含患者信息、检测结果、统计图表等

## 界面设计

### Fluent Design 风格
- **深色主题**: 主背景色 #1E1E1E
- **蓝色主色调**: #0078D7
- **现代化控件**: 圆角按钮、阴影效果
- **响应式布局**: 自适应窗口大小

### 布局结构
```
┌─────────────────────────────────────────┐
│ 导航条: 系统名称 + 主页/历史记录标签    │
├─────────────────────────────────────────┤
│ 设置按钮                   参数设置    │
├─────────────────────────────────────────┤
│ 源窗口 │ 结果窗口 │ 详细信息窗口       │
├─────────────────────────────────────────┤
│ 操作按钮栏: 7个功能按钮               │
└─────────────────────────────────────────┘
```

## 技术栈

- **前端框架**: PySide6 (Qt for Python)
- **AI模型**: YOLO (Ultralytics)
- **数据库**: MySQL
- **报告生成**: ReportLab
- **图像处理**: OpenCV, Pillow
- **数据处理**: NumPy, Pandas

## 文件结构

```
polpy_detect/
├── main_ui.py              # 主界面程序
├── database_setup.py        # 数据库设置
├── database_operations.py   # 数据库操作
├── report_generator.py      # PDF报告生成
├── polpy_utils.py          # 工具函数
├── requirements.txt         # 依赖包列表
├── install.bat             # 安装脚本
├── run.bat                 # 启动脚本
├── README.md               # 说明文档
├── pt_models/              # 模型文件目录
│   └── polpy_best.pt      # 训练好的模型
├── polpy_test_img/         # 测试图片
└── runs/                   # 检测结果输出
```

## 配置说明

### 数据库配置
在 `database_setup.py` 中修改以下参数：
```python
host='localhost'      # 数据库主机
port=3306            # 数据库端口
user='root'          # 数据库用户名
password=''          # 数据库密码
database='polyp_detection'  # 数据库名称
```

### 模型配置
- 模型文件路径: `pt_models/polpy_best.pt`
- 支持的息肉类型: 增生性息肉、腺瘤息肉
- 默认IOU阈值: 0.5
- 默认置信度阈值: 0.5

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库连接参数
   - 确保数据库用户有足够权限

2. **模型文件不存在**
   - 确保 `pt_models/polpy_best.pt` 文件存在
   - 检查模型文件是否损坏

3. **依赖包安装失败**
   - 升级pip: `python -m pip install --upgrade pip`
   - 使用国内镜像源: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/`

4. **界面显示异常**
   - 确保安装了PySide6
   - 检查系统字体是否支持

5. **导出报告失败**
   - 确保有足够的磁盘空间
   - 检查输出目录权限
   - 确保安装了reportlab库

6. **检测耗时显示为0ms**
   - 已修复：现在会正确计算和显示检测耗时
   - 检测耗时包括模型推理和结果处理时间

### 最新更新


- ✅ 修复导出报告失败的问题
- ✅ 优化主页布局：左右显示框 + 下方详情表
- ✅ 修复检测耗时显示为0ms的问题
- ✅ 重新排列按钮布局：保存和导出按钮移到顶部
- ✅ 添加系统图标支持
- ✅ 优化详情表格：序号在第一列，坐标列加宽
- ✅ 改进错误处理和日志输出

### 日志查看
系统运行时会输出详细的日志信息，包括：
- 数据库连接状态
- 模型加载过程
- 检测结果信息
- 错误和异常信息

## 开发说明

### 扩展功能
- 添加新的息肉类型识别
- 集成更多医疗设备
- 增加数据分析和可视化
- 支持云端部署

### 性能优化
- 模型推理加速
- 数据库查询优化
- 界面响应性提升
- 内存使用优化

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 联系方式

获取权重和部署相关问题请联系QQ:2642144249（备注：github）。

---

**注意**: 本系统仅供医疗辅助诊断使用，最终诊断结果应由专业医生确认。 