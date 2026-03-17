@echo off
chcp 65001 >nul
echo 正在启动图片布局管理器...
cd /d "%~dp0"
python main_ui_pic_layouter.py
pause
