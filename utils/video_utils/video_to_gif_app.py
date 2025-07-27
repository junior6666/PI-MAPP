#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转GIF工具 - 全新设计版本
功能完整、界面清晰的视频转GIF转换器
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
from convert_mp4_to_gif import convert_video_to_gif, get_video_info


class VideoToGifApp:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.create_widgets()
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("视频转GIF工具 v2.0")
        self.root.geometry("900x850")
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
    def setup_variables(self):
        """初始化变量"""
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.fps = tk.DoubleVar(value=15.0)
        self.quality = tk.StringVar(value="high")
        self.keep_colors = tk.BooleanVar(value=True)
        self.start_time = tk.DoubleVar(value=0.0)
        self.duration = tk.DoubleVar(value=0.0)
        self.progress = tk.DoubleVar(value=0.0)
        # 新增：自定义宽高设置
        self.custom_width = tk.IntVar(value=0)  # 0表示使用原始宽度
        self.custom_height = tk.IntVar(value=0)  # 0表示使用原始高度
        self.use_custom_size = tk.BooleanVar(value=False)  # 是否使用自定义尺寸
        self.video_info = None
        self.is_converting = False
        
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(title_frame, 
                              text="🎬 视频转GIF工具", 
                              font=('Arial', 24, 'bold'),
                              fg='#2c3e50',
                              bg='#f0f0f0')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Video to GIF Converter",
                                 font=('Arial', 12),
                                 fg='#7f8c8d',
                                 bg='#f0f0f0')
        subtitle_label.pack()
        
        # 文件选择和视频信息区域（并排显示）
        self.create_file_and_info_section()
        
        # 参数设置区域
        self.create_settings_section()
        
        # 转换控制区域
        self.create_control_section()
        
        # 进度显示区域
        self.create_progress_section()
        
    def create_file_and_info_section(self):
        """创建文件选择和视频信息区域（并排显示）"""
        # 主容器
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='x', padx=20, pady=10)
        
        # 文件选择区域（左侧）
        file_frame = tk.LabelFrame(main_frame, text="📁 文件选择", 
                                  font=('Arial', 12, 'bold'),
                                  fg='#2c3e50',
                                  bg='#f0f0f0',
                                  relief='groove',
                                  bd=2)
        file_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 输入文件
        input_frame = tk.Frame(file_frame, bg='#f0f0f0')
        input_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(input_frame, text="输入视频:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w')
        
        input_entry_frame = tk.Frame(input_frame, bg='#f0f0f0')
        input_entry_frame.pack(fill='x', pady=(5, 0))
        
        input_entry = tk.Entry(input_entry_frame, 
                              textvariable=self.input_file,
                              font=('Arial', 10),
                              bg='white',
                              fg='#2c3e50',
                              relief='solid',
                              bd=1)
        input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(input_entry_frame,
                              text="浏览",
                              command=self.browse_input,
                              font=('Arial', 10, 'bold'),
                              bg='#3498db',
                              fg='white',
                              relief='raised',
                              bd=2,
                              padx=15,
                              pady=5,
                              cursor='hand2')
        browse_btn.pack(side='right')
        
        # 输出文件
        output_frame = tk.Frame(file_frame, bg='#f0f0f0')
        output_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        tk.Label(output_frame, text="输出GIF:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w')
        
        output_entry_frame = tk.Frame(output_frame, bg='#f0f0f0')
        output_entry_frame.pack(fill='x', pady=(5, 0))
        
        output_entry = tk.Entry(output_entry_frame, 
                               textvariable=self.output_file,
                               font=('Arial', 10),
                               bg='white',
                               fg='#2c3e50',
                               relief='solid',
                               bd=1)
        output_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        save_btn = tk.Button(output_entry_frame,
                            text="保存",
                            command=self.browse_output,
                            font=('Arial', 10, 'bold'),
                            bg='#27ae60',
                            fg='white',
                            relief='raised',
                            bd=2,
                            padx=15,
                            pady=5,
                            cursor='hand2')
        save_btn.pack(side='right')
        
        # 视频信息区域（右侧）
        info_frame = tk.LabelFrame(main_frame, text="📊 视频信息", 
                                  font=('Arial', 12, 'bold'),
                                  fg='#2c3e50',
                                  bg='#f0f0f0',
                                  relief='groove',
                                  bd=2)
        info_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self.info_text = tk.Text(info_frame,
                                height=5,
                                font=('Consolas', 10),
                                bg='white',
                                fg='#2c3e50',
                                relief='solid',
                                bd=1,
                                state='disabled')
        self.info_text.pack(fill='both', expand=True, padx=15, pady=10)
        

        
    def create_settings_section(self):
        """创建参数设置区域"""
        settings_frame = tk.LabelFrame(self.root, text="⚙️ 转换设置", 
                                      font=('Arial', 12, 'bold'),
                                      fg='#2c3e50',
                                      bg='#f0f0f0',
                                      relief='groove',
                                      bd=2)
        settings_frame.pack(fill='x', padx=20, pady=10)
        
        # 创建两列布局
        left_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        left_frame.pack(side='left', fill='both', expand=True, padx=15, pady=10)
        
        right_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        right_frame.pack(side='right', fill='both', expand=True, padx=15, pady=10)
        
        # 左列：基本参数
        # 尺寸设置
        size_label = tk.Label(left_frame, text="尺寸设置:", 
                             font=('Arial', 10, 'bold'),
                             fg='#2c3e50',
                             bg='#f0f0f0')
        size_label.pack(anchor='w', pady=2)
        
        # 自定义尺寸选项
        custom_size_check = tk.Checkbutton(left_frame,
                                          text="使用自定义尺寸",
                                          variable=self.use_custom_size,
                                          font=('Arial', 9),
                                          fg='#2c3e50',
                                          bg='#f0f0f0',
                                          selectcolor='white',
                                          activebackground='#f0f0f0',
                                          activeforeground='#2c3e50',
                                          command=self.toggle_size_options)
        custom_size_check.pack(anchor='w', pady=2)
        
        # 自定义宽高输入框
        size_frame = tk.Frame(left_frame, bg='#f0f0f0')
        size_frame.pack(fill='x', pady=2)
        
        # 宽度输入
        width_label = tk.Label(size_frame, text="宽度:",
                              font=('Arial', 9),
                              fg='#2c3e50',
                              bg='#f0f0f0')
        width_label.pack(side='left')
        
        self.width_entry = tk.Entry(size_frame,
                                   textvariable=self.custom_width,
                                   font=('Arial', 9),
                                   bg='white',
                                   fg='#2c3e50',
                                   relief='solid',
                                   bd=1,
                                   width=8,
                                   state='disabled')
        self.width_entry.pack(side='left', padx=(5, 10))
        
        # 高度输入
        height_label = tk.Label(size_frame, text="高度:",
                               font=('Arial', 9),
                               fg='#2c3e50',
                               bg='#f0f0f0')
        height_label.pack(side='left')
        
        self.height_entry = tk.Entry(size_frame,
                                    textvariable=self.custom_height,
                                    font=('Arial', 9),
                                    bg='white',
                                    fg='#2c3e50',
                                    relief='solid',
                                    bd=1,
                                    width=8,
                                    state='disabled')
        self.height_entry.pack(side='left', padx=(5, 0))
        
        # 原始尺寸显示
        self.original_size_label = tk.Label(left_frame,
                                           text="原始尺寸: 未加载",
                                           font=('Arial', 9),
                                           fg='#7f8c8d',
                                           bg='#f0f0f0')
        self.original_size_label.pack(anchor='w', pady=2)
        

        
        # 帧率
        tk.Label(left_frame, text="目标帧率:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w', pady=(10, 2))
        
        fps_frame = tk.Frame(left_frame, bg='#f0f0f0')
        fps_frame.pack(fill='x', pady=2)
        
        fps_entry = tk.Entry(fps_frame,
                            textvariable=self.fps,
                            font=('Arial', 10),
                            bg='white',
                            fg='#2c3e50',
                            relief='solid',
                            bd=1,
                            width=10)
        fps_entry.pack(side='left')
        
        tk.Label(fps_frame, text="FPS",
                font=('Arial', 9),
                fg='#7f8c8d',
                bg='#f0f0f0').pack(side='left', padx=(5, 0))
        
        # 质量设置
        tk.Label(left_frame, text="质量等级:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w', pady=(10, 2))
        
        quality_combo = ttk.Combobox(left_frame,
                                    textvariable=self.quality,
                                    values=['low', 'medium', 'high'],
                                    state='readonly',
                                    font=('Arial', 10),
                                    width=15)
        quality_combo.pack(anchor='w')
        
        # 右列：时长控制
        # 原视频时长
        tk.Label(right_frame, text="原视频时长:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w', pady=2)
        
        self.duration_label = tk.Label(right_frame,
                                      text="0.00 秒",
                                      font=('Arial', 10),
                                      fg='#e74c3c',
                                      bg='#f0f0f0')
        self.duration_label.pack(anchor='w', pady=2)
        
        # 开始时间
        tk.Label(right_frame, text="开始时间:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w', pady=(10, 2))
        
        start_frame = tk.Frame(right_frame, bg='#f0f0f0')
        start_frame.pack(fill='x', pady=2)
        
        start_entry = tk.Entry(start_frame,
                              textvariable=self.start_time,
                              font=('Arial', 10),
                              bg='white',
                              fg='#2c3e50',
                              relief='solid',
                              bd=1,
                              width=10)
        start_entry.pack(side='left')
        
        tk.Label(start_frame, text="秒",
                font=('Arial', 9),
                fg='#7f8c8d',
                bg='#f0f0f0').pack(side='left', padx=(5, 0))
        
        # GIF时长
        tk.Label(right_frame, text="GIF时长:", 
                font=('Arial', 10, 'bold'),
                fg='#2c3e50',
                bg='#f0f0f0').pack(anchor='w', pady=(10, 2))
        
        duration_frame = tk.Frame(right_frame, bg='#f0f0f0')
        duration_frame.pack(fill='x', pady=2)
        
        duration_entry = tk.Entry(duration_frame,
                                 textvariable=self.duration,
                                 font=('Arial', 10),
                                 bg='white',
                                 fg='#2c3e50',
                                 relief='solid',
                                 bd=1,
                                 width=10)
        duration_entry.pack(side='left')
        
        tk.Label(duration_frame, text="秒 (0=使用原时长)",
                font=('Arial', 9),
                fg='#7f8c8d',
                bg='#f0f0f0').pack(side='left', padx=(5, 0))
        
        # 颜色保持选项
        color_check = tk.Checkbutton(settings_frame,
                                    text="保持原始颜色",
                                    variable=self.keep_colors,
                                    font=('Arial', 10, 'bold'),
                                    fg='#2c3e50',
                                    bg='#f0f0f0',
                                    selectcolor='white',
                                    activebackground='#f0f0f0',
                                    activeforeground='#2c3e50')
        color_check.pack(pady=5)
        
    def create_control_section(self):
        """创建转换控制区域"""
        control_frame = tk.LabelFrame(self.root, text="🎯 转换控制", 
                                     font=('Arial', 12, 'bold'),
                                     fg='#2c3e50',
                                     bg='#f0f0f0',
                                     relief='groove',
                                     bd=2)
        control_frame.pack(fill='x', padx=20, pady=15)
        
        # 按钮容器
        button_frame = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame.pack(pady=15)
        
        # 转换按钮 - 左侧
        self.convert_btn = tk.Button(button_frame,
                                    text="🚀 开始转换",
                                    command=self.start_conversion,
                                    font=('Arial', 16, 'bold'),
                                    bg='#27ae60',
                                    fg='white',
                                    relief='raised',
                                    bd=3,
                                    padx=40,
                                    pady=15,
                                    cursor='hand2')
        self.convert_btn.pack(side='left', padx=(0, 20))
        
        # 清空按钮 - 右侧
        clear_btn = tk.Button(button_frame,
                             text="🗑️ 清空设置",
                             command=self.clear_all,
                             font=('Arial', 16, 'bold'),
                             bg='#e74c3c',
                             fg='white',
                             relief='raised',
                             bd=3,
                             padx=40,
                             pady=15,
                             cursor='hand2')
        clear_btn.pack(side='left')
        
    def create_progress_section(self):
        """创建进度显示区域"""
        progress_frame = tk.LabelFrame(self.root, text="📈 转换进度", 
                                      font=('Arial', 12, 'bold'),
                                      fg='#2c3e50',
                                      bg='#f0f0f0',
                                      relief='groove',
                                      bd=2)
        progress_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame,
                                           variable=self.progress,
                                           maximum=100,
                                           mode='determinate')
        self.progress_bar.pack(fill='x', padx=15, pady=(10, 5))
        
        # 状态文本
        self.status_label = tk.Label(progress_frame,
                                    text="就绪",
                                    font=('Arial', 10),
                                    fg='#27ae60',
                                    bg='#f0f0f0')
        self.status_label.pack(pady=(0, 10))
        
    def browse_input(self):
        """选择输入文件"""
        filetypes = [
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("MP4文件", "*.mp4"),
            ("AVI文件", "*.avi"),
            ("MOV文件", "*.mov"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file.set(filename)
            self.load_video_info()
            self.auto_set_output()
            
    def browse_output(self):
        """选择输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存GIF文件",
            defaultextension=".gif",
            filetypes=[("GIF文件", "*.gif"), ("所有文件", "*.*")]
        )
        
        if filename:
            self.output_file.set(filename)
            
    def auto_set_output(self):
        """自动设置输出文件名"""
        if self.input_file.get():
            base_name = os.path.splitext(os.path.basename(self.input_file.get()))[0]
            output_dir = os.path.dirname(self.input_file.get())
            output_file = os.path.join(output_dir, f"{base_name}.gif")
            self.output_file.set(output_file)
            
    def load_video_info(self):
        """加载视频信息"""
        try:
            self.video_info = get_video_info(self.input_file.get())
            if self.video_info:
                self.display_video_info()
                # 自动设置参数
                self.fps.set(min(self.video_info['fps'], 30.0))
                self.duration_label.config(text=f"{self.video_info['duration']:.2f} 秒")
                self.status_label.config(text="视频信息加载成功", fg='#27ae60')
            else:
                self.status_label.config(text="无法读取视频信息", fg='#e74c3c')
        except Exception as e:
            self.status_label.config(text=f"读取视频信息失败: {str(e)}", fg='#e74c3c')
            
    def toggle_size_options(self):
        """切换尺寸选项的启用状态"""
        if self.use_custom_size.get():
            self.width_entry.config(state='normal')
            self.height_entry.config(state='normal')
        else:
            self.width_entry.config(state='disabled')
            self.height_entry.config(state='disabled')
            
    def display_video_info(self):
        """显示视频信息"""
        if not self.video_info:
            return
            
        info_text = f"""文件格式: {self.video_info['format']}
分辨率: {self.video_info['width']} x {self.video_info['height']}
帧率: {self.video_info['fps']:.2f} FPS
时长: {self.video_info['duration']:.2f} 秒
文件大小: {self.video_info['size'] / (1024*1024):.2f} MB"""
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state='disabled')
        
        # 更新原始尺寸显示
        self.original_size_label.config(text=f"原始尺寸: {self.video_info['width']} x {self.video_info['height']}")
        
        # 设置默认的自定义尺寸为原始尺寸
        if not self.use_custom_size.get():
            self.custom_width.set(self.video_info['width'])
            self.custom_height.set(self.video_info['height'])
        
    def update_progress(self, value, text):
        """更新进度"""
        self.progress.set(value)
        self.status_label.config(text=text)
        self.root.update_idletasks()
        
    def start_conversion(self):
        """开始转换"""
        if not self.input_file.get():
            messagebox.showerror("错误", "请选择输入视频文件")
            return
            
        if not self.output_file.get():
            messagebox.showerror("错误", "请选择输出GIF文件")
            return
            
        if self.is_converting:
            return
            
        # 开始转换
        self.is_converting = True
        self.convert_btn.config(state='disabled', text="🔄 转换中...")
        self.progress.set(0)
        self.update_progress(0, "正在准备转换...")
        
        # 在新线程中执行转换
        thread = threading.Thread(target=self.convert_video)
        thread.daemon = True
        thread.start()
        
    def convert_video(self):
        """执行视频转换"""
        try:
            # 模拟进度更新
            self.update_progress(10, "正在读取视频文件...")
            time.sleep(0.3)
            
            self.update_progress(30, "正在处理视频帧...")
            time.sleep(0.3)
            
            self.update_progress(50, "正在优化颜色...")
            time.sleep(0.3)
            
            self.update_progress(70, "正在生成GIF...")
            time.sleep(0.3)
            
            # 实际转换
            # 确定使用的宽高参数
            width = None
            height = None
            
            if self.use_custom_size.get():
                # 使用自定义尺寸
                width = self.custom_width.get() if self.custom_width.get() > 0 else None
                height = self.custom_height.get() if self.custom_height.get() > 0 else None
            
            output_path = convert_video_to_gif(
                input_path=self.input_file.get(),
                output_path=self.output_file.get(),
                target_fps=self.fps.get(),
                preserve_colors=self.keep_colors.get(),
                quality=self.quality.get(),
                start_time=self.start_time.get(),
                duration=self.duration.get() if self.duration.get() > 0 else None,
                width=width,
                height=height
            )
            
            self.update_progress(100, "转换完成！")
            
            # 在主线程中更新UI
            self.root.after(0, self.conversion_completed, output_path, None)
            
        except Exception as e:
            # 在主线程中显示错误
            self.root.after(0, self.conversion_completed, None, str(e))
            
    def conversion_completed(self, output_path, error):
        """转换完成回调"""
        self.is_converting = False
        self.convert_btn.config(state='normal', text="🚀 开始转换")
        
        if error:
            self.status_label.config(text=f"转换失败: {error}", fg='#e74c3c')
            messagebox.showerror("转换失败", f"转换过程中出现错误:\n{error}")
        else:
            self.status_label.config(text="转换成功！", fg='#27ae60')
            messagebox.showinfo("转换成功", f"GIF文件已保存至:\n{output_path}")
            
    def clear_all(self):
        """清空所有设置"""
        self.input_file.set("")
        self.output_file.set("")
        self.fps.set(15.0)
        self.quality.set("high")
        self.keep_colors.set(True)
        self.start_time.set(0.0)
        self.duration.set(0.0)
        self.progress.set(0)
        # 清空自定义尺寸设置
        self.custom_width.set(0)
        self.custom_height.set(0)
        self.use_custom_size.set(False)
        self.video_info = None
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')
        
        self.duration_label.config(text="0.00 秒")
        self.original_size_label.config(text="原始尺寸: 未加载")
        self.status_label.config(text="就绪", fg='#27ae60')
        
        # 禁用自定义尺寸输入框
        self.width_entry.config(state='disabled')
        self.height_entry.config(state='disabled')
        
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


def main():
    """主函数"""
    app = VideoToGifApp()
    app.run()


if __name__ == "__main__":
    main() 