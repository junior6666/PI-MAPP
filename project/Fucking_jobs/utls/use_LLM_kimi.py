import os
import base64

from openai import OpenAI

client = OpenAI(
    api_key="sk-v07YQ9sffsU4znH1hbODXsFsz7tkQrm6qpcYJoXLm4cqqaiE",
    base_url="https://api.moonshot.cn/v1",
)

# 在这里，你需要将 kimi.png 文件替换为你想让 Kimi 识别的图片的地址
image_path = r"/project/Fucking_jobs/screenshots/screenshot_20260412_234054_264.png"

with open(image_path, "rb") as f:
    image_data = f.read()

# 我们使用标准库 base64.b64encode 函数将图片编码成 base64 格式的 image_url
image_url = f"data:image/{os.path.splitext(image_path)[1].lstrip('.')};base64,{base64.b64encode(image_data).decode('utf-8')}"


completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "system", "content": "你是 Kimi。"},
        {
            "role": "user",
            # 注意这里，content 由原来的 str 类型变更为一个 list，这个 list 中包含多个部分的内容，图片（image_url）是一个部分（part），
            # 文字（text）是一个部分（part）
            "content": [
                {
                    "type": "image_url", # <-- 使用 image_url 类型来上传图片，内容为使用 base64 编码过的图片内容
                    "image_url": {
                        "url": image_url,
                    },
                },
                {
                    "type": "text",
                    "text": "请描述图片的内容。", # <-- 使用 text 类型来提供文字指令，例如"描述图片内容"
                },
            ],
        },
    ],
)

print(completion.choices[0].message.content)
# 输出
'''
这张图片显示的是 **LeetCode 中国站点**（leetcode.cn）的编程练习界面，具体是第 **88 题「合并两个有序数组」**（Merge Sorted Array）的解题页面。

以下是详细的内容描述：

## 整体布局
页面采用左右分栏设计：
- **左侧**：题目描述、示例和说明
- **右侧**：代码编辑器（Python3 语言）

## 左侧题目区域
1. **标题栏**：显示「88. 合并两个有序数组」，带有「已解答」状态标记，难度标记为「简单」
2. **题目要求**：
   - 给定两个按**非递减顺序**（即升序）排列的数组 `nums1` 和 `nums2`
   - 整数 `m` 和 `n` 分别表示两个数组的元素数量
   - 要求将 `nums2` 合并到 `nums1` 中，使最终数组保持非递减顺序
   
3. **重要提示**：
   - 结果必须直接存储在 `nums1` 中（而非函数返回）
   - `nums1` 的初始长度为 `m + n`，前 `m` 个元素是有效数据，后 `n` 个元素初始为 0（占位用）

4. **示例展示**：
   - **示例 1**：`nums1 = [1,2,3,0,0,0], m = 3` 与 `nums2 = [2,5,6], n = 3` 合并为 `[1,2,2,3,5,6]`
   - **示例 2**：`nums1 = [1], m = 1` 与空数组 `nums2 = [], n = 0` 合并结果仍为 `[1]`

5. **互动数据**：底部显示有 3K 点赞、5.1K 评论，当前 126 人在线

## 右侧代码编辑区
1. **语言选择**：当前选择 **Python3**，开启「智能模式」
2. **代码模板**：
   ```python
   class Solution:
       def merge(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
   ```
   - 函数签名显示该方法不返回值（`-> None`），要求直接修改 `nums1`
   - 光标停留在第 5 行，等待用户编写具体实现逻辑

3. **操作按钮**：顶部有「运行」「提交」按钮，底部有「测试用例」「测试结果」选项卡

## 其他细节
- **浏览器**：显示多个标签页，包括「面试经典 150 题」学习路径
- **计时器**：右上角显示已用时间 `01:28:29`
- **系统时间**：屏幕右下角显示时间为 **23:40**，日期为 **2026/4/12**
- **任务栏**：可见 Windows 任务栏，有微信、Chrome、VS Code 等应用程序图标

这是一个典型的在线编程练习场景，用户正在解决一个经典的数组双指针算法问题。
'''