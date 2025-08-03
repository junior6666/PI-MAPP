@echo off
echo 启动头盔检测系统...
echo.

REM 检查模型文件是否存在
if not exist "pt_models\helmet_best.pt" (
    echo 错误: 模型文件不存在，请确保 pt_models\helmet_best.pt 文件存在
    pause
    exit /b 1
)

REM 运行程序
python main.py

if errorlevel 1 (
    echo 程序运行出错
    pause
) 