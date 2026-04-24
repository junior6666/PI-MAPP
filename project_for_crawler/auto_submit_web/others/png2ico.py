#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简 PNG → ICO 转换器
用法：
    python ImgToIco.py input.png       # 生成 input.ico
    python ImgToIco.py input.png -o out.ico
拖拽：直接把 png 拖到脚本图标上
"""
import argparse
import os
import struct
import sys

try:
    from PIL import Image
except ImportError:
    print("缺少依赖，先安装：pip install Pillow")
    sys.exit(1)

# ICO 支持的分辨率（从大到小）
SIZES = [256, 128, 64, 48, 32, 16]

def png_to_ico(png_path, ico_path=None):
    if ico_path is None:
        base, _ = os.path.splitext(png_path)
        ico_path = base + ".ico"

    # 打开原图
    src: Image.Image = Image.open(png_path).convert("RGBA")

    # 生成多尺寸
    images = []
    for size in SIZES:
        im = src.resize((size, size), Image.LANCZOS)
        images.append(im)

    # 保存为 ICO
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:],
        transparency=0,
    )
    print(f"已生成：{ico_path}")
    return ico_path

def main():
    # 支持拖拽：当 argc==1 且是文件时
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        png = sys.argv[1]
        png_to_ico(png)
        return

    parser = argparse.ArgumentParser(description="PNG → ICO 转换器")
    parser.add_argument("png", help="输入 PNG 文件")
    parser.add_argument("-o", "--output", help="输出 ICO 文件名（可选）")
    args = parser.parse_args()

    if not os.path.isfile(args.png):
        print("文件不存在")
        sys.exit(2)

    png_to_ico(args.png, args.output)

if __name__ == "__main__":
    main()