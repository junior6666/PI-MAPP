# generate_icon.py
# 独立运行，生成 icon.ico 文件（64x64，黑灰风格，文字 DC）

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt
import sys


def create_dc_icon(output_path="icon.ico", size=64):
    # 必须初始化 GUI 应用（即使是非窗口用途）
    app = QApplication(sys.argv)  # 仅初始化一次

    # 创建透明背景的 pixmap
    pixmap = QPixmap(size, size)
    bg_color = QColor(40, 40, 40)  # 深灰背景
    text_color = QColor(200, 200, 200)  # 浅灰文字

    pixmap.fill(bg_color)

    # 使用 QPainter 绘制文字
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(text_color)

    # 设置字体（无衬线、加粗）
    font = QFont("Arial", 32, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "DC")
    painter.end()

    # 保存为 ICO 文件（支持多尺寸，但这里只存 64x64）
    success = pixmap.save(output_path, "ICO")
    if success:
        print(f"✅ 图标已保存：{output_path}")
    else:
        print(f"❌ 图标保存失败：{output_path}")

    return success


if __name__ == "__main__":
    create_dc_icon("icon.ico", 64)