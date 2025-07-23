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
            # opt='OptimizePlus',  # 优化设置
            # fuzz=1  # 最小化颜色变化损失
        )

    print(f"转换成功！GIF已保存至: {output_path}")


if __name__ == "__main__":

    convert_mp4_to_gif(
        input_path=r'H:\pycharm_project\PI-MAPP\utils\video_utils\video_data\test_data.mp4'
    )