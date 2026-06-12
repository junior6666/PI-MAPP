import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = r"C:\Windows\Fonts"

FONT_MAP = {
    "微软雅黑": ["msyh.ttc", "msyhbd.ttc"],
    "黑体": ["simhei.ttf"],
    "宋体": ["simsun.ttc"],
    "楷体": ["simkai.ttf"],
    "仿宋": ["simfang.ttf"],
}


class TextOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量图片添加汉字标题（Italic / 阴影 / 备份）")

        self.folder_path = tk.StringVar()
        self.text = tk.StringVar(value="示例标题")
        self.font_name = tk.StringVar(value="黑体")
        self.font_size = tk.IntVar(value=48)
        self.italic = tk.BooleanVar(value=False)
        self.font_color = tk.StringVar(value="#FFFFFF")
        self.shadow = tk.BooleanVar(value=False)
        self.shadow_color = tk.StringVar(value="#000000")
        self.shadow_x = tk.IntVar(value=2)
        self.shadow_y = tk.IntVar(value=2)
        self.pos_x = tk.IntVar(value=120)
        self.pos_y = tk.IntVar(value=120)

        self.build_ui()

    def build_ui(self):
        f = tk.Frame(self.root, padx=14, pady=14)
        f.pack(fill="both", expand=True)

        # ===== 文件 =====
        tk.Label(f, text="图片目录").grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.folder_path, width=42).grid(row=0, column=1, padx=5)
        tk.Button(f, text="选择", command=self.select_folder).grid(row=0, column=2)

        # ===== 文字 =====
        tk.Label(f, text="标题文字").grid(row=1, column=0, sticky="w", pady=(10, 2))
        tk.Entry(f, textvariable=self.text, width=42).grid(row=1, column=1, columnspan=2, pady=(10, 2))

        # ===== 字体设置 =====
        tk.Label(f, text="字体").grid(row=2, column=0, sticky="w")
        tk.OptionMenu(f, self.font_name, *FONT_MAP.keys()).grid(row=2, column=1, sticky="w")

        tk.Label(f, text="字号").grid(row=3, column=0, sticky="w")
        tk.Spinbox(f, from_=10, to=300, textvariable=self.font_size, width=10).grid(row=3, column=1, sticky="w")

        tk.Checkbutton(f, text="斜体（Italic）", variable=self.italic).grid(row=4, column=1, sticky="w")

        tk.Label(f, text="字体颜色").grid(row=5, column=0, sticky="w")
        tk.Entry(f, textvariable=self.font_color, width=12).grid(row=5, column=1, sticky="w")

        # ===== 阴影 =====
        tk.Checkbutton(f, text="启用阴影", variable=self.shadow).grid(row=6, column=1, sticky="w", pady=(10, 0))

        tk.Label(f, text="阴影颜色").grid(row=7, column=0, sticky="w")
        tk.Entry(f, textvariable=self.shadow_color, width=12).grid(row=7, column=1, sticky="w")

        tk.Label(f, text="阴影偏移 X").grid(row=8, column=0, sticky="w")
        tk.Entry(f, textvariable=self.shadow_x, width=6).grid(row=8, column=1, sticky="w")

        tk.Label(f, text="阴影偏移 Y").grid(row=9, column=0, sticky="w")
        tk.Entry(f, textvariable=self.shadow_y, width=6).grid(row=9, column=1, sticky="w")

        # ===== 位置 =====
        tk.Label(f, text="X 坐标").grid(row=10, column=0, sticky="w", pady=(10, 0))
        tk.Entry(f, textvariable=self.pos_x, width=8).grid(row=10, column=1, sticky="w")

        tk.Label(f, text="Y 坐标").grid(row=11, column=0, sticky="w")
        tk.Entry(f, textvariable=self.pos_y, width=8).grid(row=11, column=1, sticky="w")

        # ===== 操作 =====
        tk.Button(f, text="预览单张", command=self.preview_single).grid(row=12, column=1, pady=12, sticky="w")
        tk.Button(f, text="批量处理", command=self.batch_process).grid(row=12, column=2, pady=12)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)

    def get_font(self):
        fonts = FONT_MAP[self.font_name.get()]
        font_path = os.path.join(FONT_DIR, fonts[0])

        # 尝试加载 Italic
        if self.italic.get() and len(fonts) > 1:
            italic_path = os.path.join(FONT_DIR, fonts[1])
            if os.path.exists(italic_path):
                return ImageFont.truetype(italic_path, self.font_size.get())

        return ImageFont.truetype(font_path, self.font_size.get())

    def draw_text(self, image_path):
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        font = self.get_font()
        x, y = self.pos_x.get(), self.pos_y.get()

        # 阴影
        if self.shadow.get():
            sx = x + self.shadow_x.get()
            sy = y + self.shadow_y.get()
            draw.text((sx, sy), self.text.get(), fill=self.shadow_color.get(), font=font)

        # 主文字
        draw.text((x, y), self.text.get(), fill=self.font_color.get(), font=font)
        return img

    def backup_and_process(self, image_path):
        base, ext = os.path.splitext(image_path)
        backup_path = f"{base}.bak{ext}"

        if not os.path.exists(backup_path):
            Image.open(image_path).save(backup_path)

        img = self.draw_text(image_path)
        img.save(image_path)

    def preview_single(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("提示", "请先选择图片目录")
            return

        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                img = self.draw_text(os.path.join(folder, f))
                img.show()
                break

    def batch_process(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("提示", "请先选择图片目录")
            return

        count = 0
        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(folder, f)
                self.backup_and_process(full_path)
                count += 1

        messagebox.showinfo("完成", f"共处理 {count} 张图片\n原图已备份为 .bak 文件")


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    TextOverlayApp(root)
    root.mainloop()