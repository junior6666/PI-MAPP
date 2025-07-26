#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转GIF工具启动脚本
"""

import sys
import os

def main():
    """主函数"""
    try:
        # 添加当前目录到Python路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # 导入并启动应用
        from video_to_gif_app import main as app_main
        print("正在启动视频转GIF工具...")
        app_main()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖: pip install moviepy pillow numpy imageio imageio-ffmpeg")
        input("按回车键退出...")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main() 