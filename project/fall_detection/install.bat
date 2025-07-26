@echo off
echo 正在安装摔倒检测系统依赖包...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo Python版本检查通过

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装依赖包
echo 安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo 安装失败，请检查网络连接或手动安装
    pause
    exit /b 1
)

echo 安装完成！
echo.
echo 使用方法:
echo 1. 启动GUI: python main.py
echo 2. 命令行检测: python main.py --mode detect --video video.mp4
echo 3. 训练模型: python main.py --mode train --data dataset_path
echo.
pause 