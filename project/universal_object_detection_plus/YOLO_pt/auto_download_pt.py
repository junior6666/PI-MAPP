#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量下载 YOLOv8 ~ YOLO26 的检测与分割权重（含 v9/v10 尝试）
使用 ultralytics.YOLO 自动下载，带随机延时和统计
"""

import time
import random
from ultralytics import YOLO
from pathlib import Path


def main():
    # 定义模型系列和尺寸
    model_series = ["yolov8", "yolov9", "yolov10", "yolo11", "yolo26"]
    sizes = ["n", "s", "m", "l", "x"]
    v9_sizes = ["n", "s", "m", "l", "x"]

    # 任务后缀：检测无后缀，分割加 "-seg"
    tasks = {
        "detect": "",
        "segment": "-seg"
    }

    success_count = 0
    fail_count = 0
    failed_models = []

    print("🚀 开始批量下载 YOLO 权重（v8 ~ v26，含 detect/segment）...")
    print("⏳ 每次下载前将随机等待 5~15 秒...\n")

    for series in model_series:
        for task_name, suffix in tasks.items():
            for size in sizes:
                model_name = f"{series}{size}{suffix}.pt"

                # 随机延时（5~15秒）
                delay = random.randint(5, 10)
                print(f"🕒 等待 {delay} 秒后尝试下载: {model_name}")
                time.sleep(delay)

                try:
                    print(f"📥 正在加载模型: {model_name}")
                    # 关键：YOLO() 会自动下载并缓存
                    model = YOLO(model_name)

                    # 验证是否成功加载（检查是否有模型属性）
                    if hasattr(model, 'model') and model.model is not None:
                        print(f"✅ 成功下载并加载: {model_name}")
                        success_count += 1
                    else:
                        raise RuntimeError("Model loaded but invalid")

                except Exception as e:
                    error_msg = str(e)[:100]  # 截断长错误
                    print(f"❌ 失败: {model_name} | 原因: {error_msg}")
                    fail_count += 1
                    failed_models.append(model_name)

                print("-" * 60)

    # 输出统计结果
    print("\n📊 下载完成！统计结果:")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"🎯 总计: {success_count + fail_count}")

    if failed_models:
        print("\n📋 失败的模型列表:")
        for name in failed_models:
            print(f"  - {name}")

    # 显示缓存目录
    cache_dir = Path.home() / ".cache" / "ultralytics"
    print(f"\n📂 权重保存位置: {cache_dir}")


if __name__ == "__main__":
    main()