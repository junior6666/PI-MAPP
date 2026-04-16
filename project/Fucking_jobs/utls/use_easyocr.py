import easyocr
import os
import warnings

# 抑制 PyTorch pin_memory 警告
warnings.filterwarnings('ignore', message=".*pin_memory.*")

# 使用原始字符串避免路径转义问题
image_path = r'/project/Fucking_jobs/screenshots/ScreenShot_2026-04-13_140714_532.png'

# 检查文件是否存在
if not os.path.exists(image_path):
    print(f"错误: 文件不存在 - {image_path}")
else:
    # 初始化 OCR reader (CPU 模式)
    # gpu=False 可以避免 pin_memory 警告
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    # 执行 OCR 识别
    result = reader.readtext(image_path)
    
    # 输出识别结果
    print(f"共识别到 {len(result)} 个文本块:\n")
    for idx, (bbox, text, prob) in enumerate(result, 1):
        print(f'{idx}. {text} (置信度: {prob:.2f})')