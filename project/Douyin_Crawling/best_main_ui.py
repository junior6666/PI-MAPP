import json
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from DrissionPage import ChromiumPage
from PySide6.QtCore import QThread, Signal, Qt, QUrl, QObject
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QCheckBox, QFileDialog,
    QComboBox, QMessageBox, QRadioButton, QButtonGroup, QListWidget
)


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



# =================== 信号类（用于暂停/继续控制）===================
class ControlSignal(QObject):
    pause = Signal()
    resume = Signal()
    stop = Signal()


# =================== 爬虫工作线程（支持实时发送单条数据）===================
class CrawlWorker(QThread):
    log_signal = Signal(str)
    data_signal = Signal(dict)  # 改为每次发送一条数据
    status_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, mode, url=None, theme=None, pages=1, pure_mode=False):
        super().__init__()
        self.mode = mode
        self.url = url
        self.theme = theme
        self.pages = max(1, int(pages))
        self.pure_mode = pure_mode

        # 控制信号
        self.control = ControlSignal()
        self.is_paused = False
        self.is_stopped = False

        # 连接控制信号
        self.control.pause.connect(self._pause)
        self.control.resume.connect(self._resume)
        self.control.stop.connect(self._stop)

    def _pause(self):
        self.is_paused = True
        self.log_signal.emit("⏸️ 已暂停")

    def _resume(self):
        self.is_paused = False
        self.log_signal.emit("▶️ 继续爬取")

    def _stop(self):
        self.is_stopped = True
        self.log_signal.emit("⏹️ 用户中止爬取")

    def run(self):
        try:
            if self.mode == "home":
                self.crawl_from_homepage()
            elif self.mode == "search":
                self.crawl_from_search()
            else:
                self.log_signal.emit("❌ 错误：未知的爬取模式")
        except Exception as e:
            self.log_signal.emit(f"❌ 爬取出错: {str(e)}")
        finally:
            self.finished_signal.emit()

    def crawl_from_homepage(self):
        self.log_signal.emit(f"🌐 开始从主页爬取 {self.pages} 页数据...")
        driver = ChromiumPage()
        listen_url = 'aweme/v1/web/aweme/post/'
        driver.listen.start(listen_url)
        driver.get(self.url)

        count = 0

        for i in range(self.pages):
            if self.is_stopped:
                driver.close()
                return

            while self.is_paused and not self.is_stopped:
                time.sleep(0.5)

            self.log_signal.emit(f"📄 正在加载第 {i + 1} 页...")

            resp = driver.listen.wait(timeout=10)
            if not resp or not resp.response.body:
                self.log_signal.emit(f"⚠️ 第 {i + 1} 页无响应，可能已到底。")
                break

            data_str = resp.response.body
            aweme_list = data_str.get("aweme_list", [])
            for aweme in aweme_list:
                dic = self.extract_aweme_data(aweme)
                self.data_signal.emit(dic)  # 实时发送每条数据
                count += 1

            driver.scroll.to_bottom()
            time.sleep(1.5)

        driver.close()
        self.status_signal.emit(f"✅ 主页爬取完成，共获取 {count} 条数据")

    def crawl_from_search(self):
        self.log_signal.emit(f"🔍 开始搜索关键词：'{self.theme}'，共 {self.pages} 页...")
        driver = ChromiumPage()
        first_url = 'aweme/v1/web/general/search/stream/'
        next_url = 'aweme/v1/web/general/search/single/'
        url = f"https://www.douyin.com/jingxuan/search/{self.theme}"
        driver.listen.start(first_url)
        driver.get(url)

        count = 0

        for i in range(self.pages):
            if self.is_stopped:
                driver.close()
                return

            while self.is_paused and not self.is_stopped:
                time.sleep(0.5)

            self.log_signal.emit(f"📄 正在加载第 {i + 1} 页...")

            resp = driver.listen.wait(timeout=10)
            if not resp:
                self.log_signal.emit(f"⚠️ 第 {i + 1} 页无响应。")
                break

            if i == 0:
                data_list = self.deal_first_data(resp.response.body)
            else:
                data_list = self.deal_not_first_data(resp.response.body)

            for item in data_list:
                self.data_signal.emit(item)  # 实时发送每条数据
                count += 1
            driver.listen.start(next_url)
            driver.scroll.to_bottom()
            # time.sleep(1.5)
            # if i < self.pages - 1:
        driver.close()
        self.status_signal.emit(f"✅ 搜索爬取完成，共获取 {count} 条数据")

    def extract_aweme_data(self, aweme):
        author = aweme.get("author", {})
        stats = aweme.get("statistics", {})

        dic = {
            '文案': aweme.get("desc", "").strip(),
            '作者': author.get("nickname", "未知"),
            '点赞数': stats.get("digg_count", 0),
            '评论数': stats.get("comment_count", 0),
            '播放数': stats.get("play_count", 0),
            '收藏数': stats.get("collect_count", 0),
            '分享数': stats.get("share_count", 0),
            '推荐数': stats.get("recommend_count", 0),
            '发布时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aweme.get("create_time", 0))),
        }
        return dic

    def deal_first_data(self, data_str):
        lines = data_str.strip().splitlines()
        dic_list = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or re.fullmatch(r'[0-9a-fA-F]+', line):
                i += 1
                if i < len(lines):
                    try:
                        json_line = lines[i].strip()
                        data = json.loads(json_line)
                        for item in data.get("data", []):
                            aweme_info = item.get("aweme_info", {})
                            dic = {
                                '文案': aweme_info.get("desc", "").strip(),
                                '作者': aweme_info.get("author", {}).get('nickname', '无').strip(),
                                '签名': aweme_info.get("author", {}).get('signature', '无').strip(),
                            }
                            dic_list.append(dic)
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ 解析首包数据失败: {e}")
                i += 1
            else:
                i += 1
        return dic_list

    def deal_not_first_data(self, data):
        dic_list = []
        for item in data.get("data", []):
            aweme_info = item.get("aweme_info", {})
            dic = {
                '文案': aweme_info.get("desc", "").strip(),
                '作者': aweme_info.get("author", {}).get('nickname', '无').strip(),
                '签名': aweme_info.get("author", {}).get('signature', '无').strip(),
            }
            dic_list.append(dic)
        return dic_list


# =================== 主窗口 ===================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Douyin 文案爬取工具")
        self.setGeometry(100, 100, 1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1e1e, stop:1 #333333);
            }
            QLineEdit, QComboBox {
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
            QPushButton:hover { background: #444; }
            QPushButton:pressed { background: #222; }
            QLabel {
                color: #ccc;
                font-size: 14px;
            }
            QTextEdit, QListWidget {
                background: #252525;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QCheckBox, QRadioButton {
                color: white;
            }
        """)

        self.crawled_data = []  # 用于导出
        self.worker = None

        self.setup_ui()
        self.connect_signals()
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


    def setup_ui(self):
        main_layout = QVBoxLayout()

        # ========= 模式选择 =========
        mode_layout = QHBoxLayout()
        self.home_radio = QRadioButton("主页爬取")
        self.search_radio = QRadioButton("搜索爬取")
        self.home_radio.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.home_radio)
        self.mode_group.addButton(self.search_radio)

        mode_layout.addWidget(QLabel("爬取模式:"))
        mode_layout.addWidget(self.home_radio)
        mode_layout.addWidget(self.search_radio)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # ========= 输入区域 =========
        input_layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入用户主页URL")
        # 设置默认主页 URL
        self.url_input.setText(
            'https://www.douyin.com/user/MS4wLjABAAAApX522hgyNjhiAtiOGTZpWWDC3SQtdJvjWLX6pg00g4UyNnS-Zp9ISM190WvyYacK?from_tab_name=main&vid=7413737675921837350'
        )

        self.theme_input = QLineEdit()
        self.theme_input.setPlaceholderText("请输入搜索主题，如：街拍、健身")

        self.page_input = QLineEdit("2")
        self.pure_mode_cb = QCheckBox("纯净模式")

        input_layout.addWidget(self.url_input, 9)
        input_layout.addWidget(self.theme_input, 9)
        input_layout.addStretch()
        input_layout.addWidget(QLabel("页数:"), 1)
        input_layout.addWidget(self.page_input, 1)
        input_layout.addWidget(self.pure_mode_cb, 1)

        # ========= 按钮行：开始、暂停、继续 =========
        btn_layout = QHBoxLayout()
        self.start_button = QPushButton("🟢 开始爬取")
        self.pause_button = QPushButton("⏸️ 暂停")
        self.resume_button = QPushButton("▶️ 继续")
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)

        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.pause_button)
        btn_layout.addWidget(self.resume_button)
        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)
        main_layout.addLayout(input_layout)

        # ========= 文本显示区（实时更新）=========
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("实时显示爬取内容...")
        main_layout.addWidget(QLabel("爬取内容:"))
        main_layout.addWidget(self.text_output,stretch=4)

        # ========= 日志显示区（实时更新）=========
        self.log_list = QListWidget()
        # self.log_list.setPlaceholderText("运行日志...")
        main_layout.addWidget(QLabel("运行日志:"))
        main_layout.addWidget(self.log_list,stretch=1)

        # ========= 导出按钮 =========
        export_layout = QHBoxLayout()
        self.export_button = QPushButton("📤 导出数据")
        self.export_button.setEnabled(False)
        export_layout.addStretch()
        export_layout.addWidget(self.export_button)
        main_layout.addLayout(export_layout)

        # ========= 状态标签 =========
        self.status_label = QLabel("✅ 等待开始...")
        main_layout.addWidget(self.status_label)

        # 设置中心部件
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 初始状态
        self.update_input_visibility()

    def connect_signals(self):
        self.start_button.clicked.connect(self.start_crawling)
        self.pause_button.clicked.connect(self.pause_crawling)
        self.resume_button.clicked.connect(self.resume_crawling)
        self.export_button.clicked.connect(self.export_data)

        self.home_radio.toggled.connect(self.update_input_visibility)
        self.search_radio.toggled.connect(self.update_input_visibility)

        # 连接线程信号
        if self.worker:
            self.worker.log_signal.disconnect()
            self.worker.data_signal.disconnect()
            self.worker.status_signal.disconnect()
            self.worker.finished_signal.disconnect()

    def update_input_visibility(self):
        is_home = self.home_radio.isChecked()
        self.url_input.setVisible(is_home)
        self.theme_input.setVisible(not is_home)
        self.url_input.setPlaceholderText("请输入用户主页URL" if is_home else "")
        self.theme_input.setPlaceholderText("请输入搜索主题 如：街拍、健身" if not is_home else "")

    def start_crawling(self):
        self.log_list.clear()
        self.text_output.clear()
        self.export_button.setEnabled(False)
        self.crawled_data = []

        mode = "home" if self.home_radio.isChecked() else "search"
        url = self.url_input.text().strip() if mode == "home" else None
        theme = self.theme_input.text().strip() if mode == "search" else None
        pages_text = self.page_input.text().strip()
        pure_mode = self.pure_mode_cb.isChecked()

        if mode == "home" and not url:
            QMessageBox.warning(self, "输入错误", "请填写主页URL！")
            return
        if mode == "search" and not theme:
            QMessageBox.warning(self, "输入错误", "请填写搜索主题！")
            return
        if not pages_text.isdigit() or int(pages_text) < 1:
            QMessageBox.warning(self, "输入错误", "页数必须是正整数！")
            return

        pages = int(pages_text)

        # 创建线程
        self.worker = CrawlWorker(mode, url=url, theme=theme, pages=pages, pure_mode=pure_mode)
        self.worker.log_signal.connect(self.add_log)
        self.worker.data_signal.connect(self.append_text)  # 实时追加文本
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_crawl_finished)

        # 控制按钮状态
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)

        self.worker.start()
        self.add_log(f"🚀 启动爬取任务：模式={mode}, 页数={pages}")

    def pause_crawling(self):
        if self.worker and not self.worker.is_paused:
            self.worker.control.pause.emit()
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)

    def resume_crawling(self):
        if self.worker and self.worker.is_paused:
            self.worker.control.resume.emit()
            self.resume_button.setEnabled(False)
            self.pause_button.setEnabled(True)

    def add_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_list.addItem(f"[{timestamp}] {msg}")
        self.log_list.scrollToBottom()

    def append_text(self, data):
        # 添加到数据列表（用于导出）
        self.crawled_data.append(data)

        # 实时显示
        pure_mode = self.pure_mode_cb.isChecked()
        if pure_mode:
            text = data.get('文案', '')
        else:
            # 格式化显示，每行一个字段
            if self.home_radio.isChecked():
                text = (
                    f"📝 文案: {data.get('文案', '无')}\n"
                    f"👤 作者: {data.get('作者', '未知')}\n"
                    f"👍 点赞: {data.get('点赞数', 0):,}\n"
                    f"💬 评论: {data.get('评论数', 0):,}\n"
                    f"👁️ 播放: {data.get('播放数', 0):,}\n"
                    f"⭐ 收藏: {data.get('收藏数', 0):,}\n"
                    f"📤 分享: {data.get('分享数', 0):,}\n"
                    f"🎯 推荐: {data.get('推荐数', 0):,}\n"
                    f"📅 发布: {data.get('发布时间', '未知')}"
                )
            else:
                text = (
                    f"📝 文案: {data.get('文案', '无')}\n"
                    f"👤 作者: {data.get('作者', '未知')}\n"
                    f"📅 签名 {data.get('签名', '无')} \n"
                )

        current = self.text_output.toPlainText()
        separator = "\n\n" if current else ""
        self.text_output.setPlainText(current + separator + text)
        self.text_output.verticalScrollBar().setValue(
            self.text_output.verticalScrollBar().maximum()
        )  # 自动滚动到底

    def on_crawl_finished(self):
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.export_button.setEnabled(True)

    def export_data(self):
        if not self.crawled_data:
            QMessageBox.information(self, "提示", "没有可导出的数据。")
            return

        file_path, file_type = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            f"douyin_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "文本文件 (*.txt);;JSON文件 (*.json);;Excel文件 (*.xlsx)"
        )
        if not file_path:
            return

        try:
            pure_mode = self.pure_mode_cb.isChecked()
            if file_type == "文本文件 (*.txt)":
                with open(file_path, 'w', encoding='utf-8') as f:
                    content = "\n\n".join([d.get('文案', '') for d in self.crawled_data if d.get('文案')]) \
                        if pure_mode else "\n\n".join([str(d) for d in self.crawled_data])
                    f.write(content)
            elif file_type == "JSON文件 (*.json)":
                data = [d.get('文案', '') for d in self.crawled_data] if pure_mode else self.crawled_data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif file_type == "Excel文件 (*.xlsx)":
                df_data = [{'文案': d.get('文案', '')} for d in self.crawled_data] if pure_mode else self.crawled_data
                df = pd.DataFrame(df_data)
                df.to_excel(file_path, index=False)

            QMessageBox.information(self, "成功", f"数据已成功导出至：\n{file_path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(file_path).parent)))
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败：{str(e)}")


# =================== 启动应用 ===================
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())