import csv
import json
import re

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
    QPushButton, QLabel, QFileDialog, QTextEdit, QCheckBox
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon
from DrissionPage import ChromiumPage

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QLinearGradient, QBrush,
    QPen
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

    def create_icon(self, output_path: str = "icon1.ico") -> bool:
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


class CrawlerWorker(QThread):
    """爬虫工作线程"""
    status_signal = Signal(str)
    data_signal = Signal(list)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, search_theme, page_count, csv_filename='data/data_wenan.csv'):
        super().__init__()
        self.search_theme = search_theme
        self.page_count = page_count
        self.csv_filename = csv_filename
        self.csv_file = None
        self.csv_writer = None
        self.collected_data = []  # 在worker中维护完整的数据集合

    def run(self):
        try:
            # 初始化CSV文件
            self._init_csv_file()

            self.status_signal.emit("正在启动浏览器...")
            driver = ChromiumPage()

            # 监听数据包
            driver.listen.start('aweme/v1/web/general/search/stream/')

            # 构造搜索 URL
            url = f"https://www.douyin.com/jingxuan/search/{self.search_theme}"
            driver.get(url)

            collected_data = []

            for page in range(self.page_count):
                self.status_signal.emit(f"正在爬取第 {page + 1} / {self.page_count} 页...")

                try:
                    resp = driver.listen.wait(timeout=10)
                    if not resp:
                        self.status_signal.emit(f"第 {page + 1} 页未获取到数据，继续...")
                        continue

                    data_str = resp.response.body

                    # 处理第一页和其他页的不同格式
                    if page == 0:
                        new_data = self.parse_chunked_data(data_str)
                    else:
                        new_data = self.parse_json_data(data_str)

                    # 保存数据到CSV并收集
                    for item in new_data:
                        self.csv_writer.writerow(item)
                        collected_data.append(item)

                    self.data_signal.emit(new_data)  # 实时发送数据
                    # 滚动到底部准备加载下一页
                    driver.scroll.to_bottom()
                    driver.listen.start('aweme/v1/web/general/search/single/')
                except Exception as e:
                    print(f"第 {page + 1} 页爬取失败: {str(e)}")
                    self.status_signal.emit(f"第 {page + 1} 页爬取失败: {str(e)}")
                    continue

            driver.quit()
            self.status_signal.emit(f"爬取完成，共获取 {len(self.collected_data)} 条数据。")
            self.finished_signal.emit()

        except Exception as e:
            self.status_signal.emit(f"爬取异常: {str(e)}")
            self.error_signal.emit(str(e))
        finally:
            # 确保关闭CSV文件
            if self.csv_file:
                self.csv_file.close()

    def _init_csv_file(self):
        """初始化CSV文件"""
        try:
            self.csv_file = open(self.csv_filename, mode='w', encoding='utf-8', newline='')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=['文案', '作者', '签名'])
            self.csv_writer.writeheader()
        except Exception as e:
            self.status_signal.emit(f"CSV文件初始化失败: {str(e)}")
            self.error_signal.emit(str(e))

    def parse_chunked_data(self, data_str):
        """解析分块传输编码的数据（第一页）"""
        lines = data_str.strip().splitlines()
        results = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            # 匹配十六进制数字（块大小）
            if re.fullmatch(r'[0-9a-fA-F]+', line):
                i += 1  # 下一行是数据
                if i < len(lines):
                    json_line = lines[i].strip()
                    try:
                        data = json.loads(json_line)
                        results.extend(self._extract_data_from_json(data))
                    except json.JSONDecodeError as e:
                        self.status_signal.emit(f"JSON解析失败: {e}")
                i += 1
            else:
                i += 1

        return results

    def parse_json_data(self, data_str):
        """解析JSON格式的数据（第二页及以后）"""
        try:
            # data = json.loads(data_str)
            return self._extract_data_from_json(data_str)
        except json.JSONDecodeError as e:
            self.status_signal.emit(f"JSON解析失败: {e}")
            return []

    def _extract_data_from_json(self, data):
        """从JSON数据中提取信息"""
        results = []
        for item in data.get("data", []):
            aweme_info = item.get("aweme_info", {})
            desc = aweme_info.get("desc", "").strip()
            author = aweme_info.get("author", {})
            nickname = author.get('nickname', '无').strip()
            signature = author.get('signature', '无').strip()

            if desc:  # 只保留有文案的内容
                item_data = {
                    '文案': desc,
                    '作者': nickname,
                    '签名': signature
                }
                results.append(item_data)
                self.collected_data.append(item_data)  # 同时添加到完整数据集合中

        return results

    def get_collected_data(self):
        """获取收集到的完整数据"""
        return self.collected_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Douyin 文案爬取工具")
        self.setGeometry(100, 100, 900, 600)

        # 设置图标
        icon_pixmap = IconGenerator(
            bg_color=(30, 60, 120),
            text_color=(230, 255, 255),
            text="Dc",
            enable_gradient=True,
            size=128,
            font_size=48,
            corner_radius=20,
        ).pixmap()
        self.setWindowIcon(QIcon(icon_pixmap))

        # 应用渐变样式（黑灰简约）
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1e1e, stop:1 #333333);
            }
            QLineEdit {
                background: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #d0d0d0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #444, stop:1 #333);
            }
            QPushButton:pressed {
                background: #222;
            }
            QLabel {
                color: #ccc;
                font-size: 14px;
            }
            QTextEdit {
                background: #252525;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()

        # 顶部横向布局：搜索框、页数、按钮
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索主题（如：自律, 健身, 美食, 锻炼, 减肥, 早起, 阅读, 旅行")
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("页数")
        self.pure_mode_cb = QCheckBox("纯净模式")
        self.pure_mode_cb.setStyleSheet("color:white;")# <--- 新增
        self.start_button = QPushButton("开始爬取")


        top_layout.addWidget(self.search_input,stretch=2)
        top_layout.addWidget(self.page_input,stretch=1)
        top_layout.addWidget(self.pure_mode_cb)
        top_layout.addWidget(self.start_button)
        main_layout.addLayout(top_layout)

        # 文案显示区域（文本框）
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        main_layout.addWidget(self.text_output)

        # 按钮行：导出
        btn_layout = QHBoxLayout()
        self.export_button = QPushButton("导出数据")
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_button)
        main_layout.addLayout(btn_layout)

        # 状态标签
        self.status_label = QLabel("等待开始...")
        main_layout.addWidget(self.status_label)

        # 设置中心部件
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 连接信号
        self.start_button.clicked.connect(self.start_crawling)
        self.export_button.clicked.connect(self.export_data)

    def start_crawling(self):
        search_theme = self.search_input.text().strip()
        page_text = self.page_input.text().strip()

        if not search_theme:
            self.status_label.setText("请输入搜索主题！")
            return
        try:
            page_count = int(page_text)
            if page_count <= 0:
                raise ValueError
        except ValueError:
            self.status_label.setText("请输入有效的页数（正整数）！")
            return

        # 禁用按钮
        self.start_button.setEnabled(False)
        self.text_output.clear()

        # 启动爬虫线程
        self.worker = CrawlerWorker(search_theme, page_count)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.status_signal.connect(self.update_status)
        self.worker.data_signal.connect(self.append_texts)
        self.worker.finished_signal.connect(self.on_crawl_finished)
        self.worker.error_signal.connect(self.on_crawl_error)
        self.worker.finished_signal.connect(self.thread.quit)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_status(self, msg):
        self.status_label.setText(msg)

    def append_texts(self, new_data):
        pure = self.pure_mode_cb.isChecked()  # 是否开启纯净模式
        for item in new_data:
            if pure:
                text = f"{item['文案']}\n\n"
            else:
                text = f"【{item['作者']}】{item['文案']}\n"
                if item['签名'] != '无':
                    text += f"   签名: {item['签名']}\n"
                text += "\n"
            self.text_output.insertPlainText(text)

    def on_crawl_finished(self):
        self.start_button.setEnabled(True)
        self.status_label.setText("爬取完成")

    def on_crawl_error(self, error_msg):
        self.start_button.setEnabled(True)
        self.status_label.setText(f"爬取出错: {error_msg}")

    def export_data(self):
        if not self.worker:
            self.status_label.setText("没有可用的数据可导出！")
            return
            
        # 从worker获取完整的数据
        data_list = self.worker.get_collected_data()
        
        if not data_list:
            self.status_label.setText("没有数据可导出！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "CSV 文件 (*.csv);;TXT 文件 (*.txt)"
        )
        if not file_path:
            return

        try:
            ext = Path(file_path).suffix.lower()
            if ext == ".csv":
                with open(file_path, mode='w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['文案', '作者', '签名'])
                    writer.writeheader()
                    writer.writerows(data_list)
            elif ext == ".txt":
                with open(file_path, mode='w', encoding='utf-8') as f:
                    pure = self.pure_mode_cb.isChecked()
                    for item in data_list:
                        if pure:
                            f.write(f"{item['文案']}\n\n")
                        else:
                            f.write(f"【{item['作者']}】{item['文案']}\n")
                            if item['签名'] != '无':
                                f.write(f"   签名: {item['签名']}\n")
                            f.write("\n")
            self.status_label.setText(f"数据已导出到：{file_path}")
        except Exception as e:
            self.status_label.setText(f"导出失败：{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())