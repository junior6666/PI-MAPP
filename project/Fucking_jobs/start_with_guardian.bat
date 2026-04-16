@echo off
chcp 65001 >nul
echo ========================================
echo   AceInterview 启动器
echo ========================================
echo.

REM 检查参数
if "%1"=="--guardian" goto :guardian_mode
if "%1"=="--no-guardian" goto :normal_mode

REM 默认使用守护模式
echo [INFO] 默认启用守护模式（自动重启）
goto :guardian_mode

:guardian_mode
echo [INFO] 启动守护进程...
python process_guardian.py --script main_app.py --max-restarts 10 --restart-delay 3
goto :end

:normal_mode
echo [INFO] 以普通模式启动...
python main_app.py
goto :end

:end
echo.
pause
