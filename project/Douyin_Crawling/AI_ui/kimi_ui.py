import json, re, time, os, sys
from pathlib import Path
from datetime import datetime
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot, QRectF, QPoint
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                               QLabel, QCheckBox, QFileDialog, QMessageBox)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QLinearGradient, QBrush, Qt, QPen

from DrissionPage import ChromiumPage


# -------------------------------------------------
# 图标生成小工具（保持原样）
# -------------------------------------------------
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


# -------------------------------------------------
# 后台线程：主页爬取
# -------------------------------------------------
class HomePageWorker(QObject):
    finished = Signal(list)
    log = Signal(str)

    def __init__(self, url: str, pages: int):
        super().__init__()
        self.url = url
        self.pages = pages

    def run(self):
        result = []
        try:
            driver = ChromiumPage()
            driver.listen.start('aweme/v1/web/aweme/post/')
            driver.get(self.url)
            for i in range(self.pages):
                self.log.emit(f'正在爬取主页第 {i + 1} 页...')
                resp = driver.listen.wait()
                data_str = resp.response.body
                for aweme in data_str.get("aweme_list", []):
                    dic = {
                        '文案': aweme["desc"],
                        '作者': aweme["author"]["nickname"],
                        '点赞数': aweme["statistics"]["digg_count"],
                        '评论数': aweme["statistics"]["comment_count"],
                        '播放数': aweme["statistics"]["play_count"],
                        '收藏数': aweme["statistics"]["collect_count"],
                        '分享数': aweme["statistics"]["share_count"],
                        '推荐数': aweme["statistics"]["recommend_count"],
                        '发布时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aweme["create_time"]))
                    }
                    result.append(dic)
                driver.scroll.to_bottom()
            driver.quit()
        except Exception as e:
            self.log.emit(f'主页爬取失败：{e}')
        self.finished.emit(result)


# -------------------------------------------------
# 后台线程：搜索爬取
# -------------------------------------------------
class SearchWorker(QObject):
    finished = Signal(list)
    log = Signal(str)

    def __init__(self, theme: str, pages: int):
        super().__init__()
        self.theme = theme
        self.pages = pages

    @staticmethod
    def deal_first_data(data_str: str):
        lines = data_str.strip().splitlines()
        i = 0
        dic_list = []
        while i < len(lines):
            line = lines[i].strip()
            if not line or re.fullmatch(r'[0-9a-fA-F]+', line):
                i += 1
                if i < len(lines):
                    try:
                        data = json.loads(lines[i].strip())
                        for item in data.get("data", []):
                            aweme = item.get("aweme_info", {})
                            dic = {
                                '文案': aweme.get("desc", ""),
                                '作者': aweme.get("author", {}).get('nickname', '无'),
                                '签名': aweme.get("author", {}).get('signature', '无')
                            }
                            dic_list.append(dic)
                    except Exception:
                        pass
                i += 1
            else:
                i += 1
        return dic_list

    @staticmethod
    def deal_not_first_data(data):
        dic_list = []
        for item in data.get("data", []):
            aweme = item.get("aweme_info", {})
            dic = {
                '文案': aweme.get("desc", ""),
                '作者': aweme.get("author", {}).get('nickname', '无'),
                '签名': aweme.get("author", {}).get('signature', '无')
            }
            dic_list.append(dic)
        return dic_list

    def run(self):
        result = []
        try:
            driver = ChromiumPage()
            first_listen = 'aweme/v1/web/general/search/stream/'
            not_first_listen = 'aweme/v1/web/general/search/single/'
            driver.listen.start(first_listen)
            url = f"https://www.douyin.com/jingxuan/search/{self.theme}"
            driver.get(url)
            for i in range(self.pages):
                self.log.emit(f'正在爬取搜索第 {i + 1} 页...')
                resp = driver.listen.wait()
                data_str = resp.response.body
                if i == 0:
                    lst = self.deal_first_data(resp.response.body if isinstance(resp.response.body, str) else '')
                else:
                    lst = self.deal_not_first_data(data_str)
                result.extend(lst)
                driver.scroll.to_bottom()
                driver.listen.start(not_first_listen)
            driver.quit()
        except Exception as e:
            self.log.emit(f'搜索爬取失败：{e}')
        self.finished.emit(result)


# -------------------------------------------------
# 主窗口
# -------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Douyin 文案爬取工具")
        self.setGeometry(100, 100, 900, 600)

        # 图标
        icon = IconGenerator(text="Dc").pixmap()
        self.setWindowIcon(QIcon(icon))

        # 样式
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1e1e1e, stop:1 #333333); }
            QLineEdit { background:#2a2a2a; color:#e0e0e0; border:1px solid #444; border-radius:6px; padding:8px; font-size:14px; }
            QPushButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a3a3a, stop:1 #2a2a2a); color:#d0d0d0; border:1px solid #444; border-radius:6px; padding:10px; font-size:14px; font-weight:bold; }
            QPushButton:hover { background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #444, stop:1 #333); }
            QPushButton:pressed { background:#222; }
            QLabel { color:#ccc; font-size:14px; }
            QTextEdit { background:#252525; color:#e0e0e0; border:1px solid #444; border-radius:6px; padding:10px; font-family:Consolas,Monaco,monospace; font-size:13px; }
        """)

        # 布局
        main_layout = QVBoxLayout()

        # 顶部
        top = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入用户主页URL（主页爬取时必填）")
        self.theme_edit = QLineEdit()
        self.theme_edit.setPlaceholderText("搜索主题（如街拍、健身、美食）")
        self.page_edit = QLineEdit()
        self.page_edit.setPlaceholderText("页数")
        self.pure_cb = QCheckBox("纯净模式")
        self.pure_cb.setStyleSheet("color:white;")
        self.home_btn = QPushButton("爬取主页")
        self.search_btn = QPushButton("爬取搜索")

        top.addWidget(self.url_edit, 2)
        top.addWidget(self.theme_edit, 2)
        top.addWidget(self.page_edit, 1)
        top.addWidget(self.pure_cb)
        top.addWidget(self.home_btn)
        top.addWidget(self.search_btn)
        main_layout.addLayout(top)

        # 文本输出
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        main_layout.addWidget(self.output)

        # 导出
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.export_btn = QPushButton("导出数据")
        bottom.addWidget(self.export_btn)
        main_layout.addLayout(bottom)

        # 状态
        self.status = QLabel("等待开始...")
        main_layout.addWidget(self.status)

        # 设置中心
        w = QWidget()
        w.setLayout(main_layout)
        self.setCentralWidget(w)

        # 数据
        self.all_data = []

        # 事件
        self.home_btn.clicked.connect(self.start_home)
        self.search_btn.clicked.connect(self.start_search)
        self.export_btn.clicked.connect(self.export)

    def log(self, msg):
        self.status.setText(msg)

    def start_home(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入用户主页URL")
            return
        try:
            pages = int(self.page_edit.text()) if self.page_edit.text() else 2
        except ValueError:
            pages = 2
        self._start_thread(HomePageWorker(url, pages))

    def start_search(self):
        theme = self.theme_edit.text().strip()
        if not theme:
            QMessageBox.warning(self, "提示", "请输入搜索主题")
            return
        try:
            pages = int(self.page_edit.text()) if self.page_edit.text() else 2
        except ValueError:
            pages = 2
        self._start_thread(SearchWorker(theme, pages))

    def _start_thread(self, worker_obj):
        # 清理上一次
        self.output.clear()
        self.all_data.clear()
        self.log("正在启动后台线程...")
        self.thread = QThread()
        worker_obj.moveToThread(self.thread)
        worker_obj.finished.connect(self.thread.quit)
        worker_obj.finished.connect(self.on_finish)
        worker_obj.log.connect(self.log)
        self.thread.started.connect(worker_obj.run)
        self.thread.start()

    @Slot(list)
    def on_finish(self, data):
        self.all_data = data
        pure = self.pure_cb.isChecked()
        text = "\n".join([d.get("文案", "") for d in data]) if pure else json.dumps(data, ensure_ascii=False, indent=2)
        self.output.setPlainText(text)
        self.log(f"完成，共 {len(data)} 条")

    def export(self):
        if not self.all_data:
            QMessageBox.information(self, "提示", "没有可导出的数据")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", str(Path.home() / f"douyin_{datetime.now():%Y%m%d_%H%M%S}.json"),
                                              "JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", f"已保存到 {path}")


# -------------------------------------------------
# 启动
# -------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())