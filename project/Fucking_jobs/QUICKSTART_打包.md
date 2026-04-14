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
pyinstaller --name="windows_ace_process1.0.2" --windowed --onefile --icon=icon.ico --add-data "icon.ico;." --hidden-import=PySide6 --hidden-import=mss --hidden-import=PIL --hidden-import=pynput --hidden-import=easyocr --hidden-import=requests --hidden-import=websockets --hidden-import=openai --hidden-import=asyncio --collect-all easyocr --collect-all mss --collect-all pynput --noconfirm main_app.py
```

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
**A**: 这是正常的，因为包含了 Python 解释器和所有依赖。可以使用 `--onedir` 模式或排除不必要的模块。

### Q2: 运行时提示缺少模块？
**A**: 添加 `--hidden-import=模块名` 重新打包。

### Q3: 图标不显示？
**A**: 确保同时使用了 `--icon=icon.ico` 和 `--add-data "icon.ico;."`

### Q4: EasyOCR 首次运行很慢？
**A**: 正常现象，首次需要下载模型文件。可以预先下载或使用 `--collect-all easyocr`。

### Q5: 如何分发给用户？
**A**: 只需发送 `dist/AceInterview.exe` 单个文件即可，用户无需安装 Python。

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

### 打包后测试
- [ ] exe 能正常启动
- [ ] 窗口图标显示正常
- [ ] 托盘图标显示正常
- [ ] 快捷键 (Alt+X, Alt+Z) 正常工作
- [ ] OCR 识别功能正常
- [ ] WebSocket 连接正常
- [ ] 退出时程序完全关闭（无残留进程）

---

## 📞 需要帮助？

查看完整文档：`README_打包指南.md`

或运行详细日志模式：
```bash
pyinstaller --log-level=DEBUG main_app.py
```

---

**提示**: 首次打包可能需要 5-10 分钟，请耐心等待 ⏳
