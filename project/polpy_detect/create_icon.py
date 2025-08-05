from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """创建系统图标"""
    # 创建图标目录
    icon_dir = "icon_img"
    os.makedirs(icon_dir, exist_ok=True)
    
    # 创建主图标 (64x64)
    icon_size = 64
    icon = Image.new('RGBA', (icon_size, icon_size), (30, 30, 30, 255))
    draw = ImageDraw.Draw(icon)
    
    # 绘制圆形背景
    margin = 4
    circle_bbox = (margin, margin, icon_size - margin, icon_size - margin)
    draw.ellipse(circle_bbox, fill=(0, 120, 215, 255))  # 蓝色背景
    
    # 绘制医疗十字
    center = icon_size // 2
    cross_width = 8
    cross_length = 20
    
    # 垂直条
    draw.rectangle([center - cross_width//2, center - cross_length//2, 
                   center + cross_width//2, center + cross_length//2], 
                  fill=(255, 255, 255, 255))
    
    # 水平条
    draw.rectangle([center - cross_length//2, center - cross_width//2, 
                   center + cross_length//2, center + cross_width//2], 
                  fill=(255, 255, 255, 255))
    
    # 保存图标
    icon_path = os.path.join(icon_dir, "app_icon.png")
    icon.save(icon_path)
    print(f"主图标已保存到: {icon_path}")
    
    # 创建小图标 (32x32)
    small_icon = icon.resize((32, 32), Image.Resampling.LANCZOS)
    small_icon_path = os.path.join(icon_dir, "app_icon_32.png")
    small_icon.save(small_icon_path)
    print(f"小图标已保存到: {small_icon_path}")
    
    # 创建ICO文件
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    ico_images = []
    
    for size in ico_sizes:
        resized_icon = icon.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized_icon)
    
    ico_path = os.path.join(icon_dir, "app_icon.ico")
    ico_images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in ico_images])
    print(f"ICO图标已保存到: {ico_path}")
    
    return icon_path

def create_button_icons():
    """创建按钮图标"""
    icon_dir = "icon_img"
    os.makedirs(icon_dir, exist_ok=True)
    
    # 按钮图标尺寸
    btn_size = 24
    
    # 创建各种按钮图标
    icons = {
        "settings": create_settings_icon(btn_size),
        "file": create_file_icon(btn_size),
        "camera": create_camera_icon(btn_size),
        "play": create_play_icon(btn_size),
        "pause": create_pause_icon(btn_size),
        "stop": create_stop_icon(btn_size),
        "save": create_save_icon(btn_size),
        "export": create_export_icon(btn_size),
        "search": create_search_icon(btn_size),
        "user": create_user_icon(btn_size)
    }
    
    # 保存所有图标
    for name, icon in icons.items():
        icon_path = os.path.join(icon_dir, f"{name}_icon.png")
        icon.save(icon_path)
        print(f"{name}图标已保存到: {icon_path}")

def create_settings_icon(size):
    """创建设置图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    center = size // 2
    radius = size // 3
    
    # 绘制齿轮
    draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                 outline=(255, 255, 255, 255), width=2)
    
    # 绘制齿轮齿
    for i in range(8):
        angle = i * 45
        x1 = center + int((radius + 3) * 0.7 * (angle % 90 == 0))
        y1 = center + int((radius + 3) * 0.7 * (angle % 90 != 0))
        x2 = center + int((radius - 3) * 0.7 * (angle % 90 == 0))
        y2 = center + int((radius - 3) * 0.7 * (angle % 90 != 0))
        draw.line([x1, y1, x2, y2], fill=(255, 255, 255, 255), width=2)
    
    return icon

def create_file_icon(size):
    """创建文件图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制文件夹
    points = [(2, 6), (6, 2), (size-2, 2), (size-2, size-2), (2, size-2)]
    draw.polygon(points, fill=(255, 255, 255, 255))
    
    return icon

def create_camera_icon(size):
    """创建摄像头图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制摄像头主体
    draw.rectangle([4, 6, size-4, size-6], fill=(255, 255, 255, 255))
    
    # 绘制镜头
    center = size // 2
    lens_radius = size // 6
    draw.ellipse([center - lens_radius, center - lens_radius, 
                  center + lens_radius, center + lens_radius], 
                 fill=(100, 100, 100, 255))
    
    return icon

def create_play_icon(size):
    """创建播放图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制三角形
    points = [(6, 4), (6, size-4), (size-4, size//2)]
    draw.polygon(points, fill=(255, 255, 255, 255))
    
    return icon

def create_pause_icon(size):
    """创建暂停图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制两个竖条
    bar_width = 3
    gap = 2
    center = size // 2
    
    draw.rectangle([center - gap//2 - bar_width, 4, 
                   center - gap//2, size-4], fill=(255, 255, 255, 255))
    draw.rectangle([center + gap//2, 4, 
                   center + gap//2 + bar_width, size-4], fill=(255, 255, 255, 255))
    
    return icon

def create_stop_icon(size):
    """创建停止图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制正方形
    margin = 4
    draw.rectangle([margin, margin, size-margin, size-margin], fill=(255, 255, 255, 255))
    
    return icon

def create_save_icon(size):
    """创建保存图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制软盘
    draw.rectangle([2, 2, size-2, size-2], fill=(255, 255, 255, 255))
    draw.rectangle([4, 4, size-4, size//2], fill=(100, 100, 100, 255))
    
    return icon

def create_export_icon(size):
    """创建导出图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制文档
    draw.rectangle([2, 2, size-2, size-2], fill=(255, 255, 255, 255))
    
    # 绘制箭头
    center = size // 2
    draw.polygon([(center-4, 6), (center+4, 6), (center, 2)], fill=(100, 100, 100, 255))
    
    return icon

def create_search_icon(size):
    """创建搜索图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制放大镜
    center = size // 2
    radius = size // 3
    draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                 outline=(255, 255, 255, 255), width=2)
    
    # 绘制手柄
    draw.line([center + radius - 2, center + radius - 2, size-2, size-2], 
              fill=(255, 255, 255, 255), width=2)
    
    return icon

def create_user_icon(size):
    """创建用户图标"""
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    center = size // 2
    head_radius = size // 4
    
    # 绘制头部
    draw.ellipse([center - head_radius, center - head_radius, 
                  center + head_radius, center + head_radius], 
                 fill=(255, 255, 255, 255))
    
    # 绘制身体
    body_width = size // 3
    body_height = size // 2
    draw.rectangle([center - body_width//2, center + head_radius, 
                   center + body_width//2, center + head_radius + body_height], 
                  fill=(255, 255, 255, 255))
    
    return icon

if __name__ == "__main__":
    print("正在创建图标...")
    create_icon()
    create_button_icons()
    print("所有图标创建完成！") 