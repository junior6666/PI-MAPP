"""
KimiWorker 快速测试脚本
用于验证 Kimi API 调用是否正常
"""

import sys
import os
from workers import KimiWorker
from PySide6.QtCore import QCoreApplication


def test_kimi_worker():
    """测试 KimiWorker"""
    print("=" * 50)
    print("KimiWorker 测试")
    print("=" * 50)
    
    # 检查是否有可用的截图文件
    screenshot_dir = "./screenshots"
    if not os.path.exists(screenshot_dir):
        print(f"❌ 截图目录不存在: {screenshot_dir}")
        return
    
    # 查找最新的截图文件
    files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    if not files:
        print(f"❌ 没有找到截图文件")
        print(f"请先运行主程序并截图，或手动放置图片到 {screenshot_dir}")
        return
    
    # 使用最新的截图
    latest_file = sorted(files)[-1]
    image_path = os.path.join(screenshot_dir, latest_file)
    
    print(f"✅ 找到测试图片: {latest_file}")
    print(f"📍 路径: {image_path}")
    print()
    
    # 创建 Qt 应用（KimiWorker 需要）
    app = QCoreApplication(sys.argv)
    
    # 测试参数
    api_key = "sk-v07YQ9sffsU4znH1hbODXsFsz7tkQrm6qpcYJoXLm4cqqaiE"
    prompt = "请描述这张图片的内容。"
    
    print("🚀 开始测试 Kimi API...")
    print()
    
    # 创建 worker
    worker = KimiWorker(api_key, image_path, prompt)
    
    # 定义回调
    def on_completed(text, elapsed):
        print("=" * 50)
        print("✅ Kimi 分析完成!")
        print(f"⏱️  耗时: {elapsed:.2f}s")
        print("=" * 50)
        print("\n分析结果:")
        print("-" * 50)
        print(text)
        print("-" * 50)
        print()
        app.quit()
    
    def on_error(error_msg):
        print("=" * 50)
        print("❌ Kimi 分析失败!")
        print("=" * 50)
        print(f"错误信息: {error_msg}")
        print()
        app.quit()
    
    # 连接信号
    worker.kimi_completed.connect(on_completed)
    worker.error_occurred.connect(on_error)
    
    # 启动 worker
    worker.start()
    
    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    test_kimi_worker()
