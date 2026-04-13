import os
import base64
from openai import OpenAI
import time
client = OpenAI(
    api_key="sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln",
    base_url="https://api.siliconflow.cn/v1"
)
image_path = r"H:\pycharm_project\github_projects\PI-MAPP\project\Fucking_jobs\screenshots\ScreenShot_2026-04-13_140714_532.png"

with open(image_path, "rb") as f:
    image_data = f.read()

# 我们使用标准库 base64.b64encode 函数将图片编码成 base64 格式的 image_url
encode_start = time.time()
image_url = f"data:image/{os.path.splitext(image_path)[1].lstrip('.')};base64,{base64.b64encode(image_data).decode('utf-8')}"
encode_elapsed = time.time() - encode_start
print(f"📸 图片编码耗时: {encode_elapsed:.4f}秒")
model_list = ['Qwen/Qwen3.5-27B','Qwen/Qwen3.5-35B-A3B','Pro/moonshotai/Kimi-K2.5','Qwen/Qwen3.5-397B-A17B','Qwen/Qwen3.5-122B-A10B','Qwen/Qwen3.5-27B','Qwen/Qwen3.5-9B','Qwen/Qwen3.5-4B','zai-org/GLM-4.6V','Qwen/Qwen3-VL-32B-Instruct','Qwen/Qwen3-VL-8B-Instruct','Qwen/Qwen3-VL-30B-A3B-Instruct','Qwen/Qwen3-VL-235B-A22B-Instruct','Qwen/Qwen3-Omni-30B-A3B-Instruct','Qwen/Qwen3-Omni-30B-A3B-Captioner','zai-org/GLM-4.5V','Qwen/Qwen2.5-VL-32B-Instruct','Qwen/Qwen2-VL-72B-Instruct']
start_time = time.time()
response = client.chat.completions.create(
    model="Qwen/Qwen3-Omni-30B-A3B-Instruct",
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
                    "text": """你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

【任务要求】
1. 从屏幕内容中提取面试相关问题（忽略无关信息如时间、浏览器标签等）
2. 根据题型给出对应的回答：

【回答格式】

📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 代码需包含必要的注释和边界处理
- 简要说明算法思路和时间复杂度
- 如有可能，同时给出经典解法和 Pythonic 解法（如列表推导式、生成器、内置函数等）

📌 如果是选择题：
- 直接给出正确答案的序号（如：答案：B）
- 简要解释选择理由（1-2句话）
- 如果识别到多个选择题，按题目序号依次作答（如：1. 答案：A, 2. 答案：C）

📌 如果是简答题/概念题：
- 给出清晰、结构化的回答
- 分点阐述关键要点
- 适当举例说明
- 如果识别到多个简答/概念题，按题目序号依次作答（如：1. xxx  2. xxx）

📌 如果是系统设计题：
- 给出系统架构设计思路
- 列出关键技术选型
- 说明核心流程和注意事项

📌 如果是性格测试题：
- 选择积极乐观、团队协作导向的选项
- 体现责任心、学习能力、抗压能力等正面特质
- 保持前后作答一致性（若识别到相同/相似题目，选择相同选项）
- 简要说明选择理由（1句话）



【注意事项】
- 只回答识别到的面试问题，忽略屏幕上的其他干扰信息
- 回答要简洁专业，适合面试场景口头表达
- 代码题必须提供可运行的完整代码
- 如果屏幕上有多个题目，按题号依次作答（1., 2., 3. ...）
- 每个题目之间用 --- 分割线隔开"""
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
print(f"[Elapsed Time]: {elapsed_time:.2f} seconds")