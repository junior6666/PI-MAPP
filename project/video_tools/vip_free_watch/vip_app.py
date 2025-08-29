import os
import sys
import tkinter as tk
from tkinter import messagebox
import webbrowser
import re
from urllib.parse import quote_plus


class VIPVideoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('VIP免费追剧神器')
        self.root.geometry('500x500')
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f2f5')

        # 设置应用程序图标 (如果有的话)
        # self.root.iconbitmap('vip.ico')  # 取消注释并添加图标文件路径如果有的话
        try:
            # 如果是打包后的可执行文件
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'vip.ico')
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {e}")
        # 选中的通道编号，默认为 1
        self.channel = tk.IntVar(value=1)

        self.create_widgets()

    # ------------------------------------------------------------------
    def create_widgets(self):
        # 标题
        title_label = tk.Label(
            self.root,
            text='VIP免费追剧神器',
            font=('Microsoft YaHei', 16, 'bold'),
            fg='#2c3e50',
            bg='#f0f2f5'
        )
        title_label.pack(pady=(15, 10))

        # 主容器框架
        main_frame = tk.Frame(self.root, bg='#ffffff', relief=tk.RAISED, bd=1)
        main_frame.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)

        # 1. 输入区
        input_frame = tk.Frame(main_frame, bg='#ffffff')
        input_frame.pack(pady=(15, 10), padx=15, fill=tk.X)

        tk.Label(
            input_frame,
            text='视频网址:',
            font=('Microsoft YaHei', 10),
            bg='#ffffff'
        ).pack(side=tk.LEFT)

        self.url_entry = tk.Entry(
            input_frame,
            font=('Microsoft YaHei', 10),
            relief=tk.SOLID,
            bd=1
        )
        self.url_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        tk.Button(
            input_frame,
            text='清空',
            command=self.clear_entry,
            font=('Microsoft YaHei', 9),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.RIGHT)

        # 2. 解析通道单选
        channel_frame = tk.LabelFrame(
            main_frame,
            text='选择解析通道',
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#ffffff',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        channel_frame.pack(pady=10, padx=15, fill=tk.X)

        channels = [
            '通道1 - xyflv (稳定)',
            '通道2 - jsonplayer (高清)',
            '通道3 - yparse (快速)',
            '通道4 - nnxv (备用)',
            '通道5 - wmxz (备用)'
        ]

        for idx, text in enumerate(channels, start=1):
            tk.Radiobutton(
                channel_frame,
                text=text,
                variable=self.channel,
                value=idx,
                font=('Microsoft YaHei', 9),
                bg='#ffffff',
                selectcolor='#ecf0f1',
                activebackground='#ffffff'
            ).pack(anchor='w', pady=2)

        # 3. 站点按钮区域
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(pady=15, padx=15, fill=tk.X)

        sites = [
            ('爱奇艺', '#19c4fa', 'https://www.iqiyi.com'),
            ('腾讯视频', '#0052d9', 'https://v.qq.com'),
            ('优酷视频', '#00a3ef', 'https://www.youku.com')
        ]

        for text, color, url in sites:
            tk.Button(
                button_frame,
                text=text,
                command=lambda u=url: self.open_site(u),
                font=('Microsoft YaHei', 10, 'bold'),
                bg=color,
                fg='white',
                relief=tk.FLAT,
                padx=15,
                pady=5
            ).pack(side=tk.LEFT, padx=(0, 10))

        # 播放按钮
        tk.Button(
            button_frame,
            text='播放VIP视频',
            bg='#e74c3c',
            fg='white',
            font=('Microsoft YaHei', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            command=self.play_vip
        ).pack(side=tk.RIGHT)

        # 4. 提示区
        tip_frame = tk.Frame(main_frame, bg='#fff4e6')
        tip_frame.pack(pady=10, padx=15, fill=tk.X)

        tip = '提示：本工具仅供学习交流使用，请勿用于商业用途。'
        tk.Label(
            tip_frame,
            text=tip,
            fg='#e67e22',
            font=('Microsoft YaHei', 9),
            bg='#fff4e6'
        ).pack(pady=8)

    # ------------------------------------------------------------------
    def clear_entry(self):
        self.url_entry.delete(0, tk.END)

    def open_site(self, url: str):
        webbrowser.open(url)

    def play_vip(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning('提示', '请先粘贴要播放的视频网址！')
            return

        # 简单正则检测 http/https 链接
        if not re.match(r'^https?://.+', url):
            messagebox.showerror('错误', '请输入正确的视频网址！')
            return

        # 解析接口列表
        ports = [
            'https://jx.xyflv.com/?url=',
            'https://jx.jsonplayer.com/player/?url=',
            'https://yparse.ik9.cc/index.php?url=',
            'https://jx.nnxv.cn/tv.php?url=',
            'http://www.wmxz.wang/video.php?url='
        ]

        # 取选中的通道（1~5）
        idx = self.channel.get() - 1
        api = ports[idx]

        webbrowser.open(api + quote_plus(url))


# ----------------------------------------------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = VIPVideoApp(root)
    root.mainloop()