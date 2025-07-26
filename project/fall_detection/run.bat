@echo off
echo 启动摔倒检测系统...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import ultralytics, torch, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo 错误: 依赖包未安装，请先运行 install.bat
    pause
    exit /b 1
)

echo 依赖检查通过，启动GUI...
python main.py

pause 