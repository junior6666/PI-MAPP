@echo off
chcp 65001 >nul
echo ========================================
echo   截图 OCR LLM 分析工具 - 启动器
echo ========================================
echo.

echo [1/2] 检查依赖...
python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo [!] 未检测到依赖，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [✗] 依赖安装失败！
        pause
        exit /b 1
    )
    echo [√] 依赖安装完成
) else (
    echo [√] 依赖已安装
)

echo.
echo [2/2] 启动应用程序...
echo.
python main_app.py

if errorlevel 1 (
    echo.
    echo [✗] 应用程序启动失败
    pause
)
