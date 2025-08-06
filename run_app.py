#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步态分析应用启动脚本
处理各种依赖和错误情况
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """检查依赖包"""
    missing_deps = []
    
    try:
        import PySide6
        print("✓ PySide6 已安装")
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import cv2
        print("✓ OpenCV 已安装")
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
        print("✓ NumPy 已安装")
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import scipy
        print("✓ SciPy 已安装")
    except ImportError:
        missing_deps.append("scipy")
    
    try:
        import pyqtgraph
        print("✓ PyQtGraph 已安装")
    except ImportError:
        print("⚠ PyQtGraph 未安装，图表功能将被禁用")
    
    try:
        import ultralytics
        print("✓ Ultralytics 已安装")
    except ImportError:
        print("⚠ Ultralytics 未安装，YOLO功能将被禁用")
    
    if missing_deps:
        print(f"\n缺少必要依赖: {', '.join(missing_deps)}")
        print("请运行: pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """主函数"""
    print("步态分析可视化GUI应用启动器")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        print("\n依赖检查失败，无法启动应用")
        input("按任意键退出...")
        return
    
    print("\n所有依赖检查完成")
    print("正在启动应用...")
    
    try:
        # 尝试启动完整应用
        from main import main as app_main
        app_main()
    except Exception as e:
        print(f"\n启动完整应用失败: {e}")
        print("尝试启动简化版本...")
        
        try:
            # 启动简化版本
            from test_app import main as test_main
            test_main()
        except Exception as e2:
            print(f"启动简化版本也失败: {e2}")
            print("\n请检查错误信息并修复问题")
            input("按任意键退出...")

if __name__ == "__main__":
    main()