#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转GIF工具 - EXE打包脚本
使用PyInstaller将GUI程序打包成Windows可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyInstaller安装失败")
        return False


def create_spec_file():
    """创建PyInstaller配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['video_to_gif_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'moviepy',
        'moviepy.editor',
        'moviepy.video',
        'moviepy.audio',
        'imageio',
        'imageio_ffmpeg',
        'PIL',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'numpy',
        'proglog',
        'tqdm',
        'decorator',
        'imageio_ffmpeg.binding',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('video_to_gif_app.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ 配置文件创建成功")


def build_exe():
    """构建EXE文件"""
    print("开始构建EXE文件...")
    
    # 检查必要文件
    if not os.path.exists('video_to_gif_app.py'):
        print("❌ 找不到主程序文件 video_to_gif_app.py")
        return False
    
    if not os.path.exists('convert_mp4_to_gif.py'):
        print("❌ 找不到转换函数文件 convert_mp4_to_gif.py")
        return False
    
    # 创建spec文件
    create_spec_file()
    
    # 执行打包命令
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "video_to_gif_app.spec"
        ]
        
        print("执行打包命令:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ EXE文件构建成功！")
            print(f"输出目录: {os.path.abspath('dist')}")
            return True
        else:
            print("❌ 构建失败")
            print("错误输出:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return False


def create_installer_script():
    """创建安装脚本"""
    installer_content = '''@echo off
chcp 65001 >nul
echo ========================================
echo    视频转GIF工具 - 安装脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python环境
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检测成功
echo.

echo 正在安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo ✅ 依赖安装成功
echo.

echo 正在构建EXE文件...
python build_exe.py
if errorlevel 1 (
    echo ❌ EXE构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo    构建完成！
echo ========================================
echo.
echo EXE文件位置: dist\\视频转GIF工具.exe
echo.
echo 您可以直接运行该EXE文件，无需Python环境
echo.
pause
'''
    
    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    print("✅ 安装脚本创建成功")


def create_readme():
    """创建打包说明文档"""
    readme_content = '''# 视频转GIF工具 - EXE打包说明

## 📦 打包方法

### 方法一：自动打包（推荐）

1. **运行安装脚本**
   ```bash
   install.bat
   ```

2. **等待完成**
   - 自动安装依赖
   - 自动构建EXE文件
   - 完成后在 `dist` 目录找到可执行文件

### 方法二：手动打包

1. **安装PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **运行打包脚本**
   ```bash
   python build_exe.py
   ```

3. **或直接使用PyInstaller**
   ```bash
   pyinstaller --onefile --windowed --name "视频转GIF工具" video_to_gif_app.py
   ```

## 📁 输出文件

打包完成后，在 `dist` 目录下会生成：
- `视频转GIF工具.exe` - 主程序（可直接运行）

## ⚠️ 注意事项

1. **文件大小**: EXE文件可能较大（100-200MB），这是正常的
2. **首次运行**: 首次运行可能需要较长时间启动
3. **杀毒软件**: 某些杀毒软件可能误报，请添加信任
4. **依赖包含**: EXE文件已包含所有必要依赖，无需Python环境

## 🔧 故障排除

### 常见问题

1. **打包失败**
   - 确保所有依赖已正确安装
   - 检查Python版本（建议3.7+）
   - 尝试清理缓存：`pyinstaller --clean`

2. **EXE无法运行**
   - 检查是否被杀毒软件拦截
   - 尝试以管理员身份运行
   - 检查系统兼容性

3. **缺少依赖**
   - 重新安装依赖：`pip install -r requirements.txt`
   - 更新PyInstaller：`pip install --upgrade pyinstaller`

## 📋 系统要求

- **操作系统**: Windows 7/8/10/11 (64位)
- **内存**: 至少2GB RAM
- **磁盘空间**: 至少500MB可用空间
- **网络**: 首次运行可能需要下载FFmpeg

## 🎉 使用说明

1. 双击运行 `视频转GIF工具.exe`
2. 按照界面提示操作
3. 享受使用！

---

**如有问题，请查看详细使用说明文档**
'''
    
    with open('打包说明.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ 打包说明文档创建成功")


def main():
    """主函数"""
    print("=" * 50)
    print("    视频转GIF工具 - EXE打包工具")
    print("=" * 50)
    print()
    
    # 检查当前目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    print()
    
    # 检查必要文件
    required_files = ['video_to_gif_app.py', 'convert_mp4_to_gif.py', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n请确保在正确的目录下运行此脚本")
        input("按回车键退出...")
        return
    
    print("✅ 所有必要文件检查通过")
    print()
    
    # 安装PyInstaller
    if not install_pyinstaller():
        input("按回车键退出...")
        return
    
    print()
    
    # 创建辅助文件
    create_installer_script()
    create_readme()
    
    print()
    
    # 构建EXE
    if build_exe():
        print()
        print("🎉 打包完成！")
        print()
        print("输出文件:")
        exe_path = os.path.join("dist", "视频转GIF工具.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"   📁 {exe_path}")
            print(f"   📊 文件大小: {size_mb:.1f} MB")
        print()
        print("您可以直接运行该EXE文件，无需Python环境！")
    else:
        print("❌ 打包失败，请检查错误信息")
    
    print()
    input("按回车键退出...")


if __name__ == "__main__":
    main() 