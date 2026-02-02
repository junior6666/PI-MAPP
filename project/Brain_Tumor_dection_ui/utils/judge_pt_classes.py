from ultralytics import YOLO
from translate import Translator
import cv2

# # ---------------- 翻译器 ----------------
# trans = Translator(from_lang='en', to_lang='zh')   # 这里用 translate 库

# ---------------- 加载模型 ----------------
model = YOLO(r'H:\pycharm_project\github_projects\PI-MAPP\project\Brain_Tumor_dection_ui\pt_models\Brain_Tumor.pt')

# # ---------------- 一次性把英文类别译成中文 ----------------
# zh_names = {k: trans.translate(v) for k, v in model.names.items()}
# print('中文类别映射：', zh_names)
#
# # ---------------- 推理 ----------------
# results = model('https://ultralytics.com/images/bus.jpg')
#
# # ---------------- 替换 names 并绘图 ----------------
# results[0].names = zh_names                                     # 关键替换
# img = results[0].plot()                        # 中文字体
#
# # ---------------- 显示 ----------------
# cv2.imshow('translate-zh', img)
# cv2.waitKey(0)
# 获取类别信息
class_names = model.names

# 打印类别信息
print("类别信息：", class_names)