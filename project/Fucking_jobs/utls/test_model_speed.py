import os
import base64
import time
from openai import OpenAI
from datetime import datetime

# 初始化客户端
client = OpenAI(
    api_key="sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln",
    base_url="https://api.siliconflow.cn/v1"
)

# 测试图片路径
image_path = r"/project/Fucking_jobs/screenshots/screenshot_20260412_234054_264.png"

# 读取并编码图片
with open(image_path, "rb") as f:
    image_data = f.read()

image_url = f"data:image/{os.path.splitext(image_path)[1].lstrip('.')};base64,{base64.b64encode(image_data).decode('utf-8')}"

# 模型列表（去重）
model_list = [
    'Qwen/Qwen3.5-27B',
    'Qwen/Qwen3.5-35B-A3B',
    'Pro/moonshotai/Kimi-K2.5',
    'Qwen/Qwen3.5-397B-A17B',
    'Qwen/Qwen3.5-122B-A10B',
    'Qwen/Qwen3.5-9B',
    'Qwen/Qwen3.5-4B',
    'zai-org/GLM-4.6V',
    'Qwen/Qwen3-VL-32B-Instruct',
    'Qwen/Qwen3-VL-8B-Instruct',
    'Qwen/Qwen3-VL-30B-A3B-Instruct',
    'Qwen/Qwen3-VL-235B-A22B-Instruct',
    'Qwen/Qwen3-Omni-30B-A3B-Instruct',
    'Qwen/Qwen3-Omni-30B-A3B-Captioner',
    'zai-org/GLM-4.5V',
    'Qwen/Qwen2.5-VL-32B-Instruct',
    'Qwen/Qwen2-VL-72B-Instruct'
]

# 测试提示词（简化版，用于速度测试）
test_prompt = """针对面试场景 解答图中的问题
📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 代码需包含必要的注释和边界处理
- 简要说明算法思路和时间复杂度
- 如有可能，同时给出经典解法和 Pythonic 解法（如列表推导式、生成器、内置函数等）"""

# 存储测试结果
results = []
# 创建输出结果目录
output_dir = os.path.join(os.path.dirname(__file__), "model_outputs")
os.makedirs(output_dir, exist_ok=True)

print("=" * 80)
print("开始测试模型图片推理速度")
print("=" * 80)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"测试图片: {image_path}")
print(f"模型数量: {len(model_list)}")
print("=" * 80)

for idx, model_name in enumerate(model_list, 1):
    print(f"\n[{idx}/{len(model_list)}] 正在测试: {model_name}")
    
    try:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model_name,
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
                            "text": test_prompt
                        }
                    ]
                }
            ],
            max_tokens=200  # 限制输出长度，保证测试一致性
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        content = response.choices[0].message.content
        
        result = {
            'model': model_name,
            'time': elapsed_time,
            'status': 'success',
            'content_length': len(content),
            'content': content,
            'error': None
        }
        
        results.append(result)
        print(f"  ✓ 成功 | 耗时: {elapsed_time:.2f}秒 | 输出长度: {result['content_length']}字符")
        
        # 保存单个模型的输出结果
        safe_model_name = model_name.replace('/', '_').replace('-', '_')
        output_file = os.path.join(output_dir, f"{safe_model_name}.txt")
        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write(f"模型: {model_name}\n")
            out_f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out_f.write(f"耗时: {elapsed_time:.2f}秒\n")
            out_f.write(f"输出长度: {len(content)}字符\n")
            out_f.write("=" * 80 + "\n\n")
            out_f.write(content)
        
    except Exception as e:
        elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = str(e)
        
        result = {
            'model': model_name,
            'time': elapsed_time,
            'status': 'failed',
            'content_length': 0,
            'content': None,
            'error': error_msg
        }
        
        results.append(result)
        print(f"  ✗ 失败 | 耗时: {elapsed_time:.2f}秒 | 错误: {error_msg[:100]}")
        
        # 保存失败信息
        safe_model_name = model_name.replace('/', '_').replace('-', '_')
        output_file = os.path.join(output_dir, f"{safe_model_name}_ERROR.txt")
        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write(f"模型: {model_name}\n")
            out_f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out_f.write(f"状态: 失败\n")
            out_f.write("=" * 80 + "\n\n")
            out_f.write(f"错误信息:\n{error_msg}")

# 统计结果
print("\n" + "=" * 80)
print("测试结果汇总")
print("=" * 80)

# 过滤成功的结果
successful_results = [r for r in results if r['status'] == 'success']

if successful_results:
    # 按耗时排序
    sorted_results = sorted(successful_results, key=lambda x: x['time'])
    
    print(f"\n成功测试: {len(successful_results)}/{len(model_list)} 个模型")
    print(f"失败测试: {len(results) - len(successful_results)} 个模型\n")
    
    print("-" * 80)
    print(f"{'排名':<6}{'模型名称':<45}{'耗时(秒)':<12}{'状态':<8}")
    print("-" * 80)
    
    for rank, result in enumerate(sorted_results, 1):
        status_mark = "✓" if result['status'] == 'success' else "✗"
        print(f"{rank:<6}{result['model']:<45}{result['time']:<12.2f}{status_mark:<8}")
    
    print("-" * 80)
    
    # 推荐最快模型
    fastest_model = sorted_results[0]
    print(f"\n🏆 推荐模型: {fastest_model['model']}")
    print(f"   平均耗时: {fastest_model['time']:.2f}秒")
    print(f"   输出长度: {fastest_model['content_length']}字符")
    
    # 计算平均耗时
    avg_time = sum(r['time'] for r in successful_results) / len(successful_results)
    print(f"\n📊 统计信息:")
    print(f"   平均耗时: {avg_time:.2f}秒")
    print(f"   最快耗时: {sorted_results[0]['time']:.2f}秒 ({sorted_results[0]['model']})")
    print(f"   最慢耗时: {sorted_results[-1]['time']:.2f}秒 ({sorted_results[-1]['model']})")
else:
    print("\n⚠️ 所有模型测试均失败！")

# 显示失败的模型
failed_results = [r for r in results if r['status'] == 'failed']
if failed_results:
    print(f"\n❌ 失败的模型:")
    print("-" * 80)
    for result in failed_results:
        print(f"  - {result['model']}")
        print(f"    错误: {result['error'][:150]}")

# 生成报告文件
report_path = os.path.join(os.path.dirname(__file__), "模型调用报告.md")

with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# 模型图片推理速度测试报告\n\n")
    f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**测试图片**: `{image_path}`\n\n")
    f.write(f"**测试模型数量**: {len(model_list)}\n\n")
    
    f.write("---\n\n")
    
    f.write("## 📊 测试结果汇总\n\n")
    
    if successful_results:
        sorted_results = sorted(successful_results, key=lambda x: x['time'])
        
        f.write(f"- **成功测试**: {len(successful_results)}/{len(model_list)} 个模型\n")
        f.write(f"- **失败测试**: {len(failed_results)} 个模型\n")
        
        avg_time = sum(r['time'] for r in successful_results) / len(successful_results)
        f.write(f"- **平均耗时**: {avg_time:.2f}秒\n\n")
        
        f.write("---\n\n")
        
        f.write("## 🏆 推荐模型\n\n")
        fastest_model = sorted_results[0]
        f.write(f"**最佳模型**: `{fastest_model['model']}`\n\n")
        f.write(f"- 耗时: {fastest_model['time']:.2f}秒\n")
        f.write(f"- 输出长度: {fastest_model['content_length']}字符\n\n")
        
        f.write("---\n\n")
        
        f.write("## 📈 详细排名\n\n")
        f.write("| 排名 | 模型名称 | 耗时(秒) | 输出长度(字符) | 状态 | 输出文件 |\n")
        f.write("|------|----------|----------|----------------|------|----------|\n")
        
        for rank, result in enumerate(sorted_results, 1):
            safe_model_name = result['model'].replace('/', '_').replace('-', '_')
            output_file = f"model_outputs/{safe_model_name}.txt"
            f.write(f"| {rank} | `{result['model']}` | {result['time']:.2f} | {result['content_length']} | ✅ | [查看]({output_file}) |\n")
        
        f.write("\n---\n\n")
        
        f.write("## ⚡ 性能分析\n\n")
        f.write("### 快速模型 (< 5秒)\n\n")
        fast_models = [r for r in sorted_results if r['time'] < 5]
        if fast_models:
            for r in fast_models:
                f.write(f"- `{r['model']}`: {r['time']:.2f}秒\n")
        else:
            f.write("无\n")
        
        f.write("\n### 中等速度 (5-15秒)\n\n")
        medium_models = [r for r in sorted_results if 5 <= r['time'] < 15]
        if medium_models:
            for r in medium_models:
                f.write(f"- `{r['model']}`: {r['time']:.2f}秒\n")
        else:
            f.write("无\n")
        
        f.write("\n### 较慢模型 (> 15秒)\n\n")
        slow_models = [r for r in sorted_results if r['time'] >= 15]
        if slow_models:
            for r in slow_models:
                f.write(f"- `{r['model']}`: {r['time']:.2f}秒\n")
        else:
            f.write("无\n")
        
        f.write("\n---\n\n")
        
        f.write("## 💡 使用建议\n\n")
        f.write("1. **实时应用场景**: 推荐使用耗时 < 5秒的模型\n")
        f.write("2. **批量处理场景**: 可选择性价比更高的中等速度模型\n")
        f.write("3. **高精度需求**: 可考虑较慢但可能更准确的模型\n")
        f.write(f"4. **当前最优选择**: `{fastest_model['model']}`\n")
    
    if failed_results:
        f.write("\n---\n\n")
        f.write("## ❌ 测试失败的模型\n\n")
        for result in failed_results:
            safe_model_name = result['model'].replace('/', '_').replace('-', '_')
            error_file = f"model_outputs/{safe_model_name}_ERROR.txt"
            f.write(f"### `{result['model']}`\n\n")
            f.write(f"- 错误信息: {result['error']}\n")
            f.write(f"- 错误日志: [查看]({error_file})\n\n")
    
    f.write("---\n\n")
    f.write("*本报告由自动化测试脚本生成*\n")

print(f"\n📄 报告已保存至: {report_path}")
print(f"📁 模型输出已保存至: {output_dir}")
print("=" * 80)
