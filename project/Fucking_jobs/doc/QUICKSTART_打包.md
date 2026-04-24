# AceInterview 快速打包指南

## 🚀 最简单的方式（推荐新手）

### 方法一：使用自动打包脚本（一键完成）

1. **双击运行** `build.bat`
2. 等待几分钟，打包完成后在 `dist/` 目录找到 `AceInterview.exe`

就这么简单！✅

---

## 📋 手动打包步骤

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 步骤 2: 执行打包命令

在项目目录下运行：

```bash
pyinstaller --name="windows_ace_process1.0.8" ^
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
  --hidden-import=asyncio ^
  --hidden-import=base64 ^
  --hidden-import=socket ^
  --hidden-import=psutil ^
  --hidden-import=wmi ^
  --hidden-import=GPUtil ^
  --collect-all mss ^
  --collect-all pynput ^
  --exclude-module=tkinter ^
  --exclude-module=matplotlib ^
  --noconfirm ^
  main_app.py
```

**关键参数说明：**
- `--hidden-import`: 添加隐式导入的模块（如 asyncio, base64, socket 等）
- `--collect-all`: 收集完整包资源（mss/pynput 需要二进制文件）
- `--exclude-module`: 排除不需要的模块，减小体积（tkinter/matplotlib/scipy 未使用）
- `--noconfirm`: 自动覆盖旧文件，无需确认

**⚠️ 重要提示：**
- `main_app.py` 已使用相对导入（`from utls.xxx import`），无需 `--collect-all easyocr`
- EasyOCR 模型会在首次运行时自动下载到用户目录

### 步骤 3: 获取可执行文件

打包完成后，在 `dist/` 目录下找到 `AceInterview.exe`

---

## 🎯 三种打包方式对比

| 方式 | 适用人群 | 优点 | 缺点 |
|------|---------|------|------|
| **build.bat** | 新手/快速打包 | 一键完成，自动检查 | 自定义性低 |
| **命令行** | 中级用户 | 灵活控制参数 | 需要记住命令 |
| **.spec 文件** | 高级用户 | 完全自定义，可版本控制 | 配置复杂 |

---

## ⚙️ 常用打包选项

### 减小体积
```bash
--exclude-module=tkinter --exclude-module=matplotlib
```

### 加快启动速度
```bash
--upx-exclude=vcruntime140.dll
```

### 调试模式（显示控制台）
```bash
--console
```

### 多文件模式（更快启动）
```bash
--onedir  # 替换 --onefile
```

---

## ❓ 常见问题

### Q1: 打包后文件太大（>300MB）？
**A**: 当前版本已优化至约 250MB。如需进一步减小：
- 使用 `--exclude-module` 排除未使用的模块（如 tkinter、matplotlib、scipy）
- 使用 `--onedir` 模式代替 `--onefile`（启动更快，但文件更多）
- EasyOCR 模型不打包，首次运行时自动下载（减少 200MB）

### Q2: 运行时提示缺少模块？
**A**: 添加 `--hidden-import=模块名` 重新打包。常见需要添加的模块：
- `base64`, `socket`, `asyncio` - 标准库隐式导入
- `psutil`, `wmi`, `GPUtil` - 硬件信息获取
- `openai` - Kimi API 调用

### Q3: 图标不显示？
**A**: 确保同时使用了 `--icon=icon.ico` 和 `--add-data "icon.ico;."`

### Q4: EasyOCR 首次运行很慢？
**A**: 正常现象，首次使用需要下载模型文件（约 200MB）到用户目录。
- 下载位置：`C:\Users\用户名\.EasyOCR\model`
- 下载后后续运行无需再次下载
- 如需离线使用，可预先在其他机器上下载后复制该文件夹

### Q5: 如何分发给用户？
**A**: 只需发送 `dist/AceInterview.exe` 单个文件即可，用户无需安装 Python。

### Q6: 如何实现开机自启和自动重启？
**A**: 
- **推荐方案**：使用 Windows 系统服务（内置功能）
  1. 运行程序后打开「帮助」→「⚙️ 设置」
  2. 点击「📥 安装服务」按钮
  3. 程序会自动注册为Windows计划任务
  4. 实现登录自启 + 崩溃守护
- **备选方案**：使用传统脚本守护
  - 打包时已包含 `process_guardian.py`
  - 用户可手动运行守护脚本

---

## 📦 分发给用户

### 最小化分发
只需发送以下文件：
```
AceInterview.exe    # 主程序
```

### 完整分发（推荐）
```
AceInterview/
├── AceInterview.exe      # 主程序
├── process_guardian.py    # 守护脚本（备选方案）
├── README.md              # 使用说明
└── screenshots/           # 截图目录（可选，程序会自动创建）
```

---

## 🔧 开发者注意事项

### 打包前检查
- [ ] 代码能正常运行 (`python main_app.py`)
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] icon.ico 文件存在且格式正确
- [ ] 清理旧的 build/dist 目录
- [ ] utls 文件夹中的模块可正常导入（workers.py, use_LLM.py, use_LLM_kimi.py 等）

### 打包后测试
- [ ] exe 能正常启动
- [ ] 窗口图标显示正常
- [ ] 托盘图标显示正常
- [ ] 快捷键 (Alt+X, Alt+Z) 正常工作
- [ ] OCR 识别功能正常
- [ ] WebSocket 连接正常
- [ ] 退出时程序完全关闭（无残留进程）
- [ ] Windows服务管理功能正常（帮助 → ⚙️ 设置）
- [ ] 开机自启功能可用

---

## 📞 需要帮助？

查看完整文档：`README_打包指南.md`

或运行详细日志模式：
```bash
pyinstaller --log-level=DEBUG main_app.py
```

---

**提示**: 首次打包可能需要 5-10 分钟，请耐心等待 ⏳

---

## 🎯 打包优化说明（v1.0.3）

### 本次优化内容

#### 1. **移除不必要的 --add-data 参数**
- ❌ 删除：`--add-data "process_guardian.py;."`
- ❌ 删除：`--add-data "windows_service_manager.py;."`
- ❌ 删除：`--add-data "autostart_manager.py;."`
- ✅ 原因：这些模块通过 `from project.Fucking_jobs.utls.xxx import` 导入，PyInstaller 会自动处理

#### 2. **新增隐式导入模块**
根据代码分析，添加了以下必需但未被自动检测的模块：
- `base64` - Kimi API 图片编码（use_LLM_kimi.py）
- `socket` - WebSocket 服务器（workers.py）
- `psutil` - CPU/内存监控（main_app.py）
- `wmi` - Windows 硬件信息（main_app.py）
- `GPUtil` - GPU 信息获取（main_app.py）

#### 3. **排除未使用的大型模块**
- `tkinter` - 未使用（项目使用 PySide6）
- `matplotlib` - 未使用（无图表绘制）
- `scipy` - 未使用（无科学计算）
- 💡 效果：可减少约 50-100MB 体积

#### 4. **保留必要的 --collect-all**
- `mss` - 需要二进制截图库
- `pynput` - 需要键盘监听驱动
- ❌ 移除 `easyocr` - 改为首次运行时自动下载模型

### 依赖关系图

```
main_app.py
├── utls/workers.py
│   ├── mss (截图)
│   ├── PIL/Pillow (图像处理)
│   ├── pynput (热键监听)
│   ├── easyocr (OCR识别)
│   ├── requests (HTTP请求)
│   ├── websockets (WebSocket服务)
│   ├── openai (Kimi API)
│   └── asyncio, base64, socket (标准库)
├── utls/autostart_manager.py (开机自启)
├── utls/windows_service_manager.py (Windows服务)
├── psutil (系统监控)
├── wmi (硬件信息)
└── GPUtil (GPU信息)
```

### 体积优化对比

| 项目 | 优化前 | 优化后 | 说明 |
|------|--------|--------|------|
| 基础体积 | ~250MB | ~250MB | Python解释器+PySide6 |
| EasyOCR | ~200MB | ~0MB | 改为首次运行时下载 |
| 冗余模块 | ~80MB | ~0MB | 排除 tkinter/matplotlib/scipy |
| **总计** | **~530MB** | **~250MB** | **减少约 53%** |

### 进一步减小体积的方法

当前已实现延迟加载 EasyOCR（减少 200MB），如需进一步优化：

1. **使用 --onedir 模式**
   ```bash
   pyinstaller --onedir ... # 替换 --onefile
   ```
   - 优点：启动更快，总体积更小（共享DLL）
   - 缺点：生成文件夹而非单个exe

2. **使用 UPX 压缩**
   ```bash
   pyinstaller --upx-dir=/path/to/upx ...
   ```
   - 可再减小 20-30% 体积
   - 可能略微增加启动时间
   - ⚠️ 注意：Qt 应用使用 UPX 可能导致崩溃，需测试
