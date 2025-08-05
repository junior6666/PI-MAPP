@echo off
echo ========================================
echo 息肉智能检测系统 - 安装脚本
echo ========================================
echo.

REM 检查Python版本
echo 检查Python版本...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 安装Python依赖包...
echo.

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装所有依赖
echo 安装PySide6...
pip install PySide6

echo 安装ultralytics...
pip install ultralytics

echo 安装opencv-python...
pip install opencv-python

echo 安装numpy...
pip install numpy

echo 安装mysql-connector-python...
pip install mysql-connector-python

echo 安装Pillow...
pip install Pillow

echo 安装reportlab...
pip install reportlab

echo 安装matplotlib...
pip install matplotlib

echo 安装seaborn...
pip install seaborn

echo.
echo 检查模型文件...
if not exist "pt_models\polpy_best.pt" (
    echo 警告: 未找到模型文件 pt_models\polpy_best.pt
    echo 请确保模型文件存在
)

echo.
echo 初始化数据库...
python database_setup.py

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行 run.bat 启动应用程序
echo.
pause 