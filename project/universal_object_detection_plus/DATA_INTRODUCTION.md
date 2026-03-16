## 我目前所整理的权重介绍(部分) 均可在软件中直接下载

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
