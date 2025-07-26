#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版打包脚本 - 减小EXE文件大小
"""

import os
import sys
import subprocess


def create_optimized_spec():
    """创建优化的spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['video_to_gif_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'moviepy.editor',
        'imageio_ffmpeg.binding',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas', 'seaborn', 'plotly',
        'jupyter', 'notebook', 'ipython', 'IPython',
        'pytest', 'nose', 'unittest', 'doctest',
        'setuptools', 'distutils', 'pkg_resources',
        'tkinter.test', 'tkinter.tix', 'tkinter.ttk',
        'asyncio', 'concurrent.futures', 'multiprocessing',
        'xml', 'xmlrpc', 'email', 'http', 'urllib',
        'sqlite3', 'dbm', 'pickle', 'shelve',
        'bz2', 'lzma', 'zlib', 'gzip',
        'ctypes', 'curses', 'readline', 'rlcompleter',
        'pydoc', 'doctest', 'unittest', 'test',
        'lib2to3', 'pydoc_data',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='视频转GIF工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    optimize=2,
)
'''
    
    with open('video_to_gif_app_optimized.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ 优化配置文件创建成功")


def main():
    """主函数"""
    print("🚀 视频转GIF工具 - 优化打包")
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
    
    # 创建优化配置
    create_optimized_spec()
    
    # 执行优化打包
    print("🔨 正在优化打包EXE文件...")
    print("💡 使用优化配置减小文件大小...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "video_to_gif_app_optimized.spec"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 优化打包成功！")
        
        # 显示文件大小
        exe_path = os.path.join("dist", "视频转GIF工具.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📊 文件大小: {size_mb:.1f} MB")
            
            if size_mb > 200:
                print("💡 文件仍然较大，建议使用以下方法进一步优化：")
                print("   1. 使用虚拟环境只安装必要依赖")
                print("   2. 手动排除更多不需要的模块")
                print("   3. 使用--onedir模式生成文件夹")
            else:
                print("🎉 文件大小已优化！")
        
        print(f"📁 EXE文件位置: {exe_path}")
        
    except subprocess.CalledProcessError:
        print("❌ 打包失败")
    
    input("按回车退出...")


if __name__ == "__main__":
    main() 