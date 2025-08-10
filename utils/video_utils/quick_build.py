#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速打包脚本 - 一键生成EXE文件
"""

import os
import sys
import subprocess


def main():
    """主函数"""
    print("🚀 视频转GIF工具 - 快速打包")
    print("=" * 40)
    
    # 检查文件
    if not os.path.exists('video_to_gif_app.py'):
        print("❌ 找不到主程序文件")
        input("按回车退出...")
        return
    
    # 安装PyInstaller
    print("📦 正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller安装成功")
    except:
        print("❌ PyInstaller安装失败")
        input("按回车退出...")
        return
    
    # 执行打包
    print("🔨 正在打包EXE文件...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=视频转GIF工具",
        "--clean",
        "video_to_gif_app.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 打包成功！")
        print(f"📁 EXE文件位置: dist/视频转GIF工具2.0.exe")
    except subprocess.CalledProcessError:
        print("❌ 打包失败")
    
    input("按回车退出...")


if __name__ == "__main__":
    main() 