@echo off
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
echo EXE文件位置: dist\视频转GIF工具.exe
echo.
echo 您可以直接运行该EXE文件，无需Python环境
echo.
pause
