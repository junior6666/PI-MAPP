@echo off
chcp 65001 >nul
echo ========================================
echo   AceInterview 自动打包脚本
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [提示] 当前 Python 版本:
python --version
echo.

REM 清理旧文件
echo [1/6] 清理旧的打包文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "AceInterview.spec" del AceInterview.spec
echo ✓ 清理完成
echo.

REM 安装依赖
echo [2/6] 检查并安装依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
pip install pyinstaller>=5.13.0 -q
echo ✓ 依赖安装完成
echo.

REM 检查必需文件
echo [3/6] 检查必需文件...
if not exist "main_app.py" (
    echo [错误] 找不到 main_app.py
    pause
    exit /b 1
)
if not exist "workers.py" (
    echo [错误] 找不到 workers.py
    pause
    exit /b 1
)
if not exist "icon.ico" (
    echo [错误] 找不到 icon.ico
    pause
    exit /b 1
)
echo ✓ 所有必需文件存在
echo.

REM 打包
echo [4/6] 开始打包（这可能需要几分钟）...
pyinstaller --name="windows_ace_process" ^
    --windowed ^
    --onefile ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=PySide6 ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=mss ^
    --hidden-import=PIL ^
    --hidden-import=pynput ^
    --hidden-import=easyocr ^
    --hidden-import=requests ^
    --hidden-import=websockets ^
    --hidden-import=openai ^
    --hidden-import=psutil ^
    --hidden-import=wmi ^
    --hidden-import=GPUtil ^
    --hidden-import=asyncio ^
    --collect-all easyocr ^
    --collect-all mss ^
    --collect-all pynput ^
    --exclude-module=tkinter ^
    --exclude-module=matplotlib ^
    --exclude-module=scipy ^
    --noupx ^
    --noconfirm ^
    main_app.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！请查看上方错误信息
    echo.
    echo 建议：
    echo 1. 检查网络连接（需要下载依赖）
    echo 2. 确保有足够的磁盘空间（至少 2GB）
    echo 3. 查看详细日志：pyinstaller --log-level=DEBUG main_app.py
    pause
    exit /b 1
)
echo ✓ 打包完成
echo.

REM 检查输出
echo [5/6] 检查输出文件...
if exist "dist\AceInterview.exe" (
    echo ✓ 打包成功！
    for %%A in ("dist\AceInterview.exe") do set size=%%~zA
    set /a sizeMB=%size% / 1048576
    echo   文件大小: %sizeMB% MB
    echo   文件位置: %cd%\dist\AceInterview.exe
) else (
    echo [错误] 未找到输出文件
    pause
    exit /b 1
)
echo.

REM 创建必要目录
echo [6/6] 创建运行时目录...
if not exist "dist\screenshots" mkdir dist\screenshots
if not exist "dist\detection_history" mkdir dist\detection_history
echo ✓ 目录创建完成
echo.

echo ========================================
echo   🎉 打包完成！
echo ========================================
echo.
echo 📦 可执行文件: dist\AceInterview.exe
echo 📁 截图目录: dist\screenshots\
echo.
echo 📝 下一步：
echo   1. 测试运行: dist\AceInterview.exe
echo   2. 分发文件: 将 dist\AceInterview.exe 发送给用户
echo   3. 用户首次运行会自动创建所需目录
echo.
echo ⚠️  注意事项：
echo   - 首次运行可能需要较长时间（加载 OCR 模型）
echo   - 确保防火墙允许程序运行
echo   - 使用 WebSocket 功能需关闭防火墙或添加例外
echo.
pause
