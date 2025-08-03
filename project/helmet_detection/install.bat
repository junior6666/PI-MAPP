@echo off
echo 正在安装头盔检测系统依赖...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo Python版本检查通过
echo.

REM 升级pip
echo 正在升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 安装完成！
echo 现在可以运行 python main.py 启动程序
pause 