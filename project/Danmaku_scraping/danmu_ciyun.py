import requests
import xml.etree.ElementTree as ET
from typing import List, Tuple
import re
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QCursor
from PySide6.QtCore import Qt, QRect, QPoint, QSize

import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                               QFileDialog, QMessageBox, QLabel, QGridLayout, QGroupBox, QStatusBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QIcon

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple


class BilibiliDanmuCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def parse_url(self, url: str) -> str:
        """从URL中提取oid"""
        if 'oid=' in url:
            return url.split('oid=')[1].split('&')[0]
        return url

    def fetch_danmu(self, url: str) -> List[Dict[str, any]]:
        """获取弹幕数据（返回包含完整信息的字典列表）"""
        oid = self.parse_url(url)
        api_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={oid}"

        try:
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'

            # 解析XML
            root = ET.fromstring(response.text)
            danmu_list = []

            for d in root.findall('.//d'):
                if d.text:
                    # 提取所有属性
                    p_attrs = d.get('p', '').split(',')
                    if len(p_attrs) >= 8:  # 确保有足够字段
                        danmu = {
                            'time': float(p_attrs[0]),  # 出现时间（秒）
                            'mode': int(p_attrs[1]),  # 弹幕类型
                            'font_size': int(p_attrs[2]),  # 字体大小
                            'color': int(p_attrs[3]),  # 颜色值（十进制）
                            'timestamp': int(p_attrs[4]),  # 发送时间戳
                            'pool': int(p_attrs[5]),  # 弹幕池
                            'uid_crc': p_attrs[6],  # 用户ID CRC32
                            'dmid': int(p_attrs[7]),  # 弹幕ID
                            'text': d.text.strip()  # 弹幕内容
                        }
                        danmu_list.append(danmu)

            return danmu_list

        except Exception as e:
            print(f"获取弹幕失败: {str(e)}")
            return []

    def save_to_txt(self, danmu_list: List[Dict[str, any]], filename: str):
        """保存弹幕到txt文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            for dm in danmu_list:
                f.write(f"{dm['text']}\n")

    def save_to_ass(self, danmu_list: List[Dict[str, any]], filename: str,
                    video_width: int = 1920, video_height: int = 1080,
                    duration: float = 8.0):
        """
        保存弹幕为ASS字幕文件
        :param danmu_list: 弹幕数据列表
        :param filename: 输出文件名
        :param video_width: 视频宽度（像素）
        :param video_height: 视频高度（像素）
        :param duration: 弹幕显示持续时间（秒）
        """
        # ASS文件头部模板
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopStyle,Microsoft YaHei,36,&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
Style: ScrollStyle,Microsoft YaHei,36,&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,8,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(ass_header)

            for dm in danmu_list:
                # 转换时间为ASS格式 (时:分:秒.百分秒)
                start_time = self._seconds_to_ass_time(dm['time'])
                end_time = self._seconds_to_ass_time(dm['time'] + duration)

                # 转换颜色为ASS格式 (BBGGRR)
                color_str = self._color_to_ass(dm['color'])

                # 转义特殊字符
                text = self._escape_ass_text(dm['text'])

                # 根据弹幕类型生成不同样式
                if dm['mode'] == 5:  # 顶部弹幕
                    # 居中显示在顶部
                    f.write(f"Dialogue: 0,{start_time},{end_time},TopStyle,,0,0,0,,"
                            f"{{\\an8\\pos({video_width // 2},50)\\c{color_str}}}{text}\\N\n")

                else:  # 滚动弹幕（默认模式1）
                    # 从右向左滚动（底部区域）
                    f.write(f"Dialogue: 0,{start_time},{end_time},ScrollStyle,,0,0,0,,"
                            f"{{\\move({video_width},{video_height - 50},-1000,{video_height - 50})\\c{color_str}}}{text}\\N\n")

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """将秒数转换为ASS时间格式 (H:MM:SS.CS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:06.3f}"  # 保留3位毫秒

    def _color_to_ass(self, color_int: int) -> str:
        """将十进制颜色值转换为ASS格式 (BBGGRR)"""
        blue = color_int & 0xFF
        green = (color_int >> 8) & 0xFF
        red = (color_int >> 16) & 0xFF
        return f"&H{blue:02X}{green:02X}{red:02X}&"

    def _escape_ass_text(self, text: str) -> str:
        """转义ASS特殊字符"""
        # 替换特殊字符（保持简单处理）
        return text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}').replace('\n', ' ')


import re
import jieba
import numpy as np
from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator
from matplotlib import pyplot as plt


class WordCloudGenerator:
    def __init__(self, font_path="msyh.ttc", mask_path=None):
        """
        初始化词云生成器
        :param font_path: 字体文件路径
        :param mask_path: 形状蒙版图片路径
        """
        self.font_path = font_path
        self.mask = self._load_mask(mask_path) if mask_path else None

    def _load_mask(self, mask_path):
        """加载形状蒙版图片"""
        try:
            mask = np.array(Image.open(mask_path))
            # 转换为二值图像
            mask[mask.sum(axis=2) == 0] = 255  # 透明背景转白色
            return mask
        except Exception as e:
            print(f"加载蒙版失败: {str(e)}")
            return None

    def load_text_from_file(self, filename: str) -> str:
        """从文件加载文本"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return ""

    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 移除时间戳
        text = re.sub(r'\[\d+\.\d+\]\s*', '', text)
        # 保留中文、英文、数字和空格
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        return text.strip()

    def generate_wordcloud(self, text: str, output_path: str = "wordcloud.png"):
        """生成黑字白底的词云图"""
        if not text:
            print("输入文本为空")
            return False

        # 中文分词
        words = jieba.lcut(text)

        # 过滤停用词和短词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很',
                     '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它'}
        words = [word for word in words if len(word) > 1 and word not in stopwords]

        if not words:
            print("有效词汇不足")
            return False

        # 创建词云对象
        wc = WordCloud(
            font_path=self.font_path,
            width=1600,  # 提高分辨率
            height=1200,
            background_color='white',
            max_words=300,  # 增加显示词汇量
            mask=self.mask,
            contour_width=0,
            colormap=None,  # 禁用彩色映射
            color_func=lambda *args, **kwargs: "black"  # 强制使用黑色字体
        )

        # 生成词云
        wc.generate(' '.join(words))

        # 绘制并保存
        plt.figure(figsize=(16, 12), dpi=100)
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)

        # 使用白色背景保存
        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches='tight',
            pad_inches=0,
            facecolor='white'
        )
        plt.close()

        print(f"词云已保存至: {output_path}")
        return True



class CrawlerThread(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.crawler = BilibiliDanmuCrawler()

    def run(self):
        try:
            danmu_list = self.crawler.fetch_danmu(self.url)
            if danmu_list:
                self.finished.emit(danmu_list)
            else:
                self.error.emit("未获取到弹幕数据")
        except Exception as e:
            self.error.emit(str(e))


class BarrageIconGenerator:
    """生成弹幕主题图标的类"""

    @staticmethod
    def generate_icon(size=64):
        """生成弹幕主题的图标"""
        # 创建透明背景的像素图
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        # 创建绘图工具
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建渐变背景
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor("#4A00E0"))  # 深蓝紫色
        gradient.setColorAt(1, QColor("#8E2DE2"))  # 紫色
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, size, size, 15, 15)

        # 绘制弹幕气泡
        bubble_color = QColor(255, 255, 255, 200)
        painter.setBrush(bubble_color)
        painter.setPen(Qt.NoPen)

        # 绘制多个弹幕气泡
        bubbles = [
            (size * 0.2, size * 0.3, size * 0.4, size * 0.15),
            (size * 0.5, size * 0.5, size * 0.3, size * 0.1),
            (size * 0.1, size * 0.7, size * 0.5, size * 0.12),
            (size * 0.3, size * 0.2, size * 0.35, size * 0.1),
            (size * 0.6, size * 0.3, size * 0.25, size * 0.08)
        ]

        for x, y, w, h in bubbles:
            painter.drawRoundedRect(x, y, w, h, h / 2, h / 2)

        # 添加文字"弹"
        font = QFont("Microsoft YaHei", size * 0.3, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "弹")

        painter.end()

        return QIcon(pixmap)






class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.danmu_list = []
        self.init_ui()
        self.apply_styles()  # 添加样式表应用

    def init_ui(self):
        self.preview_window = None  # 用于存储预览窗口实例
        self.setWindowTitle('B站弹幕分析工具')
        self.setGeometry(100, 100, 1100, 750)  # 稍微增大窗口尺寸
        # 生成并设置应用图标
        self.app_icon = BarrageIconGenerator.generate_icon(64)
        self.setWindowIcon(self.app_icon)
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 使用网格布局代替垂直布局，更灵活
        main_layout = QGridLayout()
        central_widget.setLayout(main_layout)
        main_layout.setSpacing(15)  # 增加控件间距
        main_layout.setContentsMargins(20, 15, 20, 15)  # 设置边距

        # URL输入区域 - 使用分组框
        url_group = QGroupBox("弹幕数据源")
        url_layout = QHBoxLayout(url_group)
        url_layout.setContentsMargins(12, 15, 12, 12)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入B站弹幕API URL...")
        self.url_input.setText("https://api.bilibili.com/x/v1/dm/list.so?oid=783037295")
        self.url_input.setMinimumHeight(35)  # 增加输入框高度

        self.fetch_btn = QPushButton("获取弹幕")
        self.fetch_btn.setFixedSize(120, 40)  # 固定按钮尺寸
        self.fetch_btn.clicked.connect(self.fetch_danmu)

        url_layout.addWidget(QLabel("URL:"), 0)
        url_layout.addWidget(self.url_input, 5)
        url_layout.addWidget(self.fetch_btn, 0)

        main_layout.addWidget(url_group, 0, 0, 1, 2)  # 跨两列

        # 内容展示区域 - 添加标题和边框
        display_group = QGroupBox("弹幕内容")
        display_layout = QVBoxLayout(display_group)

        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setFont(QFont("Microsoft YaHei", 10))  # 使用更常见的中文字体
        self.content_display.setMinimumHeight(300)

        # 添加信息标签
        self.info_label = QLabel("等待获取数据...")
        self.info_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 10pt;")

        display_layout.addWidget(self.content_display)
        display_layout.addWidget(self.info_label)

        main_layout.addWidget(display_group, 1, 0, 1, 2)  # 跨两列

        # 按钮区域 - 使用水平布局
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.save_btn_ass = QPushButton("保存ASS")
        self.save_btn_ass.setFixedSize(120, 40)
        self.save_btn_ass.clicked.connect(self.save_ass)
        self.save_btn_ass.setEnabled(False)

        self.save_btn = QPushButton("保存TXT")
        self.save_btn.setFixedSize(120, 40)
        self.save_btn.clicked.connect(self.save_txt)
        self.save_btn.setEnabled(False)


        self.wordcloud_btn = QPushButton("生成词云")
        self.wordcloud_btn.setFixedSize(120, 40)
        self.wordcloud_btn.clicked.connect(self.generate_wordcloud)
        self.wordcloud_btn.setEnabled(False)

        button_layout.addStretch(1)
        button_layout.addWidget(self.save_btn_ass)
        button_layout.addSpacing(15)  # 按钮间距
        button_layout.addWidget(self.save_btn)
        button_layout.addSpacing(15)  # 按钮间距
        button_layout.addWidget(self.wordcloud_btn)
        button_layout.addStretch(1)

        main_layout.addWidget(button_group, 2, 0, 1, 2)  # 跨两列

    def apply_styles(self):
        # 应用全局样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 1px solid #DCDFE6;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #409EFF;
            }
            QPushButton {
                background-color: #409EFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66B1FF;
            }
            QPushButton:pressed {
                background-color: #3A8EE6;
            }
            QPushButton:disabled {
                background-color: #C0C4CC;
                color: #909399;
            }
            QTextEdit {
                border: 1px solid #DCDFE6;
                border-radius: 4px;
                background-color: white;
                font-family: 'Microsoft YaHei', sans-serif;
                padding: 10px;
            }
            QStatusBar {
                background: #E4E7ED;
                color: #606266;
                font-size: 10pt;
                border-top: 1px solid #DCDFE6;
            }
        """)

    def fetch_danmu(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入有效的URL")
            return

        self.fetch_btn.setEnabled(False)
        self.info_label.setText("正在获取弹幕...")

        self.crawler_thread = CrawlerThread(url)
        self.crawler_thread.finished.connect(self.on_fetch_finished)
        self.crawler_thread.error.connect(self.on_fetch_error)
        self.crawler_thread.start()

    def on_fetch_finished(self, danmu_list):
        self.danmu_list = danmu_list
        self.save_btn.setEnabled(True)
        self.save_btn_ass.setEnabled(True)
        self.wordcloud_btn.setEnabled(True)

        # 显示内容
        display_text = f"共获取到 {len(danmu_list)} 条弹幕：\n\n"
        for dm in danmu_list[:100]:  # 显示前100条
            display_text += f"[{dm['time']:.2f}s] {dm['text']}\n"
        self.content_display.setPlainText(display_text)
        self.info_label.setText(f"获取完成，共 {len(danmu_list)} 条弹幕")
        self.fetch_btn.setEnabled(True)

    def on_fetch_error(self, error_msg):
        QMessageBox.critical(self, "错误", f"获取失败：{error_msg}")
        self.info_label.setText("获取失败")
        self.fetch_btn.setEnabled(True)

    def save_txt(self):
        if not self.danmu_list:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存弹幕", "output/danmu.txt", "Text Files (*.txt)")

        if filename:
            try:
                crawler = BilibiliDanmuCrawler()
                crawler.save_to_txt(self.danmu_list, filename)
                QMessageBox.information(self, "成功", f"弹幕已保存到：{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
    def save_ass(self):
        if not self.danmu_list:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存弹幕", "output/danmu.ass", "Text Files (*.ass)")

        if filename:
            try:
                crawler = BilibiliDanmuCrawler()
                crawler.save_to_ass(self.danmu_list, filename)
                QMessageBox.information(self, "成功", f"弹幕已保存到：{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

    def generate_wordcloud(self):
        if not self.danmu_list:
            return

        try:
            # 先保存临时文件
            temp_filename = "temp_danmu.txt"
            crawler = BilibiliDanmuCrawler()
            crawler.save_to_txt(self.danmu_list, temp_filename)

            # 生成词云
            generator = WordCloudGenerator()
            text = generator.load_text_from_file(temp_filename)
            processed_text = generator.preprocess_text(text)

            output_path, _ = QFileDialog.getSaveFileName(
                self, "保存词云", "wordcloud.png", "PNG Files (*.png)")

            if output_path:
                success = generator.generate_wordcloud(processed_text, output_path)
                if success:
                    QMessageBox.information(self, "成功", f"词云已保存到：{output_path}")

                    pixmap = QPixmap(output_path)
                    if not pixmap.isNull():
                        # 获取图片原始尺寸
                        img_width = pixmap.width()
                        img_height = pixmap.height()
                        img_aspect_ratio = img_width / img_height

                        # 设置基准尺寸和最大尺寸
                        base_width = 600
                        base_height = 450
                        max_width = 1000
                        max_height = 800

                        # 计算初始窗口尺寸（保持原图宽高比）
                        if img_aspect_ratio > 1:  # 宽图
                            init_width = min(max_width, max(base_width, img_width))
                            init_height = int(init_width / img_aspect_ratio)
                        else:  # 高图或方图
                            init_height = min(max_height, max(base_height, img_height))
                            init_width = int(init_height * img_aspect_ratio)

                        # 确保最小尺寸
                        min_width = 400
                        min_height = 300
                        init_width = max(min_width, init_width)
                        init_height = max(min_height, init_height)

                        # 创建或更新预览窗口
                        if self.preview_window is None:
                            self.preview_window = QLabel()
                            self.preview_window.setWindowTitle("词云预览")
                            self.preview_window.resize(init_width, init_height)  # 设置初始尺寸
                            self.preview_window.setMinimumSize(min_width, min_height)  # 设置最小尺寸
                        else:
                            # 保持当前窗口尺寸（如果已存在）
                            current_size = self.preview_window.size()
                            init_width = current_size.width()
                            init_height = current_size.height()

                        # 缩放并显示图片
                        scaled_pixmap = pixmap.scaled(
                            init_width,
                            init_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.preview_window.setPixmap(scaled_pixmap)
                        self.preview_window.show()
                        self.preview_window.raise_()
                else:
                    QMessageBox.warning(self, "警告", "词云生成失败")

            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"词云生成失败：{str(e)}")




if __name__ == "__main__":
    # crawler = BilibiliDanmuCrawler()
    # url = "https://api.bilibili.com/x/v1/dm/list.so?oid=783037295"
    # danmu_list = crawler.fetch_danmu(url)
    # crawler.save_to_txt(danmu_list, "danmu.txt")
    # print(f"共获取 {len(danmu_list)} 条弹幕")
    #
    # generator = WordCloudGenerator()
    # text = generator.load_text_from_file("danmu.txt")
    # processed_text = generator.preprocess_text(text)
    # generator.generate_wordcloud(processed_text)
    # crawler = BilibiliDanmuCrawler()
    # url = "https://api.bilibili.com/x/v1/dm/list.so?oid=783037295"

    # # 获取弹幕数据
    # danmu_data = crawler.fetch_danmu(url)
    #
    # # 保存为TXT
    # crawler.save_to_txt(danmu_data, "danmu.txt")
    #
    # # 保存为ASS（可指定视频分辨率）
    # crawler.save_to_ass(danmu_data, "danmu.ass", video_width=1920, video_height=1080)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())