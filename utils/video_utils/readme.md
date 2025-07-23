以下是一个使用Python将MP4视频转换为GIF的脚本，该脚本使用MoviePy库并保留原始画质和时长：

```python
from moviepy.editor import VideoFileClip
import argparse
import os

def convert_mp4_to_gif(input_path, output_path=None, max_dimension=None):
    """
    将MP4视频转换为GIF，保留原始画质和时长
    
    参数:
    input_path (str): 输入的MP4文件路径
    output_path (str, 可选): 输出的GIF文件路径（默认与输入同目录同名）
    max_dimension (int, 可选): 最大尺寸（保持宽高比缩放）
    """
    # 设置默认输出路径
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}.gif")
    
    # 读取视频文件
    with VideoFileClip(input_path) as clip:
        # 可选缩放
        if max_dimension:
            clip = clip.resize(width=max_dimension) if clip.w > clip.h \
                else clip.resize(height=max_dimension)
        
        # 计算帧率（保持原速）
        fps = clip.fps
        
        # 写入GIF（保留原始时长和画质）
        clip.write_gif(
            output_path,
            fps=fps,
            program='ffmpeg',  # 使用FFmpeg提高质量
            opt='OptimizePlus',  # 优化设置
            fuzz=1  # 最小化颜色变化损失
        )
    
    print(f"转换成功！GIF已保存至: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将MP4视频转换为高质量GIF')
    parser.add_argument('input', help='输入的MP4文件路径')
    parser.add_argument('-o', '--output', help='输出的GIF文件路径（可选）')
    parser.add_argument('-s', '--size', type=int, 
                        help='最大尺寸（保持宽高比缩放，可选）')
    
    args = parser.parse_args()
    
    convert_mp4_to_gif(
        input_path=args.input,
        output_path=args.output,
        max_dimension=args.size
    )
```

### 使用说明：

1. **安装依赖库**：
   ```bash
   pip install moviepy
   ```

2. **运行脚本**：
   ```bash
   python mp4_to_gif.py input_video.mp4
   ```

3. **可选参数**：
   - `-o output.gif`：指定输出文件名
   - `-s 800`：设置最大尺寸（保持宽高比）

### 功能特点：

1. **保留原始时长**：自动计算原始视频帧率，确保GIF时长与视频一致
2. **高画质输出**：
   - 使用FFmpeg引擎处理（需要安装FFmpeg）
   - `OptimizePlus`优化算法
   - 最小化颜色损失（fuzz参数）
3. **智能缩放**：可选保持宽高比的尺寸调整
4. **自动命名**：默认使用原始文件名+`.gif`后缀

### 注意事项：

1. **FFmpeg安装**：
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: 从[官网](https://ffmpeg.org/)下载并添加PATH
   - 环境配置教程https://blog.csdn.net/Natsuago/article/details/143231558

2. **大文件处理**：
   - 长视频转换可能需要较长时间
   - 输出文件大小可能较大（GIF格式限制）
   - 建议处理时长小于30秒的视频片段

3. **颜色精度**：
   - GIF格式限制为256色，复杂场景可能有色差
   - 使用`fuzz`参数可减少颜色变化损失

此脚本平衡了画质保持和文件大小，对于需要高质量GIF转换的场景特别有用。