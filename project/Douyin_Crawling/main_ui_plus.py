import sys
import csv
import json
import re
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
    QPushButton, QLabel, QFileDialog, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from DrissionPage import ChromiumPage


def create_icon_pixmap(text="DC", size=64, bg_color=QColor(40, 40, 40), text_color=QColor(200, 200, 200)):
    """生成包含文字的正方形图标"""
    pixmap = QPixmap(size, size)
    pixmap.fill(bg_color)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(text_color)
    font = QFont("SimHei", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return pixmap


class CrawlerWorker(QThread):
    """爬虫工作线程"""
    status_signal = Signal(str)
    data_signal = Signal(list)
    finished_signal = Signal()

    def __init__(self, search_theme, page_count):
        super().__init__()
        self.search_theme = search_theme
        self.page_count = page_count

    def run(self):
        try:
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
                driver.scroll.to_bottom()
                try:
                    resp = driver.listen.wait(timeout=10)
                    if not resp:
                        self.status_signal.emit(f"第 {page + 1} 页未获取到数据，继续...")
                        continue
                    data_str = resp.response.body
                    new_data = self.parse_chunked_data(data_str)
                    collected_data.extend(new_data)
                    self.data_signal.emit(new_data)  # 实时发送数据
                except Exception as e:
                    self.status_signal.emit(f"第 {page + 1} 页爬取失败: {str(e)}")
                    continue

            driver.quit()
            self.status_signal.emit(f"爬取完成，共获取 {len(collected_data)} 条数据。")
            self.finished_signal.emit()
        except Exception as e:
            self.status_signal.emit(f"爬取异常: {str(e)}")

    def parse_chunked_data(self, data_str):
        lines = data_str.strip().splitlines()
        results = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or re.fullmatch(r'[0-9a-fA-F]+', line):
                i += 1
                if i < len(lines):
                    json_line = lines[i].strip()
                    try:
                        data = json.loads(json_line)
                        for item in data.get("data", []):
                            aweme_info = item.get("aweme_info", {})
                            desc = aweme_info.get("desc", "").strip()
                            author = aweme_info.get("author", {})
                            nickname = author.get('nickname', '无').strip()
                            signature = author.get('signature', '无').strip()
                            if desc:  # 只保留有文案的内容
                                results.append({
                                    '文案': desc,
                                    '作者': nickname,
                                    '签名': signature
                                })
                    except json.JSONDecodeError:
                        pass
                i += 1
            else:
                i += 1
        return results


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Douyin 文案爬取工具")
        self.setGeometry(100, 100, 900, 600)

        # 设置图标
        icon_pixmap = create_icon_pixmap()
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
        self.search_input.setPlaceholderText("请输入搜索主题（如：自律）")
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("页数")
        self.start_button = QPushButton("开始爬取")

        # 设置等宽
        # self.search_input.setSizePolicy(Qt.Expanding, Qt.Fixed)
        # self.page_input.setSizePolicy(Qt.Expanding, Qt.Fixed)
        # self.start_button.setSizePolicy(Qt.Expanding, Qt.Fixed)

        top_layout.addWidget(self.search_input,stretch=2)
        top_layout.addWidget(self.page_input,stretch=2)
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

        # 初始化
        self.data_list = []
        self.worker = None
        self.thread = None

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
        self.data_list.clear()

        # 启动爬虫线程
        self.worker = CrawlerWorker(search_theme, page_count)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.status_signal.connect(self.update_status)
        self.worker.data_signal.connect(self.append_texts)
        self.worker.finished_signal.connect(self.on_crawl_finished)
        self.worker.finished_signal.connect(self.thread.quit)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_status(self, msg):
        self.status_label.setText(msg)

    def append_texts(self, new_data):
        for item in new_data:
            text = f"【{item['作者']}】{item['文案']}\n"
            if item['签名'] != '无':
                text += f"   签名: {item['签名']}\n"
            text += "\n"
            self.text_output.insertPlainText(text)
            self.data_list.append(item)

    def on_crawl_finished(self):
        self.start_button.setEnabled(True)

    def export_data(self):
        if not self.data_list:
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
                    writer.writerows(self.data_list)
            elif ext == ".txt":
                with open(file_path, mode='w', encoding='utf-8') as f:
                    for item in self.data_list:
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