import sys
import csv
import json
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QHeaderView, QHBoxLayout,
    QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QLinearGradient, QPalette, QColor, QIcon, QPixmap
from DrissionPage import ChromiumPage


# 创建多线程工作类
class CrawlerThread(QThread):
    update_signal = Signal(dict)
    status_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, search_theme, page_count):
        super().__init__()
        self.search_theme = search_theme
        self.page_count = page_count
        self.is_running = True

    def run(self):
        try:
            # 初始化浏览器
            driver = ChromiumPage()

            # 监听数据包
            driver.listen.start('aweme/v1/web/general/search/stream/')

            # 构造搜索 URL
            url = f"https://www.douyin.com/jingxuan/search/{self.search_theme}"
            driver.get(url)

            # 爬取多页内容
            for page in range(self.page_count):
                if not self.is_running:
                    break

                self.status_signal.emit(f"正在爬取第{page + 1}页的内容")
                driver.scroll.to_bottom()
                try:
                    # 等待监听到数据包
                    resp = driver.listen.wait()
                    data_str = resp.response.body
                    self.parse_chunked_data(data_str)
                except Exception as e:
                    self.error_signal.emit(f"监听数据包时出错: {e}")

            driver.quit()
            self.status_signal.emit("爬取完成！")
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"爬取过程中出错: {e}")

    def parse_chunked_data(self, data_str):
        lines = data_str.strip().splitlines()
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
                        for item in data.get("data", []):
                            aweme_info = item.get("aweme_info", {})
                            desc = aweme_info.get("desc", "")
                            author = aweme_info.get("author", {})
                            nickname = author.get('nickname', '无')
                            signature = author.get('signature', '无')
                            data_item = {
                                '文案': desc,
                                '作者': nickname,
                                '签名': signature
                            }
                            self.update_signal.emit(data_item)
                    except json.JSONDecodeError as e:
                        self.error_signal.emit(f"JSON 解析失败: {e}")
                i += 1

    def stop(self):
        self.is_running = False
        self.terminate()
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Douyin 数据爬取工具")
        self.setGeometry(100, 100, 900, 700)

        # 设置应用图标
        self.setWindowIcon(self.create_icon())

        # 设置渐变背景
        self.set_gradient_style()

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 创建顶部横向布局
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # 搜索主题输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索主题（如：自律）")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 14px;
                background: rgba(255, 255, 255, 0.9);
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        top_layout.addWidget(self.search_input)

        # 页数输入框
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("请输入页数")
        self.page_input.setMaximumWidth(100)
        self.page_input.setMinimumHeight(40)
        self.page_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 14px;
                background: rgba(255, 255, 255, 0.9);
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        top_layout.addWidget(self.page_input)

        # 开始按钮
        self.start_button = QPushButton("开始爬取")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_crawling)
        self.start_button.setStyleSheet(self.get_button_style())
        top_layout.addWidget(self.start_button)

        main_layout.addLayout(top_layout)

        # 数据文本显示框
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                background: rgba(255, 255, 255, 0.9);
            }
        """)
        main_layout.addWidget(self.text_display)

        # 创建底部按钮布局
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        # 导出CSV按钮
        self.export_csv_button = QPushButton("导出CSV")
        self.export_csv_button.setMinimumHeight(40)
        self.export_csv_button.clicked.connect(lambda: self.export_data('csv'))
        self.export_csv_button.setStyleSheet(self.get_button_style())
        bottom_layout.addWidget(self.export_csv_button)

        # 导出TXT按钮
        self.export_txt_button = QPushButton("导出TXT")
        self.export_txt_button.setMinimumHeight(40)
        self.export_txt_button.clicked.connect(lambda: self.export_data('txt'))
        self.export_txt_button.setStyleSheet(self.get_button_style())
        bottom_layout.addWidget(self.export_txt_button)

        # 停止按钮
        self.stop_button = QPushButton("停止爬取")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.clicked.connect(self.stop_crawling)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff6b6b, stop: 1 #ee5a52);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff5252, stop: 1 #e53935);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e53935, stop: 1 #c62828);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        bottom_layout.addWidget(self.stop_button)

        main_layout.addLayout(bottom_layout)

        # 状态标签
        self.status_label = QLabel("等待开始...")
        self.status_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.7);
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
                color: #333333;
            }
        """)
        main_layout.addWidget(self.status_label)

        # 设置中心部件
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 初始化变量
        self.data_list = []
        self.crawler_thread = None

    def create_icon(self):
        # 创建带有"DC"文字的图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)

        from PySide6.QtGui import QPainter, QBrush, QPen
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景圆形
        gradient = QLinearGradient(0, 0, 32, 32)
        gradient.setColorAt(0, QColor("#4facfe"))
        gradient.setColorAt(1, QColor("#00f2fe"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 32, 32)

        # 绘制文字
        painter.setPen(QPen(Qt.white))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "DC")
        painter.end()

        return QIcon(pixmap)

    def set_gradient_style(self):
        # 设置窗口渐变背景
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor("#4facfe"))
        gradient.setColorAt(1, QColor("#00f2fe"))

        palette = QPalette()
        palette.setBrush(QPalette.Window, gradient)
        self.setPalette(palette)

    def get_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6a11cb, stop: 1 #2575fc);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5e10b5, stop: 1 #1c6fe4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4d0d93, stop: 1 #1565c0);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """

    def start_crawling(self):
        # 获取用户输入
        search_theme = self.search_input.text()
        try:
            page_count = int(self.page_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的页数！")
            return

        if not search_theme or not page_count:
            self.status_label.setText("请输入搜索主题和页数！")
            return

        # 清空数据
        self.text_display.clear()
        self.data_list.clear()

        # 禁用开始按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 创建并启动爬虫线程
        self.crawler_thread = CrawlerThread(search_theme, page_count)
        self.crawler_thread.update_signal.connect(self.update_display)
        self.crawler_thread.status_signal.connect(self.status_label.setText)
        self.crawler_thread.finished_signal.connect(self.on_crawling_finished)
        self.crawler_thread.error_signal.connect(self.on_crawling_error)
        self.crawler_thread.start()

    def stop_crawling(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.status_label.setText("爬取已停止")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def on_crawling_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def on_crawling_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_display(self, data_item):
        self.data_list.append(data_item)

        # 更新文本显示框
        text = f"文案: {data_item['文案']}\n作者: {data_item['作者']}\n签名: {data_item['签名']}\n{'-' * 50}\n"
        self.text_display.append(text)

    def export_data(self, format_type):
        if not self.data_list:
            QMessageBox.warning(self, "导出失败", "没有数据可导出！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"保存文件",
            "",
            f"{format_type.upper()} 文件 (*.{format_type})"
        )

        if not file_path:
            return

        try:
            if format_type == 'csv':
                with open(file_path, mode='w', encoding='utf-8', newline='') as f:
                    csv_w = csv.DictWriter(f, fieldnames=['文案', '作者', '签名'])
                    csv_w.writeheader()
                    csv_w.writerows(self.data_list)
            elif format_type == 'txt':
                with open(file_path, mode='w', encoding='utf-8') as f:
                    for item in self.data_list:
                        f.write(f"文案: {item['文案']}\n")
                        f.write(f"作者: {item['作者']}\n")
                        f.write(f"签名: {item['签名']}\n")
                        f.write("-" * 50 + "\n")

            self.status_label.setText(f"数据已导出到 {file_path}")
            QMessageBox.information(self, "导出成功", f"数据已成功导出到 {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时出错: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())