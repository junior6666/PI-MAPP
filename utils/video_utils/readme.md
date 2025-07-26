# 视频转GIF工具

这是一个功能强大的视频转GIF工具，支持多种视频格式，并提供图形用户界面。

## 功能特点

- 🎥 **多格式支持**: 支持MP4、AVI、MOV、MKV、WMV、FLV、WebM、M4V等格式
- 🎨 **颜色保持**: 优化算法保持原始视频的颜色质量
- 📏 **智能缩放**: 自动保持宽高比，支持自定义最大尺寸
- ⚡ **帧率控制**: 可自定义目标帧率，不超过原视频帧率
- 🎯 **质量选择**: 提供低、中、高三种质量选项
- 📊 **信息显示**: 自动读取并显示视频详细信息
- ⏱️ **时长控制**: 支持设置开始时间和GIF时长
- 📈 **实时进度**: 转换过程中显示详细进度信息
- 🖥️ **白净界面**: 现代化白净主题GUI界面，操作简单直观

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```python
from convert_mp4_to_gif import convert_video_to_gif, get_video_info

# 获取视频信息
info = get_video_info("video.mp4")
print(info)

# 转换视频为GIF
convert_video_to_gif(
    input_path="video.mp4",
    output_path="output.gif",
    max_dimension=480,        # 最大尺寸
    target_fps=15.0,          # 目标帧率
    preserve_colors=True,     # 保持颜色
    quality="high"            # 质量设置
)
```

### GUI界面使用

运行GUI程序：

```bash
# 普通启动
python video_to_gif_gui.py

# 带启动动画启动
python 启动GUI.py

# 测试白净主题界面
python test_white_theme.py
```

GUI界面功能：
1. **选择视频文件**: 点击"📂 浏览"按钮选择要转换的视频文件
2. **自动信息显示**: 选择文件后自动显示视频的详细信息
3. **设置参数**: 
   - 最大尺寸：设置GIF的最大宽度或高度（保持宽高比）
   - 目标帧率：设置GIF的播放帧率
   - 质量设置：选择低、中、高质量
   - 保持原始颜色：勾选以保持更好的颜色质量
4. **时长控制**:
   - 开始时间：设置从视频的哪个时间点开始转换
   - GIF时长：设置转换的GIF时长（0表示使用原视频时长）
5. **选择输出路径**: 点击"💾 保存"按钮设置GIF文件的保存位置
6. **开始转换**: 点击"🚀 开始转换"按钮开始处理
7. **实时进度**: 转换过程中显示详细的进度信息和状态

## 参数说明

### convert_video_to_gif 函数参数

- `input_path` (str): 输入视频文件路径
- `output_path` (str, 可选): 输出GIF文件路径，默认与输入同目录
- `max_dimension` (int, 可选): 最大尺寸，保持宽高比缩放
- `target_fps` (float, 可选): 目标帧率，默认使用原视频帧率
- `preserve_colors` (bool): 是否保持原始颜色，默认True
- `quality` (str): 质量设置，可选"low"、"medium"、"high"，默认"high"
- `start_time` (float): 开始时间（秒），默认0.0
- `duration` (float, 可选): 持续时间（秒），None表示到视频结束

### 质量设置说明

- **high**: 最高质量，文件较大，颜色保持最好
- **medium**: 中等质量，平衡文件大小和质量
- **low**: 较低质量，文件较小，适合快速预览

## 支持的视频格式

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)
- M4V (.m4v)

## 注意事项

1. **FFmpeg依赖**: 确保系统已安装FFmpeg，moviepy会自动下载
2. **内存使用**: 大视频文件转换时可能需要较多内存
3. **处理时间**: 转换时间取决于视频长度、分辨率和帧率
4. **文件大小**: GIF文件通常比原视频大，建议适当降低分辨率或帧率

## 故障排除

### 常见问题

1. **FFmpeg未找到**: 确保FFmpeg已正确安装或让moviepy自动下载
2. **内存不足**: 尝试降低最大尺寸或帧率
3. **格式不支持**: 检查视频格式是否在支持列表中
4. **转换失败**: 检查视频文件是否损坏，尝试其他视频文件
5. **GUI启动失败**: 运行 `python test_fix.py` 检查环境配置

### 修复验证

如果遇到GUI启动问题，可以运行修复验证脚本：

```bash
python test_fix.py
```

该脚本会检查：
- GUI模块导入是否成功
- 变量初始化是否正确
- 文件浏览功能是否正常

### 性能优化建议

- 对于长视频，建议先裁剪到需要的片段
- 适当降低帧率可以减少文件大小
- 使用中等质量设置可以平衡质量和文件大小

## 更新日志

- v2.0: 添加GUI界面，支持多格式，优化颜色保持
- v1.0: 基础MP4转GIF功能