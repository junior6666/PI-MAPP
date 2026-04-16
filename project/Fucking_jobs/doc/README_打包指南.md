# AceInterview - 面试辅助工具打包指南

## 📦 PyInstaller 打包完整指南

### 一、环境准备

#### 1.1 开发环境要求
- **Python 版本**: Python 3.9 - 3.11 (推荐 3.10)
- **操作系统**: Windows 10/11 (64位)
- **PyInstaller 版本**: >= 5.0

#### 1.2 安装依赖

```bash
# 激活虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装所有依赖
pip install -r requirements.txt

# 安装 PyInstaller
pip install pyinstaller>=5.13.0
```

### 二、打包前检查清单

#### 2.1 必需文件确认
确保以下文件存在于项目根目录：
```
Fucking_jobs/
├── main_app.py              # 主程序入口
├── workers.py               # 工作线程模块
├── icon.ico                 # 应用图标（必需）
├── requirements.txt         # 依赖列表
└── README_打包指南.md       # 本文档
```

#### 2.2 依赖包完整性检查
```bash
# 验证关键依赖是否安装
python -c "import PySide6; print('PySide6:', PySide6.__version__)"
python -c "import mss; print('mss: OK')"
python -c "import easyocr; print('easyocr: OK')"
python -c "import pynput; print('pynput: OK')"
python -c "import websockets; print('websockets: OK')"
python -c "import openai; print('openai: OK')"
python -c "import psutil; print('psutil: OK')"
```

### 三、打包命令（完整版）

#### 3.1 一键打包命令（推荐）

在项目根目录 `Fucking_jobs/` 下执行：

```bash
pyinstaller --name="windows process" ^
    --windowed ^
    --onefile ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=PySide6 ^
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
    --noconfirm ^
    main_app.py
```

**PowerShell 版本**（如果使用 PowerShell）：
```powershell
pyinstaller --name="windows process" `
    --windowed `
    --onefile `
    --icon=icon.ico `
    --add-data "icon.ico;." `
    --hidden-import=PySide6 `
    --hidden-import=mss `
    --hidden-import=PIL `
    --hidden-import=pynput `
    --hidden-import=easyocr `
    --hidden-import=requests `
    --hidden-import=websockets `
    --hidden-import=openai `
    --hidden-import=psutil `
    --hidden-import=wmi `
    --hidden-import=GPUtil `
    --hidden-import=asyncio `
    --collect-all easyocr `
    --collect-all mss `
    --collect-all pynput `
    --noconfirm `
    main_app.py
```

#### 3.2 参数说明

| 参数 | 说明 |
|------|------|
| `--name="AceInterview"` | 生成的可执行文件名称 |
| `--windowed` | 无控制台窗口（GUI 应用必需） |
| `--onefile` | 打包为单个 exe 文件 |
| `--icon=icon.ico` | 设置 exe 图标 |
| `--add-data "icon.ico;."` | 将图标文件打包到运行时目录 |
| `--hidden-import=xxx` | 显式包含动态导入的模块 |
| `--collect-all xxx` | 收集模块的所有资源文件 |
| `--noconfirm` | 覆盖已有输出目录，不询问 |

### 四、使用 .spec 文件打包（高级）

#### 4.1 创建 spec 文件

创建 `AceInterview.spec` 文件：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),  # 添加图标文件
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'mss',
        'mss.windows',
        'PIL',
        'PIL.Image',
        'pynput',
        'pynput.keyboard',
        'easyocr',
        'requests',
        'websockets',
        'openai',
        'psutil',
        'wmi',
        'GPUtil',
        'asyncio',
        'socket',
        'threading',
        'datetime',
        'base64',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy.testing',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AceInterview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩（减小体积）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 设置图标
)
```

#### 4.2 使用 spec 文件打包

```bash
pyinstaller AceInterview.spec
```

### 五、打包后处理

#### 5.1 输出文件位置

打包完成后，在 `dist/` 目录下会生成：
```
dist/
└── AceInterview.exe    # 最终的可执行文件（约 200-300 MB）
```

#### 5.2 首次运行准备

```bash
# 创建必要的目录
mkdir screenshots
mkdir detection_history
```

#### 5.3 测试运行

```bash
# 直接双击运行或在命令行执行
.\dist\AceInterview.exe
```

### 六、常见问题与解决方案

#### 6.1 打包体积过大

**问题**: 生成的 exe 文件超过 300MB

**解决方案**:
```bash
# 方法1: 排除不必要的模块
--exclude-module=tkinter ^
--exclude-module=matplotlib ^
--exclude-module=scipy

# 方法2: 使用 UPX 压缩（已默认启用）
--upx-dir=C:\path\to\upx

# 方法3: 使用 --onedir 模式（更快启动，但多个文件）
pyinstaller --onedir --name="AceInterview" ...
```

#### 6.2 缺少 DLL 或模块错误

**问题**: 运行时提示 "ModuleNotFoundError" 或 "DLL load failed"

**解决方案**:
```bash
# 添加缺失的隐藏导入
--hidden-import=missing_module_name

# 收集整个包
--collect-all package_name

# 查看打包日志，找出缺失的模块
pyinstaller --log-level=DEBUG main_app.py
```

#### 6.3 EasyOCR 模型文件问题

**问题**: EasyOCR 首次运行需要下载模型文件

**解决方案**:
```bash
# 方法1: 预先下载模型到项目目录
# 在打包前运行一次 OCR，让模型下载到 ~/.EasyOCR/

# 方法2: 手动复制模型文件到打包目录
--add-data "C:/Users/用户名/.EasyOCR/model;EasyOCR/model"

# 方法3: 在程序中指定模型路径
reader = easyocr.Reader(['ch_sim', 'en'], model_storage_directory='./models')
```

#### 6.4 图标不显示

**问题**: exe 文件或窗口没有显示图标

**解决方案**:
```bash
# 确保同时使用两个参数
--icon=icon.ico ^
--add-data "icon.ico;."

# 检查 icon.ico 格式是否正确（必须是真正的 .ico 文件）
python -c "from PIL import Image; img = Image.open('icon.ico'); print(img.format)"
```

#### 6.5 WebSocket 连接失败

**问题**: 手机无法连接到 PC 的 WebSocket 服务

**解决方案**:
1. 检查防火墙是否阻止了端口
2. 确保手机和 PC 在同一局域网
3. 检查端口是否被占用：
   ```bash
   netstat -ano | findstr :8765
   ```

#### 6.6 热键监听失败

**问题**: Alt+X 或 Alt+Z 快捷键无响应

**解决方案**:
1. 以管理员身份运行程序
2. 检查是否有其他程序占用了相同热键
3. 尝试更换热键组合

### 七、生产环境部署

#### 7.1 最小化分发包

创建分发文件夹结构：
```
AceInterview_Release/
├── AceInterview.exe          # 主程序
├── README.md                  # 使用说明
├── LICENSE                    # 许可证
└── screenshots/               # 截图保存目录（自动创建）
```

#### 7.2 创建安装脚本（可选）

创建 `install.bat`:
```batch
@echo off
echo 正在安装 AceInterview...

REM 创建必要目录
if not exist "screenshots" mkdir screenshots
if not exist "detection_history" mkdir detection_history

echo 安装完成！
echo 请双击 AceInterview.exe 运行程序
pause
```

#### 7.3 创建快捷方式（可选）

使用 VBScript 创建桌面快捷方式 `create_shortcut.vbs`:
```vbscript
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\AceInterview.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = oWS.CurrentDirectory & "\AceInterview.exe"
oLink.WorkingDirectory = oWS.CurrentDirectory
oLink.IconLocation = oWS.CurrentDirectory & "\AceInterview.exe, 0"
oLink.Save
```

### 八、性能优化建议

#### 8.1 减小打包体积

1. **使用虚拟环境**: 只安装必需的包
2. **排除不必要模块**: 
   ```bash
   --exclude-module=test ^
   --exclude-module=unittest
   ```
3. **使用 onedir 模式**: 虽然文件多，但总体积更小，启动更快

#### 8.2 提升启动速度

1. **禁用 UPX 压缩**（ trade-off: 体积增大，启动更快）:
   ```bash
   --upx-exclude=vcruntime140.dll
   ```

2. **预加载关键模块**: 在 `main_app.py` 开头添加:
   ```python
   import sys
   if getattr(sys, 'frozen', False):
       # 打包后的优化
       import multiprocessing
       multiprocessing.freeze_support()
   ```

### 九、调试技巧

#### 9.1 查看详细打包日志

```bash
pyinstaller --log-level=DEBUG --clean main_app.py
```

#### 9.2 测试打包前的代码

```bash
# 确保源代码能正常运行
python main_app.py
```

#### 9.3 检查打包内容

```bash
# 查看 spec 文件中的分析结果
pyi-archive_viewer dist/AceInterview.exe
```

#### 9.4 运行时调试

临时启用控制台窗口以便查看错误：
```bash
# 修改 spec 文件或使用以下命令
pyinstaller --console --name="AceInterview_Debug" ...
```

### 十、自动化打包脚本

创建 `build.bat` 实现一键打包：

```batch
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

REM 清理旧文件
echo [1/5] 清理旧的打包文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "AceInterview.spec" del AceInterview.spec

REM 安装依赖
echo [2/5] 检查并安装依赖...
pip install -r requirements.txt -q
pip install pyinstaller -q

REM 打包
echo [3/5] 开始打包...
pyinstaller --name="AceInterview" ^
    --windowed ^
    --onefile ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=PySide6 ^
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
    --noconfirm ^
    main_app.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！请查看上方错误信息
    pause
    exit /b 1
)

REM 检查输出
echo [4/5] 检查输出文件...
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

REM 创建必要目录
echo [5/5] 创建运行时目录...
if not exist "dist\screenshots" mkdir dist\screenshots

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 下一步：
echo 1. 测试运行: dist\AceInterview.exe
echo 2. 分发文件: 将 dist\AceInterview.exe 发送给用户
echo.
pause
```

### 十一、版本发布检查清单

发布新版本前，请确认：

- [ ] 代码已通过功能测试
- [ ] 更新了版本号（如有）
- [ ] 更新了 CHANGELOG
- [ ] 打包体积在可接受范围内（< 350MB）
- [ ] 在干净环境中测试过（无 Python 环境的电脑）
- [ ] 图标正常显示
- [ ] 所有快捷键功能正常
- [ ] WebSocket 通信正常
- [ ] OCR 识别功能正常
- [ ] LLM/Kimi API 调用正常
- [ ] 托盘图标功能正常
- [ ] 退出时所有线程正确清理
- [ ] 编写了用户手册

### 十二、技术支持

如遇到打包问题，请提供：
1. Python 版本: `python --version`
2. PyInstaller 版本: `pyinstaller --version`
3. 完整的打包日志
4. 运行时的错误截图

---

**最后更新**: 2026-04-13  
**维护者**: AceInterview Team
