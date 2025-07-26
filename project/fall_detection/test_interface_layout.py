"""
界面布局测试脚本
验证修改后的界面布局是否正确
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time

def test_interface_layout():
    """测试界面布局"""
    root = tk.Tk()
    root.title("界面布局测试")
    root.geometry("1300x900")
    root.configure(bg='#f0f0f0')
    
    # 顶部信息栏 - 一行显示
    info_frame = ttk.Frame(root)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # 使用LabelFrame包装状态信息
    status_frame = ttk.LabelFrame(info_frame, text="系统状态", padding=8)
    status_frame.pack(fill=tk.X)
    
    # 一行显示所有状态信息
    status_row = ttk.Frame(status_frame)
    status_row.pack(fill=tk.X, pady=2)
    
    # 输入源
    source_frame = ttk.Frame(status_row)
    source_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(source_frame, text="📹 输入源:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    source_label = ttk.Label(source_frame, text="图片", font=('Arial', 9), foreground='#0066cc', width=8)
    source_label.pack(side=tk.LEFT, padx=5)
    
    # 检测状态
    status_frame_inner = ttk.Frame(status_row)
    status_frame_inner.pack(side=tk.LEFT, padx=10)
    ttk.Label(status_frame_inner, text="🔍 检测状态:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    status_label = ttk.Label(status_frame_inner, text="正常", font=('Arial', 9), foreground='#cc6600', width=8)
    status_label.pack(side=tk.LEFT, padx=5)
    
    # 检测速率
    speed_frame = ttk.Frame(status_row)
    speed_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(speed_frame, text="⚡ 检测速率:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    speed_label = ttk.Label(speed_frame, text="25.0 fps", font=('Arial', 9), foreground='#009900', width=8)
    speed_label.pack(side=tk.LEFT, padx=5)
    
    # 算法
    algo_frame = ttk.Frame(status_row)
    algo_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(algo_frame, text="🧠 算法:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    algo_label = ttk.Label(algo_frame, text="阈值法", font=('Arial', 9), foreground='#990099', width=8)
    algo_label.pack(side=tk.LEFT, padx=5)
    
    # 帧信息
    frame_frame = ttk.Frame(status_row)
    frame_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(frame_frame, text="📊 帧:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
    frame_info_label = ttk.Label(frame_frame, text="1/1", font=('Arial', 9), foreground='#666666', width=10)
    frame_info_label.pack(side=tk.LEFT, padx=5)
    
    # 主框架
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 左侧控制面板（简化版）
    control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
    control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
    
    ttk.Button(control_frame, text="🖼️ 加载图片").pack(fill=tk.X, pady=2)
    ttk.Button(control_frame, text="🎬 加载视频").pack(fill=tk.X, pady=2)
    ttk.Button(control_frame, text="📹 打开摄像头").pack(fill=tk.X, pady=2)
    ttk.Button(control_frame, text="▶️ 开始检测").pack(fill=tk.X, pady=2)
    ttk.Button(control_frame, text="⏹️ 停止检测").pack(fill=tk.X, pady=2)
    
    # 右侧显示面板
    display_frame = ttk.Frame(main_frame)
    display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # 视频显示区域（双窗口）
    video_frame = ttk.LabelFrame(display_frame, text="视频显示", padding=5)
    video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    video_inner_frame = ttk.Frame(video_frame)
    video_inner_frame.pack(fill=tk.BOTH, expand=True)
    
    # 原图窗口
    original_frame = ttk.Frame(video_inner_frame)
    original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    ttk.Label(original_frame, text="原图/原视频", font=('Arial', 10, 'bold')).pack()
    original_video_label = ttk.Label(original_frame, text="请加载图片或视频", bg='#f0f0f0')
    original_video_label.pack(fill=tk.BOTH, expand=True)
    
    # 检测后窗口
    processed_frame = ttk.Frame(video_inner_frame)
    processed_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    ttk.Label(processed_frame, text="检测后", font=('Arial', 10, 'bold')).pack()
    processed_video_label = ttk.Label(processed_frame, text="请加载图片或视频", bg='#f0f0f0')
    processed_video_label.pack(fill=tk.BOTH, expand=True)
    
    # 进度条和暂停按钮
    progress_frame = ttk.Frame(video_frame)
    progress_frame.pack(fill=tk.X, pady=5)
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Scale(progress_frame, variable=progress_var, from_=0, to=100, orient=tk.HORIZONTAL)
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    pause_button = ttk.Button(progress_frame, text="暂停")
    pause_button.pack(side=tk.LEFT, padx=5)
    
    # 系统日志区域（移到视频显示下方）
    log_frame = ttk.LabelFrame(display_frame, text="📝 系统日志", padding=5)
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    # 日志工具栏
    log_toolbar = ttk.Frame(log_frame)
    log_toolbar.pack(fill=tk.X, pady=(0, 5))
    
    ttk.Button(log_toolbar, text="🗑️ 清空日志", width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(log_toolbar, text="💾 保存日志", width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(log_toolbar, text="📋 复制日志", width=10).pack(side=tk.LEFT, padx=2)
    
    # 日志文本框
    log_text = scrolledtext.ScrolledText(log_frame, height=8, width=50, 
                                        font=('Consolas', 9), 
                                        bg='#f8f8f8', fg='#333333')
    log_text.pack(fill=tk.BOTH, expand=True)
    
    # 添加测试日志
    log_text.insert(tk.END, "[12:00:00] 系统启动\n")
    log_text.insert(tk.END, "[12:00:01] 界面布局测试完成\n")
    log_text.insert(tk.END, "[12:00:02] 状态栏已改为一行显示\n")
    log_text.insert(tk.END, "[12:00:03] 检测结果区域已移除\n")
    
    # 添加说明
    info_label = ttk.Label(root, text="界面布局测试说明：\n1. 顶部状态栏已改为一行显示\n2. 检测结果区域已移除\n3. 系统日志移到视频显示下方\n4. 界面布局更加简洁", 
                          justify=tk.LEFT)
    info_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_interface_layout() 