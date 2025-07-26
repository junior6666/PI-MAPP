from moviepy.editor import VideoFileClip
import argparse
import os
import json


def get_video_info(video_path):
    """
    获取视频文件的基本信息
    
    参数:
    video_path (str): 视频文件路径
    
    返回:
    dict: 包含视频信息的字典
    """
    try:
        with VideoFileClip(video_path) as clip:
            info = {
                'width': int(clip.w),
                'height': int(clip.h),
                'fps': float(clip.fps),
                'duration': float(clip.duration),
                'size': os.path.getsize(video_path),
                'format': os.path.splitext(video_path)[1].lower()
            }
            return info
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None


def convert_video_to_gif(input_path, output_path=None, max_dimension=None, 
                        target_fps=None, preserve_colors=True, quality='high',
                        start_time=0.0, duration=None):
    """
    将视频转换为GIF，优化颜色保持和画质

    参数:
    input_path (str): 输入的视频文件路径
    output_path (str, 可选): 输出的GIF文件路径
    max_dimension (int, 可选): 最大尺寸（保持宽高比缩放）
    target_fps (float, 可选): 目标帧率（默认使用原视频帧率）
    preserve_colors (bool): 是否保持原始颜色
    quality (str): 质量设置 ('low', 'medium', 'high')
    start_time (float): 开始时间（秒）
    duration (float, 可选): 持续时间（秒，None表示到视频结束）
    """
    # 支持的视频格式
    supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    file_ext = os.path.splitext(input_path)[1].lower()
    
    if file_ext not in supported_formats:
        raise ValueError(f"不支持的视频格式: {file_ext}。支持的格式: {', '.join(supported_formats)}")
    
    # 设置默认输出路径
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}.gif")

    # 读取视频文件
    with VideoFileClip(input_path) as clip:
        # 获取原始尺寸和时长
        original_width, original_height = clip.w, clip.h
        original_duration = clip.duration
        
        # 验证时间参数
        if start_time < 0:
            start_time = 0
        if start_time >= original_duration:
            raise ValueError(f"开始时间 {start_time} 秒超过了视频总时长 {original_duration} 秒")
        
        if duration is not None:
            if duration <= 0:
                raise ValueError("持续时间必须大于0")
            if start_time + duration > original_duration:
                duration = original_duration - start_time
                print(f"警告: 调整持续时间为 {duration} 秒以匹配视频结束")
        
        # 裁剪视频片段
        if start_time > 0 or duration is not None:
            end_time = start_time + duration if duration is not None else original_duration
            clip = clip.subclip(start_time, end_time)
            print(f"裁剪视频片段: {start_time:.2f}s - {end_time:.2f}s")
        
        # 可选缩放
        if max_dimension:
            if original_width > original_height:
                new_width = min(max_dimension, original_width)
                new_height = int(original_height * (new_width / original_width))
            else:
                new_height = min(max_dimension, original_height)
                new_width = int(original_width * (new_height / original_height))
            
            clip = clip.resize((new_width, new_height))
            print(f"调整尺寸: {new_width} x {new_height}")
        
        # 设置帧率
        if target_fps is None:
            target_fps = clip.fps
        else:
            target_fps = min(target_fps, clip.fps)  # 不超过原视频帧率
        
        print(f"目标帧率: {target_fps} FPS")
        
        # 根据质量设置优化参数
        if quality == 'high':
            opt = 'OptimizePlus'
            fuzz = 0
        elif quality == 'medium':
            opt = 'OptimizeTransparency'
            fuzz = 1
        else:  # low
            opt = 'OptimizeTransparency'
            fuzz = 3
        
        print(f"质量设置: {quality} (opt={opt}, fuzz={fuzz})")
        
        # 写入GIF
        if preserve_colors:
            # 使用更好的颜色保持设置
            clip.write_gif(
                output_path,
                fps=target_fps,
                program='ffmpeg',
                opt=opt,
                fuzz=fuzz,
                verbose=False,
                logger=None
            )
        else:
            # 标准设置
            clip.write_gif(
                output_path,
                fps=target_fps,
                program='ffmpeg',
                opt=opt,
                verbose=False,
                logger=None
            )

    print(f"转换成功！GIF已保存至: {output_path}")
    return output_path


def convert_mp4_to_gif(input_path, output_path=None, max_dimension=None):
    """
    向后兼容的MP4转GIF函数
    """
    return convert_video_to_gif(input_path, output_path, max_dimension)


if __name__ == "__main__":
    # 测试转换
    test_path = r'H:\pycharm_project\PI-MAPP\utils\video_utils\video_data\test_data.mp4'
    
    # 获取视频信息
    info = get_video_info(test_path)
    if info:
        print("视频信息:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    # 转换测试
    convert_video_to_gif(
        input_path=test_path,
        max_dimension=480,
        preserve_colors=True,
        quality='high',
        start_time=0.0,
        duration=5.0  # 只转换前5秒
    )