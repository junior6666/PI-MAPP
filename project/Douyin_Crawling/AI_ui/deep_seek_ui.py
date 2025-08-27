import json
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumPage
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                               QLabel, QCheckBox, QComboBox, QMessageBox)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
import threading


# 图标生成类（简化版）
class IconGenerator:
    def __init__(self, bg_color=(30, 60, 120), text_color=(230, 255, 255),
                 text="Dc", enable_gradient=True, size=128, font_size=48, corner_radius=20):
        self.bg_color = bg_color
        self.text_color = text_color
        self.text = text
        self.enable_gradient = enable_gradient
        self.size = size
        self.font_size = font_size
        self.corner_radius = corner_radius

    @property
    def pixmap(self):
        # 创建一个简单的图标
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.transparent)
        return pixmap


# 爬虫工作线程
class CrawlerThread(QThread):
    update_signal = Signal(str, dict)  # 信号：状态消息，数据字典
    finished_signal = Signal(bool, str)  # 信号：是否成功，完成消息

    def __init__(self, mode, pages, theme=None, url=None, pure_mode=False):
        super().__init__()
        self.mode = mode  # "homepage" 或 "search"
        self.pages = pages
        self.theme = theme
        self.url = url
        self.pure_mode = pure_mode
        self.is_running = True

    def run(self):
        try:
            if self.mode == "homepage":
                self.get_data_from_homepage()
            else:
                self.get_data_from_search()
            self.finished_signal.emit(True, "爬取完成")
        except Exception as e:
            self.finished_signal.emit(False, f"错误: {str(e)}")

    def stop(self):
        self.is_running = False

    def get_data_from_homepage(self):
        listen_url = 'aweme/v1/web/aweme/post/'
        driver = ChromiumPage()
        driver.listen.start(listen_url)
        driver.get(self.url)

        for i in range(self.pages):
            if not self.is_running:
                break

            self.update_signal.emit(f'正在爬取主页第{i + 1}页的内容', {})
            resp = driver.listen.wait()
            data_str = resp.response.body

            for aweme in data_str["aweme_list"]:
                if not self.is_running:
                    break

                if self.pure_mode:
                    dic = {'文案': aweme["desc"]}
                else:
                    dic = {
                        '文案': aweme["desc"],
                        '作者': aweme["author"]["nickname"],
                        '点赞数': aweme["statistics"]["digg_count"],
                        '评论数': aweme["statistics"]["comment_count"],
                        '播放数': aweme["statistics"]["play_count"],
                        '收藏数': aweme["statistics"]["collect_count"],
                        '分享数': aweme["statistics"]["share_count"],
                        '推荐数': aweme["statistics"]["recommend_count"],
                        '发布时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aweme["create_time"])),
                    }
                self.update_signal.emit("", dic)

            driver.scroll.to_bottom()

    def deal_first_data_form_search(self, data_str):
        lines = data_str.strip().splitlines()
        i = 0
        dic_list = []
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if re.fullmatch(r'[0-9a-fA-F]+', line):
                i += 1
                if i < len(lines):
                    json_line = lines[i].strip()
                    data = json.loads(json_line)
                    for item in data.get("data", []):
                        aweme_info = item.get("aweme_info", {})
                        desc = aweme_info.get("desc", "")
                        author = aweme_info.get("author", {})
                        nickname = author.get('nickname', '无')
                        signature = author.get('signature', '无')

                        if self.pure_mode:
                            dic = {'文案': desc}
                        else:
                            dic = {
                                '文案': desc,
                                '作者': nickname,
                                '签名': signature
                            }
                        dic_list.append(dic)
                i += 1
        return dic_list

    def deal_not_first_data_form_search(self, data):
        dic_list = []
        for item in data.get("data", []):
            aweme_info = item.get("aweme_info", {})
            desc = aweme_info.get("desc", "").strip()
            author = aweme_info.get("author", {})
            nickname = author.get('nickname', '无').strip()
            signature = author.get('signature', '无').strip()

            if self.pure_mode:
                item_data = {'文案': desc}
            else:
                item_data = {
                    '文案': desc,
                    '作者': nickname,
                    '签名': signature
                }
            dic_list.append(item_data)
        return dic_list

    def get_data_from_search(self):
        first_listen_url = 'aweme/v1/web/general/search/stream/'
        not_first_listen_url = 'aweme/v1/web/general/search/single/'

        driver = ChromiumPage()
        driver.listen.start(first_listen_url)
        url = f"https://www.douyin.com/search/{self.theme}"
        driver.get(url)

        for i in range(self.pages):
            if not self.is_running:
                break

            self.update_signal.emit(f'正在搜索第{i + 1}页的内容', {})
            resp = driver.listen.wait()
            data_str = resp.response.body

            if i == 0:
                dict_list = self.deal_first_data_form_search(data_str)
            else:
                dict_list = self.deal_not_first_data_form_search(data_str)

            for dic in dict_list:
                if not self.is_running:
                    break
                self.update_signal.emit("", dic)

            driver.scroll.to_bottom()
            driver.listen.start(not_first_listen_url)


# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.crawler_thread = None
        self.data_list = []  # 存储所有爬取的数据
        self.init_ui()

    def init_ui(self):
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
        ).pixmap
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
            QComboBox {
                background: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                color: #e0e0e0;
                selection-background-color: #444;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()

        # 模式选择
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["主页爬取", "搜索爬取"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("爬取模式:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # 主页爬取相关控件
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入主页URL")
        main_layout.addWidget(QLabel("主页URL:"))
        main_layout.addWidget(self.url_input)

        # 搜索爬取相关控件
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索主题（如：街拍, 健身, 美食）")
        main_layout.addWidget(QLabel("搜索主题:"))
        main_layout.addWidget(self.search_input)

        # 页数输入和纯净模式
        options_layout = QHBoxLayout()
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("页数 (默认: 2)")
        self.page_input.setText("2")
        self.pure_mode_cb = QCheckBox("纯净模式 (只显示文案)")
        options_layout.addWidget(QLabel("爬取页数:"))
        options_layout.addWidget(self.page_input)
        options_layout.addWidget(self.pure_mode_cb)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("开始爬取")
        self.stop_button = QPushButton("停止爬取")
        self.stop_button.setEnabled(False)
        self.export_button = QPushButton("导出数据")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.export_button)
        main_layout.addLayout(button_layout)

        # 文案显示区域
        main_layout.addWidget(QLabel("爬取结果:"))
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        main_layout.addWidget(self.text_output)

        # 状态标签
        self.status_label = QLabel("等待开始...")
        main_layout.addWidget(self.status_label)

        # 设置中心部件
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 连接信号
        self.start_button.clicked.connect(self.start_crawling)
        self.stop_button.clicked.connect(self.stop_crawling)
        self.export_button.clicked.connect(self.export_data)

        # 初始模式设置
        self.on_mode_changed(0)

    def on_mode_changed(self, index):
        # 根据选择的模式显示/隐藏相关控件
        if index == 0:  # 主页爬取
            self.url_input.setVisible(True)
            self.search_input.setVisible(False)
            self.centralWidget().layout().itemAt(1).widget().setVisible(True)  # URL标签
            self.centralWidget().layout().itemAt(3).widget().setVisible(False)  # 搜索标签
        else:  # 搜索爬取
            self.url_input.setVisible(False)
            self.search_input.setVisible(True)
            self.centralWidget().layout().itemAt(1).widget().setVisible(False)  # URL标签
            self.centralWidget().layout().itemAt(3).widget().setVisible(True)  # 搜索标签

    def start_crawling(self):
        # 获取输入参数
        try:
            pages = int(self.page_input.text() or "2")
        except ValueError:
            QMessageBox.warning(self, "输入错误", "页数必须是整数")
            return

        pure_mode = self.pure_mode_cb.isChecked()
        mode_index = self.mode_combo.currentIndex()

        if mode_index == 0:  # 主页爬取
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "输入错误", "请输入主页URL")
                return

            self.crawler_thread = CrawlerThread(
                "homepage", pages, url=url, pure_mode=pure_mode
            )
        else:  # 搜索爬取
            theme = self.search_input.text().strip()
            if not theme:
                QMessageBox.warning(self, "输入错误", "请输入搜索主题")
                return

            self.crawler_thread = CrawlerThread(
                "search", pages, theme=theme, pure_mode=pure_mode
            )

        # 连接信号和槽
        self.crawler_thread.update_signal.connect(self.update_output)
        self.crawler_thread.finished_signal.connect(self.crawling_finished)

        # 清空之前的数据
        self.data_list = []
        self.text_output.clear()

        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("爬取中...")

        # 启动线程
        self.crawler_thread.start()

    def stop_crawling(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.crawler_thread.wait()
            self.status_label.setText("已停止")

    def crawling_finished(self, success, message):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText(message)

    def update_output(self, status_msg, data_dict):
        if status_msg:
            self.status_label.setText(status_msg)
            return

        # 添加数据到列表
        self.data_list.append(data_dict)

        # 更新文本显示
        cursor = self.text_output.textCursor()
        cursor.movePosition(QTextCursor.End)

        if self.pure_mode_cb.isChecked():
            text = data_dict.get('文案', '') + "\n\n"
        else:
            text = "\n".join([f"{k}: {v}" for k, v in data_dict.items()]) + "\n\n"

        cursor.insertText(text)
        self.text_output.setTextCursor(cursor)
        self.text_output.ensureCursorVisible()

    def export_data(self):
        if not self.data_list:
            QMessageBox.information(self, "导出", "没有数据可导出")
            return

        # 这里可以实现导出到文件的功能
        # 例如：保存为JSON、CSV等格式
        QMessageBox.information(self, "导出", f"共{len(self.data_list)}条数据，导出功能待实现")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())