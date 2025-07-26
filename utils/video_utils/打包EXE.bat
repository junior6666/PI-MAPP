@echo off
chcp 65001 >nul
title 视频转GIF工具 - EXE打包

echo.
echo ========================================
echo    视频转GIF工具 - EXE打包工具
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python环境
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python环境检测成功
echo.

echo 正在安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    echo 请检查网络连接或手动安装依赖
    pause
    exit /b 1
)

echo ✅ 依赖安装成功
echo.

echo 正在安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ❌ PyInstaller安装失败
    pause
    exit /b 1
)

echo ✅ PyInstaller安装成功
echo.

echo 开始构建EXE文件...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --onefile --windowed --name "视频转GIF工具" --clean video_to_gif_app.py

if errorlevel 1 (
    echo.
    echo ❌ EXE构建失败
    echo 请检查错误信息并重试
    pause
    exit /b 1
)

echo.
echo ========================================
echo    构建完成！
echo ========================================
echo.
echo ✅ EXE文件构建成功
echo.
echo 📁 文件位置: dist\视频转GIF工具.exe
echo.
echo 🎉 您可以直接运行该EXE文件，无需Python环境！
echo.
echo 按任意键打开输出目录...
pause >nul

if exist "dist" (
    explorer dist
) else (
    echo 输出目录不存在
)

echo.
echo 感谢使用视频转GIF工具！
pause 