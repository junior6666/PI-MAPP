import ast
import sys

import requests
from ultralytics import YOLO

import threading
import cv2
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import csv

class BatchDetectionThread(QThread):
    """批量检测线程"""
    result_ready = Signal(str, object, object, float, object, list)  # 文件路径, 原图, 结果图, 耗时, 检测结果, 类别名称
    progress_updated = Signal(int)
    current_file_changed = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, model, folder_path, confidence_threshold=0.25, supported_formats=None):
        super().__init__()
        self.model = model
        self.folder_path = folder_path
        self.confidence_threshold = confidence_threshold
        self.supported_formats = supported_formats or ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.tif']
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0

    def run(self):
        self.is_running = True

        try:
            # 收集所有支持的图片文件
            image_files = []
            for fmt in self.supported_formats:
                image_files.extend(Path(self.folder_path).rglob(f'*{fmt}'))
                # image_files.extend(Path(self.folder_path).rglob(f'*{fmt.upper()}'))

            total_files = len(image_files)
            if total_files == 0:
                self.status_changed.emit("文件夹中没有找到支持的图片格式")
                self.finished.emit()
                return

            self.status_changed.emit(f"开始批量处理 {total_files} 个文件...")

            # 获取类别名称
            class_names = list(self.model.names.values())

            for i, img_path in enumerate(image_files):
                if not self.is_running:
                    break

                self.current_file_changed.emit(str(img_path))

                try:
                    # 处理单个图片
                    start_time = time.time()
                    results = self.model(str(img_path), conf=self.confidence_threshold, verbose=False)
                    end_time = time.time()

                    # 获取原图
                    original_img = cv2.imread(str(img_path))
                    if original_img is not None:
                        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

                        # 获取结果图
                        result_img = results[0].plot()
                        result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)

                        self.result_ready.emit(str(img_path), original_img, result_img,
                                               end_time - start_time, results, class_names)
                        self.processed_count += 1

                except Exception as e:
                    self.error_occurred.emit(f"处理文件 {img_path.name} 时发生错误: {str(e)}")
                    self.error_count += 1

                # 更新进度
                progress = int(((i + 1) / total_files) * 100)
                self.progress_updated.emit(progress)

                # 状态更新
                if (i + 1) % 10 == 0 or i == total_files - 1:
                    self.status_changed.emit(
                        f"处理进度: {i + 1}/{total_files} (成功: {self.processed_count}, 错误: {self.error_count})")

        except Exception as e:
            self.error_occurred.emit(f"批量处理发生错误: {str(e)}")
        finally:
            self.is_running = False
            # self.finished.emit()

    def stop(self):
        """停止批量检测"""
        self.is_running = False

class MultiCameraMonitorThread(QThread):
    camera_result_ready = Signal(int, object, object, float, object, list)
    camera_error = Signal(int, str)
    camera_status = Signal(int, str)
    finished = Signal()

    def __init__(self, model, camera_ids, conf=0.25, fps=10):
        super().__init__()
        self.model = model
        self.cam_ids = camera_ids
        self.conf = conf
        self.period = 1.0 / fps  # 帧间隔
        self.caps = {}  # {id: cv2.VideoCapture}
        self.active = {}  # {id: bool} 是否在线
        self.last_t = {}  # {id: float}

        # 线程同步
        self._run_flag = True
        self._pause_cond = QWaitCondition()
        self._pause_mutex = QMutex()
        self._paused_flag = False

    # ----------------- 生命周期 -----------------
    def run(self):
        self._open_all()
        if not self.caps:
            self.finished.emit()
            return

        cls_names = list(self.model.names.values())

        while self._run_flag:
            self._pause_mutex.lock()
            if self._paused_flag:
                self._pause_cond.wait(self._pause_mutex)
            self._pause_mutex.unlock()

            for cid in list(self.caps.keys()):
                if not self._run_flag:
                    break
                if not self._grab_and_infer(cid, cls_names):
                    self._reconnect_later(cid)  # 断线后异步重连
            self.msleep(10)

        self._close_all()
        self.finished.emit()

    def stop(self):
        self._run_flag = False
        self.resume()  # 确保等待线程被唤醒
        self.wait()

    def pause(self):
        self._pause_mutex.lock()
        self._paused_flag = True
        self._pause_mutex.unlock()

    def resume(self):
        self._pause_mutex.lock()
        self._paused_flag = False
        self._pause_mutex.unlock()
        self._pause_cond.wakeAll()

    # ----------------- 私有工具 -----------------
    def _open_all(self):
        for cid in self.cam_ids:
            cap = cv2.VideoCapture(cid, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                self.caps[cid] = cap
                self.active[cid] = True
                self.last_t[cid] = 0.0
                self.camera_status.emit(cid, "已连接")
            else:
                self.camera_error.emit(cid, "无法打开")
                cap.release()

    def _close_all(self):
        for cap in self.caps.values():
            cap.release()
        self.caps.clear()

    def _grab_and_infer(self, cid, cls_names):
        cap = self.caps.get(cid)
        if not cap or not cap.isOpened():
            return False

        # 读帧非阻塞：先 grab 再 retrieve
        if not cap.grab():
            return False

        now = time.time()
        if now - self.last_t[cid] < self.period:
            return True  # 未超时，但帧已 grab，避免堆积
        self.last_t[cid] = now

        ret, frame = cap.retrieve()
        if not ret:
            return False

        try:
            t0 = time.time()
            results = self.model(frame, conf=self.conf, verbose=False)
            infer_ms = (time.time() - t0) * 1000
            out_img = results[0].plot()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_out = cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB)
            self.camera_result_ready.emit(cid, rgb_frame, rgb_out,
                                          infer_ms / 1000.0, results, cls_names)
            return True
        except Exception as e:
            self.camera_error.emit(cid, f"推理异常: {e}")
            return False

    def _reconnect_later(self, cid):
        # 简单策略：5 秒后重试
        if self.active.get(cid) is False:
            return
        self.active[cid] = False
        self.camera_status.emit(cid, "重连中…")
        threading.Timer(5.0, lambda: self._try_reopen(cid)).start()

    def _try_reopen(self, cid):
        if cid in self.caps:
            self.caps[cid].release()
        cap = cv2.VideoCapture(cid)
        if cap.isOpened():
            self.caps[cid] = cap
            self.active[cid] = True
            self.camera_status.emit(cid, "已重连")
        else:
            cap.release()
            self._reconnect_later(cid)


class ModelSelectionDialog(QDialog):
    """模型选择对话框"""

    # 常量定义
    LOCAL_TAB_INDEX = 0
    NETWORK_TAB_INDEX = 1
    MODEL_NAME_COL = 0
    SIZE_COL = 1
    MODIFIED_COL = 2
    PATH_COL = 3
    STATUS_COL = 4
    ACTION_COL = 5

    COLUMN_HEADERS_LOCAL = ["模型名称", "大小", "修改时间", "路径"]
    COLUMN_HEADERS_NETWORK = ["模型名称", "大小(MB)", "修改时间", "类别数量", "状态", "操作"]

    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.selected_model = None
        self.network_models = []
        self.init_ui()
        self.load_network_models()

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("🔧 高级模型选择")
        self.setModal(True)
        self.resize(800, 500)
        # self.setStyleSheet(self._get_dialog_stylesheet())

        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 本地模型标签页
        self.local_tab = QWidget()
        self.setup_local_tab()
        self.tab_widget.addTab(self.local_tab, "💻 本地资源模型")

        # 网络模型标签页
        self.network_tab = QWidget()
        self.setup_network_tab()
        self.tab_widget.addTab(self.network_tab, "🌐 网络资源模型")

        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _get_dialog_stylesheet(self):
        """返回对话框样式表"""
        return """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ced4da;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                alternate-background-color: #f8f9fa;
                selection-background-color: #d0ebff;
            }
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 1px 1px 1px 1px;
                font-weight: bold;
                font-size: 8px;
                min-width: 40px;
                min-height: 15px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:pressed {
                background-color: #228be6;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """

    def setup_local_tab(self):
        """设置本地模型标签页"""
        layout = QVBoxLayout(self.local_tab)

        # 路径选择组
        path_group = QGroupBox("📁 自定义模型路径")
        path_layout = QHBoxLayout(path_group)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入自定义模型目录路径...")
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_models)
        path_layout.addWidget(refresh_btn)

        layout.addWidget(path_group)

        # 模型列表组
        models_group = QGroupBox("📋 可用模型")
        models_layout = QVBoxLayout(models_group)

        self.model_table = self._create_table(self.COLUMN_HEADERS_LOCAL, 4)
        self.model_table.doubleClicked.connect(self.accept)
        models_layout.addWidget(self.model_table)

        layout.addWidget(models_group)
        self.refresh_models()

    def setup_network_tab(self):
        """设置网络模型标签页"""
        layout = QVBoxLayout(self.network_tab)

        # 下载路径组
        path_group = QGroupBox("📥 下载设置")
        path_layout = QHBoxLayout(path_group)

        self.download_path_edit = QLineEdit()
        self.download_path_edit.setText(str(Path("pt_models").absolute()))
        self.download_path_edit.setPlaceholderText("模型下载目录路径...")
        path_layout.addWidget(self.download_path_edit)

        browse_download_btn = QPushButton("📂 浏览")
        browse_download_btn.clicked.connect(self.browse_download_path)
        path_layout.addWidget(browse_download_btn)

        layout.addWidget(path_group)

        # 网络模型组
        models_group = QGroupBox("📋 网络模型资源")
        models_layout = QVBoxLayout(models_group)

        self.network_table = self._create_table(self.COLUMN_HEADERS_NETWORK, 6)
        self.network_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.network_table.customContextMenuRequested.connect(self.show_network_context_menu)
        self.network_table.doubleClicked.connect(self.show_network_model_info)
        models_layout.addWidget(self.network_table)

        layout.addWidget(models_group)

    def _create_table(self, headers, column_count):
        """创建标准表格控件"""
        table = QTableWidget()
        table.setColumnCount(column_count)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        return table

    def browse_path(self):
        """浏览自定义路径"""
        path = QFileDialog.getExistingDirectory(self, "选择模型目录")
        if path:
            self.path_edit.setText(path)
            self.refresh_models()

    def browse_download_path(self):
        """浏览下载路径"""
        path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if path:
            self.download_path_edit.setText(path)

    def refresh_models(self):
        """刷新本地模型列表"""
        try:
            custom_path = self.path_edit.text() or None
            models = self.model_manager.scan_models(custom_path)

            self.model_table.setRowCount(len(models))
            for row, model in enumerate(models):
                self.model_table.setItem(row, self.MODEL_NAME_COL, QTableWidgetItem(model['name']))
                self.model_table.setItem(row, self.SIZE_COL, QTableWidgetItem(model['size']))
                self.model_table.setItem(row, self.MODIFIED_COL, QTableWidgetItem(model['modified']))
                self.model_table.setItem(row, self.PATH_COL, QTableWidgetItem(model['path']))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新模型列表失败: {str(e)}")

    def load_network_models(self):
        """加载网络模型数据"""
        try:
            csv_path = Path("pt_files_report.csv")
            if not csv_path.exists():
                QMessageBox.warning(self, "警告", "未找到网络模型数据文件 pt_files_report.csv")
                return

            models_data = self._read_csv_with_encodings(csv_path)
            if not models_data:
                QMessageBox.warning(self, "警告", "无法正确读取网络模型数据文件")
                return

            self.network_models = models_data
            self.refresh_network_models()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载网络模型数据失败: {str(e)}")

    def _read_csv_with_encodings(self, file_path):
        """尝试多种编码读取CSV文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                    if data and '文件名' in data[0]:
                        return data
            except UnicodeDecodeError:
                continue
        return []

    def refresh_network_models(self):
        """刷新网络模型列表"""
        self.network_table.setRowCount(len(self.network_models))

        for row, model in enumerate(self.network_models):
            # 基本信息列
            self.network_table.setItem(row, self.MODEL_NAME_COL, QTableWidgetItem(model['文件名']))
            self.network_table.setItem(row, self.SIZE_COL, QTableWidgetItem(f"{model['大小(MB)']} MB"))
            self.network_table.setItem(row, self.MODIFIED_COL, QTableWidgetItem(model['修改日期']))
            self.network_table.setItem(row, self.STATUS_COL - 1, QTableWidgetItem(model['类别数量']))  # 类别数量列

            # 状态列 - 根据本地文件存在情况判断
            download_path = Path(self.download_path_edit.text())
            local_path = download_path / model['文件名']
            is_downloaded = local_path.exists()
            
            status_text = "已下载" if is_downloaded else "未下载"
            status_color = QColor("#27ae60") if is_downloaded else QColor("#e74c3c")
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.network_table.setItem(row, self.STATUS_COL, status_item)

            # 操作列
            self._create_operation_buttons(row, model)

    def _create_operation_buttons(self, row, model):
        """创建操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # 下载按钮
        download_btn = QPushButton("📥 下载")
        download_btn.setStyleSheet(self._get_dialog_stylesheet())
        download_btn.setFixedSize(70, 28)
        download_btn.clicked.connect(lambda _, r=row: self.download_network_model(r))

        # 复制链接按钮
        copy_btn = QPushButton("🔗 复制")
        copy_btn.setStyleSheet(self._get_dialog_stylesheet())
        copy_btn.setFixedSize(70, 28)
        copy_btn.clicked.connect(lambda _, m=model: self.copy_download_link(m))

        # 检查是否已下载
        download_path = Path(self.download_path_edit.text())

        local_path = download_path / model['文件名']
        is_downloaded = local_path.exists()
        
        if is_downloaded:
            download_btn.setText("✅ 已下载")
            download_btn.setEnabled(False)


        layout.addWidget(download_btn)
        layout.addWidget(copy_btn)
        layout.addStretch()

        self.network_table.setCellWidget(row, self.ACTION_COL, widget)

    def show_network_model_info(self):
        """显示网络模型详细信息"""
        row = self.network_table.currentRow()
        if row < 0 or row >= len(self.network_models):
            return

        model = self.network_models[row]
        try:
            class_info = ast.literal_eval(model['类别信息'])
            class_text = "\n".join([f"{k}: {v}" for k, v in class_info.items()])
        except:
            class_text = model['类别信息']

        info = (
            f"模型名称: {model['文件名']}\n"
            f"大小: {model['大小(MB)']} MB\n"
            f"修改时间: {model['修改日期']}\n"
            f"类别数量: {model['类别数量']}\n\n"
            f"类别信息:\n{class_text}"
        )
        QMessageBox.information(self, "模型详细信息", info)

    def show_network_context_menu(self, pos):
        """显示网络模型右键菜单"""
        row = self.network_table.currentRow()
        if row < 0:
            return

        menu = QMenu(self)
        download_action = menu.addAction("📥 下载模型")
        download_action.triggered.connect(lambda: self.download_network_model(row))
        menu.exec_(self.network_table.viewport().mapToGlobal(pos))

    def download_network_model(self, row):
        """下载网络模型"""
        if row >= len(self.network_models):
            return

        model = self.network_models[row]
        model_name = model['文件名']
        download_dir = Path(self.download_path_edit.text())

        try:
            # 准备下载目录
            download_dir.mkdir(parents=True, exist_ok=True)
            local_path = download_dir / model_name

            # 检查文件存在
            if local_path.exists():
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"模型文件 {model_name} 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # 更新状态
            status_item = self.network_table.item(row, self.STATUS_COL)
            status_item.setText("下载中...")
            status_item.setForeground(QColor("#f39c12"))

            # 执行下载
            self._perform_download(model_name, local_path)

            # 更新状态
            status_item.setText("已下载")
            status_item.setForeground(QColor("#27ae60"))

            # 更新按钮状态
            widget = self.network_table.cellWidget(row, self.ACTION_COL)
            for btn in widget.findChildren(QPushButton):
                if "下载" in btn.text():
                    btn.setText("✅ 已下载")
                    btn.setEnabled(False)

            QMessageBox.information(
                self, "下载完成",
                f"模型 {model_name} 下载完成！\n保存路径: {local_path}"
            )

        except Exception as e:
            # 恢复状态
            status_item = self.network_table.item(row, self.STATUS_COL)
            status_item.setText("下载失败")
            status_item.setForeground(QColor("#e74c3c"))
            QMessageBox.critical(self, "下载失败", f"错误: {str(e)}")

    def _perform_download(self, model_name, save_path):
        """执行实际的下载操作"""
        url = f"https://github.com/JingW-ui/PI-MAPP/releases/download/pt_download/{model_name}"

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def copy_download_link(self, model):
        """复制下载链接到剪贴板"""
        try:
            if not model or '文件名' not in model:
                raise ValueError("模型数据无效")

            url = f"https://github.com/JingW-ui/PI-MAPP/releases/download/pt_download/{model['文件名']}"
            QApplication.clipboard().setText(url)
            QMessageBox.information(self, "复制成功", "下载链接已复制到剪贴板")
        except Exception as e:
            QMessageBox.critical(self, "复制失败", f"错误: {str(e)}")

    def accept(self):
        """确认选择模型"""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == self.LOCAL_TAB_INDEX:
            self._handle_local_selection()
        elif current_tab == self.NETWORK_TAB_INDEX:
            self._handle_network_selection()
        else:
            super().accept()

    def _handle_local_selection(self):
        """处理本地模型选择"""
        row = self.model_table.currentRow()
        if row >= 0:
            self.selected_model = self.model_table.item(row, self.PATH_COL).text()
            super().accept()

    def _handle_network_selection(self):
        """处理网络模型选择"""
        row = self.network_table.currentRow()
        if row < 0:
            return

        model = self.network_models[row]
        model_name = model['文件名']
        local_path = Path(self.download_path_edit.text()) / model_name

        if not local_path.exists():
            QMessageBox.warning(self, "警告", "请先下载选中的网络模型！")
            return

        self.selected_model = str(local_path)
        super().accept()


class DetectionResultWidget(QWidget):
    """检测结果显示组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🎯 检测结果详情表")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        # title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["序号", "类别", "置信度", "坐标 (x,y)", "尺寸 (w×h)"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                font-size: 10pt;
                font-weight: bold;
                height: 12px;     /* 在 QSS 里 height 对表头 section 生效 */
            }
        """)
        self.result_table.setMaximumHeight(200)
        self.result_table.setAlternatingRowColors(True)

        layout.addWidget(self.result_table)

        # 统计信息
        self.stats_label = QLabel("等待检测结果...")
        self.stats_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(236, 240, 241, 0.9), stop:1 rgba(189, 195, 199, 0.9));
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            color: #2c3e50;
            font-weight: bold;
        """)
        layout.addWidget(self.stats_label)

    def update_results(self, results, class_names, inference_time):
        """更新检测结果"""
        if not results or not results[0].boxes or len(results[0].boxes) == 0:
            self.result_table.setRowCount(0)
            self.stats_label.setText("❌ 未检测到目标")
            return

        boxes = results[0].boxes
        confidences = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy()

        # 更新表格
        self.result_table.setRowCount(len(confidences))

        class_counts = {}
        for i, (conf, cls, box) in enumerate(zip(confidences, classes, xyxy)):
            class_name = class_names[cls] if cls < len(class_names) else f"类别{cls}"

            # 统计类别数量
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            self.result_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.result_table.setItem(i, 1, QTableWidgetItem(class_name))

            # 置信度带颜色
            conf_item = QTableWidgetItem(f"{conf:.3f}")
            if conf > 0.8:
                conf_item.setBackground(QColor(46, 204, 113, 100))  # 绿色
            elif conf > 0.5:
                conf_item.setBackground(QColor(241, 196, 15, 100))  # 黄色
            else:
                conf_item.setBackground(QColor(231, 76, 60, 100))  # 红色
            self.result_table.setItem(i, 2, conf_item)

            self.result_table.setItem(i, 3, QTableWidgetItem(f"({box[0]:.0f},{box[1]:.0f})"))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{box[2] - box[0]:.0f}×{box[3] - box[1]:.0f}"))

        # 更新统计信息
        total_objects = len(confidences)
        avg_confidence = np.mean(confidences)

        stats_text = f"✅ 检测到 {total_objects} 个目标 | "
        stats_text += f"🎯 平均置信度: {avg_confidence:.3f} | "
        stats_text += f"⏱️ 耗时: {inference_time:.3f}秒\n"
        stats_text += "📊 类别统计: " + " | ".join([f"{name}: {count}" for name, count in class_counts.items()])

        self.stats_label.setText(stats_text)

class MonitoringWidget(QWidget):
    """监控页面组件"""

    def __init__(self, model_manager, camera_manager):
        super().__init__()
        self.model_manager = model_manager
        self.camera_manager = camera_manager
        self.monitoring_thread = None
        self.camera_labels = {}
        self.current_model = None
        self.start_monitor_btn = QPushButton("🚀 开始监控")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 控制面板
        control_group = QGroupBox("🖥️ 监控控制")
        control_group.setMaximumHeight(80)  # 单位像素
        control_layout = QHBoxLayout(control_group)
        model_layout = QHBoxLayout()
        # 模型选择
        model_camera_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))

        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.init_model_combo()
        model_layout.addWidget(self.model_combo)

        select_model_btn = QPushButton("🔧 选择模型")
        select_model_btn.clicked.connect(self.select_model)
        model_layout.addWidget(select_model_btn)
        model_camera_layout.addLayout(model_layout)

        # 摄像头选择
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel("摄像头:"))

        self.camera_list = QListWidget()
        # self.camera_list.setMaximumHeight(20)
        self.camera_list.setMaximumWidth(300)
        self.camera_list.setSelectionMode(QListWidget.MultiSelection)
        self.refresh_cameras()
        camera_layout.addWidget(self.camera_list)

        refresh_camera_btn = QPushButton("🔄 刷新")
        refresh_camera_btn.clicked.connect(self.refresh_cameras)
        camera_layout.addWidget(refresh_camera_btn)
        camera_layout.addStretch()

        model_camera_layout.addLayout(camera_layout)
        control_layout.addLayout(model_camera_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()

        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.start_monitor_btn.setEnabled(True)
        btn_layout.addWidget(self.start_monitor_btn)

        self.stop_monitor_btn = QPushButton("⏸️ 暂停")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        btn_layout.addWidget(self.stop_monitor_btn)

        self.clear_monitor_btn = QPushButton("🗑️ 清除监控")
        self.clear_monitor_btn.clicked.connect(self.clear_monitoring)
        self.clear_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_monitor_btn)

        control_layout.addLayout(btn_layout)

        layout.addWidget(control_group)

        # 监控显示区域
        self.monitor_scroll = QScrollArea()
        self.monitor_scroll.setStyleSheet("""
            QScrollArea {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(236, 240, 241, 0.9),
                    stop:1 rgba(189, 195, 199, 0.9));
                border-radius: 8px;
            }
            QScrollArea > QWidget > QWidget {   /* viewport */
                background: transparent;
            }
            QScrollArea::corner {               /* 右下角空白三角 */
                background: transparent;
            }
        """)
        self.monitor_widget = QWidget()
        self.monitor_layout = QGridLayout(self.monitor_widget)
        self.monitor_scroll.setWidget(self.monitor_widget)
        self.monitor_scroll.setWidgetResizable(True)

        layout.addWidget(self.monitor_scroll)

    def init_model_combo(self):
        """初始化模型下拉框"""
        self.model_combo.clear()
        models = self.model_manager.scan_models()

        if not models:
            self.model_combo.addItem("无可用模型")
            self.model_combo.setEnabled(False)
        else:
            self.model_combo.addItems([model['name'] for model in models])
            self.model_combo.setEnabled(True)
            self.try_load_default_model()

    def try_load_default_model(self):
        """尝试加载默认模型"""
        if self.model_combo.count() > 0 and self.model_combo.itemText(0) != "无可用模型":
            first_model = self.model_combo.itemText(0)
            self.load_model_by_name(first_model)

    def load_model_by_name(self, model_name):
        """根据名称加载模型"""
        models = self.model_manager.scan_models()
        for model in models:
            if model['name'] == model_name:
                self.load_model(model['path'])
                break

    def on_model_changed(self, model_text):
        """模型选择改变"""
        if model_text != "无可用模型":
            self.load_model_by_name(model_text)

    def load_model(self, model_path):
        """加载模型"""
        try:
            self.current_model = YOLO(model_path)
            self.start_monitor_btn.setEnabled(True)
            return True
        except Exception as e:
            pass

            return False

    def select_model(self):
        """选择模型"""
        dialog = ModelSelectionDialog(self.model_manager, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_model:
            try:
                self.current_model = YOLO(dialog.selected_model)
                model_name = Path(dialog.selected_model).name
                self.model_combo.clear()
                self.model_combo.addItem(model_name)
                self.start_monitor_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"模型加载成功: {model_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"模型加载失败: {str(e)}")

    def refresh_cameras(self):
        """刷新摄像头列表"""
        self.camera_manager.scan_cameras()
        self.camera_list.clear()

        for camera in self.camera_manager.get_available_cameras():
            item = QListWidgetItem(f"📹 {camera['name']} ({camera['resolution']})")
            item.setData(Qt.UserRole, camera['id'])
            self.camera_list.addItem(item)

    def start_monitoring(self):
        """开始监控"""
        if not self.current_model:
            QMessageBox.warning(self, "警告", "请先选择模型")
            return

        selected_items = self.camera_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择至少一个摄像头")
            return

        camera_ids = [item.data(Qt.UserRole) for item in selected_items]

        # 清空之前的显示
        self.clear_monitor_display()
        self.clear_monitor_btn.setEnabled(True)

        # 创建显示标签
        self.create_camera_labels(camera_ids)
        # 设置等高宽
        self.set_equal_column_stretch()
        # 启动监控线程
        self.monitoring_thread = MultiCameraMonitorThread(self.current_model, camera_ids)
        self.monitoring_thread.camera_result_ready.connect(self.update_camera_display)
        self.monitoring_thread.camera_error.connect(self.handle_camera_error)
        self.monitoring_thread.finished.connect(self.on_monitoring_finished)

        self.monitoring_thread.start()

        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)

    def stop_monitoring(self):
        """暂停/继续监控"""
        if self.monitoring_thread and self.monitoring_thread._run_flag:
            if self.monitoring_thread._paused_flag:  # 监测是否已暂停
                self.monitoring_thread.resume()  # 恢复
                self.stop_monitor_btn.setText("⏸️ 暂停")  # 按钮文字：暂停
            else:
                self.monitoring_thread.pause()  # 暂停
                self.stop_monitor_btn.setText("▶️ 继续")  # 按钮文字：继续

    def clear_monitoring(self):
        """停止监控"""
        self.monitoring_thread.stop()
        self.clear_monitor_display()
        self.clear_monitor_btn.setEnabled(False)

    def create_camera_labels(self, camera_ids):
        """创建摄像头显示标签"""
        self.camera_labels = {}

        cols = 2  # 每行2个摄像头
        for i, camera_id in enumerate(camera_ids):
            row = i // cols
            col = i % cols

            # 创建摄像头组
            camera_group = QGroupBox(f"📹 摄像头 {camera_id}")
            camera_group.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(248, 249, 250, 0.9), stop:1 rgba(233, 236, 239, 0.9));
                color: #7f8c8d;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;

            """)
            # camera_group.setMaximumHeight(350)
            camera_layout = QVBoxLayout(camera_group)

            # 图像显示标签
            image_label = QLabel("等待连接...")
            image_label.setMinimumSize(300, 240)
            image_label.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(248, 249, 250, 0.9), stop:1 rgba(233, 236, 239, 0.9));
                color: #7f8c8d;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;

            """)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setScaledContents(True)

            camera_layout.addWidget(image_label, stretch=6)

            # 状态标签
            status_label = QLabel("状态: 初始化中...")
            status_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            camera_layout.addWidget(status_label)
            camera_layout.addStretch()

            self.camera_labels[camera_id] = {
                'image': image_label,
                'status': status_label,
                'group': camera_group
            }

            self.monitor_layout.addWidget(camera_group, row, col)

    def set_equal_column_stretch(self):
        for c in range(self.monitor_layout.columnCount()):
            self.monitor_layout.setColumnStretch(c, 1)
        for r in range(self.monitor_layout.rowCount()):
            self.monitor_layout.setRowStretch(r, 1)

    def clear_monitor_display(self):
        """清空监控显示"""
        for camera_id in list(self.camera_labels.keys()):
            self.camera_labels[camera_id]['group'].deleteLater()
        self.camera_labels.clear()

    def update_camera_display(self, camera_id, original_img, result_img, inference_time, results, class_names):
        """更新摄像头显示"""
        if camera_id not in self.camera_labels:
            return

        # 显示结果图
        self.display_image(result_img, self.camera_labels[camera_id]['image'])

        # 更新状态
        if results and results[0].boxes and len(results[0].boxes) > 0:
            object_count = len(results[0].boxes)
            self.camera_labels[camera_id]['status'].setText(
                f"状态: 检测到 {object_count} 个目标 | 耗时: {inference_time:.3f}s"
            )
        else:
            self.camera_labels[camera_id]['status'].setText(
                f"状态: 无目标 | 耗时: {inference_time:.3f}s"
            )

    def handle_camera_error(self, camera_id, error_msg):
        """处理摄像头错误"""
        if camera_id in self.camera_labels:
            self.camera_labels[camera_id]['status'].setText(f"错误: {error_msg}")
            self.camera_labels[camera_id]['status'].setStyleSheet("color: red; font-size: 10px;")

    def on_monitoring_finished(self):
        """监控结束"""
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)

        for camera_id in self.camera_labels:
            self.camera_labels[camera_id]['status'].setText("状态: 已停止")

    def display_image(self, img_array, label):
        """显示图像"""
        if img_array is None:
            return

        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)

class StyleManager:
    """样式管理器 - 提供渐变和现代化UI样式"""

    @staticmethod
    def get_main_stylesheet():
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }

            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid rgba(52, 152, 219, 0.7);
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(245, 245, 245, 0.9));
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton {
                padding: 2px 8px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                color: white;
                min-width: 65px;
                min-height: 25px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                transform: translateY(-1px);
            }

            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }

            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
                color: #7f8c8d;
            }

            QComboBox {
                padding: 2px 8px;
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #f8f9fa);
                font-size: 12px;
                min-width: 150px;
                min-height: 25px;
            }

            QComboBox:focus {
                border-color: #3498db;
                background: white;
            }

            QProgressBar {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 11px;
                max-height: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                border-radius: 6px;
                margin: 1px;
            }

            QTextEdit {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.95);
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                selection-background-color: #3498db;
            }

            QSlider::groove:horizontal {
                border: 1px solid rgba(189, 195, 199, 0.5);
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: 2px solid #2980b9;
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 12px;
            }

            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }

            QSpinBox, QDoubleSpinBox {
                padding: 6px 10px;
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 6px;
                background: white;
                min-width: 80px;
                font-size: 12px;
            }

            QTabWidget::pane {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(245, 245, 245, 0.95));
                margin-top: 5px;
            }

            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 12px 25px;
                margin-right: 3px;
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
            }

            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-color: rgba(52, 152, 219, 0.7);
            }

            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5dbdb, stop:1 #bdc3c7);
            }

            QTableWidget {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: white;
                gridline-color: rgba(189, 195, 199, 0.3);
                selection-background-color: rgba(52, 152, 219, 0.2);
                alternate-background-color: rgba(248, 249, 250, 0.5);
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
            }

            QTableWidget::item:selected {
                background: rgba(52, 152, 219, 0.3);
                color: #2c3e50;
            }

            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }

            QListWidget {
                border: 2px solid rgba(189, 195, 199, 0.5);
                border-radius: 8px;
                background: white;
                selection-background-color: rgba(52, 152, 219, 0.2);
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(189, 195, 199, 0.2);
            }

            QListWidget::item:selected {
                background: rgba(52, 152, 219, 0.3);
                color: #2c3e50;
            }

            QScrollBar:vertical {
                background: rgba(236, 240, 241, 0.5);
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
            }
        """

    @staticmethod
    def get_image_label_style():
        return """
            border: 3px solid rgba(52, 152, 219, 0.3);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(248, 249, 250, 0.9), stop:1 rgba(233, 236, 239, 0.9));
            color: #7f8c8d;
            font-weight: bold;
            font-size: 14px;
            border-radius: 10px;
            padding: 15px;
        """

class CameraManager:
    """摄像头管理器 - 处理多摄像头检测和管理"""

    def __init__(self):
        self.cameras = []
        self.scan_cameras()

    def scan_cameras(self):
        """扫描可用摄像头"""
        self.cameras = []

        # 检测摄像头（检测前8个索引）
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    # 获取摄像头信息
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)

                    camera_info = {
                        'id': i,
                        'name': f"摄像头 {i}",
                        'resolution': f"{width}x{height}",
                        'fps': fps if fps > 0 else 30,
                        'available': True
                    }
                    self.cameras.append(camera_info)
                cap.release()

        # 如果没有摄像头，添加虚拟摄像头用于测试
        if not self.cameras:
            self.cameras.append({
                'id': -1,
                'name': "未检测到摄像头",
                'resolution': "N/A",
                'fps': 0,
                'available': False
            })

    def get_available_cameras(self):
        """获取可用摄像头列表"""
        return [cam for cam in self.cameras if cam['available']]

    def get_camera_info(self, camera_id):
        """获取摄像头信息"""
        for cam in self.cameras:
            if cam['id'] == camera_id:
                return cam
        return None

class ModelManager:
    """模型管理器 - 处理模型扫描和加载"""

    def __init__(self):
        self.models_paths = [
            Path("pt_models"),
            Path("models"),
            Path("weights"),
        ]
        self.current_model = None
        self.class_names = []

    def scan_models(self, custom_path=None):
        """扫描模型文件"""
        models = []
        search_paths = self.models_paths.copy()

        if custom_path and Path(custom_path).exists():
            search_paths.insert(0, Path(custom_path))

        for model_dir in search_paths:
            if model_dir.exists():
                try:
                    pt_files = sorted(model_dir.glob("*.pt"))
                    for pt_file in pt_files:
                        models.append({
                            'name': pt_file.name,
                            'path': str(pt_file),
                            'size': self._get_file_size(pt_file),
                            'modified': self._get_modification_time(pt_file)
                        })
                except Exception as e:
                    print(f"扫描目录 {model_dir} 时出错: {e}")

        return models

    def load_model(self, model_path):
        """加载模型"""
        try:
            self.current_model = YOLO(model_path)
            self.class_names = list(self.current_model.names.values())
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def get_class_names(self):
        """获取类别名称"""
        return self.class_names

    def _get_file_size(self, file_path):
        """获取文件大小"""
        try:
            size = file_path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown"

    def _get_modification_time(self, file_path):
        """获取修改时间"""
        try:
            timestamp = file_path.stat().st_mtime
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except:
            return "Unknown"

class DetectionThread(QThread):
    """增强的检测线程"""
    result_ready = Signal(object, object, float, object, list)  # 原图, 结果图, 耗时, 检测结果, 类别名称
    progress_updated = Signal(int)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    fps_updated = Signal(float)
    finished = Signal()

    def __init__(self, model, source_type, source_path=None, camera_id=0, confidence_threshold=0.25):
        super().__init__()
        self.model = model
        self.source_type = source_type
        self.source_path = source_path
        self.camera_id = camera_id
        self.confidence_threshold = confidence_threshold
        self.is_running = False
        self.is_paused = False
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()

    def run(self):
        self.is_running = True
        try:
            if self.source_type == 'image':
                self._process_image()
            elif self.source_type == 'video':
                self._process_video()
            elif self.source_type == 'camera':
                self._process_camera()
        except Exception as e:
            self.error_occurred.emit(f"检测过程发生错误: {str(e)}")
        finally:
            self.is_running = False
            self.finished.emit()

    def _process_image(self):
        """处理单张图片"""
        if not self.source_path or not Path(self.source_path).exists():
            self.error_occurred.emit("图片文件不存在")
            return

        self.status_changed.emit("正在处理图片...")

        start_time = time.time()
        results = self.model(self.source_path, conf=self.confidence_threshold, verbose=False)
        end_time = time.time()

        original_img = cv2.imread(self.source_path)
        if original_img is None:
            self.error_occurred.emit("无法读取图片文件")
            return

        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        result_img = results[0].plot()
        result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        class_names = list(self.model.names.values())

        self.result_ready.emit(original_img, result_img, end_time - start_time, results, class_names)
        self.progress_updated.emit(100)

    def _process_video(self):
        """处理视频文件"""
        if not self.source_path or not Path(self.source_path).exists():
            self.error_occurred.emit("视频文件不存在")
            return

        cap = cv2.VideoCapture(self.source_path)
        if not cap.isOpened():
            self.error_occurred.emit("无法打开视频文件")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        class_names = list(self.model.names.values())

        self.status_changed.emit(f"开始处理视频 (共{total_frames}帧)...")

        while cap.isOpened() and self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                break

            start_time = time.time()
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            end_time = time.time()

            original_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result_img = results[0].plot()
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)

            self.result_ready.emit(original_img, result_img, end_time - start_time, results, class_names)

            frame_count += 1
            if total_frames > 0:
                progress = int((frame_count / total_frames) * 100)
                self.progress_updated.emit(progress)

            # 更新FPS
            self._update_fps()

            # 状态更新（每30帧更新一次）
            if frame_count % 30 == 0:
                current_fps = self._get_current_fps()
                self.status_changed.emit(f"处理中... {frame_count}/{total_frames} 帧 (FPS: {current_fps:.1f})")

            time.sleep(0.033)  # 约30fps

        cap.release()

    def _process_camera(self):
        """处理摄像头"""
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            self.error_occurred.emit(f"无法打开摄像头 {self.camera_id}")
            return

        # 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        class_names = list(self.model.names.values())
        self.status_changed.emit(f"摄像头 {self.camera_id} 已启动...")

        while cap.isOpened() and self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                break

            start_time = time.time()
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            end_time = time.time()

            original_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result_img = results[0].plot()
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)

            self.result_ready.emit(original_img, result_img, end_time - start_time, results, class_names)

            # 更新FPS
            self._update_fps()

            # 状态更新（每60帧更新一次）
            if self.frame_count % 60 == 0:
                current_fps = self._get_current_fps()
                self.status_changed.emit(f"摄像头运行中 (FPS: {current_fps:.1f})")

            time.sleep(0.033)  # 约30fps

        cap.release()

    def _update_fps(self):
        """更新FPS计算"""
        self.frame_count += 1
        self.fps_counter += 1

        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_updated.emit(fps)
            self.fps_counter = 0
            self.last_fps_time = current_time

    def _get_current_fps(self):
        """获取当前FPS"""
        current_time = time.time()
        if current_time - self.last_fps_time > 0:
            return self.fps_counter / (current_time - self.last_fps_time)
        return 0

    def pause(self):
        self.is_paused = True
        self.status_changed.emit(f"暂停中...")

    def resume(self):
        self.is_paused = False
        self.status_changed.emit(f"恢复检测")


    def stop(self):
        self.is_running = False
        self.status_changed.emit(f"检测结束!")

class EnhancedDetectionUI(QMainWindow):
    """增强的检测UI主窗口"""

    def __init__(self):
        super().__init__()
        self.model = None
        self.detection_thread = None
        self.batch_detection_thread = None
        self.current_source_type = 'image'
        self.current_source_path = None
        self.confidence_threshold = 0.25
        self.batch_results = []
        self.current_batch_index = 0

        # 管理器
        self.camera_manager = CameraManager()
        self.model_manager = ModelManager()
        self.log_text = QTextEdit()
        self.init_ui()
        self.setWindowIcon(self.create_enhanced_icon())

        # 应用样式
        self.setStyleSheet(StyleManager.get_main_stylesheet())


    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🚀 Enhanced Object Detection System v2.0")
        self.setGeometry(100, 100, 1400, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧控制面板
        left_widget = self.create_control_panel()
        left_widget.setMaximumWidth(500)
        left_widget.setMinimumWidth(400)

        # 右侧显示区域
        right_widget = self.create_display_area()

        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([450, 1250])

        main_layout.addWidget(main_splitter)

        # 状态栏
        self.statusBar().showMessage("🎯 就绪 - 请选择模型和检测源")

        # 尝试加载默认模型
        self.try_load_default_model()


    def create_control_panel(self):
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 模型配置
        model_group = QGroupBox("🤖 模型配置")
        model_layout = QVBoxLayout(model_group)

        # 模型选择
        model_select_layout = QHBoxLayout()
        model_select_layout.addWidget(QLabel("选择模型:"))

        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.init_model_combo()
        model_select_layout.addWidget(self.model_combo)

        advanced_model_btn = QPushButton("🔧 高级")
        advanced_model_btn.clicked.connect(self.show_model_selection_dialog)
        advanced_model_btn.setMaximumWidth(80)
        model_select_layout.addWidget(advanced_model_btn)

        model_layout.addLayout(model_select_layout)

        # 置信度配置
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度阈值:"))

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setMinimum(1)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(self.on_confidence_changed)
        conf_layout.addWidget(self.conf_slider)

        self.conf_spinbox = QDoubleSpinBox()
        self.conf_spinbox.setRange(0.01, 1.0)
        self.conf_spinbox.setSingleStep(0.01)
        self.conf_spinbox.setValue(0.25)
        self.conf_spinbox.setDecimals(2)
        self.conf_spinbox.valueChanged.connect(self.on_confidence_spinbox_changed)
        conf_layout.addWidget(self.conf_spinbox)

        model_layout.addLayout(conf_layout)
        layout.addWidget(model_group)

        # 检测源配置
        source_group = QGroupBox("📁 检测源配置")
        source_layout = QVBoxLayout(source_group)

        # 检测模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("检测模式:"))

        self.source_combo = QComboBox()
        self.source_combo.addItems(["📷 单张图片", "🎬 视频文件", "📹 摄像头", "📂 文件夹批量"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        mode_layout.addWidget(self.source_combo)
        source_layout.addLayout(mode_layout)

        # 摄像头选择（仅摄像头模式显示）
        self.camera_select_layout = QHBoxLayout()
        self.camera_select_layout.addWidget(QLabel("摄像头:"))

        self.camera_combo = QComboBox()
        self.refresh_camera_list()
        self.camera_select_layout.addWidget(self.camera_combo)

        refresh_camera_btn = QPushButton("🔄")
        refresh_camera_btn.setMaximumWidth(40)
        refresh_camera_btn.clicked.connect(self.refresh_camera_list)
        self.camera_select_layout.addWidget(refresh_camera_btn)

        source_layout.addLayout(self.camera_select_layout)

        # 文件选择
        file_layout = QHBoxLayout()
        self.select_file_btn = QPushButton("📁 选择文件/文件夹")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        source_layout.addLayout(file_layout)

        # 当前文件显示
        self.current_file_label = QLabel("未选择文件")
        self.current_file_label.setWordWrap(True)
        self.current_file_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        source_layout.addWidget(self.current_file_label)

        layout.addWidget(source_group)

        # 检测控制
        control_group = QGroupBox("🎮 检测控制")
        control_layout = QVBoxLayout(control_group)

        # 控制按钮
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ 开始检测")
        self.start_btn.clicked.connect(self.start_detection)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.clicked.connect(self.pause_detection)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        control_layout.addLayout(btn_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        control_layout.addLayout(progress_layout)

        layout.addWidget(control_group)

        # 检测结果详情
        # self.result_detail_widget = DetectionResultWidget()
        # layout.addWidget(self.result_detail_widget)

        # 日志区域
        log_group = QGroupBox("📋 运行日志")
        log_layout = QVBoxLayout(log_group)

        # self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(180)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)

        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()

        self.clear_log_btn = QPushButton("🗑️ 清除")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMaximumWidth(100)
        log_btn_layout.addWidget(self.clear_log_btn)

        log_layout.addLayout(log_btn_layout)
        layout.addWidget(log_group)

        # layout.addStretch()
        return widget

    def create_display_area(self):
        """创建显示区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 实时检测标签页
        realtime_tab = self.create_realtime_tab()
        self.tab_widget.addTab(realtime_tab, "🎯 实时检测")

        # 批量结果标签页
        batch_tab = self.create_batch_tab()
        self.tab_widget.addTab(batch_tab, "📊 批量结果")

        # 监控页面标签页
        monitor_tab = MonitoringWidget(self.model_manager, self.camera_manager)
        self.tab_widget.addTab(monitor_tab, "🖥️ 实时监控")
        layout.addWidget(self.tab_widget)
        return widget

    def create_realtime_tab(self):
        """创建实时检测标签页"""
        widget = QWidget()
        layout_top = QVBoxLayout(widget)
        layout = QHBoxLayout(widget)

        # 原图显示
        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)

        original_title = QLabel("📷 源")
        original_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin: 0px;")
        original_layout.addWidget(original_title)

        self.original_label = QLabel("等待加载源...")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setMinimumSize(500, 400)
        self.original_label.setStyleSheet(StyleManager.get_image_label_style())
        original_layout.addWidget(self.original_label)

        # 结果图显示
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)

        result_title = QLabel("🎯 检测结果")
        result_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin: 0px;")
        result_layout.addWidget(result_title)

        self.result_label = QLabel("等待检测结果...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(500, 400)
        self.result_label.setStyleSheet(StyleManager.get_image_label_style())
        result_layout.addWidget(self.result_label)

        layout.addWidget(original_container)
        layout.addWidget(result_container)
        layout_top.addLayout(layout)
        # 检测结果详情
        self.result_detail_widget = DetectionResultWidget()
        layout_top.addWidget(self.result_detail_widget)
        layout_top.addStretch()
        return widget

    def create_batch_tab(self):
        """创建批量结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 控制栏
        control_bar = QHBoxLayout()
        control_bar.addWidget(QLabel("📊 批量检测结果:"))
        control_bar.addStretch()

        # 导航按钮
        self.prev_result_btn = QPushButton("⬅️ 上一个")
        self.prev_result_btn.clicked.connect(self.show_prev_result)
        self.prev_result_btn.setEnabled(False)
        control_bar.addWidget(self.prev_result_btn)

        self.result_index_label = QLabel("0/0")
        self.result_index_label.setStyleSheet("font-weight: bold; margin: 0 10px;")
        control_bar.addWidget(self.result_index_label)

        self.next_result_btn = QPushButton("下一个 ➡️")
        self.next_result_btn.clicked.connect(self.show_next_result)
        self.next_result_btn.setEnabled(False)
        control_bar.addWidget(self.next_result_btn)

        # 保存按钮
        self.save_results_btn = QPushButton("💾 保存结果")
        self.save_results_btn.clicked.connect(self.save_batch_results)
        self.save_results_btn.setEnabled(False)
        control_bar.addWidget(self.save_results_btn)

        # 清空按钮
        self.clear_results_btn = QPushButton("🗑️ 清空结果")
        self.clear_results_btn.clicked.connect(self.clear_batch_results)
        self.clear_results_btn.setEnabled(False)
        control_bar.addWidget(self.clear_results_btn)

        layout.addLayout(control_bar)

        # 图像显示
        image_layout = QHBoxLayout()

        self.batch_original_label = QLabel("📷 批量检测: 原图")
        self.batch_original_label.setAlignment(Qt.AlignCenter)
        self.batch_original_label.setMinimumSize(500, 400)
        self.batch_original_label.setStyleSheet(StyleManager.get_image_label_style())

        self.batch_result_label = QLabel("🎯 批量检测: 结果图")
        self.batch_result_label.setAlignment(Qt.AlignCenter)
        self.batch_result_label.setMinimumSize(500, 400)
        self.batch_result_label.setStyleSheet(StyleManager.get_image_label_style())

        image_layout.addWidget(self.batch_original_label)
        image_layout.addWidget(self.batch_result_label)
        layout.addLayout(image_layout)

        # 结果信息
        self.batch_info_label = QLabel("📁 选择文件夹开始批量检测...")
        self.batch_info_label.setWordWrap(True)
        self.batch_info_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(236, 240, 241, 0.9), stop:1 rgba(189, 195, 199, 0.9));
            padding: 15px;
            border-radius: 8px;
            font-size: 12px;
            color: #2c3e50;
        """)
        layout.addWidget(self.batch_info_label)

        return widget

    def init_model_combo(self):
        """初始化模型下拉框"""
        self.model_combo.clear()
        models = self.model_manager.scan_models()

        if not models:
            self.model_combo.addItem("无可用模型")
            self.model_combo.setEnabled(False)
        else:
            self.model_combo.addItems([model['name'] for model in models])
            self.model_combo.setEnabled(True)

    def try_load_default_model(self):
        """尝试加载默认模型"""
        if self.model_combo.count() > 0 and self.model_combo.itemText(0) != "无可用模型":
            first_model = self.model_combo.itemText(0)
            self.load_model_by_name(first_model)

    def load_model_by_name(self, model_name):
        """根据名称加载模型"""
        models = self.model_manager.scan_models()
        for model in models:
            if model['name'] == model_name:
                self.load_model(model['path'])
                break

    def load_model(self, model_path):
        """加载模型"""
        try:
            self.model = YOLO(model_path)
            self.log_message(f"✅ 模型加载成功: {Path(model_path).name}")
            self.update_button_states()
            return True
        except Exception as e:
            self.log_message(f"❌ 模型加载失败: {str(e)}")
            self.model = None
            return False

    def show_model_selection_dialog(self):
        """显示模型选择对话框"""
        dialog = ModelSelectionDialog(self.model_manager, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_model:
            if self.load_model(dialog.selected_model):
                model_name = Path(dialog.selected_model).name
                # 更新下拉框
                index = self.model_combo.findText(model_name)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                else:
                    self.model_combo.addItem(model_name)
                    self.model_combo.setCurrentText(model_name)

    def refresh_camera_list(self):
        """刷新摄像头列表"""
        self.camera_manager.scan_cameras()
        self.camera_combo.clear()

        cameras = self.camera_manager.get_available_cameras()
        if cameras:
            for camera in cameras:
                self.camera_combo.addItem(f"{camera['name']} ({camera['resolution']})", camera['id'])
        else:
            self.camera_combo.addItem("未检测到摄像头", -1)

    def on_model_changed(self, model_text):
        """模型选择改变"""
        if model_text != "无可用模型":
            self.load_model_by_name(model_text)

    def on_confidence_changed(self, value):
        """置信度滑块改变"""
        conf_value = value / 100.0
        self.confidence_threshold = conf_value
        self.conf_spinbox.blockSignals(True)
        self.conf_spinbox.setValue(conf_value)
        self.conf_spinbox.blockSignals(False)

    def on_confidence_spinbox_changed(self, value):
        """置信度数值框改变"""
        self.confidence_threshold = value
        self.conf_slider.blockSignals(True)
        self.conf_slider.setValue(int(value * 100))
        self.conf_slider.blockSignals(False)

    def on_source_changed(self, source_text):
        """检测源改变"""
        source_map = {
            "📷 单张图片": "image",
            "🎬 视频文件": "video",
            "📹 摄像头": "camera",
            "📂 文件夹批量": "batch"
        }
        self.current_source_type = source_map.get(source_text)

        # 显示/隐藏摄像头选择
        is_camera = self.current_source_type == "camera"
        for i in range(self.camera_select_layout.count()):
            item = self.camera_select_layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(is_camera)

        self.current_source_path = None
        self.current_file_label.setText("未选择文件")
        self.clear_display_windows()
        self.update_button_states()

    def update_button_states(self):
        """更新按钮状态"""
        has_model = self.model is not None

        if self.current_source_type == "camera":
            has_source = self.camera_combo.currentData() != -1
            self.select_file_btn.setEnabled(False)
        else:
            has_source = self.current_source_path is not None
            self.select_file_btn.setEnabled(True)

        self.start_btn.setEnabled(has_model and has_source)

    def select_file(self):
        """选择文件或文件夹"""
        if self.current_source_type == "image":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;所有文件 (*)"
            )
        elif self.current_source_type == "video":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频", "",
                "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
            )
        elif self.current_source_type == "batch":
            file_path = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        else:
            return

        if file_path:
            self.current_source_path = file_path
            self.current_file_label.setText(f"📁 已选择: {Path(file_path).name}")
            self.log_message(f"📁 已选择: {file_path}")
            self.update_button_states()

            if self.current_source_type in ["image", "video"]:
                self.preview_file(file_path)

    def preview_file(self, file_path):
        """预览文件"""
        try:
            if self.current_source_type == "image":
                img = cv2.imread(file_path)
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    self.display_image(img_rgb, self.original_label)
                    self.result_label.clear()
                    self.result_label.setText("等待检测结果...")
        except Exception as e:
            self.log_message(f"❌ 预览文件失败: {str(e)}")

    def start_detection(self):
        """开始检测"""
        if not self.model:
            self.log_message("❌ 错误: 模型未加载")
            return

        if self.current_source_type == "batch":
            self.start_batch_detection()
        else:
            self.start_single_detection()

    def start_single_detection(self):
        """开始单个检测"""
        camera_id = 0
        if self.current_source_type == "camera":
            camera_id = self.camera_combo.currentData()
            if camera_id == -1:
                self.log_message("❌ 错误: 没有可用的摄像头")
                return

        self.detection_thread = DetectionThread(
            self.model, self.current_source_type, self.current_source_path, camera_id, self.confidence_threshold
        )
        self.detection_thread.result_ready.connect(self.on_detection_result)
        self.detection_thread.progress_updated.connect(self.progress_bar.setValue)
        self.detection_thread.status_changed.connect(self.statusBar().showMessage)
        self.detection_thread.error_occurred.connect(self.log_message)
        self.detection_thread.finished.connect(self.on_detection_finished)

        self.update_detection_ui_state(True)
        self.tab_widget.setCurrentIndex(0)  # 切换到实时检测

        self.detection_thread.start()
        self.log_message(f"🚀 开始{self.current_source_type}检测...")

    def start_batch_detection(self):
        """开始批量检测"""
        self.batch_results.clear()

        self.batch_detection_thread = BatchDetectionThread(
            self.model, self.current_source_path, self.confidence_threshold
        )
        self.batch_detection_thread.result_ready.connect(self.on_batch_result)
        self.batch_detection_thread.progress_updated.connect(self.progress_bar.setValue)
        self.batch_detection_thread.current_file_changed.connect(self.statusBar().showMessage)
        self.batch_detection_thread.finished.connect(self.on_batch_finished)

        self.update_detection_ui_state(True)
        self.tab_widget.setCurrentIndex(1)  # 切换到批量结果

        self.batch_detection_thread.start()
        self.log_message("🚀 开始批量检测...")

    def update_detection_ui_state(self, detecting):
        """更新检测状态的UI"""
        self.start_btn.setEnabled(not detecting)
        self.pause_btn.setEnabled(detecting and self.current_source_type != "batch")
        self.stop_btn.setEnabled(detecting)
        self.source_combo.setEnabled(not detecting)
        self.select_file_btn.setEnabled(not detecting and self.current_source_type != "camera")
        self.model_combo.setEnabled(not detecting)

    def pause_detection(self):
        """暂停/恢复检测"""
        if self.detection_thread and self.detection_thread.is_running:
            if self.detection_thread.is_paused:
                self.detection_thread.resume()
                self.pause_btn.setText("⏸️ 暂停")
                self.log_message("▶️ 检测已恢复")
            else:
                self.detection_thread.pause()
                self.pause_btn.setText("▶️ 继续")
                self.log_message("⏸️ 检测已暂停")

    def stop_detection(self):
        """停止检测"""
        if self.detection_thread and self.detection_thread.is_running:
            self.detection_thread.stop()
            self.detection_thread.wait()

        if self.batch_detection_thread and self.batch_detection_thread.is_running:
            self.batch_detection_thread.stop()
            self.batch_detection_thread.wait()

        self.on_detection_finished()

    def on_detection_result(self, original_img, result_img, inference_time, results, class_names):
        """检测结果回调"""
        # 显示图像
        self.display_image(original_img, self.original_label)
        self.display_image(result_img, self.result_label)

        # 更新结果详情
        self.result_detail_widget.update_results(results, class_names, inference_time)

        # 记录日志（简化版，避免过多输出）
        if results and results[0].boxes and len(results[0].boxes) > 0:
            object_count = len(results[0].boxes)

            # 统计类别
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            class_counts = {}
            for cls in classes:
                class_name = class_names[cls] if cls < len(class_names) else f"类别{cls}"
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            class_summary = ", ".join([f"{name}:{count}" for name, count in class_counts.items()])
            self.log_message(f"🎯 检测到 {object_count} 个目标: {class_summary} (耗时: {inference_time:.3f}s)")
        else:
            self.log_message(f"⚪ 未检测到目标 (耗时: {inference_time:.3f}s)")

    def on_batch_result(self, file_path, original_img, result_img, inference_time, results, class_names):
        """批量检测结果回调"""
        # 计算目标数量
        object_count = len(results[0].boxes) if results and results[0].boxes else 0

        # 保存结果
        result_data = {
            'file_path': file_path,
            'original_img': original_img,
            'result_img': result_img,
            'inference_time': inference_time,
            'results': results,
            'class_names': class_names,
            'object_count': object_count
        }

        self.batch_results.append(result_data)

        # 显示第一个结果
        if len(self.batch_results) == 1:
            self.current_batch_index = 0
            self.show_batch_result(0)

        self.update_batch_navigation()

        # 记录日志
        filename = Path(file_path).name
        if object_count > 0:
            self.log_message(f"✅ {filename}: {object_count} 个目标 ({inference_time:.3f}s)")
        else:
            self.log_message(f"⚪ {filename}: 无目标 ({inference_time:.3f}s)")

    def on_batch_finished(self):
        """批量检测完成"""
        total_count = len(self.batch_results)
        total_objects = sum(result['object_count'] for result in self.batch_results)

        self.log_message(f"🎉 批量检测完成! 处理了 {total_count} 张图片，检测到 {total_objects} 个目标")
        self.statusBar().showMessage(f"批量检测完成 - {total_count} 张图片，{total_objects} 个目标")

        self.save_results_btn.setEnabled(True)
        self.clear_results_btn.setEnabled(True)
        self.result_index_label.setText(f"1/{len(self.batch_results)}")
        self.on_detection_finished()

    def on_detection_finished(self):
        """检测完成回调"""
        self.update_detection_ui_state(False)
        self.pause_btn.setText("⏸️ 暂停")
        self.progress_bar.setValue(0)

    def show_batch_result(self, index):
        """显示批量结果"""
        if 0 <= index < len(self.batch_results):
            result = self.batch_results[index]

            self.display_image(result['original_img'], self.batch_original_label)
            self.display_image(result['result_img'], self.batch_result_label)

            filename = Path(result['file_path']).name
            object_count = result['object_count']
            inference_time = result['inference_time']

            info_text = f"📁 文件: {filename}\n"
            info_text += f"🎯 检测目标: {object_count} 个\n"
            info_text += f"⏱️ 推理耗时: {inference_time:.3f} 秒\n"

            if result['results'] and result['results'][0].boxes and len(result['results'][0].boxes) > 0:
                # 显示类别统计
                classes = result['results'][0].boxes.cls.cpu().numpy().astype(int)
                confidences = result['results'][0].boxes.conf.cpu().numpy()

                class_counts = {}
                for cls in classes:
                    class_name = result['class_names'][cls] if cls < len(result['class_names']) else f"类别{cls}"
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1

                info_text += "📊 类别统计: " + ", ".join(
                    [f"{name}:{count}" for name, count in class_counts.items()]) + ""
                info_text += f"🎯 平均置信度: {np.mean(confidences):.3f}"

            self.batch_info_label.setText(info_text)
            self.result_index_label.setText(f"{index + 1}/{len(self.batch_results)}")

    def show_prev_result(self):
        """显示上一个结果"""
        if self.current_batch_index > 0:
            self.current_batch_index -= 1
            self.show_batch_result(self.current_batch_index)
            self.update_batch_navigation()

    def show_next_result(self):
        """显示下一个结果"""
        if self.current_batch_index < len(self.batch_results) - 1:
            self.current_batch_index += 1
            self.show_batch_result(self.current_batch_index)
            self.update_batch_navigation()

    def update_batch_navigation(self):
        """更新批量结果导航"""
        has_results = len(self.batch_results) > 0
        self.prev_result_btn.setEnabled(has_results and self.current_batch_index > 0)
        self.next_result_btn.setEnabled(has_results and self.current_batch_index < len(self.batch_results) - 1)

    def clear_batch_results(self):
        self.batch_results.clear()
        self.batch_result_label.setText('🎯 批量检测: 结果图')
        self.batch_original_label.setText('📷 批量检测: 原图')
        self.batch_info_label.setText('📁 选择文件夹开始批量检测...')
        self.result_index_label.setText("0/0")
        self.save_results_btn.setEnabled(False)
        self.next_result_btn.setEnabled(False)
        self.prev_result_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(False)


    def save_batch_results(self):
        """保存批量检测结果"""
        if not self.batch_results:
            QMessageBox.information(self, "提示", "没有可保存的结果")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_dir:
            return

        try:
            save_path = Path(save_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_dir = save_path / f"detection_results_{timestamp}"
            result_dir.mkdir(exist_ok=True)

            # 保存检测结果图片
            for i, result in enumerate(self.batch_results):
                file_name = Path(result['file_path']).stem
                result_img = cv2.cvtColor(result['result_img'], cv2.COLOR_RGB2BGR)
                result_save_path = result_dir / f"{file_name}_result.jpg"
                cv2.imwrite(str(result_save_path), result_img)

            # 保存检测报告
            self.save_detection_report(result_dir)

            QMessageBox.information(self, "成功", f"结果已保存到:\n{result_dir}")
            self.log_message(f"💾 结果已保存到: {result_dir}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            self.log_message(f"❌ 保存失败: {str(e)}")

    def save_detection_report(self, result_dir):
        """保存检测报告"""
        report_path = result_dir / "detection_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🎯 Enhanced Object Detection System - 批量检测报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"📅 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🎚️ 置信度阈值: {self.confidence_threshold}\n")
            f.write(f"📂 处理图片数量: {len(self.batch_results)}\n")
            f.write(f"🎯 总检测目标数: {sum(r['object_count'] for r in self.batch_results)}\n")
            f.write("\n📊 详细结果:\n")
            f.write("-" * 60 + "\n")

            for i, result in enumerate(self.batch_results, 1):
                f.write(f"{i}. 📁 {Path(result['file_path']).name}\n")
                f.write(f"   🎯 检测目标: {result['object_count']} 个\n")
                f.write(f"   ⏱️ 推理耗时: {result['inference_time']:.3f} 秒\n")

                if result['results'] and result['results'][0].boxes and len(result['results'][0].boxes) > 0:
                    confidences = result['results'][0].boxes.conf.cpu().numpy()
                    classes = result['results'][0].boxes.cls.cpu().numpy().astype(int)

                    f.write(f"   📈 置信度范围: {np.min(confidences):.3f} - {np.max(confidences):.3f}\n")

                    # 类别统计
                    class_counts = {}
                    for cls in classes:
                        class_name = result['class_names'][cls] if cls < len(result['class_names']) else f"类别{cls}"
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1

                    f.write("   📊 类别分布: " + ", ".join(
                        [f"{name}:{count}" for name, count in class_counts.items()]) + "\n")

                f.write("\n")

    def clear_display_windows(self):
        """清空显示窗口"""
        self.original_label.clear()
        self.original_label.setText("等待加载源...")
        self.result_label.clear()
        self.result_label.setText("等待检测结果...")

    def display_image(self, img_array, label):
        """显示图像"""
        if img_array is None:
            return

        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
    def clear_display(self,lable):
        pass

    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # 限制日志行数
        max_lines = 1000
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > max_lines:
            keep_lines = lines[-500:]
            self.log_text.setPlainText('\n'.join(keep_lines))

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.log_message("🗑️ 日志已清除")

    def create_enhanced_icon(self, size=64):
        """创建增强的应用图标"""
        icon = QIcon()

        for s in [16, 32, 48, 64, 128, 256]:
            pixmap = QPixmap(s, s)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 渐变背景
            gradient = QRadialGradient(s / 2, s / 2, s / 2)
            gradient.setColorAt(0, QColor("#3498db"))
            gradient.setColorAt(1, QColor("#2c3e50"))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, s, s)

            # 十字准星
            painter.setPen(QPen(QColor("white"), max(1, s // 32), Qt.SolidLine))
            center = s / 2
            arm_len = s * 0.25

            painter.drawLine(center - arm_len, center, center + arm_len, center)
            painter.drawLine(center, center - arm_len, center, center + arm_len)

            # 中心圆点
            painter.setBrush(QBrush(QColor("white")))
            r = max(2, s // 16)
            painter.drawEllipse(center - r, center - r, 2 * r, 2 * r)

            # AI 眼睛效果
            painter.setPen(QPen(QColor("#e74c3c"), max(1, s // 64), Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)

            # 外圈
            outer_r = s * 0.35
            painter.drawEllipse(center - outer_r, center - outer_r, 2 * outer_r, 2 * outer_r)

            painter.end()
            icon.addPixmap(pixmap)

        return icon

def main():
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("Enhanced Object Detection System")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("AI Vision Lab")

    # 设置高DPI缩放
    # app.setAttribute(Qt.AA_EnableHighDpiScaling)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 创建主窗口
    window = EnhancedDetectionUI()
    window.show()

    # 启动消息
    window.log_message("🚀 Enhanced Object Detection System v2.0 已启动")
    window.log_message("✨ 新功能: 渐变UI、多摄像头支持、实时监控、增强日志等")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()