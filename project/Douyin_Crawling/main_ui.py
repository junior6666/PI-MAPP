import sys
import csv
import json
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QHeaderView
)
from PySide6.QtCore import Qt
from DrissionPage import ChromiumPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Douyin 数据爬取工具")
        self.setGeometry(100, 100, 800, 600)

        # 创建主布局
        layout = QVBoxLayout()

        # 搜索主题输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索主题（如：自律）")
        layout.addWidget(self.search_input)

        # 页数输入框
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("请输入页数")
        layout.addWidget(self.page_input)

        # 开始按钮
        self.start_button = QPushButton("开始爬取")
        self.start_button.clicked.connect(self.start_crawling)
        layout.addWidget(self.start_button)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["文案", "作者", "签名"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        layout.addWidget(self.export_button)

        # 状态标签
        self.status_label = QLabel("等待开始...")
        layout.addWidget(self.status_label)

        # 设置中心部件
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 初始化变量
        self.data_list = []

    def start_crawling(self):
        # 获取用户输入
        search_theme = self.search_input.text()
        page_count = int(self.page_input.text())

        if not search_theme or not page_count:
            self.status_label.setText("请输入搜索主题和页数！")
            return

        # 清空表格和数据列表
        self.table.setRowCount(0)
        self.data_list.clear()

        # 打开 CSV 文件
        self.f = open('data/data_wenan.csv', mode='w', encoding='utf-8', newline='')
        self.csv_w = csv.DictWriter(self.f, fieldnames=['文案', '作者', '签名'])
        self.csv_w.writeheader()

        # 初始化浏览器
        self.driver = ChromiumPage()

        # 监听数据包
        self.driver.listen.start('aweme/v1/web/general/search/stream/')

        # 构造搜索 URL
        url = f"https://www.douyin.com/jingxuan/search/{search_theme}"
        self.driver.get(url)

        # 爬取多页内容
        for page in range(page_count):
            self.status_label.setText(f"正在爬取第{page + 1}页的内容")
            self.driver.scroll.to_bottom()
            try:
                # 等待监听到数据包
                resp = self.driver.listen.wait()
                data_str = resp.response.body
                self.parse_chunked_data(data_str)
            except Exception as e:
                self.status_label.setText(f"监听数据包时出错: {e}")

        # 关闭文件
        self.f.close()
        self.status_label.setText("爬取完成！")

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
                            dic = {
                                '文案': desc,
                                '作者': nickname,
                                '签名': signature
                            }
                            self.csv_w.writerow(dic)
                            self.data_list.append(dic)
                            self.update_table()

                    except json.JSONDecodeError as e:
                        print(f"JSON 解析失败: {e}")
                i += 1

    def update_table(self):
        row_count = self.table.rowCount()
        for item in self.data_list[row_count:]:
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)
            self.table.setItem(row_count, 0, QTableWidgetItem(item['文案']))
            self.table.setItem(row_count, 1, QTableWidgetItem(item['作者']))
            self.table.setItem(row_count, 2, QTableWidgetItem(item['签名']))

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "CSV 文件 (*.csv)")
        if file_path:
            with open(file_path, mode='w', encoding='utf-8', newline='') as f:
                csv_w = csv.DictWriter(f, fieldnames=['文案', '作者', '签名'])
                csv_w.writeheader()
                csv_w.writerows(self.data_list)
            self.status_label.setText(f"数据已导出到 {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())