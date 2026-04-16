import os
import base64
from openai import OpenAI
import time
from pathlib import Path

# 配置API客户端
client = OpenAI(
    api_key="sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln",
    base_url="https://api.siliconflow.cn/v1"
)

# 配置路径
input_folder = r"C:\Users\pc\Downloads\screenshots"
output_folder = r"C:\Users\pc\Downloads\screenshots\r"

# 支持的图片格式
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}

def ensure_output_folder():
    """确保输出文件夹存在"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ 创建输出文件夹: {output_folder}")

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    ext = os.path.splitext(image_path)[1].lstrip('.')
    image_url = f"data:image/{ext};base64,{base64.b64encode(image_data).decode('utf-8')}"
    return image_url

def ocr_image(image_path):
    """对单张图片进行OCR识别"""
    try:
        # 编码图片
        encode_start = time.time()
        image_url = image_to_base64(image_path)
        encode_elapsed = time.time() - encode_start
        
        # 调用API
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
                            "text": "Convert the document to markdown"
                        }
                    ]
                }
            ]
        )
        
        elapsed_time = time.time() - start_time
        content = response.choices[0].message.content
        
        return content, encode_elapsed, elapsed_time
        
    except Exception as e:
        print(f"❌ 处理失败: {image_path}")
        print(f"   错误信息: {str(e)}")
        return None, 0, 0

def process_batch():
    """批量处理图片"""
    ensure_output_folder()
    
    # 获取所有图片文件
    image_files = []
    for file in os.listdir(input_folder):
        ext = os.path.splitext(file)[1].lower()
        if ext in SUPPORTED_FORMATS:
            image_files.append(file)
    
    if not image_files:
        print(f"⚠️ 在 {input_folder} 中未找到支持的图片文件")
        return
    
    print(f"📸 找到 {len(image_files)} 张图片，开始批量处理...\n")
    
    success_count = 0
    fail_count = 0
    total_start = time.time()
    
    for idx, filename in enumerate(image_files, 1):
        image_path = os.path.join(input_folder, filename)
        
        # 生成输出文件名（同名但扩展名为.txt）
        output_filename = os.path.splitext(filename)[0] + ".txt"
        output_path = os.path.join(output_folder, output_filename)
        
        print(f"[{idx}/{len(image_files)}] 处理: {filename}")
        
        # 执行OCR
        content, encode_time, api_time = ocr_image(image_path)
        
        if content:
            # 保存结果到txt文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            success_count += 1
            print(f"   ✅ 成功 | 编码: {encode_time:.2f}s | API: {api_time:.2f}s | 保存至: {output_filename}")
        else:
            fail_count += 1
            print(f"   ❌ 失败")
        
        print()
    
    total_time = time.time() - total_start
    
    # 打印统计信息
    print("=" * 60)
    print("📊 处理完成统计:")
    print(f"   总图片数: {len(image_files)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {fail_count}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均每张: {total_time/len(image_files):.2f}秒")
    print(f"   结果保存在: {output_folder}")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 DeepSeek OCR 批量处理工具")
    print(f"📂 输入文件夹: {input_folder}")
    print(f"📁 输出文件夹: {output_folder}")
    print("-" * 60)
    
    process_batch()
    
    print("\n按回车键退出...")
    input()
