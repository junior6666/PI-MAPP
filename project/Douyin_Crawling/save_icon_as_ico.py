
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QLinearGradient, QBrush,
    QPen, QPainterPath
)
from PySide6.QtCore import Qt, QPoint, QRectF
import sys


class IconGenerator:
    """
    用于生成单色或渐变背景、圆角正方形、中央文字的图标。

    参数
    ----
    bg_color: QColor | tuple[int,int,int]
        背景主色，默认 (40,40,40)
    text_color: QColor | tuple[int,int,int]
        文字颜色，默认 (200,200,200)
    text: str
        中央文字，默认 "DC"
    enable_gradient: bool
        是否使用线性渐变（黑→深灰），默认 False
    size: int
        图标宽高，默认 64
    font_size: int
        文字字号，默认 24
    corner_radius: int | float
        圆角半径，默认 10
    """

    def __init__(
        self,
        bg_color=(40, 40, 40),
        text_color=(200, 200, 200),
        text="DC",
        enable_gradient=False,
        size=64,
        font_size=24,
        corner_radius=10,
    ):
        # 统一转为 QColor
        self.bg_color = self._to_qcolor(bg_color)
        self.text_color = self._to_qcolor(text_color)
        self.text = text
        self.enable_gradient = enable_gradient
        self.size = size
        self.font_size = font_size
        self.corner_radius = corner_radius

        # 初始化 Qt 应用（保证只初始化一次）
        if QApplication.instance() is None:
            self._app = QApplication(sys.argv)
        else:
            self._app = QApplication.instance()

    # ----------------- 公有方法 -----------------

    def create_icon(self, output_path: str = "icon.ico") -> bool:
        """
        根据当前属性生成 .ico 文件并返回是否成功。
        """
        pixmap = self._render_pixmap()
        ok = pixmap.save(output_path, "ICO")
        print("✅ 图标已保存：" + output_path if ok else "❌ 图标保存失败：" + output_path)
        return ok

    def pixmap(self) -> QPixmap:
        """
        返回渲染后的 QPixmap，便于在内存中直接使用（如设置窗口图标等）。
        """
        return self._render_pixmap()

    # ----------------- 私有方法 -----------------

    @staticmethod
    def _to_qcolor(color) -> QColor:
        if isinstance(color, QColor):
            return color
        if isinstance(color, (tuple, list)) and len(color) == 3:
            return QColor(*color)
        raise ValueError("颜色参数必须是 QColor 或 (r,g,b) 元组/列表")

    def _render_pixmap(self) -> QPixmap:
        """真正执行绘制逻辑"""
        size = self.size
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)  # 先整体透明

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景（纯色或渐变）
        rect = QRectF(0, 0, size, size)
        if self.enable_gradient:
            gradient = QLinearGradient(QPoint(0, 0), QPoint(0, size))
            gradient.setColorAt(0, self.bg_color)
            gradient.setColorAt(1, QColor(0, 0, 0))
            brush = QBrush(gradient)
        else:
            brush = QBrush(self.bg_color)

        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)  # 无边框
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)

        # 文字
        painter.setPen(QPen(self.text_color))
        font = QFont("Arial", self.font_size, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text)

        painter.end()
        return pixmap


if __name__ == "__main__":
    icon_pixmap = IconGenerator(
        bg_color=(30, 60, 120),
        text_color=(230, 255, 255),
        text="Dc",
        enable_gradient=True,
        size=128,
        font_size=48,
        corner_radius=20,
    ).create_icon("icon.ico")
