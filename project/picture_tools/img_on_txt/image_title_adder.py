import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import glob

class ImageTitleAdder:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量加标题工具 - 支持拖拽定位")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 750)

        # 数据存储
        self.image_paths = []
        self.current_image = None
        self.preview_photo = None
        self.current_index = 0

        # 标题设置
        self.title_settings = {
            'text': '示例标题',
            'font_size': 40,
            'font_color': '#FFFFFF',
            'opacity': 255,
            'position': 'custom',       # custom 表示自定义拖拽位置
            'margin_x': 20,
            'margin_y': 20,
            'font_path': None,
            'custom_x': None,           # 自定义X坐标（相对于图片）
            'custom_y': None,           # 自定义Y坐标（相对于图片）
        }

        # 拖拽状态
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.title_offset_x = 0       # 标题相对于鼠标点击位置的偏移
        self.title_offset_y = 0

        # 预览缩放比例
        self.preview_scale = 1.0
        self.preview_offset_x = 0
        self.preview_offset_y = 0

        # 九宫格位置映射
        self.position_map = {
            'top-left':      ('left',   'top'),
            'top-center':    ('center', 'top'),
            'top-right':     ('right',  'top'),
            'center-left':   ('left',   'center'),
            'center':        ('center', 'center'),
            'center-right':  ('right',  'center'),
            'bottom-left':   ('left',   'bottom'),
            'bottom-center': ('center', 'bottom'),
            'bottom-right':  ('right',  'bottom'),
        }

        self.setup_ui()
        self.load_system_fonts()

    def setup_ui(self):
        # 主框架
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧面板
        left_frame = ttk.Frame(self.paned, width=420)
        self.paned.add(left_frame, weight=1)

        # 右侧预览面板
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        # ==================== 左侧面板内容 ====================
        # 1. 路径选择区域
        path_frame = ttk.LabelFrame(left_frame, text="图片路径", padding=10)
        path_frame.pack(fill=tk.X, padx=5, pady=5)

        self.path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.path_var, state='readonly').pack(fill=tk.X, side=tk.LEFT, expand=True)
        ttk.Button(path_frame, text="浏览文件夹", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="浏览文件", command=self.browse_files).pack(side=tk.LEFT)

        # 图片列表
        list_frame = ttk.LabelFrame(left_frame, text="图片列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_container, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind('<<ListboxSelect>>', self.on_list_select)

        # 2. 标题设置区域
        settings_frame = ttk.LabelFrame(left_frame, text="标题设置", padding=10)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        # 标题文字
        row = 0
        ttk.Label(settings_frame, text="标题文字:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.text_var = tk.StringVar(value=self.title_settings['text'])
        ttk.Entry(settings_frame, textvariable=self.text_var).grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.text_var.trace('w', lambda *args: self.update_preview())

        # 字体大小
        row += 1
        ttk.Label(settings_frame, text="字体大小:").grid(row=row, column=0, sticky=tk.W, pady=3)
        size_frame = ttk.Frame(settings_frame)
        size_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.size_var = tk.IntVar(value=self.title_settings['font_size'])
        ttk.Spinbox(size_frame, from_=10, to=200, textvariable=self.size_var, width=8, command=self.update_preview).pack(side=tk.LEFT)
        self.size_var.trace('w', lambda *args: self.update_preview())
        ttk.Label(size_frame, text="px").pack(side=tk.LEFT, padx=3)

        # 字体颜色
        row += 1
        ttk.Label(settings_frame, text="字体颜色:").grid(row=row, column=0, sticky=tk.W, pady=3)
        color_frame = ttk.Frame(settings_frame)
        color_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.color_var = tk.StringVar(value=self.title_settings['font_color'])
        self.color_btn = tk.Button(color_frame, bg=self.title_settings['font_color'], width=4, height=1, 
                                   command=self.choose_color, relief=tk.RIDGE)
        self.color_btn.pack(side=tk.LEFT)
        ttk.Label(color_frame, textvariable=self.color_var).pack(side=tk.LEFT, padx=5)

        # 透明度
        row += 1
        ttk.Label(settings_frame, text="透明度:").grid(row=row, column=0, sticky=tk.W, pady=3)
        opacity_frame = ttk.Frame(settings_frame)
        opacity_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.opacity_var = tk.IntVar(value=self.title_settings['opacity'])
        ttk.Scale(opacity_frame, from_=0, to=255, variable=self.opacity_var, orient=tk.HORIZONTAL, 
                  length=150, command=lambda v: self.on_opacity_change(v)).pack(side=tk.LEFT)
        self.opacity_label = ttk.Label(opacity_frame, text="255")
        self.opacity_label.pack(side=tk.LEFT, padx=5)

        # 位置选择（九宫格 + 自定义拖拽）
        row += 1
        ttk.Label(settings_frame, text="标题位置:").grid(row=row, column=0, sticky=tk.W, pady=3)
        pos_frame = ttk.Frame(settings_frame)
        pos_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)

        self.position_var = tk.StringVar(value=self.title_settings['position'])
        positions = [
            ('top-left', '左上'), ('top-center', '中上'), ('top-right', '右上'),
            ('center-left', '左中'), ('center', '正中'), ('center-right', '右中'),
            ('bottom-left', '左下'), ('bottom-center', '中下'), ('bottom-right', '右下'),
        ]

        pos_grid = ttk.Frame(pos_frame)
        pos_grid.pack()
        for i, (val, text) in enumerate(positions):
            r, c = divmod(i, 3)
            ttk.Radiobutton(pos_grid, text=text, variable=self.position_var, value=val,
                          command=self.on_position_change).grid(row=r, column=c, padx=2, pady=2)

        # 自定义位置按钮
        row += 1
        custom_pos_frame = ttk.Frame(settings_frame)
        custom_pos_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=5)

        self.custom_pos_btn = ttk.Button(custom_pos_frame, text="🖱️ 启用拖拽定位", 
                                         command=self.enable_drag_mode)
        self.custom_pos_btn.pack(side=tk.LEFT, padx=2)

        ttk.Button(custom_pos_frame, text="📍 重置到中心", 
                   command=self.reset_to_center).pack(side=tk.LEFT, padx=2)

        # 显示当前坐标
        self.coord_var = tk.StringVar(value="坐标: 自动")
        ttk.Label(custom_pos_frame, textvariable=self.coord_var).pack(side=tk.LEFT, padx=10)

        # 边距设置
        row += 1
        ttk.Label(settings_frame, text="水平边距:").grid(row=row, column=0, sticky=tk.W, pady=3)
        margin_x_frame = ttk.Frame(settings_frame)
        margin_x_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.margin_x_var = tk.IntVar(value=self.title_settings['margin_x'])
        ttk.Spinbox(margin_x_frame, from_=0, to=500, textvariable=self.margin_x_var, width=8, command=self.update_preview).pack(side=tk.LEFT)
        self.margin_x_var.trace('w', lambda *args: self.update_preview())
        ttk.Label(margin_x_frame, text="px").pack(side=tk.LEFT, padx=3)

        row += 1
        ttk.Label(settings_frame, text="垂直边距:").grid(row=row, column=0, sticky=tk.W, pady=3)
        margin_y_frame = ttk.Frame(settings_frame)
        margin_y_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.margin_y_var = tk.IntVar(value=self.title_settings['margin_y'])
        ttk.Spinbox(margin_y_frame, from_=0, to=500, textvariable=self.margin_y_var, width=8, command=self.update_preview).pack(side=tk.LEFT)
        self.margin_y_var.trace('w', lambda *args: self.update_preview())
        ttk.Label(margin_y_frame, text="px").pack(side=tk.LEFT, padx=3)

        # 自定义字体
        row += 1
        ttk.Label(settings_frame, text="自定义字体:").grid(row=row, column=0, sticky=tk.W, pady=3)
        font_frame = ttk.Frame(settings_frame)
        font_frame.grid(row=row, column=1, sticky=tk.EW, pady=3)
        self.font_path_var = tk.StringVar()
        ttk.Entry(font_frame, textvariable=self.font_path_var, state='readonly', width=20).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(font_frame, text="浏览", command=self.browse_font).pack(side=tk.LEFT, padx=2)
        ttk.Button(font_frame, text="清除", command=self.clear_font).pack(side=tk.LEFT)

        # 操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(btn_frame, text="应用到当前", command=self.apply_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="批量处理全部", command=self.batch_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="保存当前预览", command=self.save_current_preview).pack(side=tk.LEFT, padx=2)

        # 进度条
        self.progress = ttk.Progressbar(left_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        self.status_var = tk.StringVar(value="就绪 - 请先选择图片文件夹或文件")
        ttk.Label(left_frame, textvariable=self.status_var).pack(anchor=tk.W, padx=5)

        settings_frame.columnconfigure(1, weight=1)

        # ==================== 右侧预览区域 ====================
        preview_frame = ttk.LabelFrame(right_frame, text="实时预览 (可拖拽标题调整位置)", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas_container = ttk.Frame(preview_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_container, bg='#2e2e2e', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(fill=tk.X)

        self.canvas.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # 绑定拖拽事件
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # 导航按钮
        nav_frame = ttk.Frame(preview_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        ttk.Button(nav_frame, text="◀ 上一张", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(nav_frame, text="0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(nav_frame, text="下一张 ▶", command=self.next_image).pack(side=tk.LEFT, padx=5)

        # 拖拽提示
        self.drag_hint = ttk.Label(nav_frame, text="", foreground="gray")
        self.drag_hint.pack(side=tk.RIGHT, padx=10)

    def load_system_fonts(self):
        """尝试加载系统中文字体"""
        possible_fonts = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simkai.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]

        for fpath in possible_fonts:
            if os.path.exists(fpath):
                self.title_settings['font_path'] = fpath
                break

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
            patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp']
            self.image_paths = []
            for pattern in patterns:
                self.image_paths.extend(glob.glob(os.path.join(folder, pattern)))
                self.image_paths.extend(glob.glob(os.path.join(folder, pattern.upper())))

            self.image_paths = sorted(list(set(self.image_paths)))
            self.refresh_list()

    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.image_paths = list(files)
            self.path_var.set(os.path.dirname(self.image_paths[0]) if self.image_paths else "")
            self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for path in self.image_paths:
            self.listbox.insert(tk.END, os.path.basename(path))

        self.status_var.set(f"共 {len(self.image_paths)} 张图片")
        self.page_label.config(text=f"0 / {len(self.image_paths)}")

        if self.image_paths:
            self.current_index = 0
            self.listbox.selection_set(0)
            self.load_image(0)

    def on_list_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.load_image(self.current_index)

    def load_image(self, index):
        if not self.image_paths or index < 0 or index >= len(self.image_paths):
            return

        try:
            self.current_image = Image.open(self.image_paths[index])
            if self.current_image.mode != 'RGB':
                self.current_image = self.current_image.convert('RGB')
            self.page_label.config(text=f"{index + 1} / {len(self.image_paths)}")

            # 重置自定义坐标
            if self.title_settings['custom_x'] is None:
                self.reset_to_center()

            self.update_preview()
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")

    # ==================== 拖拽功能 ====================
    def enable_drag_mode(self):
        """启用拖拽定位模式"""
        self.position_var.set('custom')
        self.custom_pos_btn.config(text="✅ 拖拽模式已启用")
        self.drag_hint.config(text="🖱️ 在预览区拖拽标题调整位置")
        self.status_var.set("拖拽模式已启用 - 请在预览区拖拽标题")
        self.update_preview()

    def on_position_change(self):
        """位置选择改变时"""
        pos = self.position_var.get()
        if pos != 'custom':
            self.custom_pos_btn.config(text="🖱️ 启用拖拽定位")
            self.drag_hint.config(text="")
            self.coord_var.set("坐标: 自动")
        self.update_preview()

    def reset_to_center(self):
        """重置标题到图片中心"""
        if self.current_image is None:
            return
        w, h = self.current_image.size
        self.title_settings['custom_x'] = w // 2
        self.title_settings['custom_y'] = h // 2
        self.position_var.set('custom')
        self.custom_pos_btn.config(text="✅ 拖拽模式已启用")
        self.coord_var.set(f"坐标: ({self.title_settings['custom_x']}, {self.title_settings['custom_y']})")
        self.update_preview()

    def on_drag_start(self, event):
        """开始拖拽"""
        if self.current_image is None:
            return
        if self.position_var.get() != 'custom':
            return

        # 检查是否点击在标题区域内
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # 获取标题在canvas上的位置
        title_x, title_y, title_w, title_h = self.get_title_canvas_rect()

        if title_x <= canvas_x <= title_x + title_w and title_y <= canvas_y <= title_y + title_h:
            self.dragging = True
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.title_offset_x = canvas_x - title_x
            self.title_offset_y = canvas_y - title_y
            self.canvas.config(cursor="fleur")
            self.drag_hint.config(text="🖐️ 拖拽中...")

    def on_drag_move(self, event):
        """拖拽中"""
        if not self.dragging or self.current_image is None:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # 计算新的图片坐标
        new_canvas_x = canvas_x - self.title_offset_x
        new_canvas_y = canvas_y - self.title_offset_y

        # 转换回图片坐标
        img_x = int((new_canvas_x - self.preview_offset_x) / self.preview_scale)
        img_y = int((new_canvas_y - self.preview_offset_y) / self.preview_scale)

        # 边界限制
        img_w, img_h = self.current_image.size
        text_w, text_h = self.get_text_size()

        img_x = max(0, min(img_x, img_w - text_w))
        img_y = max(0, min(img_y, img_h - text_h))

        self.title_settings['custom_x'] = img_x
        self.title_settings['custom_y'] = img_y
        self.coord_var.set(f"坐标: ({img_x}, {img_y})")

        self.update_preview()

    def on_drag_end(self, event):
        """结束拖拽"""
        if self.dragging:
            self.dragging = False
            self.canvas.config(cursor="")
            self.drag_hint.config(text="🖱️ 在预览区拖拽标题调整位置")

    def on_mouse_move(self, event):
        """鼠标移动时改变光标"""
        if self.current_image is None or self.position_var.get() != 'custom':
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        title_x, title_y, title_w, title_h = self.get_title_canvas_rect()

        if title_x <= canvas_x <= title_x + title_w and title_y <= canvas_y <= title_y + title_h:
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="")

    def get_text_size(self):
        """获取文字尺寸"""
        text = self.text_var.get() or " "
        font_size = int(self.size_var.get())
        font = self.get_font(font_size)

        # 创建临时图像计算尺寸
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        return text_w, text_h

    def get_title_canvas_rect(self):
        """获取标题在canvas上的矩形区域"""
        if self.current_image is None:
            return 0, 0, 0, 0

        text_w, text_h = self.get_text_size()

        if self.position_var.get() == 'custom' and self.title_settings['custom_x'] is not None:
            img_x = self.title_settings['custom_x']
            img_y = self.title_settings['custom_y']
        else:
            img_w, img_h = self.current_image.size
            position = self.position_var.get()
            x_align, y_align = self.position_map.get(position, ('center', 'bottom'))
            margin_x = int(self.margin_x_var.get() or 0)
            margin_y = int(self.margin_y_var.get() or 0)

            if x_align == 'left':
                img_x = margin_x
            elif x_align == 'center':
                img_x = (img_w - text_w) // 2
            else:
                img_x = img_w - text_w - margin_x

            if y_align == 'top':
                img_y = margin_y
            elif y_align == 'center':
                img_y = (img_h - text_h) // 2
            else:
                img_y = img_h - text_h - margin_y

        # 转换到canvas坐标
        canvas_x = self.preview_offset_x + img_x * self.preview_scale
        canvas_y = self.preview_offset_y + img_y * self.preview_scale
        canvas_w = text_w * self.preview_scale
        canvas_h = text_h * self.preview_scale

        return canvas_x, canvas_y, canvas_w, canvas_h

    def update_preview(self):
        if self.current_image is None:
            return

        text = self.text_var.get()
        if not text:
            text = " "

        preview = self.add_title_to_image(self.current_image.copy(), text, preview_mode=True)

        canvas_w = self.canvas.winfo_width() or 800
        canvas_h = self.canvas.winfo_height() or 600

        img_w, img_h = preview.size
        self.preview_scale = min((canvas_w - 40) / img_w, (canvas_h - 40) / img_h, 1.0)

        if self.preview_scale < 1.0:
            new_w = int(img_w * self.preview_scale)
            new_h = int(img_h * self.preview_scale)
            preview = preview.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            new_w = img_w
            new_h = img_h

        self.preview_offset_x = max((canvas_w - new_w) // 2, 0)
        self.preview_offset_y = max((canvas_h - new_h) // 2, 0)

        self.preview_photo = ImageTk.PhotoImage(preview)

        self.canvas.delete("all")
        self.canvas.create_image(self.preview_offset_x, self.preview_offset_y, 
                                anchor=tk.NW, image=self.preview_photo)

        # 如果是自定义位置模式，绘制标题边框提示
        if self.position_var.get() == 'custom':
            title_x, title_y, title_w, title_h = self.get_title_canvas_rect()
            # 绘制虚线边框
            self.canvas.create_rectangle(
                title_x, title_y, title_x + title_w, title_y + title_h,
                outline="#00FF00", dash=(4, 2), width=2, tags="title_border"
            )
            # 绘制四角标记
            marker_size = 6
            for mx, my in [(title_x, title_y), (title_x + title_w, title_y),
                          (title_x, title_y + title_h), (title_x + title_w, title_y + title_h)]:
                self.canvas.create_oval(mx - marker_size, my - marker_size, 
                                       mx + marker_size, my + marker_size,
                                       fill="#00FF00", outline="", tags="title_border")

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_font(self, size):
        """获取字体对象"""
        font_path = self.font_path_var.get() or self.title_settings['font_path']

        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                pass

        fallback_fonts = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]

        for fpath in fallback_fonts:
            if os.path.exists(fpath):
                try:
                    return ImageFont.truetype(fpath, size)
                except:
                    continue

        return ImageFont.load_default()

    def add_title_to_image(self, image, text, preview_mode=False):
        """给图片添加标题"""
        img = image.copy().convert('RGBA')
        width, height = img.size

        text_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)

        font_size = int(self.size_var.get())
        color = self.color_var.get()
        opacity = int(self.opacity_var.get())
        position = self.position_var.get()
        margin_x = int(self.margin_x_var.get() or 0)
        margin_y = int(self.margin_y_var.get() or 0)

        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except:
            r, g, b = 255, 255, 255

        font = self.get_font(font_size)

        # 计算文字尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 计算位置
        if position == 'custom' and self.title_settings['custom_x'] is not None:
            x = self.title_settings['custom_x']
            y = self.title_settings['custom_y']
        else:
            x_align, y_align = self.position_map.get(position, ('center', 'bottom'))

            if x_align == 'left':
                x = margin_x
            elif x_align == 'center':
                x = (width - text_w) // 2
            else:
                x = width - text_w - margin_x

            if y_align == 'top':
                y = margin_y
            elif y_align == 'center':
                y = (height - text_h) // 2
            else:
                y = height - text_h - margin_y

        x = max(0, min(x, width - text_w))
        y = max(0, min(y, height - text_h))

        draw.text((x, y), text, fill=(r, g, b, opacity), font=font)

        result = Image.alpha_composite(img, text_layer)
        return result.convert('RGB')

    def on_opacity_change(self, value):
        self.opacity_label.config(text=str(int(float(value))))
        self.update_preview()

    def choose_color(self):
        color = colorchooser.askcolor(color=self.color_var.get(), title="选择字体颜色")
        if color[1]:
            self.color_var.set(color[1])
            self.color_btn.config(bg=color[1])
            self.update_preview()

    def browse_font(self):
        font_path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("字体文件", "*.ttf *.ttc *.otf"), ("所有文件", "*.*")]
        )
        if font_path:
            self.font_path_var.set(font_path)
            self.update_preview()

    def clear_font(self):
        self.font_path_var.set("")
        self.update_preview()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.load_image(self.current_index)

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.load_image(self.current_index)

    def apply_current(self):
        if not self.image_paths or self.current_index >= len(self.image_paths):
            messagebox.showwarning("警告", "请先选择图片")
            return

        path = self.image_paths[self.current_index]
        output_path = self.process_single_image(path)
        messagebox.showinfo("完成", f"已保存到:\n{output_path}")

    def batch_process(self):
        if not self.image_paths:
            messagebox.showwarning("警告", "请先选择图片")
            return

        if not messagebox.askyesno("确认", f"将对 {len(self.image_paths)} 张图片添加标题并保存到原目录，是否继续？"):
            return

        self.progress['maximum'] = len(self.image_paths)
        self.progress['value'] = 0

        success = 0
        failed = 0
        failed_list = []

        for i, path in enumerate(self.image_paths):
            try:
                self.process_single_image(path)
                success += 1
            except Exception as e:
                failed += 1
                failed_list.append(f"{os.path.basename(path)}: {str(e)}")

            self.progress['value'] = i + 1
            self.status_var.set(f"处理中... {i+1}/{len(self.image_paths)}")
            self.root.update_idletasks()

        self.status_var.set(f"完成！成功: {success}, 失败: {failed}")

        msg = f"批量处理完成！\n成功: {success} 张\n失败: {failed} 张"
        if failed_list:
            msg += "\n\n失败详情:\n" + "\n".join(failed_list[:5])
            if len(failed_list) > 5:
                msg += f"\n... 等共 {len(failed_list)} 个失败"
        messagebox.showinfo("完成", msg)

    def process_single_image(self, path):
        """处理单张图片，返回输出路径"""
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        text = self.text_var.get()
        if not text:
            text = " "

        result = self.add_title_to_image(img, text)

        dir_name = os.path.dirname(path)
        base_name = os.path.basename(path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_titled{ext}")

        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(dir_name, f"{name}_titled_{counter}{ext}")
            counter += 1

        if ext.lower() in ['.jpg', '.jpeg']:
            result.save(output_path, 'JPEG', quality=95)
        elif ext.lower() == '.png':
            result.save(output_path, 'PNG')
        else:
            result.save(output_path)

        return output_path

    def save_current_preview(self):
        if self.current_image is None:
            messagebox.showwarning("警告", "没有可保存的预览")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("所有文件", "*.*")]
        )
        if path:
            text = self.text_var.get() or " "
            result = self.add_title_to_image(self.current_image, text)
            result.save(path)
            messagebox.showinfo("完成", f"已保存到: {path}")


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = ImageTitleAdder(root)
    root.mainloop()


if __name__ == "__main__":
    main()
