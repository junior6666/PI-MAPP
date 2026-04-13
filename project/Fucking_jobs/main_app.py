"""
截图 OCR LLM WebSocket 集成应用 - PySide6 主程序
功能：快捷键截图 → OCR识别 → LLM分析 → WebSocket发送到手机
"""

import sys
import os
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QLabel, QTextEdit,
                                QGroupBox, QFormLayout, QLineEdit, QSpinBox,
                                QCheckBox, QMessageBox, QSplitter, QStatusBar,
                                QSystemTrayIcon, QMenu, QTabWidget, QProgressBar,
                                QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QFont, QTextCursor, QIcon, QPalette, QColor

# 导入工作线程类
from workers import (ScreenshotWorker, OCRWorker, LLMWorker, KimiWorker, WebSocketServerWorker)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 启用双缓冲和优化渲染
        self.setAttribute(Qt.WA_DeleteOnClose, False)
                
        # 设置窗口合理尺寸,防止出现黑色边框
        self.setMinimumSize(1000, 600)
                
        self.setWindowTitle("💻 系统资源管理器")
        self.setGeometry(100, 100, 1100, 700)
        
        # 设置窗口图标（兼容打包环境）
        icon_path = self._get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 工作线程实例
        self.screenshot_worker = None
        self.ocr_worker = None
        self.llm_worker = None
        self.kimi_worker = None
        self.websocket_worker = None
        
        # 数据存储
        self.current_image_path = None
        self.ocr_result = ""
        self.llm_result = ""
        self.kimi_result = ""
        
        # 时间记录
        self.screenshot_timestamp = None  # 快捷键触发时间
        self.ocr_elapsed = 0.0
        self.llm_elapsed = 0.0
        
        # 初始化 UI
        self.init_ui()
        
        # 设置默认勾选自动 OCR 和自动 LLM
        self.auto_ocr_check.setChecked(True)
        self.auto_llm_check.setChecked(True)
        
        # 初始化状态栏
        self.statusBar().showMessage("就绪")
        
        # 更新 IP 地址显示
        QTimer.singleShot(300, self.update_ip_display)
        
        # 加载保存的配置
        QTimer.singleShot(400, self.load_saved_config)
        
        # 延迟启动截图监听（等待 UI 完全加载）
        QTimer.singleShot(500, self.auto_start_screenshot)
        
        # 延迟启动快速分析快捷键（Alt+Z）
        QTimer.singleShot(1000, self.start_quick_analysis_hotkey)
        
        # 延迟启动 WebSocket 服务
        QTimer.singleShot(1500, self.auto_start_websocket)
        
        # 初始化系统托盘（在UI完全加载后）
        QTimer.singleShot(2000, self.init_system_tray)
        
    def init_ui(self):
        """初始化用户界面 - 伪装成系统资源管理器"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 标签页1: 系统概览（伪装）
        self.system_overview_tab = self.create_system_overview_tab()
        self.tab_widget.addTab(self.system_overview_tab, "📊 系统概览")
        
        # 标签页2: 性能监控（伪装）
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "⚡ 性能监控")
        
        # 标签页3: 磁盘管理（伪装）
        self.disk_tab = self.create_disk_tab()
        self.tab_widget.addTab(self.disk_tab, "💾 磁盘管理")
        
        # 标签页4: 最近文件（伪装）
        self.recent_files_tab = self.create_recent_files_tab()
        self.tab_widget.addTab(self.recent_files_tab, "📁 最近文件")
        
        # 标签页5: 帮助（真正的核心功能）
        self.help_tab = self.create_help_tab()
        self.tab_widget.addTab(self.help_tab, "❓ 帮助")
        
        main_layout.addWidget(self.tab_widget)
        
        # 禁用资源监控定时器（避免打包后闪烁）
        # 如需启用，将下面一行注释去掉
        # self.resource_timer = QTimer()
        # self.resource_timer.timeout.connect(self.update_resource_info)
        # self.resource_timer.start(10000)
        
    def create_system_overview_tab(self):
        """创建系统概览标签页（显示模拟硬件信息）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 硬件信息横向布局（左中右）
        hardware_layout = QHBoxLayout()
        hardware_layout.setSpacing(12)
        
        # CPU 信息（左）
        cpu_group = QGroupBox("🔲 CPU 处理器信息")
        cpu_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #4A90E2;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
        cpu_layout = QVBoxLayout()
        cpu_layout.setContentsMargins(10, 10, 10, 10)
        
        self.cpu_info_text = QTextEdit()
        self.cpu_info_text.setReadOnly(True)
        self.cpu_info_text.setMaximumHeight(180)
        self.cpu_info_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: white;
                padding: 8px;
                font-size: 12px;
                font-family: 'Consolas', 'Microsoft YaHei';
            }
        """)
        cpu_layout.addWidget(self.cpu_info_text)
        
        cpu_group.setLayout(cpu_layout)
        hardware_layout.addWidget(cpu_group, stretch=1)
        
        # GPU 信息（中）
        gpu_group = QGroupBox("🎮 GPU 显卡信息")
        gpu_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #9B59B6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
        gpu_layout = QVBoxLayout()
        gpu_layout.setContentsMargins(10, 10, 10, 10)
        
        self.gpu_info_text = QTextEdit()
        self.gpu_info_text.setReadOnly(True)
        self.gpu_info_text.setMaximumHeight(180)
        self.gpu_info_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: white;
                padding: 8px;
                font-size: 12px;
                font-family: 'Consolas', 'Microsoft YaHei';
            }
        """)
        gpu_layout.addWidget(self.gpu_info_text)
        
        gpu_group.setLayout(gpu_layout)
        hardware_layout.addWidget(gpu_group, stretch=1)
        
        # 内存信息（右）
        mem_group = QGroupBox("💾 内存信息")
        mem_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #27AE60;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
        mem_layout = QVBoxLayout()
        mem_layout.setContentsMargins(10, 10, 10, 10)
        
        self.mem_info_text = QTextEdit()
        self.mem_info_text.setReadOnly(True)
        self.mem_info_text.setMaximumHeight(180)
        self.mem_info_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: white;
                padding: 8px;
                font-size: 12px;
                font-family: 'Consolas', 'Microsoft YaHei';
            }
        """)
        mem_layout.addWidget(self.mem_info_text)
        
        mem_group.setLayout(mem_layout)
        hardware_layout.addWidget(mem_group, stretch=1)
        
        layout.addLayout(hardware_layout)
        
        # 实时使用率
        usage_group = QGroupBox("📊 实时资源使用率")
        usage_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #E67E22;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
        usage_layout = QVBoxLayout()
        usage_layout.setContentsMargins(15, 15, 15, 15)
        usage_layout.setSpacing(12)
        
        # CPU 使用率
        cpu_usage_widget = QWidget()
        cpu_usage_layout = QVBoxLayout(cpu_usage_widget)
        cpu_usage_layout.setContentsMargins(0, 0, 0, 0)
        cpu_usage_layout.setSpacing(5)
        
        self.cpu_usage_label = QLabel("CPU 使用率: 加载中...")
        self.cpu_usage_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2C3E50;")
        cpu_usage_layout.addWidget(self.cpu_usage_label)
        
        self.cpu_usage_progress = QProgressBar()
        self.cpu_usage_progress.setRange(0, 100)
        self.cpu_usage_progress.setTextVisible(True)
        self.cpu_usage_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                text-align: center;
                background-color: #ECF0F1;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498DB, stop:1 #2980B9);
                border-radius: 3px;
            }
        """)
        cpu_usage_layout.addWidget(self.cpu_usage_progress)
        usage_layout.addWidget(cpu_usage_widget)
        
        # GPU 使用率
        gpu_usage_widget = QWidget()
        gpu_usage_layout = QVBoxLayout(gpu_usage_widget)
        gpu_usage_layout.setContentsMargins(0, 0, 0, 0)
        gpu_usage_layout.setSpacing(5)
        
        self.gpu_usage_label = QLabel("GPU 使用率: 加载中...")
        self.gpu_usage_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2C3E50;")
        gpu_usage_layout.addWidget(self.gpu_usage_label)
        
        self.gpu_usage_progress = QProgressBar()
        self.gpu_usage_progress.setRange(0, 100)
        self.gpu_usage_progress.setTextVisible(True)
        self.gpu_usage_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                text-align: center;
                background-color: #ECF0F1;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9B59B6, stop:1 #8E44AD);
                border-radius: 3px;
            }
        """)
        gpu_usage_layout.addWidget(self.gpu_usage_progress)
        usage_layout.addWidget(gpu_usage_widget)
        
        # 内存使用率
        mem_usage_widget = QWidget()
        mem_usage_layout = QVBoxLayout(mem_usage_widget)
        mem_usage_layout.setContentsMargins(0, 0, 0, 0)
        mem_usage_layout.setSpacing(5)
        
        self.mem_usage_label = QLabel("内存使用率: 加载中...")
        self.mem_usage_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2C3E50;")
        mem_usage_layout.addWidget(self.mem_usage_label)
        
        self.mem_usage_progress = QProgressBar()
        self.mem_usage_progress.setRange(0, 100)
        self.mem_usage_progress.setTextVisible(True)
        self.mem_usage_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                text-align: center;
                background-color: #ECF0F1;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27AE60, stop:1 #229954);
                border-radius: 3px;
            }
        """)
        mem_usage_layout.addWidget(self.mem_usage_progress)
        usage_layout.addWidget(mem_usage_widget)
        
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)
        
        layout.addStretch()
        
        # 初始化时获取模拟硬件信息
        QTimer.singleShot(1000, self.get_simulated_hardware_info)
        
        return widget
    
    def create_performance_tab(self):
        """创建性能监控标签页（模拟数据）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 性能信息
        perf_group = QGroupBox("实时性能监控")
        perf_layout = QVBoxLayout()
        
        self.perf_info = QLabel("性能数据加载中...")
        self.perf_info.setAlignment(Qt.AlignCenter)
        perf_layout.addWidget(self.perf_info)
        
        # 进程列表表格（模拟数据）
        self.perf_table = QTableWidget()
        self.perf_table.setColumnCount(5)
        self.perf_table.setHorizontalHeaderLabels(["进程名", "PID", "CPU%", "内存(MB)", "状态"])
        self.perf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.perf_table.setRowCount(15)
        
        # 填充模拟进程数据
        import random
        fake_processes = [
            ("chrome.exe", 1234, random.uniform(5, 25), random.uniform(200, 800)),
            ("explorer.exe", 5678, random.uniform(1, 5), random.uniform(100, 300)),
            ("svchost.exe", 9012, random.uniform(0.5, 3), random.uniform(50, 150)),
            ("python.exe", 3456, random.uniform(10, 40), random.uniform(300, 600)),
            ("code.exe", 7890, random.uniform(3, 15), random.uniform(400, 700)),
            ("wechat.exe", 2345, random.uniform(1, 8), random.uniform(150, 350)),
            ("qq.exe", 6789, random.uniform(0.5, 5), random.uniform(100, 250)),
            ("edge.exe", 1357, random.uniform(8, 30), random.uniform(250, 650)),
            ("taskmgr.exe", 2468, random.uniform(0.2, 2), random.uniform(30, 80)),
            ("spoolsv.exe", 3579, random.uniform(0.1, 1), random.uniform(20, 60)),
            ("dllhost.exe", 4680, random.uniform(0.3, 2), random.uniform(40, 100)),
            ("conhost.exe", 5791, random.uniform(0.1, 1), random.uniform(15, 50)),
            ("RuntimeBroker.exe", 6802, random.uniform(0.2, 1.5), random.uniform(30, 90)),
            ("SearchApp.exe", 7913, random.uniform(0.5, 3), random.uniform(80, 200)),
            ("ShellExperienceHost.exe", 8024, random.uniform(0.3, 2), random.uniform(60, 150)),
        ]
        
        for i, (name, pid, cpu, mem) in enumerate(fake_processes):
            self.perf_table.setItem(i, 0, QTableWidgetItem(name))
            self.perf_table.setItem(i, 1, QTableWidgetItem(str(pid)))
            self.perf_table.setItem(i, 2, QTableWidgetItem(f"{cpu:.1f}"))
            self.perf_table.setItem(i, 3, QTableWidgetItem(f"{mem:.1f}"))
            self.perf_table.setItem(i, 4, QTableWidgetItem("运行中"))
        
        perf_layout.addWidget(self.perf_table)
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # 更新性能信息标签
        self.perf_info.setText(f"共 {len(fake_processes)} 个进程 | 更新时间: {self.get_current_time()}")
        
        return widget
    
    def create_disk_tab(self):
        """创建磁盘管理标签页（模拟数据）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        disk_group = QGroupBox("磁盘分区信息")
        disk_layout = QVBoxLayout()
        
        self.disk_info = QLabel("正在扫描磁盘...")
        disk_layout.addWidget(self.disk_info)
        
        # 磁盘使用进度条容器
        self.disk_progress_container = QWidget()
        self.disk_progress_layout = QVBoxLayout(self.disk_progress_container)
        
        # 添加模拟磁盘分区
        import random
        simulated_disks = [
            ("C:", "NTFS", 500, random.uniform(60, 85)),
            ("D:", "NTFS", 1000, random.uniform(40, 70)),
            ("E:", "NTFS", 2000, random.uniform(30, 60)),
        ]
        
        disk_rows = []
        for drive, fs, total_gb, usage_percent in simulated_disks:
            used_gb = total_gb * usage_percent / 100
            free_gb = total_gb - used_gb
            
            # 创建进度条和标签
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(usage_percent))
            
            label_text = f"{drive} - {usage_percent:.1f}% 已用"
            label = QLabel(label_text)
            
            self.disk_progress_layout.addWidget(label)
            self.disk_progress_layout.addWidget(progress)
            
            # 添加到表格数据
            disk_rows.append([
                drive,
                fs,
                f"{total_gb:.1f} GB",
                f"{used_gb:.1f} GB",
                f"{free_gb:.1f} GB"
            ])
        
        disk_layout.addWidget(self.disk_progress_container)
        
        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)
        
        # 磁盘详细信息表格
        disk_detail_group = QGroupBox("磁盘详细信息")
        disk_detail_layout = QVBoxLayout()
        
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(5)
        self.disk_table.setHorizontalHeaderLabels(["盘符", "文件系统", "总容量", "已用空间", "可用空间"])
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.disk_table.setRowCount(len(disk_rows))
        
        for i, row_data in enumerate(disk_rows):
            for j, value in enumerate(row_data):
                self.disk_table.setItem(i, j, QTableWidgetItem(value))
        
        disk_detail_layout.addWidget(self.disk_table)
        disk_detail_group.setLayout(disk_detail_layout)
        layout.addWidget(disk_detail_group)
        
        # 更新磁盘信息标签
        self.disk_info.setText(f"共 {len(disk_rows)} 个分区 | 更新时间: {self.get_current_time()}")
        
        layout.addStretch()
        return widget
    
    def create_recent_files_tab(self):
        """创建最近文件标签页（伪装）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        files_group = QGroupBox("最近修改的文件")
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(3)
        self.files_table.setHorizontalHeaderLabels(["文件名", "修改时间", "大小"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.files_table.setRowCount(8)
        
        # 填充一些假的文件数据
        import datetime
        fake_files = [
            ["document.docx", "2024-01-15 14:30", "2.5 MB"],
            ["report.xlsx", "2024-01-15 13:20", "1.8 MB"],
            ["presentation.pptx", "2024-01-15 12:10", "5.2 MB"],
            ["notes.txt", "2024-01-15 11:00", "12 KB"],
            ["image.png", "2024-01-15 10:45", "3.4 MB"],
            ["data.csv", "2024-01-15 09:30", "856 KB"],
            ["config.json", "2024-01-14 18:20", "4 KB"],
            ["backup.zip", "2024-01-14 16:00", "125 MB"],
        ]
        
        for i, file_info in enumerate(fake_files):
            for j, val in enumerate(file_info):
                self.files_table.setItem(i, j, QTableWidgetItem(val))
        
        files_layout.addWidget(self.files_table)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        return widget
    
    def create_help_tab(self):
        """创建帮助标签页（包含真正的核心功能）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建内部标签页
        self.help_inner_tabs = QTabWidget()
        
        # 主页介绍
        self.main_intro_tab = self.create_main_intro_tab()
        self.help_inner_tabs.addTab(self.main_intro_tab, "🏠 主页")
        
        # Case1: Alt+X 工作流
        self.case1_tab = self.create_case1_tab()
        self.help_inner_tabs.addTab(self.case1_tab, "⚡ Case1 (Alt+X)")
        
        # Case2: Alt+Z 工作流
        self.case2_tab = self.create_case2_tab()
        self.help_inner_tabs.addTab(self.case2_tab, "🚀 Case2 (Alt+Z)")
        
        # R 标签：结果展示
        self.r_tab = self.create_r_tab()
        self.help_inner_tabs.addTab(self.r_tab, "📊 R - 结果")
        
        layout.addWidget(self.help_inner_tabs)
        
        return widget
    
    def create_main_intro_tab(self):
        """创建主页介绍标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        # 简介
        intro_text = QTextEdit()
        intro_text.setReadOnly(True)
        intro_text.setMaximumHeight(350)  # 增加高度
        intro_text.setMinimumHeight(330)
        intro_content = """
<h3 style='color: #4ecca3;'>🎯 产品定位</h3>
<p>这是一款伪装成<b>"系统资源管理器"</b>的AI面试辅助工具，支持快捷键截图、OCR识别、LLM智能分析，并可通过手机实时接收分析结果。</p>

<h3 style='color: #4ecca3;'>⚡ 两大核心工作流</h3>
<ul>
<li><b>Case1 (Alt+X)：</b>完整流程 - 截图 → OCR文字识别 → LLM分析 → 推送手机（约20s）</li>
<li><b>Case2 (Alt+Z)：</b>快速流程 - 截图 → Kimi视觉模型直接分析 → 推送手机（约30s，更准确）</li>
</ul>

<h3 style='color: #4ecca3;'>📱 手机端连接</h3>
<p>在下方配置WebSocket服务器后，手机浏览器访问 <code>ws://[PC IP]:端口</code> 即可实时查看分析结果和工作流状态。</p>

<h3 style='color: #4ecca3;'>💡 使用建议</h3>
<ul>
<li>面试时推荐使用 <b>Case2 (Alt+Z)</b>，虽然稍慢但识别更准确</li>
<li>日常练习可使用 <b>Case1 (Alt+X)</b>，速度更快且可查看OCR文本</li>
<li>可在下方编辑提示词来定制AI回答风格</li>
<li>所有配置修改后会自动保存，下次启动自动加载</li>
</ul>
        """
        intro_text.setHtml(intro_content)
        layout.addWidget(intro_text)
        
        # 提示词和WebSocket左右布局
        config_layout = QHBoxLayout()
        config_layout.setSpacing(15)
        
        # 左侧：提示词编辑组
        prompt_group = QGroupBox("📝 提示词配置")
        prompt_layout = QVBoxLayout()
        
        self.main_prompt_input = QTextEdit()
        self.main_prompt_input.setPlaceholderText("请输入提示词...")
        self.main_prompt_input.setText("""你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

【任务要求】
1. 从屏幕内容中提取面试相关问题（忽略无关信息如时间、浏览器标签等）
2. 根据题型给出对应的回答：

【回答格式】

📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t,l,r 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 代码需包含必要的注释和边界处理
- 简要说明算法思路和时间复杂度
- 如有可能，同时给出经典解法和 Pythonic 解法（如列表推导式、生成器、内置函数等）

📌 如果是选择题：
- 直接给出正确答案的序号（如：答案：B）
- 简要解释选择理由（1-2句话）
- 如果识别到多个选择题，按题目序号依次作答（如：1. 答案：A, 2. 答案：C）

📌 如果是简答题/概念题：
- 给出清晰、结构化的回答
- 分点阐述关键要点
- 适当举例说明
- 如果识别到多个简答/概念题，按题目序号依次作答（如：1. xxx  2. xxx）

📌 如果是系统设计题：
- 给出系统架构设计思路
- 列出关键技术选型
- 说明核心流程和注意事项

📌 如果是性格测试题：
- 选择积极乐观、团队协作导向的选项
- 体现责任心、学习能力、抗压能力等正面特质
- 保持前后作答一致性（若识别到相同/相似题目，选择相同选项）
- 简要说明选择理由（1句话）



【注意事项】
- 只回答识别到的面试问题，忽略屏幕上的其他干扰信息
- 回答要简洁专业，适合面试场景口头表达
- 代码题必须提供可运行的完整代码
- 如果屏幕上有多个题目，按题号依次作答（1., 2., 3. ...）
- 每个题目之间用 --- 分割线隔开""")
        prompt_layout.addWidget(self.main_prompt_input)
        
        # 保存按钮
        save_prompt_btn = QPushButton("💾 保存提示词")
        save_prompt_btn.clicked.connect(self.save_prompt_config)
        prompt_layout.addWidget(save_prompt_btn)
        
        prompt_group.setLayout(prompt_layout)
        config_layout.addWidget(prompt_group, stretch=1)
        
        # 右侧：WebSocket 控制组
        ws_group = QGroupBox("📡 WebSocket 服务器配置")
        ws_layout = QFormLayout()
        
        # 本机 IP 显示
        ip_widget = QWidget()
        ip_layout = QHBoxLayout(ip_widget)
        ip_layout.setContentsMargins(0, 0, 0, 0)
        ip_layout.setSpacing(8)
        
        self.ip_label = QLabel("加载中...")
        
        self.btn_copy_ip = QPushButton("📋 复制IP")
        self.btn_copy_ip.clicked.connect(self.copy_ip_to_clipboard)
        
        ip_layout.addWidget(self.ip_label)
        ip_layout.addWidget(self.btn_copy_ip)
        
        ws_layout.addRow("本机 IP:", ip_widget)
        
        self.ws_port_input = QSpinBox()
        self.ws_port_input.setRange(1024, 65535)
        self.ws_port_input.setValue(8765)
        ws_layout.addRow("端口号:", self.ws_port_input)
        
        self.ws_status_label = QLabel("未启动")
        ws_layout.addRow("状态:", self.ws_status_label)
        
        self.btn_toggle_ws = QPushButton("▶️ 启动 WebSocket 服务")
        self.btn_toggle_ws.setCheckable(True)
        self.btn_toggle_ws.clicked.connect(self.toggle_websocket)
        ws_layout.addRow(self.btn_toggle_ws)
        
        self.btn_send_to_phone = QPushButton("📤 发送结果到手机")
        self.btn_send_to_phone.setEnabled(False)
        self.btn_send_to_phone.clicked.connect(self.send_to_phone)
        ws_layout.addRow(self.btn_send_to_phone)
        
        ws_group.setLayout(ws_layout)
        config_layout.addWidget(ws_group, stretch=1)
        
        layout.addLayout(config_layout)
        
        layout.addStretch()
        
        return widget
    
    def create_case1_tab(self):
        """创建 Case1 (Alt+X) 工作流配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 工作流说明
        workflow_info = QTextEdit()
        workflow_info.setReadOnly(True)
        workflow_info.setMaximumHeight(150)  # 增加高度
        workflow_info.setMinimumHeight(130)
        workflow_content = """
<h3 style='color: #4ecca3;'>⚡ Case1: OCR 工作流模式</h3>
<p><b>快捷键：</b>Alt + X &nbsp;&nbsp; <b>耗时：</b>约20秒 &nbsp;&nbsp; <b>特点：</b>先OCR提取文字，再调用文本LLM分析</p>
<p><b>工作流程：</b>按下 Alt+X → 截图保存 → OCR文字识别 → LLM分析 → 结果推送到手机</p>
<p><b>适用场景：</b>日常练习、需要查看OCR文本、速度优先的场景</p>
        """
        workflow_info.setHtml(workflow_content)
        layout.addWidget(workflow_info)
        
        # 截图设置和OCR左右布局
        top_config_layout = QHBoxLayout()
        top_config_layout.setSpacing(15)
        
        # 左侧：截图设置
        screenshot_group = QGroupBox("📸 截图设置")
        screenshot_layout = QFormLayout()
        
        self.case1_hotkey_input = QLineEdit("<alt>+x")
        screenshot_layout.addRow("热键组合:", self.case1_hotkey_input)
        
        self.save_dir_input = QLineEdit("./screenshots")
        self.save_dir_input.setReadOnly(True)
        screenshot_layout.addRow("保存目录:", self.save_dir_input)
        
        self.btn_toggle_screenshot = QPushButton("停止截图监听")
        self.btn_toggle_screenshot.setCheckable(True)
        self.btn_toggle_screenshot.setChecked(True)
        self.btn_toggle_screenshot.clicked.connect(self.toggle_screenshot)
        screenshot_layout.addRow(self.btn_toggle_screenshot)
        
        screenshot_group.setLayout(screenshot_layout)
        top_config_layout.addWidget(screenshot_group, stretch=1)
        
        # 右侧：OCR 控制组
        ocr_group = QGroupBox("🔍 OCR 文字识别")
        ocr_layout = QVBoxLayout()
        
        self.btn_ocr = QPushButton("开始 OCR 识别")
        self.btn_ocr.setEnabled(False)
        self.btn_ocr.clicked.connect(self.start_ocr)
        ocr_layout.addWidget(self.btn_ocr)
        
        self.auto_ocr_check = QCheckBox("截图后自动进行 OCR")
        ocr_layout.addWidget(self.auto_ocr_check)
        
        ocr_group.setLayout(ocr_layout)
        top_config_layout.addWidget(ocr_group, stretch=1)
        
        layout.addLayout(top_config_layout)
        
        # LLM 控制组
        llm_group = QGroupBox("🤖 LLM 智能分析")
        llm_layout = QFormLayout()
        
        self.api_key_input = QLineEdit("ak_2Fw1hL0xA8H33yj1wn4pW8ag0w84y")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        llm_layout.addRow("API Key:", self.api_key_input)
        
        self.model_input = QLineEdit("LongCat-Flash-Chat")
        llm_layout.addRow("模型名称:", self.model_input)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入提示词...")
        self.prompt_input.setMaximumHeight(120)
        self.prompt_input.setText("""你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

【任务要求】
1. 从屏幕内容中提取面试相关问题（忽略无关信息如时间、浏览器标签等）
2. 根据题型给出对应的回答：

【回答格式】

📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t,l,r 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 代码需包含必要的注释和边界处理
- 简要说明算法思路和时间复杂度
- 如有可能，同时给出经典解法和 Pythonic 解法（如列表推导式、生成器、内置函数等）

📌 如果是选择题：
- 直接给出正确答案的序号（如：答案：B）
- 简要解释选择理由（1-2句话）
- 如果识别到多个选择题，按题目序号依次作答（如：1. 答案：A, 2. 答案：C）

📌 如果是简答题/概念题：
- 给出清晰、结构化的回答
- 分点阐述关键要点
- 适当举例说明
- 如果识别到多个简答/概念题，按题目序号依次作答（如：1. xxx  2. xxx）

📌 如果是系统设计题：
- 给出系统架构设计思路
- 列出关键技术选型
- 说明核心流程和注意事项

📌 如果是性格测试题：
- 选择积极乐观、团队协作导向的选项
- 体现责任心、学习能力、抗压能力等正面特质
- 保持前后作答一致性（若识别到相同/相似题目，选择相同选项）
- 简要说明选择理由（1句话）



【注意事项】
- 只回答识别到的面试问题，忽略屏幕上的其他干扰信息
- 回答要简洁专业，适合面试场景口头表达
- 代码题必须提供可运行的完整代码
- 如果屏幕上有多个题目，按题号依次作答（1., 2., 3. ...）
- 每个题目之间用 --- 分割线隔开""")
        llm_layout.addRow("提示词:", self.prompt_input)
        
        self.btn_llm = QPushButton("调用 LLM 分析")
        self.btn_llm.setEnabled(False)
        self.btn_llm.clicked.connect(self.start_llm)
        llm_layout.addRow(self.btn_llm)
        
        self.auto_llm_check = QCheckBox("OCR 完成后自动调用 LLM")
        llm_layout.addRow(self.auto_llm_check)
        
        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)
        
        layout.addStretch()
        
        return widget
    
    def create_case2_tab(self):
        """创建 Case2 (Alt+Z) 工作流配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 顶部左右布局：工作流说明 + 快速分析设置
        top_layout = QVBoxLayout()
        top_layout.setSpacing(15)
        
        # 左侧：工作流说明
        workflow_info = QTextEdit()
        workflow_info.setReadOnly(True)
        workflow_info.setMaximumHeight(120)
        workflow_info.setMinimumHeight(100)
        workflow_content = """
<h3 style='color: #4ecca3;'>🚀 Case2: 快速分析模式</h3>
<p><b>快捷键：</b>Alt + Z &nbsp;&nbsp; <b>耗时：</b>约30秒 &nbsp;&nbsp; <b>特点：</b>跳过OCR，直接调用Kimi视觉大模型分析（更准确）</p>
<p><b>工作流程：</b>按下 Alt+Z → 全屏截图 → Kimi AI分析 → 结果推送到手机</p>
        """
        workflow_info.setHtml(workflow_content)
        workflow_info.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: white;
                padding: 8px;
                font-size: 12px;
            }
        """)
        top_layout.addWidget(workflow_info, stretch=1)
        
        # 右侧：快速分析设置
        quick_group = QGroupBox("🚀 快速分析设置")
        quick_layout = QFormLayout()
        
        self.case2_hotkey_input = QLineEdit("<alt>+z")
        quick_layout.addRow("热键组合:", self.case2_hotkey_input)
        
        self.kimi_api_key_input = QLineEdit("sk-v07YQ9sffsU4znH1hbODXsFsz7tkQrm6qpcYJoXLm4cqqaiE")
        self.kimi_api_key_input.setEchoMode(QLineEdit.Password)
        quick_layout.addRow("Kimi API Key:", self.kimi_api_key_input)

        # 备用模型配置（SiliconFlow）
        self.backup_api_key_input = QLineEdit("sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln")
        self.backup_api_key_input.setEchoMode(QLineEdit.Password)
        self.backup_api_key_input.setPlaceholderText("备用模型 API Key")
        quick_layout.addRow("备用 API Key:", self.backup_api_key_input)

        self.backup_base_url_input = QLineEdit("https://api.siliconflow.cn/v1")
        self.backup_base_url_input.setPlaceholderText("备用模型 Base URL")
        quick_layout.addRow("备用 Base URL:", self.backup_base_url_input)

        status_label = QLabel("✅ 快速分析已启用 (Alt+Z)")
        quick_layout.addRow("状态:", status_label)

        quick_group.setLayout(quick_layout)
        top_layout.addWidget(quick_group, stretch=1)
        
        layout.addLayout(top_layout)
        
        # 说明
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(350)
        info_text.setMinimumHeight(310)
        info_content = """
<h3 style='color: #4ecca3;'>💡 使用说明</h3>
<ul>
<li><b>优势：</b>Kimi-K2.5 是视觉大模型，可以直接理解图片内容，无需OCR中间步骤</li>
<li><b>适用场景：</b>有明确题目的面试场景，需要更准确的题目识别</li>
<li><b>注意：</b>虽然流程上更快（跳过OCR），但实际耗时约30秒，比OCR流程稍慢</li>
<li><b>自动触发：</b>程序启动后自动启用 Alt+Z 快捷键监听</li>
</ul>

<h3 style='color: #4ecca3;'>🔄 模型降级策略</h3>
<p>当主模型 Kimi-K2.5 连续失败2次后，会自动切换到备选模型：</p>
<ol>
<li>Qwen/Qwen3-Omni-30B-A3B-Instruct</li>
<li>Qwen/Qwen3-VL-8B-Instruct</li>
<li>Qwen/Qwen3-VL-32B-Instruct</li>
<li>Qwen/Qwen3-VL-235B-A22B-Instruct</li>
<li>zai-org/GLM-4.5V</li>
<li>Pro/moonshotai/Kimi-K2.5 (SiliconFlow)</li>
</ol>
        """
        info_text.setHtml(info_content)
        layout.addWidget(info_text)
        
        layout.addStretch()
        
        return widget
    
    def create_r_tab(self):
        """创建 R 结果展示标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 截图结果
        screenshot_result_group = QGroupBox("📷 截图信息")
        screenshot_result_layout = QVBoxLayout()
        
        self.screenshot_info_label = QLabel("暂无截图")
        self.screenshot_info_label.setAlignment(Qt.AlignCenter)
        screenshot_result_layout.addWidget(self.screenshot_info_label)
        
        screenshot_result_group.setLayout(screenshot_result_layout)
        layout.addWidget(screenshot_result_group)
        
        # OCR 结果
        ocr_result_group = QGroupBox("🔤 OCR 识别结果")
        ocr_result_layout = QVBoxLayout()
        
        self.ocr_result_text = QTextEdit()
        self.ocr_result_text.setReadOnly(True)
        self.ocr_result_text.setPlaceholderText("OCR 识别结果将显示在这里...")
        ocr_result_layout.addWidget(self.ocr_result_text)
        
        # OCR 耗时标签（右下角）
        ocr_timing_layout = QHBoxLayout()
        ocr_timing_layout.addStretch()
        self.ocr_time_label = QLabel("")
        ocr_timing_layout.addWidget(self.ocr_time_label)
        ocr_result_layout.addLayout(ocr_timing_layout)
        
        ocr_result_group.setLayout(ocr_result_layout)
        layout.addWidget(ocr_result_group)
        
        # LLM 结果
        llm_result_group = QGroupBox("💬 LLM 分析结果")
        llm_result_layout = QVBoxLayout()
        
        self.llm_result_text = QTextEdit()
        self.llm_result_text.setReadOnly(True)
        self.llm_result_text.setPlaceholderText("LLM 分析结果将显示在这里...")
        llm_result_layout.addWidget(self.llm_result_text)
        
        # LLM 耗时标签（右下角）
        llm_timing_layout = QHBoxLayout()
        llm_timing_layout.addStretch()
        self.llm_time_label = QLabel("")
        llm_timing_layout.addWidget(self.llm_time_label)
        llm_result_layout.addLayout(llm_timing_layout)
        
        llm_result_group.setLayout(llm_result_layout)
        layout.addWidget(llm_result_group)
        
        return widget
    
    def _get_resource_path(self, relative_path):
        """获取资源文件的绝对路径（兼容打包环境）"""
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = sys._MEIPASS
        else:
            # 开发环境
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_simulated_hardware_info(self):
        """获取模拟硬件信息（伪装用）"""
        import random
        
        # CPU 模拟信息
        cpu_models = [
            "Intel(R) Core(TM) i7-12700K @ 3.60GHz",
            "AMD Ryzen 7 5800X 8-Core Processor",
            "Intel(R) Core(TM) i9-13900K @ 3.00GHz",
            "AMD Ryzen 9 7950X 16-Core Processor",
        ]
        cpu_model = random.choice(cpu_models)
        cores = random.choice([8, 12, 16])
        threads = cores * 2
        freq = random.uniform(3.0, 4.5)
        cache = random.choice([16384, 24576, 32768])
        
        cpu_info = [
            f"处理器: {cpu_model}",
            f"架构: x86_64",
            f"核心数: {cores} 物理 / {threads} 逻辑",
            f"频率: {freq:.2f} GHz",
            f"三级缓存: {cache // 1024} MB",
        ]
        self.cpu_info_text.setText('\n'.join(cpu_info))
        
        # GPU 模拟信息
        gpu_models = [
            ("NVIDIA GeForce RTX 4070", 12, "¥4,500 - ¥5,500"),
            ("NVIDIA GeForce RTX 3080", 10, "¥5,000 - ¥6,500 (二手)"),
            ("AMD Radeon RX 7900 XT", 20, "¥6,000 - ¥7,500"),
            ("NVIDIA GeForce RTX 4060 Ti", 8, "¥3,000 - ¥3,800"),
            ("Intel(R) Iris(R) Xe Graphics", 0, "类型: 集成显卡"),
        ]
        gpu_name, vram, price = random.choice(gpu_models)
        driver_version = f"{random.randint(30, 32)}.{random.randint(0, 99)}.{random.randint(10000, 99999)}"
        
        gpu_info = [f"显卡型号: {gpu_name}"]
        if vram > 0:
            gpu_info.append(f"显存: {vram} GB")
        gpu_info.append(f"驱动版本: {driver_version}")
        gpu_info.append(f"参考价格: {price}")
        
        self.gpu_info_text.setText('\n'.join(gpu_info))
        
        # 内存模拟信息
        total_mem = random.choice([16, 32, 64])
        used_percent = random.uniform(35, 65)
        used_gb = total_mem * used_percent / 100
        available_gb = total_mem - used_gb
        
        mem_info = [
            f"总内存: {total_mem}.00 GB",
            f"可用内存: {available_gb:.2f} GB",
            f"已使用: {used_gb:.2f} GB ({used_percent:.1f}%)",
        ]
        self.mem_info_text.setText('\n'.join(mem_info))
        
        # 设置初始使用率（随机值）
        cpu_usage = random.uniform(15, 45)
        gpu_usage = random.uniform(10, 60)
        mem_usage = random.uniform(40, 70)
        
        self.cpu_usage_label.setText(f"CPU 使用率: {cpu_usage:.1f}%")
        self.cpu_usage_progress.setValue(int(cpu_usage))
        self.gpu_usage_label.setText(f"GPU 使用率: {gpu_usage:.1f}%")
        self.gpu_usage_progress.setValue(int(gpu_usage))
        self.mem_usage_label.setText(f"内存使用率: {mem_usage:.1f}% ({used_gb:.2f} GB / {total_mem:.2f} GB)")
        self.mem_usage_progress.setValue(int(mem_usage))
    

    
    # ==================== 槽函数 ====================
    
    def auto_start_screenshot(self):
        """自动启动截图监听（程序启动时调用）"""
        # 模拟点击按钮启动截图监听
        self.toggle_screenshot(True)
    
    def auto_start_websocket(self):
        """自动启动 WebSocket 服务（程序启动时调用）"""
        # 模拟点击按钮启动 WebSocket 服务
        self.toggle_websocket(True)
    
    def start_quick_analysis_hotkey(self):
        """启动快速分析快捷键（Alt+Z）"""
        try:
            from pynput import keyboard
            import threading
            
            # 创建全局热键监听器
            self.quick_analysis_listener = keyboard.GlobalHotKeys({
                '<alt>+z': self.on_quick_analysis_triggered
            })
            self.quick_analysis_listener.start()
            
            self.statusBar().showMessage("快速分析快捷键已启用 (Alt+Z)")
            print("✅ 快速分析快捷键 Alt+Z 已启用")
            
        except Exception as e:
            print(f"❌ 快速分析快捷键启动失败: {e}")
    
    @Slot()
    def toggle_screenshot(self, checked):
        """切换截图监听状态"""
        if checked:
            # 优先使用 Case1 的热键配置
            hotkey = self.case1_hotkey_input.text().strip() if hasattr(self, 'case1_hotkey_input') else self.hotkey_input.text().strip()
            if not hotkey:
                QMessageBox.warning(self, "警告", "请输入热键组合！")
                self.btn_toggle_screenshot.setChecked(False)
                return
            
            save_dir = self.save_dir_input.text()
            os.makedirs(save_dir, exist_ok=True)
            
            # 创建并启动截图工作线程
            self.screenshot_worker = ScreenshotWorker(hotkey, save_dir)
            self.screenshot_worker.screenshot_taken.connect(self.on_screenshot_taken)
            self.screenshot_worker.error_occurred.connect(self.on_error)
            self.screenshot_worker.start()
            
            self.btn_toggle_screenshot.setText("停止截图监听")
            self.statusBar().showMessage(f"截图监听已启动 - 热键: {hotkey}")
        else:
            if self.screenshot_worker:
                self.screenshot_worker.stop()
                self.screenshot_worker.wait()
                self.screenshot_worker = None
            
            self.btn_toggle_screenshot.setText("启动截图监听")
            self.statusBar().showMessage("截图监听已停止")
    
    @Slot(str)
    def on_screenshot_taken(self, image_path):
        """截图完成回调"""
        from datetime import datetime
        self.current_image_path = image_path
        self.screenshot_timestamp = time.time()  # 记录快捷键触发时间
        filename = os.path.basename(image_path)
        self.screenshot_info_label.setText(f"✅ 截图成功!\n{filename}")
        self.btn_ocr.setEnabled(True)
        
        # 清空之前的耗时显示
        self.ocr_time_label.setText("")
        self.llm_time_label.setText("")
        
        self.statusBar().showMessage(f"截图已保存: {filename}")
        
        # 发送截图触发状态到手机（静默，不打印日志）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:已触发截图]", silent=True)
        
        # 如果启用了自动 OCR
        if self.auto_ocr_check.isChecked():
            # 发送OCR开始状态
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:OCR分析中]", silent=True)
            self.start_ocr()
    
    def on_quick_analysis_triggered(self):
        """快速分析快捷键触发（Alt+Z）"""
        print("🚀 快速分析流程启动...")
        
        # 发送截图触发状态到手机（静默）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:已触发截图]", silent=True)
        
        # 1. 先进行截图
        self.perform_quick_screenshot()
    
    def perform_quick_screenshot(self):
        """执行快速截图"""
        try:
            import mss
            from PIL import Image
            from datetime import datetime
            
            # 创建截图目录
            save_dir = "./screenshots"
            os.makedirs(save_dir, exist_ok=True)
            
            # 截取屏幕
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"quick_{timestamp}.png"
                filepath = os.path.join(save_dir, filename)
                
                # 保存图片
                img.save(filepath)
                
                print(f"📸 快速截图完成: {filename}")
                
                # 发送LLM开始状态（快速分析跳过OCR，直接进入LLM）
                if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                    self.websocket_worker.send_message("[STATUS:LLM分析中]", silent=True)
                
                # 2. 调用 Kimi 分析
                self.start_kimi_analysis(filepath)
                
        except Exception as e:
            print(f"❌ 快速截图失败: {e}")
            self.statusBar().showMessage(f"快速截图失败: {str(e)}")
    
    @Slot()
    def start_ocr(self):
        """开始 OCR 识别"""
        if not self.current_image_path:
            QMessageBox.warning(self, "警告", "请先进行截图！")
            return
        
        if not os.path.exists(self.current_image_path):
            QMessageBox.warning(self, "错误", "截图文件不存在！")
            return
        
        # 禁用按钮
        self.btn_ocr.setEnabled(False)
        self.btn_ocr.setText("识别中...")
        
        # 发送OCR开始状态到手机（静默）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:OCR分析中]", silent=True)
        
        # 创建并启动 OCR 工作线程
        self.ocr_worker = OCRWorker(self.current_image_path)
        self.ocr_worker.ocr_completed.connect(self.on_ocr_completed)
        self.ocr_worker.error_occurred.connect(self.on_error)
        self.ocr_worker.start()
        
        self.statusBar().showMessage("正在进行 OCR 识别...")
    
    @Slot(str, float)
    def on_ocr_completed(self, ocr_text, elapsed_time):
        """OCR 完成回调"""
        self.ocr_result = ocr_text
        self.ocr_result_text.setText(ocr_text)
        self.ocr_elapsed = elapsed_time
        
        self.btn_ocr.setEnabled(True)
        self.btn_ocr.setText("开始 OCR 识别")
        self.btn_llm.setEnabled(True)
        
        # 显示 OCR 耗时
        self.ocr_time_label.setText(f"⏱️ {elapsed_time:.2f}s")
        
        self.statusBar().showMessage(f"OCR 识别完成 (耗时: {elapsed_time:.2f}s)")
        
        # 如果启用了自动 LLM
        if self.auto_llm_check.isChecked():
            self.start_llm()
    
    @Slot()
    def start_llm(self):
        """开始 LLM 分析"""
        if not self.ocr_result:
            QMessageBox.warning(self, "警告", "请先进行 OCR 识别！")
            return
        
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        prompt = self.prompt_input.toPlainText().strip()
        
        if not api_key or not model or not prompt:
            QMessageBox.warning(self, "警告", "请填写完整的 LLM 配置！")
            return
        
        # 禁用按钮
        self.btn_llm.setEnabled(False)
        self.btn_llm.setText("分析中...")
        
        # 发送LLM开始状态到手机（静默）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:LLM分析中]", silent=True)
        
        # 构建完整提示词
        full_prompt = f"{prompt}\n\n识别到的文字内容：\n{self.ocr_result}"
        
        # 创建并启动 LLM 工作线程
        self.llm_worker = LLMWorker(api_key, model, full_prompt)
        self.llm_worker.llm_completed.connect(self.on_llm_completed)
        self.llm_worker.error_occurred.connect(self.on_error)
        self.llm_worker.start()
        
        self.statusBar().showMessage("正在调用 LLM 分析...")
    
    @Slot(str, float)
    def on_llm_completed(self, llm_text, elapsed_time):
        """LLM 完成回调"""
        self.llm_result = llm_text
        self.llm_result_text.setText(llm_text)
        self.llm_elapsed = elapsed_time
        
        self.btn_llm.setEnabled(True)
        self.btn_llm.setText("调用 LLM 分析")
        
        # 显示 LLM 耗时
        self.llm_time_label.setText(f"⏱️ {elapsed_time:.2f}s")
        
        # 计算整体耗时
        total_elapsed = 0.0
        if self.screenshot_timestamp:
            from datetime import datetime
            total_elapsed = time.time() - self.screenshot_timestamp
        
        # 如果 WebSocket 已启动且有客户端连接，自动发送结果
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            # 发送完成状态（带总耗时）
            self.websocket_worker.send_message(f"[STATUS:已完成] [ELAPSED:{total_elapsed:.2f}]")
            
            # 自动发送到手机
            self.send_to_phone()
            
            # 显示整体耗时
            if total_elapsed > 0:
                self.statusBar().showMessage(f"LLM 分析完成 (总耗时: {total_elapsed:.2f}s)，已自动发送到手机")
            else:
                self.statusBar().showMessage("LLM 分析完成，已自动发送到手机")
        else:
            if total_elapsed > 0:
                self.statusBar().showMessage(f"LLM 分析完成 (总耗时: {total_elapsed:.2f}s)")
            else:
                self.statusBar().showMessage("LLM 分析完成")
    
    def start_kimi_analysis(self, image_path):
        """开始 Kimi 图片分析"""
        try:
            # 使用 main_app 中的提示词
            prompt = """你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

【任务要求】
1. 从屏幕内容中提取面试相关问题（忽略无关信息如时间、浏览器标签等）
2. 根据题型给出对应的回答：

【回答格式】

📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 代码需包含必要的注释和边界处理
- 简要说明算法思路和时间复杂度
- 如有可能，同时给出经典解法和 Pythonic 解法（如列表推导式、生成器、内置函数等）

📌 如果是选择题：
- 直接给出正确答案的序号（如：答案：B）
- 简要解释选择理由（1-2句话）
- 如果识别到多个选择题，按题目序号依次作答（如：1. 答案：A, 2. 答案：C）

📌 如果是简答题/概念题：
- 给出清晰、结构化的回答
- 分点阐述关键要点
- 适当举例说明
- 如果识别到多个简答/概念题，按题目序号依次作答（如：1. xxx  2. xxx）

📌 如果是系统设计题：
- 给出系统架构设计思路
- 列出关键技术选型
- 说明核心流程和注意事项

📌 如果是性格测试题：
- 选择积极乐观、团队协作导向的选项
- 体现责任心、学习能力、抗压能力等正面特质
- 保持前后作答一致性（若识别到相同/相似题目，选择相同选项）
- 简要说明选择理由（1句话）



【注意事项】
- 只回答识别到的面试问题，忽略屏幕上的其他干扰信息
- 回答要简洁专业，适合面试场景口头表达
- 代码题必须提供可运行的完整代码
- 如果屏幕上有多个题目，按题号依次作答（1., 2., 3. ...）
- 每个题目之间用 --- 分割线隔开"""
            
            # 使用 use_LLM_kimi.py 中的 API Key
            api_key = "sk-v07YQ9sffsU4znH1hbODXsFsz7tkQrm6qpcYJoXLm4cqqaiE"
            
            print(f"🤖 开始 Kimi 分析...")
            self.statusBar().showMessage("正在调用 Kimi 分析图片...")
            
            # 发送Kimi开始状态到手机
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:LLM分析中]")
            
            # 创建并启动 Kimi 工作线程
            self.kimi_worker = KimiWorker(api_key, image_path, prompt)
            self.kimi_worker.kimi_completed.connect(self.on_kimi_completed)
            self.kimi_worker.error_occurred.connect(self.on_error)
            self.kimi_worker.start()
            
        except Exception as e:
            print(f"❌ 启动 Kimi 分析失败: {e}")
            self.statusBar().showMessage(f"Kimi 分析启动失败: {str(e)}")
    
    @Slot(str, float)
    def on_kimi_completed(self, kimi_text, elapsed_time):
        """Kimi 完成回调"""
        self.kimi_result = kimi_text
        
        # 在LLM结果区显示（因为是分析结果）
        self.llm_result_text.setText(kimi_text)
        self.llm_elapsed = elapsed_time
        
        # 显示Kimi耗时
        self.llm_time_label.setText(f"⏱️ {elapsed_time:.2f}s (Kimi)")
        
        # 计算整体耗时（从截图触发开始计算）
        total_elapsed = 0.0
        if self.screenshot_timestamp:
            total_elapsed = time.time() - self.screenshot_timestamp
        
        print(f"✅ Kimi 分析完成 (耗时: {elapsed_time:.2f}s)")
        
        # 如果WebSocket已启动且有客户端连接，自动发送结果
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            # 发送完成状态（带总耗时）
            self.websocket_worker.send_message(f"[STATUS:已完成] [ELAPSED:{total_elapsed:.2f}]")
            
            # 构建发送消息
            message = f"""🤖 Kimi 智能分析结果

{kimi_text}

⏰ {self.get_current_time()}"""
            
            # 发送消息
            self.websocket_worker.send_message(message)
            
            if total_elapsed > 0:
                self.statusBar().showMessage(f"Kimi 分析完成 (总耗时: {total_elapsed:.2f}s)，已发送到手机")
            else:
                self.statusBar().showMessage("Kimi 分析完成，已发送到手机")
        else:
            if total_elapsed > 0:
                self.statusBar().showMessage(f"Kimi 分析完成 (总耗时: {total_elapsed:.2f}s)，请手动发送")
            else:
                self.statusBar().showMessage("Kimi 分析完成，请手动发送")
    
    @Slot()
    def toggle_websocket(self, checked):
        """切换 WebSocket 服务状态"""
        if checked:
            port = self.ws_port_input.value()
            
            # 创建并启动 WebSocket 工作线程
            self.websocket_worker = WebSocketServerWorker(port)
            self.websocket_worker.client_connected.connect(self.on_ws_client_connected)
            self.websocket_worker.client_disconnected.connect(self.on_ws_client_disconnected)
            self.websocket_worker.message_sent.connect(self.on_ws_message_sent)
            self.websocket_worker.error_occurred.connect(self.on_error)
            self.websocket_worker.start()
            
            self.btn_toggle_ws.setText("停止 WebSocket 服务")
            self.ws_status_label.setText("启动中...")
            self.statusBar().showMessage(f"WebSocket 服务启动中...")
        else:
            if self.websocket_worker:
                self.websocket_worker.stop()
                self.websocket_worker.wait()
                self.websocket_worker = None
            
            self.btn_toggle_ws.setText("启动 WebSocket 服务")
            self.ws_status_label.setText("未启动")
            self.btn_send_to_phone.setEnabled(False)
            self.statusBar().showMessage("WebSocket 服务已停止")
    
    @Slot()
    def on_ws_client_connected(self):
        """WebSocket 客户端连接回调"""
        self.ws_status_label.setText("✅ 已连接")
        self.ws_status_label.setStyleSheet("color: #4ecca3;")
        self.statusBar().showMessage("手机已连接")
        
        # 如果有结果，启用发送按钮
        if self.llm_result:
            self.btn_send_to_phone.setEnabled(True)
    
    @Slot()
    def on_ws_client_disconnected(self):
        """WebSocket 客户端断开回调"""
        self.ws_status_label.setText("❌ 已断开")
        self.ws_status_label.setStyleSheet("color: #e94560;")
        self.btn_send_to_phone.setEnabled(False)
        self.statusBar().showMessage("手机已断开")
    
    @Slot()
    def on_ws_message_sent(self):
        """WebSocket 消息发送回调"""
        self.statusBar().showMessage("消息已发送到手机")
    
    @Slot()
    def send_to_phone(self):
        """发送结果到手机"""
        if not self.websocket_worker or not self.websocket_worker.is_running:
            QMessageBox.warning(self, "警告", "WebSocket 服务未启动！")
            return
        
        if not self.llm_result:
            QMessageBox.warning(self, "警告", "没有可发送的结果！")
            return
        
        # 构建发送消息（只发送 LLM 分析结果）
        message = f"""🤖 LLM 智能分析结果

{self.llm_result}

⏰ {self.get_current_time()}"""
        
        # 发送消息
        self.websocket_worker.send_message(message)
    
    @Slot(str)
    def on_error(self, error_msg):
        """错误处理回调"""
        QMessageBox.critical(self, "错误", error_msg)
        self.statusBar().showMessage(f"错误: {error_msg}")
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_prompt_config(self):
        """保存提示词配置"""
        try:
            prompt_text = self.main_prompt_input.toPlainText()
            
            # 保存到文件
            config_file = "prompt_config.json"
            import json
            
            config_data = {
                "main_prompt": prompt_text,
                "last_modified": self.get_current_time()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 同步更新到 Case1 的提示词输入框
            if hasattr(self, 'prompt_input'):
                self.prompt_input.setText(prompt_text)
            
            QMessageBox.information(self, "成功", "✅ 提示词已保存！")
            self.statusBar().showMessage("提示词配置已保存")
            print(f"💾 提示词已保存到 {config_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            print(f"❌ 保存提示词失败: {e}")
    
    def load_saved_config(self):
        """加载保存的配置"""
        try:
            import json
            import os
            
            config_file = "prompt_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载提示词
                if "main_prompt" in config_data:
                    saved_prompt = config_data["main_prompt"]
                    
                    # 更新主页提示词
                    if hasattr(self, 'main_prompt_input'):
                        self.main_prompt_input.setText(saved_prompt)
                    
                    # 更新 Case1 提示词
                    if hasattr(self, 'prompt_input'):
                        self.prompt_input.setText(saved_prompt)
                    
                    print(f"✅ 已加载保存的提示词配置 (修改时间: {config_data.get('last_modified', '未知')})")
                else:
                    print("⚠️ 配置文件无提示词数据")
            else:
                print("ℹ️ 未找到保存的配置文件，使用默认配置")
                
        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}，使用默认配置")
    
    def get_local_ip(self):
        """获取本机局域网 IP"""
        import socket
        try:
            # 通过连接外部地址获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def update_ip_display(self):
        """更新IP地址显示"""
        ip = self.get_local_ip()
        self.ip_label.setText(ip)
        print(f"🌐 本机局域网IP: {ip}")
    
    def copy_ip_to_clipboard(self):
        """复制 IP 地址到剪贴板"""
        from PySide6.QtWidgets import QApplication as QtApp
        ip = self.ip_label.text()
        if ip and ip != "加载中...":
            clipboard = QtApp.clipboard()
            clipboard.setText(ip)
            
            # 临时修改按钮文本提示
            original_text = self.btn_copy_ip.text()
            self.btn_copy_ip.setText("✅ 已复制")
            self.btn_copy_ip.setStyleSheet("""
                QPushButton {
                    background-color: #5fffc8;
                }
            """)
            
            # 2秒后恢复
            QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))
            
            self.statusBar().showMessage(f"IP 地址已复制: {ip}")
        else:
            QMessageBox.warning(self, "警告", "IP 地址尚未加载完成！")
    
    def _reset_copy_button(self, original_text):
        """恢复复制按钮样式"""
        self.btn_copy_ip.setText(original_text)
        self.btn_copy_ip.setStyleSheet("""
            QPushButton {
                background-color: #4ecca3;
                color: #0f0f23;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5fffc8;
            }
            QPushButton:pressed {
                background-color: #3db892;
            }
        """)
    
    def init_system_tray(self):
        """初始化系统托盘"""
        # 检查系统是否支持托盘图标
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ 系统不支持托盘图标")
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标（兼容打包环境）
        icon_path = self._get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            print(f"✅ 托盘图标加载成功: {icon_path}")
        else:
            print(f"⚠️ 托盘图标文件不存在: {icon_path}")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏窗口动作
        self.show_action = tray_menu.addAction("📺 显示窗口")
        self.show_action.triggered.connect(self.show_window_from_tray)
        
        tray_menu.addSeparator()
        
        # 退出动作
        quit_action = tray_menu.addAction("🚪 退出程序")
        quit_action.triggered.connect(self.quit_application)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置双击托盘图标的行为
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        print("✅ 系统托盘已启用")
    
    def on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window_visibility()
    
    def toggle_window_visibility(self):
        """切换窗口显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show_window_from_tray()
    
    def show_window_from_tray(self):
        """从托盘显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """退出应用程序 - 真正关闭整个系统"""
        print("🔄 正在关闭系统...")
        
        # 停止所有工作线程
        if self.screenshot_worker:
            print("⏳ 正在停止截图监听...")
            self.screenshot_worker.stop()
            self.screenshot_worker.wait(2000)  # 最多等待2秒
            print("✅ 截图监听已停止")
        
        if self.ocr_worker and self.ocr_worker.isRunning():
            print("⏳ 正在停止 OCR 识别...")
            self.ocr_worker.terminate()
            self.ocr_worker.wait(1000)
            print("✅ OCR 识别已停止")
        
        if self.llm_worker and self.llm_worker.isRunning():
            print("⏳ 正在停止 LLM 分析...")
            self.llm_worker.terminate()
            self.llm_worker.wait(1000)
            print("✅ LLM 分析已停止")
        
        if self.kimi_worker and self.kimi_worker.isRunning():
            print("⏳ 正在停止 Kimi 分析...")
            self.kimi_worker.terminate()
            self.kimi_worker.wait(1000)
            print("✅ Kimi 分析已停止")
        
        # 先停止 WebSocket 服务（需要等待异步任务清理）
        if self.websocket_worker:
            print("⏳ 正在停止 WebSocket 服务...")
            self.websocket_worker.stop()
            self.websocket_worker.wait(5000)  # 等待最多5秒让异步任务清理
            print("✅ WebSocket 服务已停止")
        
        # 停止快速分析监听器
        if hasattr(self, 'quick_analysis_listener') and self.quick_analysis_listener:
            try:
                print("⏳ 正在停止快捷键监听...")
                self.quick_analysis_listener.stop()
                print("✅ 快捷键监听已停止")
            except:
                pass
        
        # 移除托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        print("✅ 系统已关闭")
        # 强制退出应用
        QApplication.quit()
    
    def changeEvent(self, event):
        """窗口状态改变事件 - 捕获最小化操作"""
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # 窗口被最小化时，隐藏到托盘（无提示）
                if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                    self.hide()
                    event.ignore()  # 忽略最小化事件
                    return
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件 - 最小化到托盘而非退出"""
        # 如果用户点击关闭按钮，隐藏到托盘而不是退出（无提示）
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()  # 忽略关闭事件
            return
        
        # 真正退出时的清理工作
        print("🔄 正在关闭系统...")
        
        # 停止所有工作线程
        if self.screenshot_worker:
            print("⏳ 正在停止截图监听...")
            self.screenshot_worker.stop()
            self.screenshot_worker.wait(2000)
            print("✅ 截图监听已停止")
        
        if self.ocr_worker and self.ocr_worker.isRunning():
            print("⏳ 正在停止 OCR 识别...")
            self.ocr_worker.terminate()
            self.ocr_worker.wait(1000)
            print("✅ OCR 识别已停止")
        
        if self.llm_worker and self.llm_worker.isRunning():
            print("⏳ 正在停止 LLM 分析...")
            self.llm_worker.terminate()
            self.llm_worker.wait(1000)
            print("✅ LLM 分析已停止")
        
        if self.kimi_worker and self.kimi_worker.isRunning():
            print("⏳ 正在停止 Kimi 分析...")
            self.kimi_worker.terminate()
            self.kimi_worker.wait(1000)
            print("✅ Kimi 分析已停止")
        
        # 先停止 WebSocket 服务（需要等待异步任务清理）
        if self.websocket_worker:
            print("⏳ 正在停止 WebSocket 服务...")
            self.websocket_worker.stop()
            self.websocket_worker.wait(5000)
            print("✅ WebSocket 服务已停止")
        
        # 停止快速分析监听器
        if hasattr(self, 'quick_analysis_listener') and self.quick_analysis_listener:
            try:
                print("⏳ 正在停止快捷键监听...")
                self.quick_analysis_listener.stop()
                print("✅ 快捷键监听已停止")
            except:
                pass
        
        # 移除托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        print("✅ 系统已关闭")
        event.accept()


def main():
    """主函数"""
    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 优化渲染性能
    app.setAttribute(Qt.AA_UseSoftwareOpenGL, False)  # 使用硬件加速
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 默认隐藏窗口，只显示托盘图标
    window.hide()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
