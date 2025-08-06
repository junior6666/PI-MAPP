#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Object Detection System v2.0 - 启动脚本
快速启动目标检测系统
"""

import sys
import os
from pathlib import Path

# 添加项目路径到系统路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        'ultralytics',
        'PySide6',
        'cv2',
        'numpy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PySide6':
                from PySide6.QtWidgets import QApplication
            elif package == 'ultralytics':
                from ultralytics import YOLO
            elif package == 'numpy':
                import numpy
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 请运行以下命令安装:")
        print("pip install ultralytics PySide6 opencv-python numpy")
        return False

    return True


def create_directories():
    """创建必要的目录"""
    directories = [
        "pt_models",
        "models",
        "weights",
        "results",
        "logs"
    ]

    for directory in directories:
        dir_path = current_dir / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建目录: {directory}")


def main():
    """主函数"""
    print("🚀 Enhanced Object Detection System v2.0")
    print("=" * 50)

    # 检查依赖
    print("🔍 检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ 依赖检查通过")

    # 创建目录
    print("📁 创建必要目录...")
    create_directories()

    # 启动主程序
    print("🎯 启动目标检测系统...")
    try:
        # 尝试导入并启动主程序
        from enhanced_ui_main import main as ui_main
        ui_main()
    except ImportError:
        try:
            # 备用启动方案
            from enhanced_detection_main import main as detection_main
            detection_main()
        except ImportError:
            print("❌ 无法找到主程序文件，请检查项目完整性")
            sys.exit(1)


if __name__ == "__main__":
    main()