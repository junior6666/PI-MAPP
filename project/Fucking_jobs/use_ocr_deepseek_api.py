import os
import base64
from openai import OpenAI
import time
client = OpenAI(
    api_key="sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln",
    base_url="https://api.siliconflow.cn/v1"
)
image_path = r"H:\pycharm_project\github_projects\PI-MAPP\project\Fucking_jobs\screenshots\quick_20260413_150359_424.png"

with open(image_path, "rb") as f:
    image_data = f.read()

# 我们使用标准库 base64.b64encode 函数将图片编码成 base64 格式的 image_url
encode_start = time.time()
image_url = f"data:image/{os.path.splitext(image_path)[1].lstrip('.')};base64,{base64.b64encode(image_data).decode('utf-8')}"
encode_elapsed = time.time() - encode_start
print(f"📸 图片编码耗时: {encode_elapsed:.4f}秒")
start_time = time.time()
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-OCR",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                },
                {
                    "type": "text",
                    "text": """Convert the document to markdown"""
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
print(f"[Elapsed Time]: {elapsed_time:.2f} seconds")