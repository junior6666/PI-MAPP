"""
视频窗口稳定性测试
验证移除自适应缩放后视频播放是否稳定
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
import time
import threading

def test_video_stability():
    """测试视频窗口稳定性"""
    root = tk.Tk()
    root.title("视频稳定性测试")
    root.geometry("800x600")
    
    # 创建视频显示区域
    video_frame = ttk.LabelFrame(root, text="视频显示", padding=10)
    video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 创建视频标签
    video_label = ttk.Label(video_frame, text="测试视频")
    video_label.pack(fill=tk.BOTH, expand=True)
    
    # 创建控制按钮
    control_frame = ttk.Frame(root)
    control_frame.pack(fill=tk.X, padx=10, pady=5)
    
    is_playing = False
    video_capture = None
    
    def start_test():
        nonlocal is_playing, video_capture
        if not is_playing:
            # 创建测试视频（彩色渐变）
            is_playing = True
            start_button.config(text="停止")
            
            def video_loop():
                frame_count = 0
                while is_playing:
                    # 创建测试帧（彩色渐变）
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    frame[:, :, 0] = (frame_count * 2) % 256  # 蓝色通道
                    frame[:, :, 1] = (frame_count * 3) % 256  # 绿色通道
                    frame[:, :, 2] = (frame_count * 5) % 256  # 红色通道
                    
                    # 添加帧计数文字
                    cv2.putText(frame, f"Frame: {frame_count}", (50, 50), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    # 转换为PIL图像并显示
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    from PIL import Image, ImageTk
                    pil_image = Image.fromarray(frame_rgb)
                    photo = ImageTk.PhotoImage(pil_image)
                    video_label.configure(image=photo, text="")
                    video_label.image = photo
                    
                    frame_count += 1
                    time.sleep(0.05)  # 20fps
            
            threading.Thread(target=video_loop, daemon=True).start()
        else:
            is_playing = False
            start_button.config(text="开始测试")
    
    def open_camera():
        nonlocal video_capture
        if video_capture is None:
            video_capture = cv2.VideoCapture(0)
            if video_capture.isOpened():
                camera_button.config(text="关闭摄像头")
                
                def camera_loop():
                    while video_capture and video_capture.isOpened():
                        ret, frame = video_capture.read()
                        if ret:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            from PIL import Image, ImageTk
                            pil_image = Image.fromarray(frame_rgb)
                            photo = ImageTk.PhotoImage(pil_image)
                            video_label.configure(image=photo, text="")
                            video_label.image = photo
                        time.sleep(0.05)
                
                threading.Thread(target=camera_loop, daemon=True).start()
        else:
            video_capture.release()
            video_capture = None
            camera_button.config(text="打开摄像头")
    
    start_button = ttk.Button(control_frame, text="开始测试", command=start_test)
    start_button.pack(side=tk.LEFT, padx=5)
    
    camera_button = ttk.Button(control_frame, text="打开摄像头", command=open_camera)
    camera_button.pack(side=tk.LEFT, padx=5)
    
    # 添加说明
    info_label = ttk.Label(root, text="测试说明：\n1. 点击'开始测试'查看生成的测试视频\n2. 点击'打开摄像头'查看实时摄像头\n3. 观察视频是否稳定播放，无抖动现象", 
                          justify=tk.LEFT)
    info_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_video_stability() 