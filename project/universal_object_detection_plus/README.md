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
## YOLOv8 - YOLOv12 权重下载链接 🚀

### 代码自动下载 🧑‍💻
```python
from ultralytics import YOLO
# 下面任意一行代码都可以自动从对应链接下载权重到当前目录，你也可以手动从链接中下载权重（需要科学上网）;经测试，目前该UI支持以下所有权重

# YOLOv8
model = YOLO('yolov8s.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov8m.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov8l.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov8x.pt')  # 🌟 你可以选择 s/m/l/x 版本

# YOLOv9
model = YOLO('yolov9s.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov9m.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov9l.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov9x.pt')  # 🌟 你可以选择 s/m/l/x 版本

# YOLOv10
model = YOLO('yolov10s.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov10m.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov10l.pt')  # 🌟 你可以选择 s/m/l/x 版本
model = YOLO('yolov10x.pt')  # 🌟 你可以选择 s/m/l/x 版本

# YOLOv11
model = YOLO('yolo11n.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo11m.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo11l.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo11x.pt')  # 🌟 你可以选择 n/m/l/x 版本

# YOLOv12
model = YOLO('yolo12n.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo12m.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo12l.pt')  # 🌟 你可以选择 n/m/l/x 版本
model = YOLO('yolo12x.pt')  # 🌟 你可以选择 n/m/l/x 版本
```

## 🌐 手动下载链接（需访问 GitHub）

您可以复制以下链接，在浏览器中直接下载对应模型权重：

### YOLOv8
- `yolov8s.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt) 🔗
- `yolov8m.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt) 🔗
- `yolov8l.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt) 🔗
- `yolov8x.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x.pt) 🔗

### YOLOv9
- `yolov9s.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov9s.pt) 🔗
- `yolov9m.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov9m.pt) 🔗
- `yolov9l.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov9l.pt) 🔗
- `yolov9x.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov9x.pt) 🔗

### YOLOv10
- `yolov10s.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10s.pt) 🔗
- `yolov10m.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10m.pt) 🔗
- `yolov10l.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10l.pt) 🔗
- `yolov10x.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10x.pt) 🔗

### YOLOv11
- `yolo11n.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt) 🔗
- `yolo11m.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt) 🔗
- `yolo11l.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt) 🔗
- `yolo11x.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt) 🔗

### YOLOv12
- `yolo12n.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo12n.pt) 🔗
- `yolo12m.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo12m.pt) 🔗
- `yolo12l.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo12l.pt) 🔗
- `yolo12x.pt` → [下载链接](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo12x.pt) 🔗
---
###  权重和数据获取技巧
kaggle: https://www.kaggle.com
该网页中有非常多的公开数据集，可以说没有你找不到的 只有你想不到的。
找到数据集后，可以在网页中下载数据集在本地训练（可直接在kaggle中训练），也可找到数据集相关的code,查看其output 运气好可直接下载对应数据集的权重
---
## 我目前所整理的权重介绍及获取方式 

### 垃圾检测 (Garbage Detection)
- **权重名**：`garbage_detection.pt` (垃圾检测权重)
- **分类目标**：
  - 0: Aluminium foil (铝箔)
  - 1: Bottle cap (瓶盖)
  - 2: Bottle (瓶子)
  - 3: Broken glass (碎玻璃)
  - 4: Can (罐子)
  - 5: Carton (纸板)
  - 6: Cigarette (香烟)
  - 7: Cup (杯子)
  - 8: Lid (盖子)
  - 9: Other litter (其他垃圾)
  - 10: Other plastic (其他塑料)
  - 11: Paper (纸张)
  - 12: Plastic bag - wrapper (塑料袋 - 包装纸)
  - 13: Plastic container (塑料容器)
  - 14: Pop tab (拉环)
  - 15: Straw (吸管)
  - 16: Styrofoam piece (泡沫塑料碎片)
  - 17: Unlabeled litter (未标记的垃圾)

### 头盔检测 (Helmet Detection)
- **权重名**：`helmet_detection.pt` (头盔检测权重)
- **分类目标**：
  - 0: Helmet (头盔)
  - 1: Face (面部)

### 息肉诊断 (Polyp Diagnosis)
- **权重名**：`polyp_diagnosis.pt` (息肉诊断权重)
- **分类目标**：
  - 0: O_Hyperplastic (增生性息肉)
  - 1: 1_Adenomatic (腺瘤性息肉)

### 文档分析 (Document Analysis)
- **权重名**：`document_analysis.pt` (文档分析权重)
- **分类目标**：
  - 0: Caption (标题)
  - 1: Footnote (脚注)
  - 2: Formula (公式)
  - 3: List-item (列表项)
  - 4: Page-footer (页脚)
  - 5: Page-header (页眉)
  - 6: Picture (图片)
  - 7: Section-header (节标题)
  - 8: Table (表格)
  - 9: Text (文本)
  - 10: Title (标题)

### 火情诊断 (Fire and Smoke Detection)
- **权重名**：`fire_smoke_detection.pt` (火情诊断权重)
- **分类目标**：
  - 0: fire (火)
  - 1: smoke (烟)

### 摔倒检测 (Fall Detection)
- **权重名**：`fall_detection.pt` (摔倒检测权重)
- **分类目标**：
  - 0: Fall Detected (检测到摔倒)
  - 1: Walking (行走)
  - 2: Sitting (坐着)

### 动物检测 (Animal Detection)
- **权重名**：`animal_detection.pt` (动物检测权重)
- **分类目标**：
  - 0: tit (山雀)
  - 1: bullfinch (金翅雀)
  - 2: squirrel (松鼠)
  - 3: jay (鹊)

### 无人机检测 (Drone Detection)
- **权重名**：`drone_detection.pt` (无人机检测权重)
- **分类目标**：
  - 0: drone (无人机)

### vis_drone2019_数据集目标检测 (vis_drone2019 Dataset Object Detection)
- **权重名**：`vis_drone2019_detection.pt` (vis_drone2019 数据集目标检测权重)
- **分类目标**：
  - 0: pedestrian (行人)
  - 1: people (人群)
  - 2: bicycle (自行车)
  - 3: car (汽车)
  - 4: van (面包车)
  - 5: truck (卡车)
  - 6: tricycle (三轮车)
  - 7: awning-tricycle (带遮阳篷的三轮车)
  - 8: bus (公共汽车)
  - 9: motor (摩托车)
### 日常交通工具检测（监控视角）
类别对照表（ID → 中文名称）
| ID | 英文名称 | 中文名称 |
|----|--------|--------|
| 0 | articulated_truck | 铰接式卡车 |
| 1 | bicycle | 自行车 |
| 2 | bus | 公交车 |
| 3 | car | 小汽车 |
| 4 | motorcycle | 摩托车 |
| 5 | motorized_vehicle | 机动车辆（泛指） |
| 6 | non-motorized_vehicle | 非机动车辆（泛指） |
| 7 | pedestrian | 行人 |
| 8 | pickup_truck | 皮卡车 |
| 9 | single_unit_truck | 单体卡车 |
| 10 | work_van | 厢式工作车/作业面包车 |

---
### 战舰检测（仅供学习研究）
类别对照表（ID → 中文名称）

| ID | 英文名称 | 中文名称 |
|----|--------|--------|
| 0 | AOE | 快速战斗支援舰（AOE） |
| 1 | Arleigh Burke DD | 阿利·伯克级驱逐舰 |
| 2 | Asagiri DD | 朝雾级驱逐舰 |
| 3 | Atago DD | 爱宕级驱逐舰 |
| 4 | Austin LL | 奥斯汀级船坞登陆舰 |
| 5 | Barge | 驳船 |
| 6 | Cargo | 货船 |
| 7 | Commander | 指挥舰 |
| 8 | Container Ship | 集装箱船 |
| 9 | Dock | 浮船坞 |
| 10 | EPF | 远征快速运输舰 |
| 11 | Enterprise | 企业号航空母舰 |
| 12 | Ferry | 渡轮 |
| 13 | Fishing Vessel | 渔船 |
| 14 | Hatsuyuki DD | 初雪级驱逐舰 |
| 15 | Hovercraft | 气垫船 |
| 16 | Hyuga DD | 日向级直升机驱逐舰 |
| 17 | LHA LL | 两栖攻击舰（LHA） |
| 18 | LSD 41 LL | 惠德贝岛级船坞登陆舰 |
| 19 | Masyuu AS | 摩周级补给舰 |
| 20 | Medical Ship | 医疗船 |
| 21 | Midway | 中途岛号航空母舰 |
| 22 | Motorboat | 摩托艇 |
| 23 | Nimitz | 尼米兹级航空母舰 |
| 24 | Oil Tanker | 油轮 |
| 25 | Osumi LL | 大隅级运输登陆舰 |
| 26 | Other Aircraft Carrier | 其他航空母舰 |
| 27 | Other Auxiliary Ship | 其他辅助舰船 |
| 28 | Other Destroyer | 其他驱逐舰 |
| 29 | Other Frigate | 其他护卫舰 |
| 30 | Other Landing | 其他登陆舰 |
| 31 | Other Merchant | 其他商船 |
| 32 | Other Ship | 其他船舶 |
| 33 | Other Warship | 其他军舰 |
| 34 | Patrol | 巡逻艇 |
| 35 | Perry FF | 佩里级护卫舰 |
| 36 | RoRo | 滚装船 |
| 37 | Sailboat | 帆船 |
| 38 | Sanantonio AS | 圣安东尼奥级船坞运输舰 |
| 39 | Submarine | 潜艇 |
| 40 | Test Ship | 试验船 |
| 41 | Ticonderoga | 提康德罗加级巡洋舰 |
| 42 | Training Ship | 训练舰 |
| 43 | Tugboat | 拖船 |
| 44 | Wasp LL | 黄蜂级两栖攻击舰 |
| 45 | Yacht | 游艇 |
| 46 | YuDao LL | 玉岛级登陆舰 |
| 47 | YuDeng LL | 玉登级登陆舰 |
| 48 | YuTing LL | 玉亭级登陆舰 |
| 49 | YuZhao LL | 玉昭级登陆舰 |
### 足球运动员检测

| 类别编号 | 英文原名 | 中文翻译 |
|---------|----------|----------|
| 0       | football | 足球     |
| 1       | player   | 运动员   |

### 粉刺检测

| 类别编号 | 英文原名 | 中文翻译 |
|---------|----------|----------|
| 0       | Acne     | 粉刺     |

### 国际象棋检测

| 类别编号 | 英文原名      | 中文翻译 |
|---------|---------------|----------|
| 0       | bishop        | 象       |
| 1       | black-bishop  | 黑象     |
| 2       | black-king    | 黑王     |
| 3       | black-knight  | 黑马     |
| 4       | black-pawn    | 黑兵     |
| 5       | black-queen   | 黑后     |
| 6       | black-rook    | 黑车     |
| 7       | white-bishop  | 白象     |
| 8       | white-king    | 白王     |
| 9       | white-knight  | 白马     |
| 10      | white-pawn    | 白兵     |
| 11      | white-queen   | 白后     |
| 12      | white-rook    | 白车     |

### 牙科检测

| 类别编号 | 英文原名          | 中文翻译     |
|---------|-------------------|--------------|
| 0       | 1st Molar         | 第一磨牙     |
| 1       | 1st Premolar      | 第一前磨牙   |
| 2       | 2nd Molar         | 第二磨牙     |
| 3       | 2nd Premolar      | 第二前磨牙   |
| 4       | Canine            | 尖牙（犬齿） |
| 5       | Central Incisor   | 中切牙       |
| 6       | Lateral Incisor   | 侧切牙       |

### 交通信号灯（节选）

| 类别编号 | 英文原名                                                                                      | 中文翻译                     |
|---------|-----------------------------------------------------------------------------------------------|------------------------------|
| 104     | 50 meters between vehicles                                                                    | 保持50米车距                 |
| 147     | Advance direction sign exit ahead from other road than motorway or expressway                 | 前方出口预告（非高速）       |
| 148     | Axle weight limit-2ton                                                                        | 轴重限制2吨                  |
| 149     | Bus stop                                                                                      | 公交停靠站                   |
| 150     | Cattle                                                                                        | 牲畜出没                     |
| 151     | Crossroad intersection                                                                        | 交叉口                       |
| 152     | Crossroads                                                                                    | 十字交叉路口                 |
| 153     | Cycle track                                                                                   | 自行车道                     |
| 154     | Cyclist and mopeds rides on carriageway                                                       | 自行车/助力车混行            |
| 155     | Cyclists                                                                                      | 注意自行车                   |
| 156     | Dangerous shoulder                                                                            | 路肩危险                     |
| 157     | Dip                                                                                           | 路面凹陷                     |
| 158     | Direction sign exit sign                                                                      | 出口方向标志                 |
| 159     | Direction to be followed                                                                      | 强制通行方向                 |
| 160     | End of all restrictions                                                                       | 解除全部限制                 |
| 161     | End of lane reserved for public transport                                                     | 公交专用道结束               |
| 162     | Falling rocks                                                                                 | 落石                         |
| 163     | Filling station                                                                               | 加油站                       |
| 261     | tunnel in 2 km                                                                                | 2 km 处有隧道                |
| 262     | two way traffic                                                                               | 双向交通                     |
| 263     | warning wild animal                                                                           | 注意野生动物                 |

### 水果检测

| 类别编号 | 英文原名   | 中文翻译 |
|---------|------------|----------|
| 0       | Apple      | 苹果     |
| 1       | Banana     | 香蕉     |
| 2       | Grape      | 葡萄     |
| 3       | Orange     | 橙子     |
| 4       | Pineapple  | 菠萝     |
| 5       | Watermelon | 西瓜     |

### 眼球检测

| 类别编号 | 标签 | 中文翻译 |
|---------|----|----------|
| 0       | 0  | 眼球     |

### 脑部肿瘤检测

| 类别编号 | 英文原名   | 中文翻译 |
|---------|------------|----------|
| 0       | glioma     | 胶质瘤   |
| 1       | meningioma | 脑膜瘤   |
| 2       | pituitary  | 垂体瘤   |

### 凹坑检测

| 类别编号 | 英文原名 | 中文翻译   |
|---------|----------|------------|
| 0       | Potholes | 路面凹坑   |

### 立方体检测

| 类别编号 | 英文原名              | 中文翻译         |
|---------|-----------------------|------------------|
| 0       | big green cube        | 大绿色立方体     |
| 1       | brown hole            | 棕色孔洞         |
| 2       | small red cylinder    | 小红色圆柱体     |
| 3       | yellow cube           | 黄色立方体       |

#### 🎉 **联系方式** 📧
联系邮箱：2642144249@qq.com


🔗 **打赏支付方式**：
- 微信支付 <img src="donate/donate.png" alt="描述" width="" height="200">
支付宝  <img src="donate/zhifubao.jpg" alt="描述" width="" height="200">



🌟 **私人定制**：如有特殊需求，可联系邮箱 2642144249@qq.com 进行定制，我们将根据您的需求提供专属服务。
### 2. 启动应用程序
```bash
# 运行主程序
python enhanced_ui_main.py

# 或者运行其他版本
python enhanced_detection_main.py  # 基础版本
```

## 基本使用流程
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
- **独立控制**: 每个摄像头可以独立控制开始/停止（TODO）
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
- **项目打包**: pyinstaller -F -w   --name YOLO_DETECTOR enhanced_ui_main.py


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
* 类别信息： {0: 'Aluminium foil', 1: 'Bottle cap', 2: 'Bottle', 3: 'Broken glass', 4: 'Can', 5: 'Carton', 6: 'Cigarette', 7: 'Cup', 8: 'Lid', 9: 'Other litter', 10: 'Other plastic', 11: 'Paper', 12: 'Plastic bag - wrapper', 13: 'Plastic container', 14: 'Pop tab', 15: 'Straw', 16: 'Styrofoam piece', 17: 'Unlabeled litter'}
![垃圾检测.png](ui_predict_results/%E5%9E%83%E5%9C%BE%E6%A3%80%E6%B5%8B.png)
* 头盔检测
* 类别信息： {0: 'Helmet', 1: 'Face'}
![头盔检测.png](ui_predict_results/%E5%A4%B4%E7%9B%94%E6%A3%80%E6%B5%8B.png)
* 息肉诊断
* 类别信息： {0: 'O_Hyperplastic', 1: '1_Adenomatic'}
![息肉诊断.png](ui_predict_results/%E6%81%AF%E8%82%89%E8%AF%8A%E6%96%AD.png)
* 文档分析
* 类别信息： {0: 'Caption', 1: 'Footnote', 2: 'Formula', 3: 'List-item', 4: 'Page-footer', 5: 'Page-header', 6: 'Picture', 7: 'Section-header', 8: 'Table', 9: 'Text', 10: 'Title'}
![文档分析.png](ui_predict_results/%E6%96%87%E6%A1%A3%E5%88%86%E6%9E%90.png)
* 火情诊断
* 类别信息： {0: 'fire', 1: 'smoke'}
![火情检测.png](ui_predict_results/%E7%81%AB%E6%83%85%E6%A3%80%E6%B5%8B.png)
* 摔倒检测
* 类别信息： {0: 'Fall Detected', 1: 'Walking', 2: 'Sitting'}
![摔倒检测.png](ui_predict_results/%E6%91%94%E5%80%92%E6%A3%80%E6%B5%8B.png)
* 动物检测
* 类别信息： {0: 'tit', 1: 'bullfinch', 2: 'squirrel', 3: 'jay'}
![动物检测.png](ui_predict_results/%E5%8A%A8%E7%89%A9%E6%A3%80%E6%B5%8B.png)
* 无人机检测
* 类别信息：{0: 'drone'}
![无人机检测.png](ui_predict_results/%E6%97%A0%E4%BA%BA%E6%9C%BA%E6%A3%80%E6%B5%8B.png)
* vis_drone2019_数据集目标检测
* 类别信息： {0: 'pedestrian', 1: 'people', 2: 'bicycle', 3: 'car', 4: 'van', 5: 'truck', 6: 'tricycle', 7: 'awning-tricycle', 8: 'bus', 9: 'motor'}
![vis_drone2019数据集目标检测.png](ui_predict_results/vis_drone2019%E6%95%B0%E6%8D%AE%E9%9B%86%E7%9B%AE%E6%A0%87%E6%A3%80%E6%B5%8B.png)
* Daily Transportation Detection（日常交通工具检测，监控视角）
* 类别信息： {0: 'articulated_truck', 1: 'bicycle', 2: 'bus', 3: 'car', 4: 'motorcycle', 5: 'motorized_vehicle', 6: 'non-motorized_vehicle', 7: 'pedestrian', 8: 'pickup_truck', 9: 'single_unit_truck', 10: 'work_van'}
![日常交通工具检测.png](ui_predict_results/%E6%97%A5%E5%B8%B8%E4%BA%A4%E9%80%9A%E5%B7%A5%E5%85%B7%E6%A3%80%E6%B5%8B.png)
* 战舰检测（仅可用作学习研究）
* 类别信息： {0: 'AOE', 1: 'Arleigh Burke DD', 2: 'Asagiri DD', 3: 'Atago DD', 4: 'Austin LL', 5: 'Barge', 6: 'Cargo', 7: 'Commander', 8: 'Container Ship', 9: 'Dock', 10: 'EPF', 11: 'Enterprise', 12: 'Ferry', 13: 'Fishing Vessel', 14: 'Hatsuyuki DD', 15: 'Hovercraft', 16: 'Hyuga DD', 17: 'LHA LL', 18: 'LSD 41 LL', 19: 'Masyuu AS', 20: 'Medical Ship', 21: 'Midway', 22: 'Motorboat', 23: 'Nimitz', 24: 'Oil Tanker', 25: 'Osumi LL', 26: 'Other Aircraft Carrier', 27: 'Other Auxiliary Ship', 28: 'Other Destroyer', 29: 'Other Frigate', 30: 'Other Landing', 31: 'Other Merchant', 32: 'Other Ship', 33: 'Other Warship', 34: 'Patrol', 35: 'Perry FF', 36: 'RoRo', 37: 'Sailboat', 38: 'Sanantonio AS', 39: 'Submarine', 40: 'Test Ship', 41: 'Ticonderoga', 42: 'Training Ship', 43: 'Tugboat', 44: 'Wasp LL', 45: 'Yacht', 46: 'YuDao LL', 47: 'YuDeng LL', 48: 'YuTing LL', 49: 'YuZhao LL'}
![战舰检测.png](ui_predict_results/%E6%88%98%E8%88%B0%E6%A3%80%E6%B5%8B.png)
---
* 足球运动员检测
* 类别信息： {0: 'football', 1: 'player'}
![足球运动员检测.png](ui_predict_results/%E8%B6%B3%E7%90%83%E8%BF%90%E5%8A%A8%E5%91%98%E6%A3%80%E6%B5%8B.png)
* 粉刺检测
* 类别信息： {0: 'Acne'}
![粉刺检测.png](ui_predict_results/%E7%B2%89%E5%88%BA%E6%A3%80%E6%B5%8B.png)
* 国际象棋检测
* 类别信息： {0: 'bishop', 1: 'black-bishop', 2: 'black-king', 3: 'black-knight', 4: 'black-pawn', 5: 'black-queen', 6: 'black-rook', 7: 'white-bishop', 8: 'white-king', 9: 'white-knight', 10: 'white-pawn', 11: 'white-queen', 12: 'white-rook'}
![国际象棋检测.png](ui_predict_results/%E5%9B%BD%E9%99%85%E8%B1%A1%E6%A3%8B%E6%A3%80%E6%B5%8B.png)
* 牙科检测
* 类别信息： {0: '1st Molar', 1: '1st Premolar', 2: '2nd Molar', 3: '2nd Premolar', 4: 'Canine', 5: 'Central Incisor', 6: 'Lateral Incisor'}
![牙科检测.png](ui_predict_results/%E7%89%99%E7%A7%91%E6%A3%80%E6%B5%8B.png)
* 交通信号灯
* 类别信息： {0: '0', 1: '1', 2: '100', 3: '101', 4: '102', 5: '103', 6: '105', 7: '106', 8: '107', 9: '108', 10: '109', 11: '110', 12: '111', 13: '112', 14: '113', 15: '115', 16: '116', 17: '117', 18: '12', 19: '120', 20: '121', 21: '122', 22: '123', 23: '124', 24: '125', 25: '127', 26: '128', 27: '129', 28: '131', 29: '132', 30: '133', 31: '136', 32: '137', 33: '138', 34: '139', 35: '140', 36: '141', 37: '142', 38: '143', 39: '144', 40: '145', 41: '146', 42: '147', 43: '148', 44: '149', 45: '15', 46: '150', 47: '153', 48: '154', 49: '155', 50: '156', 51: '158', 52: '159', 53: '16', 54: '161', 55: '163', 56: '164', 57: '166', 58: '167', 59: '168', 60: '169', 61: '17', 62: '170', 63: '171', 64: '172', 65: '173', 66: '174', 67: '175', 68: '177', 69: '178', 70: '179', 71: '18', 72: '180', 73: '181', 74: '19', 75: '2', 76: '20', 77: '21', 78: '22', 79: '23', 80: '24', 81: '27', 82: '28', 83: '29', 84: '3', 85: '31', 86: '32', 87: '33', 88: '34', 89: '35', 90: '36', 91: '39', 92: '4', 93: '40', 94: '41', 95: '42', 96: '43', 97: '45', 98: '46', 99: '47', 100: '48', 101: '49', 102: '5', 103: '50', 104: '50 meters between vehicles', 105: '51', 106: '52', 107: '53', 108: '54', 109: '55', 110: '56', 111: '57', 112: '59', 113: '60', 114: '62', 115: '63', 116: '64', 117: '65', 118: '66', 119: '67', 120: '68', 121: '69', 122: '70', 123: '71', 124: '73', 125: '74', 126: '76', 127: '78', 128: '79', 129: '8', 130: '81', 131: '82', 132: '83', 133: '84', 134: '85', 135: '86', 136: '87', 137: '88', 138: '89', 139: '90', 140: '91', 141: '93', 142: '94', 143: '95', 144: '97', 145: '98', 146: '99', 147: 'Advance direction sign exit ahead from other road than motorway or expressway', 148: 'Axle weight limit-2ton', 149: 'Bus stop', 150: 'Cattle', 151: 'Crossroad intersection', 152: 'Crossroads', 153: 'Cycle track', 154: 'Cyclist and mopeds rides on carrigeway', 155: 'Cyclists', 156: 'Dangerous shoulder', 157: 'Dip', 158: 'Direction sign exit sign', 159: 'Direction to be followed', 160: 'End of all restrictions', 161: 'End of lane reserved for public transport', 162: 'Falling rocks', 163: 'Filling station', 164: 'First aid post', 165: 'Give way (Yield)', 166: 'Give way -Yield-', 167: 'Guarded level crossing ahead', 168: 'Height limit-3.5m', 169: 'Horn prohibited', 170: 'Hotel', 171: 'Keep left', 172: 'Left curve', 173: 'Level crossing countdown marker', 174: 'Loose gravel', 175: 'Main highways', 176: 'Marking for sharp bends', 177: 'Motorway', 178: 'Narrow bridge', 179: 'Narrow road', 180: 'National border', 181: 'No Left turn', 182: 'No Right turn', 183: 'No entry', 184: 'No entry for Trucks', 185: 'No entry for bicycles', 186: 'No entry for bullock carts', 187: 'No entry for hand carts', 188: 'No entry for motor vehicles', 189: 'No entry for pedestrians', 190: 'No parking', 191: 'No passing', 192: 'No snowmobiles', 193: 'No stopping', 194: 'No vehicles exceeding 12 tonnes', 195: 'No vehicles exceeding length shown', 196: 'No vehicles in both directions', 197: 'No vehicles or combination of vehicles exceeding weight shown', 198: 'Oblique side road junction', 199: 'One-way traffic', 200: 'Parking', 201: 'Parking allowed for 15min', 202: 'Passing without stopping prohibited', 203: 'Pedestrian crossing', 204: 'Priority over oncoming vehicles', 205: 'Refreshments', 206: 'Restaurant', 207: 'Restriction zone', 208: 'Right curve', 209: 'Road hump', 210: 'Road number sign', 211: 'Roadworks', 212: 'Roundabout', 213: 'School', 214: 'Side road junction', 215: 'Slippery road', 216: 'Speed refulcation bump', 217: 'Staggered side road junction', 218: 'Steep ascent', 219: 'Steep descent', 220: 'Steep downhill', 221: 'Steep uphill', 222: 'Stop', 223: 'Stop at customs', 224: 'Straight ahead', 225: 'Symbol plate for specified vehicle or road user category', 226: 'T-junction', 227: 'Telephone', 228: 'Traffic signals', 229: 'Turn Right', 230: 'Turn left', 231: 'Turn left ahead', 232: 'Turn left or straight ahead', 233: 'Turn right ahead', 234: 'Uneven road', 235: 'Unguarded level crossing ahead', 236: 'Unprotected quay', 237: 'Weight limit-5ton', 238: 'Y-junction', 239: 'adjoining way', 240: 'axle weight limit 30tonnes', 241: 'end of the speed limit', 242: 'exit', 243: 'falling rocks (from) left', 244: 'falling rocks -from- left', 245: 'length limit-10m', 246: 'lowspeed zone', 247: 'no entry for bicycles and humans', 248: 'no motorcycles', 249: 'no turning left', 250: 'no u turn', 251: 'snowmobiles', 252: 'speed limit-100', 253: 'speed limit-110', 254: 'speed limit-30', 255: 'speed limit-50', 256: 'speed limit-60', 257: 'speed limit-70', 258: 'speed limit-80', 259: 'speed limit-90', 260: 'speed-limit-120', 261: 'tunnel in 2 km', 262: 'two way traffic', 263: 'warning wild animal'}
![交通信号灯检测.png](ui_predict_results/%E4%BA%A4%E9%80%9A%E4%BF%A1%E5%8F%B7%E7%81%AF%E6%A3%80%E6%B5%8B.png)
* 水果检测
* 类别信息： {0: 'Apple', 1: 'Banana', 2: 'Grape', 3: 'Orange', 4: 'Pineapple', 5: 'Watermelon'}
![水果检测（low_acc）.png](ui_predict_results/%E6%B0%B4%E6%9E%9C%E6%A3%80%E6%B5%8B%EF%BC%88low_acc%EF%BC%89.png)
* 眼球检测
* 类别信息： {0: '0'}
![眼球检测.png](ui_predict_results/%E7%9C%BC%E7%90%83%E6%A3%80%E6%B5%8B.png)
* 脑部肿瘤
* 类别信息： {0: 'glioma', 1: 'meningioma', 2: 'pituitary'}
![脑部肿瘤检测.png](ui_predict_results/%E8%84%91%E9%83%A8%E8%82%BF%E7%98%A4%E6%A3%80%E6%B5%8B.png)* 
* 凹坑检测
* 类别信息： {0: 'Potholes'}
![路面凹坑检测.png](ui_predict_results/%E8%B7%AF%E9%9D%A2%E5%87%B9%E5%9D%91%E6%A3%80%E6%B5%8B.png)
* 立方体检测
* 类别信息： {0: 'big green cube', 1: 'brown hole', 2: 'small red cylinder', 3: 'yellow cube'}
![立方体检测.png](ui_predict_results/%E7%AB%8B%E6%96%B9%E4%BD%93%E6%A3%80%E6%B5%8B.png)

---



**Enhanced Object Detection System v2.0** - 让目标检测更加简单、高效、美观！

🌟 如果这个项目对您有帮助，请给我们一个Star！
