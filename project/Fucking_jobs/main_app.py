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
                               QCheckBox, QMessageBox, QSystemTrayIcon, QMenu, QTabWidget, QProgressBar,
                               QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QDoubleSpinBox, QRadioButton,
                               QComboBox)
from PySide6.QtCore import Qt, Slot, QTimer, QEvent
from PySide6.QtGui import QFont, QIcon

# 导入工作线程类和管理器（统一从 workers 模块导入）
from utls.workers import (
    ScreenshotWorker, 
    OCRWorker, 
    LLMWorker, 
    KimiWorker, 
    WebSocketServerWorker,
    AutoStartManager,
    WindowsServiceManager,
    CodeOrganizeWorker,
    AutoTypeWorker
)


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
        
        # 初始化自启管理器
        self.autostart_manager = AutoStartManager(
            app_name="AceInterview",
            app_path=sys.executable if getattr(sys, 'frozen', False) else None
        )
        
        # 初始化 Windows 服务管理器
        self.service_manager = WindowsServiceManager(
            task_name="AceInterviewGuardian",
            app_path=sys.executable if getattr(sys, 'frozen', False) else None
        )
        
        # 工作线程实例
        self.screenshot_worker = None
        self.ocr_worker = None
        self.llm_worker = None
        self.kimi_worker = None
        self.websocket_worker = None
        self.code_organize_worker = None  # 代码整理Worker
        self.auto_type_worker = None      # 自动写入Worker
        
        # 数据存储
        self.current_image_path = None
        self.ocr_result = ""
        self.llm_result = ""
        self.kimi_result = ""
        self.organized_code = ""  # 整理后的代码
        self.code_file_path = None  # 代码文件路径
        
        # 结果时间戳（用于Alt+S工作流选择最新结果）
        self.llm_result_timestamp = None  # LLM结果的时间戳
        self.kimi_result_timestamp = None  # Kimi结果的时间戳
        
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
        
        # 延迟启动模型切换快捷键（Alt+1）
        QTimer.singleShot(1200, self.start_model_toggle_hotkey)
        
        # 延迟启动 Kimi 模型切换快捷键（Alt+2）
        QTimer.singleShot(1400, self.start_kimi_model_toggle_hotkey)
        
        # 延迟启动后备模型快捷键（Alt+3 ~ Alt+7）
        QTimer.singleShot(1600, self.start_backup_model_hotkeys)
        
        # 延迟启动自动写入快捷键（Alt+S）
        QTimer.singleShot(1800, self.start_auto_type_hotkey)
        
        # 延迟启动切换下一张手机照片快捷键（Alt+C）
        QTimer.singleShot(2000, self.start_next_photo_hotkey)
        
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
        
        # 添加自启控制到状态栏
        self.add_autostart_control_to_statusbar()
        
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
        
        # Case3: Alt+S 工作流
        self.case3_tab = self.create_case3_tab()
        self.help_inner_tabs.addTab(self.case3_tab, "⌨️ Case3 (Alt+S)")
        
        # 提示词管理标签页
        self.prompt_tab = self.create_prompt_tab()
        self.help_inner_tabs.addTab(self.prompt_tab, "📝 提示词")
        
        # R 标签：结果展示
        self.r_tab = self.create_r_tab()
        self.help_inner_tabs.addTab(self.r_tab, "📊 R - 结果")
        
        # 设置标签：开机自启和守护配置
        self.settings_tab = self.create_settings_tab()
        self.help_inner_tabs.addTab(self.settings_tab, "⚙️ 设置")
        
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
<li>可在 <b>📝 提示词</b> 标签页中编辑提示词来定制AI回答风格（Case1和Case2共用）</li>
<li>所有配置修改后会自动保存，下次启动自动加载</li>
</ul>
        """
        intro_text.setHtml(intro_content)
        layout.addWidget(intro_text)
        
        # 提示词和WebSocket左右布局
        config_layout = QHBoxLayout()
        config_layout.setSpacing(15)
        
        # 左侧：提示词快捷入口（引导到提示词标签页）
        prompt_group = QGroupBox("📝 提示词配置")
        prompt_layout = QVBoxLayout()
        
        prompt_hint = QLabel(
            "💡 提示词统一管理已移至 <b>📝 提示词</b> 标签页\n"
            "在那里您可以：\n"
            "• 选择不同的提示词模板（通用、华为机考、测评题等）\n"
            "• 自定义编辑提示词\n"
            "• Case1和Case2共用同一套提示词配置"
        )
        prompt_hint.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
        """)
        prompt_hint.setWordWrap(True)
        prompt_layout.addWidget(prompt_hint)
        
        # 保留 main_prompt_input 作为只读预览（与共享提示词同步）
        self.main_prompt_input = QTextEdit()
        self.main_prompt_input.setReadOnly(True)  # 设置为只读
        self.main_prompt_input.setMaximumHeight(150)
        self.main_prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        self.main_prompt_input.setText("加载中...")
        prompt_layout.addWidget(QLabel("当前提示词预览（只读）:"))
        prompt_layout.addWidget(self.main_prompt_input)
        
        # 跳转到提示词标签页按钮
        goto_prompt_btn = QPushButton("📝 前往提示词配置页面")
        goto_prompt_btn.clicked.connect(lambda: self.help_inner_tabs.setCurrentIndex(4))  # 提示词标签页索引为4
        prompt_layout.addWidget(goto_prompt_btn)
        
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
    
    def create_prompt_tab(self):
        """创建提示词管理标签页（Case1和Case2共用）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 顶部说明
        info_group = QGroupBox("📝 提示词配置说明")
        info_layout = QVBoxLayout()
        info_text = QLabel(
            "此处的提示词将被 Case1 (Alt+X) 和 Case2 (Alt+Z) 共同使用。\n"
            "您可以选择不同的提示词模板，或自定义编辑后保存。"
        )
        info_text.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 模板选择区域
        template_group = QGroupBox("📋 提示词模板")
        template_layout = QHBoxLayout()
        template_layout.setSpacing(10)
        
        # 模板选择下拉框
        self.template_selector = QComboBox()
        self.template_selector.addItem("🔧 通用提示词（默认）")
        self.template_selector.addItem("💻 华为机考专用提示词（处理输入输出，可完整运行）")
        self.template_selector.currentIndexChanged.connect(self.on_template_changed)
        self.template_selector.setMaximumWidth(400)
        template_layout.addWidget(QLabel("选择模板:"))
        template_layout.addWidget(self.template_selector)
        template_layout.addStretch()
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # 提示词编辑区域
        prompt_edit_group = QGroupBox("✏️ 提示词编辑")
        prompt_edit_layout = QVBoxLayout()
        
        self.shared_prompt_input = QTextEdit()
        self.shared_prompt_input.setPlaceholderText("请输入或编辑提示词...")
        self.shared_prompt_input.setText("""你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

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
- 每个题目之间用 --- 分割线隔开
- 返回markdown格式""")
        prompt_edit_layout.addWidget(self.shared_prompt_input)
        
        prompt_edit_group.setLayout(prompt_edit_layout)
        layout.addWidget(prompt_edit_group)
        
        # 操作按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.save_shared_prompt_btn = QPushButton("💾 保存提示词")
        self.save_shared_prompt_btn.clicked.connect(self.save_shared_prompt_config)
        self.save_shared_prompt_btn.setMaximumWidth(150)
        btn_layout.addWidget(self.save_shared_prompt_btn)
        
        self.reset_prompt_btn = QPushButton("🔄 恢复默认")
        self.reset_prompt_btn.clicked.connect(self.reset_to_default_prompt)
        self.reset_prompt_btn.setMaximumWidth(150)
        btn_layout.addWidget(self.reset_prompt_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        return widget
    
    def on_template_changed(self, index):
        """模板选择改变时的回调"""
        templates = [
            # 通用提示词
            """你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

【任务要求】
1. 从屏幕内容中提取面试相关问题（忽略无关信息如时间、浏览器标签等）
2. 根据题型给出对应的回答：

【回答格式】

📌 如果是编程题：
- 提供完整的 Python 代码实现
- 变量名尽量简洁（能用单字母就用单字母，如 x, y, k, v, i, j, t,l,r 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 非Leetcode答题模式下，需根据题意处理好输入输出
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
- 每个题目之间用 --- 分割线隔开
- 返回markdown格式""",
            # 华为机考专用提示词
            """
你是一位华为机考答题助手。请分析屏幕截图中的编程题目，给出符合华为机考要求的完整可运行代码。

【核心要求】
1. 只输出完整的 Python 代码，不要有任何解释、注释或额外文字
2. 代码必须能够直接复制粘贴到华为机考平台并正确运行
3. 严格遵循题目描述的输入输出格式（特别注意空格、换行、分隔符）

【输入处理规范】
- 单行整数：n = int(input())
- 单行多个整数：a, b = map(int, input().split())
- 数组/列表：arr = list(map(int, input().split()))
- 多行数据：使用 for 循环或 while 循环读取
- 字符串：s = input().strip()
- 注意：根据题目描述判断是否需要 .strip() 或 .split()

【输出处理规范】
- 单个结果：print(result)
- 多个结果用空格分隔：print(' '.join(map(str, result_list)))
- 多个结果用换行分隔：使用循环逐个 print()
- 浮点数：print(f"{result:.2f}") 或 print(round(result, 2))
- 特别注意：
  * 题目要求末尾无空格时，使用 ' '.join() 而非手动拼接
  * 题目要求特定格式时，严格按照格式输出
  * 避免多余的换行或空格

【代码风格】
- 变量名简洁：使用 n, m, arr, res, i, j, x, y 等
- 避免冗余命名：不用 result, temp, data, output 等
- 逻辑清晰：适当使用函数封装复杂逻辑
- 边界处理：考虑空输入、单元素、最大值等边界情况

【常见陷阱规避】
- 多组测试用例：使用 while True + try-except 或先读取用例数
- 大数运算：注意 Python 自动支持大数，无需特殊处理
- 时间复杂度：优先使用高效算法（哈希表、双指针、二分等）
- 内存限制：避免不必要的大数组或递归深度过大

【输出格式示例】
✅ 正确：print(' '.join(map(str, [1, 2, 3])))  # 输出: 1 2 3
❌ 错误：print(1, 2, 3)  # 输出: 1 2 3（有空格但不可控）

✅ 正确：for item in result: print(item)  # 每行一个
❌ 错误：print(result)  # 可能带括号和逗号

【最终检查清单】
□ 代码是否完整可运行？
□ 输入处理是否符合题目描述？
□ 输出格式是否完全匹配要求（空格、换行、分隔符）？
□ 是否去除了所有注释和多余文字？
□ 边界情况是否已处理？

请根据题目要求，给出完整的、可运行的解决方案。"""
        ]
        
        if 0 <= index < len(templates):
            self.shared_prompt_input.setText(templates[index])
            print(f"✅ 已切换到模板: {self.template_selector.currentText()}")
    
    def save_shared_prompt_config(self):
        """保存共享提示词配置（Case1和Case2共用）"""
        try:
            prompt_text = self.shared_prompt_input.toPlainText()
            
            # 保存到文件
            config_file = "prompt_config.json"
            import json
            
            config_data = {
                "shared_prompt": prompt_text,
                "last_modified": self.get_current_time()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 同步更新到主页提示词预览框（如果存在）
            if hasattr(self, 'main_prompt_input') and self.main_prompt_input:
                self.main_prompt_input.setText(prompt_text)
            
            print(f"💾 共享提示词已保存到 {config_file}")
            self.statusBar().showMessage("✅ 提示词配置已保存", 3000)
            
        except Exception as e:
            print(f"❌ 保存提示词失败: {e}")
            self.statusBar().showMessage(f"❌ 保存失败: {str(e)}")
    
    def reset_to_default_prompt(self):
        """恢复到默认提示词"""
        self.template_selector.setCurrentIndex(0)  # 切换到通用提示词
        self.statusBar().showMessage("✅ 已恢复到默认提示词", 2000)
    
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
<p><b>提示词配置：</b>请在 📝 提示词 标签页中统一配置（Case1和Case2共用）</p>
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
        
        # LLM 控制组（移除提示词输入框，改用共享提示词）
        llm_group = QGroupBox("🤖 LLM 智能分析")
        llm_layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("请填入 LongCat API Key")
        self.api_key_input.textChanged.connect(lambda _: self._on_api_key_changed())
        api_key_widget = QWidget()
        api_key_hlayout = QHBoxLayout(api_key_widget)
        api_key_hlayout.setContentsMargins(0, 0, 0, 0)
        api_key_hlayout.setSpacing(6)
        api_key_hlayout.addWidget(self.api_key_input, stretch=1)
        btn_copy_longcat = QPushButton("📋 获取")
        btn_copy_longcat.setToolTip("复制获取地址到剪贴板")
        btn_copy_longcat.setMaximumWidth(70)
        btn_copy_longcat.clicked.connect(lambda: self._copy_api_url("https://longcat.chat/platform/api_keys", "LongCat"))
        api_key_hlayout.addWidget(btn_copy_longcat)
        llm_layout.addRow("LongCat API Key:", api_key_widget)
        
        self.model_input = QLineEdit("LongCat-Flash-Chat")
        llm_layout.addRow("模型名称:", self.model_input)
        
        # 提示词配置提示
        prompt_hint = QLabel("💡 提示词已在 📝 提示词 标签页中统一配置")
        prompt_hint.setStyleSheet("color: #4ecca3; font-size: 12px; padding: 8px; background-color: #f0f9ff; border-radius: 4px;")
        llm_layout.addRow("提示词:", prompt_hint)
        
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
    
    def create_case3_tab(self):
        """创建 Case3 (Alt+S) 自动写入配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 工作流说明
        workflow_info = QTextEdit()
        workflow_info.setReadOnly(True)
        workflow_info.setMaximumHeight(160)
        workflow_info.setMinimumHeight(140)
        workflow_content = """
<h3 style='color: #4ecca3;'>⌨️ Case3: 自动写入模式</h3>
<p><b>快捷键：</b>Alt + S &nbsp;&nbsp; <b>特点：</b>自动将整理后的代码输入到目标窗口</p>
<p><b>工作流程：</b>按下 Alt+S → 整理代码文件 → 模拟键盘输入 → 完成写入</p>
<p><b>适用场景：</b>面试时需要快速输入代码、自动化代码提交</p>
<p><b>控制方式：</b>Alt+L 暂停/恢复 | Ctrl+K 停止</p>
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
        layout.addWidget(workflow_info)
        
        # 顶部左右布局：延迟设置 + 代码整理提示词
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # 左侧：延迟设置
        delay_group = QGroupBox("⏱️ 输入延迟设置")
        delay_layout = QFormLayout()
        
        # 延迟滑块
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setRange(1, 50)  # 0.01 ~ 0.50
        self.delay_slider.setValue(5)  # 默认 0.05
        self.delay_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_slider.setTickInterval(5)
        self.delay_slider.valueChanged.connect(self.update_delay_label)
        
        delay_widget = QWidget()
        delay_hlayout = QHBoxLayout(delay_widget)
        delay_hlayout.setContentsMargins(0, 0, 0, 0)
        delay_hlayout.addWidget(self.delay_slider)
        
        self.delay_value_label = QLabel("0.05s")
        self.delay_value_label.setMinimumWidth(60)
        self.delay_value_label.setAlignment(Qt.AlignCenter)
        self.delay_value_label.setStyleSheet("font-weight: bold; color: #4ecca3;")
        delay_hlayout.addWidget(self.delay_value_label)
        
        delay_layout.addRow("字符间隔:", delay_widget)
        
        # 思考时间范围设置
        think_time_widget = QWidget()
        think_time_layout = QHBoxLayout(think_time_widget)
        think_time_layout.setContentsMargins(0, 0, 0, 0)
        think_time_layout.setSpacing(8)
        
        # 最小值
        self.think_time_min_spinbox = QDoubleSpinBox()
        self.think_time_min_spinbox.setRange(0.1, 10.0)
        self.think_time_min_spinbox.setValue(1.0)
        self.think_time_min_spinbox.setSingleStep(0.1)
        self.think_time_min_spinbox.setSuffix("s")
        self.think_time_min_spinbox.setMaximumWidth(120)
        think_time_layout.addWidget(QLabel("最小:"))
        think_time_layout.addWidget(self.think_time_min_spinbox)
        

        
        # 最大值
        self.think_time_max_spinbox = QDoubleSpinBox()
        self.think_time_max_spinbox.setRange(0.1, 10.0)
        self.think_time_max_spinbox.setValue(2.0)
        self.think_time_max_spinbox.setSingleStep(0.1)
        self.think_time_max_spinbox.setSuffix("s")
        self.think_time_max_spinbox.setMaximumWidth(120)
        think_time_layout.addWidget(QLabel("最大:"))
        think_time_layout.addWidget(self.think_time_max_spinbox)
        think_time_layout.addStretch()
        delay_layout.addRow("思考时间:", think_time_widget)
        
        # 延迟说明
        delay_info = QLabel("范围: 0.01s ~ 0.50s | 值越小输入越快")
        delay_info.setStyleSheet("color: #666; font-size: 11px;")
        delay_layout.addRow(delay_info)
        
        # 快捷模式按钮
        mode_btn_widget = QWidget()
        mode_btn_layout = QHBoxLayout(mode_btn_widget)
        mode_btn_layout.setContentsMargins(0, 5, 0, 0)
        mode_btn_layout.setSpacing(10)
        
        # 熟练模式按钮 - 快速输入 (0.02s)
        expert_btn = QPushButton("🚀 熟练模式")
        expert_btn.setToolTip("设置为快速输入模式 (0.02s)")
        expert_btn.clicked.connect(lambda: self.set_delay_mode(2, "熟练模式"))
        mode_btn_layout.addWidget(expert_btn)
        
        # 新手模式按钮 - 慢速输入 (0.15s)
        beginner_btn = QPushButton("🐢 新手模式")
        beginner_btn.setToolTip("设置为慢速输入模式 (0.15s)")
        beginner_btn.clicked.connect(lambda: self.set_delay_mode(15, "新手模式"))
        mode_btn_layout.addWidget(beginner_btn)
        
        mode_btn_layout.addStretch()
        delay_layout.addRow("快捷模式:", mode_btn_widget)
        
        # 思考时间快捷设置按钮
        think_quick_btn_widget = QWidget()
        think_quick_btn_layout = QHBoxLayout(think_quick_btn_widget)
        think_quick_btn_layout.setContentsMargins(0, 5, 0, 0)
        think_quick_btn_layout.setSpacing(10)
        
        # 快速思考模式 (0.5~1.0s)
        quick_think_btn = QPushButton("⚡ 快速思考")
        quick_think_btn.setToolTip("设置思考时间为 0.5~1.0s")
        quick_think_btn.clicked.connect(lambda: self.set_think_time_mode(0.5, 1.0, "快速思考"))
        think_quick_btn_layout.addWidget(quick_think_btn)
        
        # 正常思考模式 (1.0~2.0s)
        normal_think_btn = QPushButton("🎯 正常思考")
        normal_think_btn.setToolTip("设置思考时间为 1.0~2.0s")
        normal_think_btn.clicked.connect(lambda: self.set_think_time_mode(1.0, 2.0, "正常思考"))
        think_quick_btn_layout.addWidget(normal_think_btn)
        
        # 深度思考模式 (2.0~3.5s)
        deep_think_btn = QPushButton("🤔 深度思考")
        deep_think_btn.setToolTip("设置思考时间为 2.0~3.5s")
        deep_think_btn.clicked.connect(lambda: self.set_think_time_mode(2.0, 3.5, "深度思考"))
        think_quick_btn_layout.addWidget(deep_think_btn)
        
        think_quick_btn_layout.addStretch()
        delay_layout.addRow("思考模式:", think_quick_btn_widget)
        
        # 错误率设置
        error_rate_widget = QWidget()
        error_rate_layout = QHBoxLayout(error_rate_widget)
        error_rate_layout.setContentsMargins(0, 0, 0, 0)
        error_rate_layout.setSpacing(8)
        
        self.error_rate_spinbox = QDoubleSpinBox()
        self.error_rate_spinbox.setRange(0.0, 1.0)
        self.error_rate_spinbox.setValue(0.08)
        self.error_rate_spinbox.setSingleStep(0.01)
        self.error_rate_spinbox.setDecimals(2)
        self.error_rate_spinbox.setMaximumWidth(120)
        error_rate_layout.addWidget(QLabel("错误率:"))
        error_rate_layout.addWidget(self.error_rate_spinbox)
        error_rate_layout.addStretch()
        delay_layout.addRow("打字错误:", error_rate_widget)
        
        # 长行随机换行率设置
        line_break_widget = QWidget()
        line_break_layout = QHBoxLayout(line_break_widget)
        line_break_layout.setContentsMargins(0, 0, 0, 0)
        line_break_layout.setSpacing(8)
        
        self.line_break_rate_spinbox = QDoubleSpinBox()
        self.line_break_rate_spinbox.setRange(0.0, 1.0)
        self.line_break_rate_spinbox.setValue(0.7)
        self.line_break_rate_spinbox.setSingleStep(0.05)
        self.line_break_rate_spinbox.setDecimals(2)
        self.line_break_rate_spinbox.setMaximumWidth(120)
        line_break_layout.addWidget(QLabel("换行率:"))
        line_break_layout.addWidget(self.line_break_rate_spinbox)
        line_break_layout.addStretch()
        delay_layout.addRow("长行换行:", line_break_widget)
        
        # 复制时机设置
        copy_timing_widget = QWidget()
        copy_timing_layout = QHBoxLayout(copy_timing_widget)
        copy_timing_layout.setContentsMargins(0, 0, 0, 0)
        copy_timing_layout.setSpacing(10)
        
        self.copy_after_organize_radio = QRadioButton("整理后复制")
        self.copy_after_organize_radio.setToolTip("代码整理完成后立即复制到剪切板")
        self.copy_after_organize_radio.toggled.connect(lambda checked: self.on_copy_timing_changed('after_organize', checked))
        self.copy_after_complete_radio = QRadioButton("写入后复制")
        self.copy_after_complete_radio.setToolTip("自动写入完成后才复制到剪切板（默认）")
        self.copy_after_complete_radio.setChecked(True)  # 默认选中
        self.copy_after_complete_radio.toggled.connect(lambda checked: self.on_copy_timing_changed('after_complete', checked))
        
        copy_timing_layout.addWidget(self.copy_after_organize_radio)
        copy_timing_layout.addWidget(self.copy_after_complete_radio)
        copy_timing_layout.addStretch()
        delay_layout.addRow("复制时机:", copy_timing_widget)
        
        delay_group.setLayout(delay_layout)
        top_layout.addWidget(delay_group, stretch=1)
        
        # 右侧：代码整理提示词
        prompt_group = QGroupBox("📝 代码整理提示词")
        prompt_layout = QVBoxLayout()
        
        self.case3_prompt_input = QTextEdit()
        self.case3_prompt_input.setPlaceholderText("请输入代码整理提示词...")
        self.case3_prompt_input.setText("""角色设定：你是一名正在参加技术面试的候选人，需要在白板上写出最优解。

任务指令：请根据以下要求，对提供的代码进行重构和整理：

解法选择：
- 仅保留最经典/最优的解法，舍弃其他非主流解法及所有文字分析
- 如果有多种解法，只保留时间复杂度最优的那个

代码规范（面试级）：
- 去噪：删除代码中所有的注释和多余的空行，仅保留核心逻辑
- 命名：使用最符合 Python 语法的极简变量名（如 x, y, k, v, i, j, t, l, r 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 风格：模拟人在面试高压环境下书写的极简风格

输出约束：
- 直接输出 Markdown 代码块，不要包含任何前置的解释、标题或后置的说明
- 只输出一个代码块，格式为：```python\n...代码...\n```
- 如果原内容包含多个题目，用 --- 分隔每个题目的代码块""")
        self.case3_prompt_input.setMaximumHeight(500)
        prompt_layout.addWidget(self.case3_prompt_input)
        
        prompt_group.setLayout(prompt_layout)
        top_layout.addWidget(prompt_group, stretch=1)
        
        layout.addLayout(top_layout)
        
        # 保存配置按钮（外部靠左侧）
        save_btn_widget = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_widget)
        save_btn_layout.setContentsMargins(0, 10, 0, 0)
        save_btn_layout.setSpacing(10)
        
        self.save_case3_btn = QPushButton("💾 保存配置")
        self.save_case3_btn.clicked.connect(self.save_case3_config)
        self.save_case3_btn.setMaximumWidth(150)
        save_btn_layout.addWidget(self.save_case3_btn)
        save_btn_layout.addStretch()
        
        layout.addWidget(save_btn_widget)
        
        layout.addStretch()
        
        return widget
    
    def update_delay_label(self, value):
        """更新延迟显示标签"""
        delay = value / 100.0
        self.delay_value_label.setText(f"{delay:.2f}s")
    
    def set_delay_mode(self, slider_value, mode_name):
        """设置延迟模式"""
        self.delay_slider.setValue(slider_value)
        print(f"✅ 已切换到{mode_name}，延迟: {slider_value/100.0:.2f}s")
    
    def set_think_time_mode(self, min_val, max_val, mode_name):
        """设置思考时间模式"""
        self.think_time_min_spinbox.setValue(min_val)
        self.think_time_max_spinbox.setValue(max_val)
        print(f"✅ 已切换到{mode_name}模式，思考时间: {min_val}~{max_val}s")
    
    def on_copy_timing_changed(self, timing_type, checked):
        """复制时机改变时的回调"""
        if checked:
            if timing_type == 'after_organize':
                print("📋 已选择：整理后立即复制（需点击保存按钮生效）")
            else:
                print("📋 已选择：写入完成后复制（需点击保存按钮生效）")
    
    def save_case3_config(self):
        """保存 Case3 配置"""
        try:
            import json
            # 使用当前工作目录而不是__file__，兼容打包环境
            config_file = os.path.join(os.getcwd(), 'case3_config.json')
            
            config = {
                'delay': self.delay_slider.value() / 100.0,
                'think_time_min': self.think_time_min_spinbox.value(),
                'think_time_max': self.think_time_max_spinbox.value(),
                'error_rate': self.error_rate_spinbox.value(),
                'line_break_rate': self.line_break_rate_spinbox.value(),
                'copy_timing': 'after_organize' if self.copy_after_organize_radio.isChecked() else 'after_complete',
                'prompt': self.case3_prompt_input.toPlainText()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            copy_timing_text = '整理后立即复制' if config['copy_timing'] == 'after_organize' else '写入完成后复制'
            print(f"✅ Case3 配置已保存: delay={config['delay']}, think_time={config['think_time_min']}-{config['think_time_max']}s, error_rate={config['error_rate']}, line_break_rate={config['line_break_rate']}, copy_timing={copy_timing_text}, prompt_length={len(config['prompt'])}")
            self.statusBar().showMessage("✅ Case3 配置已保存！", 3000)
            
        except Exception as e:
            print(f"❌ 保存 Case3 配置失败: {e}")
            self.statusBar().showMessage(f"❌ 保存配置失败: {str(e)}")
    
    def load_case3_config(self):
        """加载 Case3 配置"""
        try:
            import json
            # 使用当前工作目录而不是__file__，兼容打包环境
            config_file = os.path.join(os.getcwd(), 'case3_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载延迟设置
                if 'delay' in config:
                    delay_value = int(config['delay'] * 100)
                    delay_value = max(1, min(50, delay_value))  # 限制在 1~50 范围内
                    self.delay_slider.setValue(delay_value)
                    self.delay_value_label.setText(f"{config['delay']:.2f}s")
                
                # 加载思考时间范围
                if 'think_time_min' in config:
                    self.think_time_min_spinbox.setValue(config['think_time_min'])
                if 'think_time_max' in config:
                    self.think_time_max_spinbox.setValue(config['think_time_max'])
                
                # 加载错误率
                if 'error_rate' in config:
                    self.error_rate_spinbox.setValue(config['error_rate'])
                
                # 加载长行随机换行率
                if 'line_break_rate' in config:
                    self.line_break_rate_spinbox.setValue(config['line_break_rate'])
                
                # 加载复制时机设置
                if 'copy_timing' in config:
                    if config['copy_timing'] == 'after_organize':
                        self.copy_after_organize_radio.setChecked(True)
                    else:
                        self.copy_after_complete_radio.setChecked(True)
                
                # 加载提示词
                if 'prompt' in config and config['prompt']:
                    self.case3_prompt_input.setText(config['prompt'])
                
                copy_timing_text = '整理后立即复制' if config.get('copy_timing') == 'after_organize' else '写入完成后复制'
                print(f"✅ Case3 配置已加载: delay={config.get('delay', 0.05)}, think_time={config.get('think_time_min', 1.0)}-{config.get('think_time_max', 2.0)}s, error_rate={config.get('error_rate', 0.08)}, line_break_rate={config.get('line_break_rate', 0.7)}, copy_timing={copy_timing_text}")
            else:
                print("ℹ️ 未找到 Case3 配置文件，使用默认配置")
                
        except Exception as e:
            print(f"⚠️ 加载 Case3 配置失败: {e}，使用默认配置")
    
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
        
        self.kimi_api_key_input = QLineEdit()
        self.kimi_api_key_input.setEchoMode(QLineEdit.Password)
        self.kimi_api_key_input.setPlaceholderText("请填入 Kimi API Key")
        self.kimi_api_key_input.textChanged.connect(lambda _: self._on_api_key_changed())
        kimi_key_widget = QWidget()
        kimi_key_hlayout = QHBoxLayout(kimi_key_widget)
        kimi_key_hlayout.setContentsMargins(0, 0, 0, 0)
        kimi_key_hlayout.setSpacing(6)
        kimi_key_hlayout.addWidget(self.kimi_api_key_input, stretch=1)
        btn_copy_kimi = QPushButton("📋 获取")
        btn_copy_kimi.setToolTip("复制获取地址到剪贴板")
        btn_copy_kimi.setMaximumWidth(70)
        btn_copy_kimi.clicked.connect(lambda: self._copy_api_url("https://platform.moonshot.cn/console/api-keys", "Kimi"))
        kimi_key_hlayout.addWidget(btn_copy_kimi)
        quick_layout.addRow("Kimi API Key:", kimi_key_widget)

        # 备用模型配置（SiliconFlow）
        self.backup_api_key_input = QLineEdit()
        self.backup_api_key_input.setEchoMode(QLineEdit.Password)
        self.backup_api_key_input.setPlaceholderText("请填入 SiliconFlow API Key")
        self.backup_api_key_input.textChanged.connect(lambda _: self._on_api_key_changed())
        sf_key_widget = QWidget()
        sf_key_hlayout = QHBoxLayout(sf_key_widget)
        sf_key_hlayout.setContentsMargins(0, 0, 0, 0)
        sf_key_hlayout.setSpacing(6)
        sf_key_hlayout.addWidget(self.backup_api_key_input, stretch=1)
        btn_copy_sf = QPushButton("📋 获取")
        btn_copy_sf.setToolTip("复制获取地址到剪贴板")
        btn_copy_sf.setMaximumWidth(70)
        btn_copy_sf.clicked.connect(lambda: self._copy_api_url("https://cloud.siliconflow.cn/i/A6FuRXZM", "SiliconFlow"))
        sf_key_hlayout.addWidget(btn_copy_sf)
        quick_layout.addRow("SiliconFlow API Key:", sf_key_widget)

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

<h3 style='color: #4ecca3;'>⌨️ 快捷键列表</h3>
<ul>
<li><b>Alt + X：</b>Case1 工作流 - 截图 → OCR → LLM</li>
<li><b>Alt + Z：</b>Case2 工作流 - 截图 → Kimi 直接分析</li>
<li><b>Alt + C：</b>切换下一张手机照片（仅手机模式下有效，循环切换）</li>
<li><b>Alt + 1：</b>切换 OCR 模型（DeepSeek-OCR ↔ EasyOCR）</li>
<li><b>Alt + 2：</b>切换 Kimi 主模型（Kimi-K2.5 ↔ QwenA3B）</li>
<li><b>Alt + 3：</b>设置 Qwen-VL-8B 为主模型</li>
<li><b>Alt + 4：</b>设置 Qwen-VL-32B 为主模型</li>
<li><b>Alt + 5：</b>设置 Qwen-VL-235B 为主模型</li>
<li><b>Alt + 6：</b>设置 GLM-4.5V 为主模型</li>
<li><b>Alt + 7：</b>设置 Kimi-K2.5(SF) 为主模型</li>
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
    
    def create_settings_tab(self):
        """创建设置标签页（开机自启、守护配置、全局设置）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # ========== 第一部分：图片来源设置 ==========
        image_source_group = QGroupBox("📸 图片来源设置")
        image_source_layout = QHBoxLayout()
        image_source_layout.setSpacing(12)
        
        # 说明文字
        source_info = QLabel(
            "选择 Alt+X 和 Alt+Z 快捷键触发时使用的图片来源：\n"
            "• PC屏幕截图：快速稳定，适合日常练习\n"
            "• 手机物理拍照：更准确，适合正式面试场景"
        )
        source_info.setStyleSheet("color: #666; font-size: 12px;")
        image_source_layout.addWidget(source_info)
        
        # RadioButton 组
        self.image_source_radio_group = QWidget()
        radio_layout = QVBoxLayout(self.image_source_radio_group)
        radio_layout.setContentsMargins(10, 10, 10, 10)
        radio_layout.setSpacing(10)
        
        # PC屏幕截图选项
        self.pc_screenshot_radio = QRadioButton("💻 PC屏幕截图（默认，通过 mss 库截取屏幕）")
        self.pc_screenshot_radio.setChecked(True)
        self.pc_screenshot_radio.toggled.connect(lambda: self.on_image_source_changed('pc'))
        radio_layout.addWidget(self.pc_screenshot_radio)
        
        # 手机物理拍照选项
        self.phone_photo_radio = QRadioButton("📱 手机物理拍照（通过 WebSocket 接收，保存在 phone_photo 目录）")
        self.phone_photo_radio.toggled.connect(lambda: self.on_image_source_changed('phone'))
        radio_layout.addWidget(self.phone_photo_radio)
        
        image_source_layout.addWidget(self.image_source_radio_group)
        
        # 状态显示和提示
        source_status_widget = QWidget()
        source_status_layout = QHBoxLayout(source_status_widget)
        source_status_layout.setContentsMargins(0, 5, 0, 0)
        
        self.image_source_status_label = QLabel("✅ 当前使用：PC屏幕截图")
        self.image_source_status_label.setStyleSheet("color: #4ecca3; font-weight: bold; font-size: 12px;")
        source_status_layout.addWidget(self.image_source_status_label)
        
        source_status_layout.addStretch()
        
        # 保存按钮
        self.btn_save_image_source = QPushButton("💾 保存图片来源配置")
        self.btn_save_image_source.setMaximumWidth(180)
        self.btn_save_image_source.clicked.connect(self.save_global_config)
        source_status_layout.addWidget(self.btn_save_image_source)
        
        image_source_layout.addWidget(source_status_widget)
        
        image_source_group.setLayout(image_source_layout)
        layout.addWidget(image_source_group)
        
        # ========== 第二部分：开机自启设置 ==========
        autostart_group = QGroupBox("🔄 开机自启设置")
        autostart_layout = QVBoxLayout()
        autostart_layout.setSpacing(10)
        
        # 说明文字
        autostart_info = QLabel(
            "启用后，程序将在 Windows 启动时自动运行。\n"
            "适合需要7×24小时持续运行的场景。"
        )
        autostart_info.setStyleSheet("color: #666; font-size: 12px;")
        autostart_layout.addWidget(autostart_info)
        
        # 状态和控制按钮横向布局
        control_layout = QHBoxLayout()
        
        self.autostart_status_label = QLabel("加载中...")
        control_layout.addWidget(self.autostart_status_label)
        
        control_layout.addStretch()
        
        self.btn_toggle_autostart = QPushButton("启用开机自启")
        self.btn_toggle_autostart.setMinimumWidth(120)
        self.btn_toggle_autostart.clicked.connect(self.toggle_autostart)
        control_layout.addWidget(self.btn_toggle_autostart)
        
        autostart_layout.addLayout(control_layout)
        
        # 更新自启状态
        self.update_autostart_status()
        
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        # Windows 服务管理组（更可靠的方案）
        service_group = QGroupBox("🛡️  Windows 系统服务（推荐）")
        service_layout = QVBoxLayout()
        service_layout.setSpacing(10)
        
        # 说明文字
        service_info = QLabel(
            "将程序注册为 Windows 计划任务，实现真正的7×24小时守护。\n"
            "⚠️ 注意：需要以管理员身份运行才能安装服务\n"
            "✅ 系统级保护  ✅ 崩溃自动重启  ✅ 登录自动启动"
        )
        service_info.setStyleSheet("color: #4ecca3; font-size: 12px; font-weight: bold;")
        service_layout.addWidget(service_info)
        
        # 服务状态显示
        status_layout = QHBoxLayout()
        self.service_status_label = QLabel("检查中...")
        status_layout.addWidget(self.service_status_label)
        status_layout.addStretch()
        service_layout.addLayout(status_layout)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.btn_install_service = QPushButton("📥 安装服务")
        self.btn_install_service.setMinimumWidth(100)
        self.btn_install_service.clicked.connect(self.install_windows_service)
        btn_layout.addWidget(self.btn_install_service)
        
        self.btn_uninstall_service = QPushButton("🗑️ 卸载服务")
        self.btn_uninstall_service.setMinimumWidth(100)
        self.btn_uninstall_service.clicked.connect(self.uninstall_windows_service)
        btn_layout.addWidget(self.btn_uninstall_service)
        
        self.btn_check_service = QPushButton("🔄 刷新状态")
        self.btn_check_service.setMinimumWidth(100)
        self.btn_check_service.clicked.connect(self.check_service_status)
        btn_layout.addWidget(self.btn_check_service)
        
        service_layout.addLayout(btn_layout)
        
        # 初始检查状态
        QTimer.singleShot(1500, self.check_service_status)
        
        service_group.setLayout(service_layout)
        layout.addWidget(service_group)
        
        # 守护进程说明组（传统方案，作为备选）
        guardian_group = QGroupBox("📝 传统守护方案（备选）")
        guardian_layout = QVBoxLayout()
        guardian_layout.setSpacing(10)
        
        guardian_info = QTextEdit()
        guardian_info.setReadOnly(True)
        guardian_info.setMaximumHeight(220)
        guardian_content = """
<h3 style='color: #4ecca3;'>⚠️ 注意</h3>
<p>以下为传统的脚本守护方案，<b>推荐使用上方的 Windows 系统服务</b>，更加稳定可靠。</p>

<h3 style='color: #4ecca3;'>🔧 配置参数</h3>
<ul>
<li><b>--max-restarts:</b> 最大重启次数（默认10次）</li>
<li><b>--restart-delay:</b> 重启延迟秒数（默认3秒）</li>
<li><b>--log-file:</b> 日志文件路径（默认guardian.log）</li>
</ul>

<h3 style='color: #4ecca3;'>📊 查看日志</h3>
<p>所有重启事件都会记录到 <code>guardian.log</code> 文件中。</p>
        """
        guardian_info.setHtml(guardian_content)
        guardian_info.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: white;
                padding: 10px;
                font-size: 12px;
            }
        """)
        guardian_layout.addWidget(guardian_info)
        
        # 快速操作按钮
        quick_btn_layout = QHBoxLayout()
        
        btn_open_log_file = QPushButton("📄 查看守护日志")
        btn_open_log_file.clicked.connect(self.open_guardian_log)
        quick_btn_layout.addWidget(btn_open_log_file)
        
        guardian_layout.addLayout(quick_btn_layout)
        
        guardian_group.setLayout(guardian_layout)
        layout.addWidget(guardian_group)
        
        layout.addStretch()
        
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
    
    def start_model_toggle_hotkey(self):
        """启动模型切换快捷键（Alt+1）"""
        try:
            from pynput import keyboard
            
            # 创建全局热键监听器
            self.model_toggle_listener = keyboard.GlobalHotKeys({
                '<alt>+1': self.on_model_toggle_triggered
            })
            self.model_toggle_listener.start()
            
            self.statusBar().showMessage("模型切换快捷键已启用 (Alt+1)")
            print("✅ 模型切换快捷键 Alt+1 已启用")
            
        except Exception as e:
            print(f"❌ 模型切换快捷键启动失败: {e}")
    
    def start_kimi_model_toggle_hotkey(self):
        """启动 Kimi 模型切换快捷键（Alt+2）"""
        try:
            from pynput import keyboard
            
            # 创建全局热键监听器
            self.kimi_model_toggle_listener = keyboard.GlobalHotKeys({
                '<alt>+2': self.on_kimi_model_toggle_triggered
            })
            self.kimi_model_toggle_listener.start()
            
            self.statusBar().showMessage("Kimi模型切换快捷键已启用 (Alt+2)")
            print("✅ Kimi模型切换快捷键 Alt+2 已启用")
            
        except Exception as e:
            print(f"❌ Kimi模型切换快捷键启动失败: {e}")
    
    def start_backup_model_hotkeys(self):
        """启动后备模型快捷键（Alt+3 ~ Alt+7）"""
        try:
            from pynput import keyboard

            # 定义后备模型映射
            backup_models = {
                '<alt>+3': KimiWorker.BACKUP_MODELS[0],  # Qwen/Qwen3-VL-8B-Instruct
                '<alt>+4': KimiWorker.BACKUP_MODELS[1],  # Qwen/Qwen3-VL-32B-Instruct
                '<alt>+5': KimiWorker.BACKUP_MODELS[2],  # Qwen/Qwen3-VL-235B-A22B-Instruct
                '<alt>+6': KimiWorker.BACKUP_MODELS[3],  # zai-org/GLM-4.5V
                '<alt>+7': KimiWorker.BACKUP_MODELS[4],  # Pro/moonshotai/Kimi-K2.5
            }
            
            # 创建回调函数映射
            handlers = {}
            for hotkey, model in backup_models.items():
                # 使用闭包捕获 model 变量
                def make_handler(m):
                    return lambda: self.on_backup_model_triggered(m)
                handlers[hotkey] = make_handler(model)
            
            # 创建全局热键监听器
            self.backup_model_listener = keyboard.GlobalHotKeys(handlers)
            self.backup_model_listener.start()
            
            self.statusBar().showMessage("后备模型快捷键已启用 (Alt+3~7)")
            print("✅ 后备模型快捷键 Alt+3~7 已启用")
            
        except Exception as e:
            print(f"❌ 后备模型快捷键启动失败: {e}")
    
    @Slot()
    def toggle_screenshot(self, checked):
        """切换截图监听状态 - 静默处理错误"""
        if checked:
            # 优先使用 Case1 的热键配置
            hotkey = self.case1_hotkey_input.text().strip() if hasattr(self, 'case1_hotkey_input') else self.hotkey_input.text().strip()
            if not hotkey:
                print("⚠️ 请输入热键组合！")
                self.statusBar().showMessage("⚠️ 请输入热键组合！")
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
        # 【关键】记录快捷键触发时间（Case1: Alt+X）
        self.screenshot_timestamp = time.time()
        self.current_image_path = image_path
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
        self._interrupt_all_tasks()
        # 如果启用了自动 OCR
        if self.auto_ocr_check.isChecked():
            # 发送OCR开始状态
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:OCR分析中]", silent=True)
            self.start_ocr()

    def _interrupt_all_tasks(self):
        """中断所有正在进行的任务（用于新任务触发时）"""
        interrupted = False

        # 中断 OCR 任务
        if self.ocr_worker and self.ocr_worker.isRunning():
            print("🛑 检测到旧 OCR 任务，立即中断...")
            try:
                self.ocr_worker.interrupt()
                # 使用 terminate 强制终止（因为 easyocr 不支持原生中断）
                self.ocr_worker.terminate()
                # 等待线程结束，设置较短超时避免阻塞
                self.ocr_worker.wait(500)
            except Exception as e:
                print(f"⚠️ OCR 任务中断异常: {e}")
            finally:
                self.ocr_worker = None
                interrupted = True

        # 中断 LLM 任务
        if self.llm_worker and self.llm_worker.isRunning():
            print("🛑 检测到旧 LLM 任务，立即中断...")
            try:
                self.llm_worker.interrupt()  # 先关闭 session
                self.llm_worker.terminate()   # 再强制终止
                self.llm_worker.wait(500)     # 短暂等待
            except Exception as e:
                print(f"⚠️ LLM 任务中断异常: {e}")
            finally:
                self.llm_worker = None
                interrupted = True

        # 中断 Kimi 任务（需要更谨慎，因为涉及 OpenAI SDK）
        if self.kimi_worker and self.kimi_worker.isRunning():
            print("🛑 检测到旧 Kimi 任务，立即中断...")
            try:
                self.kimi_worker.interrupt()
                # 【关键】给 Kimi 任务更长的等待时间，让它有机会清理资源
                self.kimi_worker.wait(1000)  # 先尝试优雅退出
                
                # 如果还没退出，再强制终止
                if self.kimi_worker.isRunning():
                    print("⚠️ Kimi 任务未响应，强制终止...")
                    self.kimi_worker.terminate()
                    self.kimi_worker.wait(1000)  # 等待强制终止完成
            except Exception as e:
                print(f"⚠️ Kimi 任务中断异常: {e}")
            finally:
                # 【关键】确保引用被清除，即使发生异常
                try:
                    self.kimi_worker = None
                except:
                    pass
                interrupted = True

        if interrupted:
            print("✅ 旧任务已全部中断，准备处理新任务")
            # 通知手机端（可选）
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:旧任务已中断，处理新任务]", silent=True)

    def on_quick_analysis_triggered(self):
        """快速分析快捷键触发（Alt+Z）"""
        print("🚀 快速分析流程启动...")
        # 【关键】立即中断所有旧任务
        self._interrupt_all_tasks()
        # 【关键】记录快捷键触发时间（必须在截图前）
        self.screenshot_timestamp = time.time()
        # 发送截图触发状态到手机（静默）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:已触发截图]", silent=True)
        
        # 1. 先进行截图
        self.perform_quick_screenshot()
    
    def on_model_toggle_triggered(self):
        """模型切换快捷键触发（Alt+1）"""
        try:

            # 调用切换方法
            current_model = OCRWorker.toggle_model()
            
            # 显示提示消息
            self.statusBar().showMessage(f"OCR 模型已切换为: {current_model}")
            
            # 如果 WebSocket 已连接，通知手机端
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message(f"[STATUS:OCR模型切换为{current_model}]", silent=True)
            
            print(f"✅ 当前 OCR 模型: {current_model}")
            
        except Exception as e:
            print(f"❌ 模型切换失败: {e}")
            self.statusBar().showMessage(f"模型切换失败: {str(e)}")
    
    def _simplify_model_name(self, model_name):
        """简化模型名称显示：超过15字符时截取前7后8"""
        if not model_name:
            return model_name
        
        if len(model_name) > 15:
            return f"{model_name[:3]}...{model_name[10:18]}..."
        return model_name
    
    def on_kimi_model_toggle_triggered(self):
        """Kimi 模型切换快捷键触发（Alt+2）"""
        try:

            # 调用切换方法
            current_model = KimiWorker.toggle_kimi_model()
            
            # 显示提示消息
            self.statusBar().showMessage(f"Kimi 主模型已切换为: {current_model}")
            
            # 如果 WebSocket 已连接，通知手机端（去掉Kimi字样，简化长名称）
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                simplified_model = current_model
                self.websocket_worker.send_message(f"[STATUS:主模型切换为{simplified_model}]", silent=True)
            
            print(f"✅ 当前 Kimi 主模型: {current_model}")
            
        except Exception as e:
            print(f"❌ Kimi 模型切换失败: {e}")
            self.statusBar().showMessage(f"Kimi 模型切换失败: {str(e)}")
    
    def on_backup_model_triggered(self, model_name):
        """后备模型快捷键触发（Alt+3~7）"""
        try:
            # 设置为主模型
            model_short = KimiWorker.set_primary_model(model_name)
            
            # 显示提示消息
            self.statusBar().showMessage(f"Kimi 主模型已设置为: {model_short}")
            
            # 如果 WebSocket 已连接，通知手机端（去掉Kimi字样，简化长名称）
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:

                self.websocket_worker.send_message(f"[STATUS:主模型设置为{model_short}]", silent=True)
            
            print(f"✅ 当前 Kimi 主模型: {model_short}")
            
        except Exception as e:
            print(f"❌ 设置主模型失败: {e}")
            self.statusBar().showMessage(f"设置主模型失败: {str(e)}")
    
    def start_auto_type_hotkey(self):
        """启动自动写入快捷键（Alt+S启动，Alt+L暂停/恢复，Ctrl+K停止）"""
        try:
            from pynput import keyboard
            
            # 创建全局热键监听器
            self.auto_type_listener = keyboard.GlobalHotKeys({
                '<alt>+s': self.on_auto_type_triggered,
                '<alt>+l': self.on_auto_type_toggle_pause,
                '<ctrl>+k': self.on_auto_type_stop  # 停止功能
            })
            self.auto_type_listener.start()
            
            self.statusBar().showMessage("自动写入快捷键已启用 (Alt+S启动, Alt+L暂停/恢复, Ctrl+K停止)")
            print("✅ 自动写入快捷键已启用: Alt+S(启动), Alt+L(暂停/恢复), Ctrl+K(停止)")
            
        except Exception as e:
            print(f"❌ 自动写入快捷键启动失败: {e}")
    
    def start_next_photo_hotkey(self):
        """启动切换下一张手机照片快捷键（Alt+C）"""
        try:
            from pynput import keyboard
            
            # 创建全局热键监听器
            self.next_photo_listener = keyboard.GlobalHotKeys({
                '<alt>+c': self.on_next_photo_triggered
            })
            self.next_photo_listener.start()
            
            self.statusBar().showMessage("切换下一张照片快捷键已启用 (Alt+C)")
            print("✅ 切换下一张照片快捷键 Alt+C 已启用")
            
        except Exception as e:
            print(f"❌ 切换下一张照片快捷键启动失败: {e}")
    
    def on_next_photo_triggered(self):
        """切换下一张手机照片快捷键触发（Alt+C）- 仅切换图片，不触发分析"""
        print("🔄 切换下一张手机照片...")
        
        # 检查当前图片来源是否为手机模式
        image_source = self.get_current_image_source()
        if image_source != 'phone':
            print("⚠️ 当前不是手机拍照模式，请先在设置中切换为手机拍照模式")
            self.statusBar().showMessage("⚠️ 当前不是手机拍照模式", 3000)
            
            # 发送提示到手机
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:请先切换到手机拍照模式]", silent=True)
            return
        
        # 【关键】确保照片列表已加载
        # 如果列表为空，先触发一次加载
        if not ScreenshotWorker._phone_photo_list:
            print("📱 首次加载手机照片列表...")
            # 创建一个临时 ScreenshotWorker 实例来加载列表
            temp_worker = ScreenshotWorker()
            test_path = temp_worker._get_latest_phone_photo()
            
            if not test_path:
                print("⚠️ 没有可用的手机照片")
                self.statusBar().showMessage("⚠️ 没有可用的手机照片", 3000)
                
                if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                    self.websocket_worker.send_message("[STATUS:没有可用的手机照片]", silent=True)
                return
            
            print(f"✅ 照片列表加载成功，共 {len(ScreenshotWorker._phone_photo_list)} 张")
        
        # 切换到下一张照片
        next_photo_path = ScreenshotWorker.get_next_phone_photo()
        
        if not next_photo_path:
            print("⚠️ 切换失败")
            self.statusBar().showMessage("⚠️ 切换失败", 3000)
            
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:切换失败]", silent=True)
            return
        
        # 获取当前照片信息
        photo_info = ScreenshotWorker.get_current_photo_info()
        if photo_info:
            current_index = photo_info['index']
            total = photo_info['total']
            filename = photo_info['filename']
            
            print(f"📱 已切换到第 {current_index}/{total} 张: {filename}")
            print(f"💡 提示：按 Alt+Z 或 Alt+X 开始分析当前图片")
            
            # 更新当前图片路径(供后续 Alt+Z/X 使用)
            self.current_image_path = next_photo_path
                        
            # 发送状态和图片到手机(包含图片Base64数据)
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                try:
                    import base64
                    import json
                                
                    # 读取图片并转换为Base64
                    with open(next_photo_path, 'rb') as f:
                        image_data = f.read()
                                
                    # 获取图片扩展名
                    ext = os.path.splitext(next_photo_path)[1].lstrip('.')
                    mime_type = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else 'image/png'
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                                
                    # 构建JSON消息
                    message = {
                        'type': 'image_switch',
                        'status': f'已切换到第{current_index}/{total}张',
                        'filename': filename,
                        'index': current_index,
                        'total': total,
                        'data': f'data:{mime_type};base64,{base64_data}'
                    }
                                
                    # 发送JSON消息
                    self.websocket_worker.send_message(json.dumps(message), silent=True)
                    print(f"📱 已发送图片到手机: {filename} ({len(base64_data)} bytes)")
                                
                except Exception as e:
                    print(f"⚠️ 发送图片失败: {e}")
                    # 降级为纯文本消息
                    status_msg = f"[STATUS:已切换到第{current_index}/{total}张] [FILE:{filename}]"
                    self.websocket_worker.send_message(status_msg, silent=True)
            
            # 更新UI状态栏
            self.statusBar().showMessage(f"📱 已切换到第 {current_index}/{total} 张: {filename} (按 Alt+Z/X 分析)", 5000)
            
            # 启用 OCR 和 LLM 按钮（如果之前有截图）
            if hasattr(self, 'btn_ocr'):
                self.btn_ocr.setEnabled(True)
        else:
            print("❌ 获取照片信息失败")
            self.statusBar().showMessage("❌ 获取照片信息失败", 3000)
    
    def on_auto_type_toggle_pause(self):
        """自动写入暂停/恢复快捷键触发（Alt+L）"""
        if hasattr(self, 'auto_type_worker') and self.auto_type_worker and self.auto_type_worker.isRunning():
            # 检查是否已经停止或即将停止
            if hasattr(self.auto_type_worker, '_stop_flag') and self.auto_type_worker._stop_flag:
                print("⚠️ 自动写入任务正在停止中，无法暂停/恢复")
                self.statusBar().showMessage("⚠️ 任务正在停止中", 2000)
                return
            
            print("⏸️▶️ 切换自动写入暂停/恢复状态...")
            self.auto_type_worker.toggle_pause()
            
            # 根据当前状态显示不同的提示
            if hasattr(self.auto_type_worker, '_paused'):
                if self.auto_type_worker._paused:
                    self.statusBar().showMessage("⏸️ 写入已暂停（Alt+L恢复 / Ctrl+K停止）", 3000)
                else:
                    self.statusBar().showMessage("▶️ 写入已恢复", 2000)
        else:
            print("⚠️ 当前没有正在运行的自动写入任务")
            self.statusBar().showMessage("⚠️ 当前没有正在运行的自动写入任务", 2000)
    
    def on_auto_type_stop(self):
        """自动写入停止快捷键触发（Ctrl+K）"""
        if hasattr(self, 'auto_type_worker') and self.auto_type_worker and self.auto_type_worker.isRunning():
            print("🛑 正在停止自动写入...")
            self.statusBar().showMessage("🛑 正在停止自动写入...", 2000)
            
            # 发送状态到手机 - 停止写入
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:停止写入]", silent=True)
            
            # 调用停止方法
            self.auto_type_worker.stop_typing()
            
            # 等待线程结束（非阻塞）
            QTimer.singleShot(500, self.check_auto_type_stopped)
        else:
            print("⚠️ 当前没有正在运行的自动写入任务")
            self.statusBar().showMessage("⚠️ 当前没有正在运行的自动写入任务", 2000)
    
    def check_auto_type_stopped(self):
        """检查自动写入是否已停止"""
        if hasattr(self, 'auto_type_worker') and self.auto_type_worker:
            if not self.auto_type_worker.isRunning():
                print("✅ 自动写入已完全停止")
                self.statusBar().showMessage("✅ 自动写入已停止", 3000)
            else:
                # 如果还在运行，继续等待
                QTimer.singleShot(500, self.check_auto_type_stopped)
    
    def _interrupt_running_threads(self):
        """中断正在运行的代码整理和自动写入线程"""
        interrupted = False
        
        # 检查并中断代码整理Worker
        if hasattr(self, 'code_organize_worker') and self.code_organize_worker and self.code_organize_worker.isRunning():
            print("⚠️ 检测到正在运行的代码整理任务，正在中断...")
            if hasattr(self.code_organize_worker, 'interrupt'):
                self.code_organize_worker.interrupt()
            # 等待线程结束（非阻塞）
            self.code_organize_worker.wait(1000)  # 最多等待1秒
            interrupted = True
            print("✅ 代码整理任务已中断")
        
        # 检查并中断自动写入Worker
        if hasattr(self, 'auto_type_worker') and self.auto_type_worker and self.auto_type_worker.isRunning():
            print("⚠️ 检测到正在运行的自动写入任务，正在中断...")
            if hasattr(self.auto_type_worker, 'stop_typing'):
                self.auto_type_worker.stop_typing()
            # 等待线程结束（非阻塞）
            self.auto_type_worker.wait(1000)  # 最多等待1秒
            interrupted = True
            print("✅ 自动写入任务已中断")
        
        if interrupted:
            self.statusBar().showMessage("⚠️ 已中断上次任务，全力处理本次请求", 2000)
            # 发送状态到手机 - 任务中断
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:任务中断]", silent=True)
    
    def on_auto_type_triggered(self):
        """自动写入快捷键触发（Alt+S）- 完整流程：代码整理 -> 保存 -> 自动写入"""
        print("🚀 自动写入流程启动...")
        
        # 【关键优化】检查是否有正在运行的线程，如果有则先中断
        self._interrupt_running_threads()
        
        # 检查是否有可用的API结果
        if not self.kimi_result and not self.llm_result:
            print("⚠️ 没有可用的API结果，请先执行 Case1 或 Case2 工作流")
            self.statusBar().showMessage("⚠️ 请先执行截图分析工作流")
            return
        
        # 【关键】记录开始时间
        self.auto_type_start_time = time.time()
        
        # 步骤1: 发送状态到手机 - 整体代码中
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:整理代码中]", silent=True)
        
        self.statusBar().showMessage("正在整理代码...")
        print("📝 开始整理代码...")
        
        # 步骤2: 启动代码整理Worker
        self.start_code_organize()
    
    def start_code_organize(self):
        """启动代码整理流程 - 使用最新的结果（无论是Kimi还是LLM）"""
        try:
            # 【关键改进】选择最新的结果，而不是默认优先Kimi
            latest_result, result_source = self._get_latest_api_result()
            
            if not latest_result:
                print("⚠️ 没有可用的API结果")
                self.statusBar().showMessage("⚠️ 请先执行截图分析工作流")
                return
            
            print(f"📝 使用 {result_source} 的最新结果进行代码整理...")
            
            # 获取 LongCat API Key（用于代码整理）
            longcat_key = self.api_key_input.text().strip()
            
            # 获取 Case3 自定义提示词
            case3_prompt = None
            if hasattr(self, 'case3_prompt_input') and self.case3_prompt_input:
                case3_prompt = self.case3_prompt_input.toPlainText().strip()
            
            # 创建代码整理Worker - 根据来源传递对应的结果
            if result_source == "Kimi":
                self.code_organize_worker = CodeOrganizeWorker(
                    kimi_result=latest_result,
                    llm_result=None,  # 不传递旧结果
                    save_dir="./code_output",
                    custom_prompt=case3_prompt,
                    longcat_api_key=longcat_key
                )
            else:  # LLM
                self.code_organize_worker = CodeOrganizeWorker(
                    kimi_result=None,  # 不传递旧结果
                    llm_result=latest_result,
                    save_dir="./code_output",
                    custom_prompt=case3_prompt,
                    longcat_api_key=longcat_key
                )
            
            # 连接信号
            self.code_organize_worker.organize_completed.connect(self.on_code_organize_completed)
            self.code_organize_worker.error_occurred.connect(self.on_error)
            self.code_organize_worker.status_update.connect(self.on_code_status_update)
            self.code_organize_worker.file_saved.connect(self.on_code_file_saved)
            
            # 启动
            self.code_organize_worker.start()
            
        except Exception as e:
            print(f"❌ 代码整理启动失败: {e}")
            self.statusBar().showMessage(f"代码整理失败: {str(e)}")
    
    def _get_latest_api_result(self):
        """获取最新的API结果（比较时间戳）
        
        Returns:
            tuple: (result_text, source_name) 或 (None, None)
        """
        # 如果只有一个结果有值，直接返回
        has_kimi = bool(self.kimi_result and self.kimi_result.strip())
        has_llm = bool(self.llm_result and self.llm_result.strip())
        
        if has_kimi and not has_llm:
            print(f"🔍 只有Kimi结果可用")
            return self.kimi_result, "Kimi"
        elif has_llm and not has_kimi:
            print(f"🔍 只有LLM结果可用")
            return self.llm_result, "LLM"
        elif not has_kimi and not has_llm:
            print(f"🔍 没有可用的API结果")
            return None, None
        
        # 两个都有值，比较时间戳
        if self.kimi_result_timestamp and self.llm_result_timestamp:
            kimi_time = self.kimi_result_timestamp
            llm_time = self.llm_result_timestamp
            time_diff = abs(kimi_time - llm_time)
            
            print(f"🔍 Kimi时间戳: {kimi_time:.2f}, LLM时间戳: {llm_time:.2f}, 时间差: {time_diff:.2f}s")
            
            if kimi_time >= llm_time:
                print(f"🔍 选择Kimi结果（更新 {time_diff:.2f}s）")
                return self.kimi_result, "Kimi"
            else:
                print(f"🔍 选择LLM结果（更新 {time_diff:.2f}s）")
                return self.llm_result, "LLM"
        elif self.kimi_result_timestamp:
            print(f"🔍 只有Kimi有时间戳，选择Kimi")
            return self.kimi_result, "Kimi"
        elif self.llm_result_timestamp:
            print(f"🔍 只有LLM有时间戳，选择LLM")
            return self.llm_result, "LLM"
        else:
            # 都没有时间戳，默认优先Kimi（保持向后兼容）
            print(f"⚠️ 都没有时间戳，默认选择Kimi")
            return self.kimi_result, "Kimi"
    
    @Slot(str)
    def on_code_status_update(self, status):
        """代码整理状态更新"""
        self.statusBar().showMessage(status)
    
    @Slot(str)
    def on_code_file_saved(self, filepath):
        """代码文件保存完成"""
        self.code_file_path = filepath
        print(f"💾 代码文件已保存: {filepath}")
    
    @Slot(str)
    def on_code_to_clipboard(self, filtered_code):
        """将过滤后的代码复制到剪切板（在主线程中执行）"""
        try:
            from PySide6.QtWidgets import QApplication as QtApp
            clipboard = QtApp.clipboard()
            clipboard.setText(filtered_code)
            print("📋 代码已成功复制到剪切板")
            self.statusBar().showMessage("✅ 代码已复制到剪切板", 3000)
        except Exception as e:
            print(f"⚠️ 复制到剪切板失败: {str(e)}")
    
    @Slot(str, float)
    def on_code_organize_completed(self, organized_code, elapsed_time):
        """代码整理完成回调"""
        self.organized_code = organized_code
        organize_elapsed = elapsed_time
        
        print(f"✅ 代码整理完成 (耗时: {organize_elapsed:.2f}s)")
        self.statusBar().showMessage(f"代码整理完成 ({organize_elapsed:.2f}s)，准备写入...")
        
        # 保存过滤后的代码，用于自动输入完成后复制到剪切板
        if hasattr(self.code_organize_worker, 'filtered_code'):
            self.filtered_code_for_clipboard = self.code_organize_worker.filtered_code
            print(f"💾 已保存过滤后的代码 ({len(self.filtered_code_for_clipboard)} 字符)")
        else:
            self.filtered_code_for_clipboard = None
        
        # 检查是否设置为"整理后立即复制"
        copy_timing = 'after_complete'  # 默认
        try:
            import json
            # 使用当前工作目录而不是__file__，兼容打包环境
            config_file = os.path.join(os.getcwd(), 'case3_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    copy_timing = config.get('copy_timing', 'after_complete')
        except Exception as e:
            print(f"⚠️ 读取配置失败: {e}，使用默认设置")
        
        # 如果设置为"整理后复制"，立即复制到剪切板
        if copy_timing == 'after_organize' and self.filtered_code_for_clipboard:
            print("📋 检测到设置为'整理后复制'，立即复制到剪切板...")
            self.on_code_to_clipboard(self.filtered_code_for_clipboard)
        
        # 发送整理后的代码到手机端显示
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            code_message = f"""📝 整理后的代码\n
{organized_code}```
⏱️ 整理耗时: {organize_elapsed:.2f}s"""
            self.websocket_worker.send_message(code_message)
            print("📤 已将整理后的代码发送到手机端")
        
        # 步骤3: 启动自动写入
        if self.code_file_path:
            self.start_auto_type()
        else:
            print("❌ 代码文件路径不存在")
            self.statusBar().showMessage("代码文件路径错误")
    
    def start_auto_type(self):
        """启动自动写入流程"""
        try:
            if not self.code_file_path or not os.path.exists(self.code_file_path):
                print("❌ 代码文件不存在")
                self.statusBar().showMessage("代码文件不存在")
                return
            
            # 检查复制时机设置
            copy_timing = 'after_complete'  # 默认
            try:
                import json
                # 使用当前工作目录而不是__file__，兼容打包环境
                config_file = os.path.join(os.getcwd(), 'case3_config.json')
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        copy_timing = config.get('copy_timing', 'after_complete')
            except Exception as e:
                print(f"⚠️ 读取配置失败: {e}，使用默认设置")
            
            # 创建自动写入Worker，并传递过滤后的代码
            # 从 UI 中获取 delay 和 think_time 参数
            delay = self.delay_slider.value() / 100.0
            think_time_min = self.think_time_min_spinbox.value()
            think_time_max = self.think_time_max_spinbox.value()
            error_rate = self.error_rate_spinbox.value()
            line_break_rate = self.line_break_rate_spinbox.value()
            
            self.auto_type_worker = AutoTypeWorker(
                code_file_path=self.code_file_path,
                delay=delay,
                think_time_min=think_time_min,
                think_time_max=think_time_max,
                error_rate=error_rate,
                line_break_rate=line_break_rate
            )
            
            # 设置过滤后的代码，用于输入完成后复制到剪切板
            if hasattr(self, 'filtered_code_for_clipboard'):
                self.auto_type_worker.filtered_code = self.filtered_code_for_clipboard
            
            # 连接信号
            self.auto_type_worker.typing_started.connect(self.on_typing_started)
            self.auto_type_worker.typing_paused.connect(self.on_typing_paused)
            self.auto_type_worker.typing_resumed.connect(self.on_typing_resumed)
            self.auto_type_worker.typing_completed.connect(self.on_typing_completed)
            
            # 根据配置决定是否在写入完成后复制
            if copy_timing == 'after_complete':
                self.auto_type_worker.clipboard_ready.connect(self.on_code_to_clipboard)  # 写入完成后复制到剪切板
                print("📋 已设置：写入完成后复制")
            else:
                print("📋 已设置：整理后立即复制（跳过写入后复制）")
            
            self.auto_type_worker.error_occurred.connect(self.on_error)
            self.auto_type_worker.status_update.connect(self.on_auto_type_status_update)
            self.auto_type_worker.progress_update.connect(self.on_typing_progress_update)
            
            # 启动
            self.auto_type_worker.start()
            
        except Exception as e:
            print(f"❌ 自动写入启动失败: {e}")
            self.statusBar().showMessage(f"自动写入失败: {str(e)}")
    
    @Slot()
    def on_typing_started(self):
        """自动写入开始"""
        print("⌨️ 自动写入已开始")
        
        # 发送状态到手机 - 自动写入中
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:自动写入中]", silent=True)
        
        self.statusBar().showMessage("⌨️ 自动写入中...（Alt+L暂停/恢复 | Ctrl+K停止）")
    
    @Slot()
    def on_typing_paused(self):
        """自动写入暂停"""
        print("⏸️ 自动写入已暂停")
        self.statusBar().showMessage("⏸️ 写入已暂停（Alt+L恢复 | Ctrl+K停止）")
        
        # 发送状态到手机 - 暂停写入
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:暂停写入]", silent=True)

    @Slot()
    def on_typing_resumed(self):
        """自动写入恢复"""
        print("▶️ 自动写入已恢复")
        self.statusBar().showMessage("恢复写入...")
        
        # 发送状态到手机 - 恢复写入
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:恢复写入]", silent=True)
    
    @Slot(float)
    def on_typing_completed(self, total_elapsed):
        """自动写入完成"""
        overall_elapsed = time.time() - self.auto_type_start_time
        print(f"✅ 自动写入完成! (写入耗时: {total_elapsed:.2f}s, 总耗时: {overall_elapsed:.2f}s)")
        self.statusBar().showMessage(f"写入完成! (总耗时: {overall_elapsed:.2f}s)")
        
        # 发送状态到手机 - 写入完成（总耗时）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message(f"[STATUS:写入完成] [ELAPSED:{overall_elapsed:.2f}]", silent=True)
    
    @Slot(int, int)
    def on_typing_progress_update(self, current_line, total_lines):
        """写入进度更新"""
        if current_line % 10 == 0 or current_line == total_lines:
            progress_text = f"已输入 {current_line}/{total_lines} 行"
            self.statusBar().showMessage(progress_text)
    
    @Slot(str)
    def on_auto_type_status_update(self, status):
        """自动写入状态更新"""
        self.statusBar().showMessage(status)
    
    def perform_quick_screenshot(self):
        """执行快速截图（根据配置选择图片来源）"""
        try:
            # 检查图片来源配置
            image_source = self.get_current_image_source()
            
            if image_source == 'phone':
                # 使用手机拍照来源
                self.perform_phone_photo_analysis()
            else:
                # 使用 PC 屏幕截图（默认）
                self.perform_pc_screenshot_analysis()
                
        except Exception as e:
            print(f"❌ 快速分析失败: {e}")
            self.statusBar().showMessage(f"快速分析失败: {str(e)}")
    
    def get_current_image_source(self):
        """获取当前图片来源配置"""
        try:
            import json
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                # 打包后：使用 exe 所在目录
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境：使用当前工作目录
                base_dir = os.getcwd()
            
            config_file = os.path.join(base_dir, 'global_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return config_data.get('image_source', 'pc')
            else:
                return 'pc'  # 默认使用 PC 截图
        except Exception as e:
            print(f"⚠️ 读取图片来源配置失败: {e}，使用默认值")
            return 'pc'
    
    def perform_pc_screenshot_analysis(self):
        """执行 PC 屏幕截图分析"""
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
                
                print(f"📸 PC 截图完成: {filename}")
                
                # 发送LLM开始状态（快速分析跳过OCR，直接进入LLM）
                if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                    self.websocket_worker.send_message("[STATUS:LLM分析中]", silent=True)
                
                # 调用 Kimi 分析
                self.start_kimi_analysis(filepath)
                
        except Exception as e:
            print(f"❌ PC 截图失败: {e}")
            self.statusBar().showMessage(f"PC 截图失败: {str(e)}")
    
    def perform_phone_photo_analysis(self):
        """执行手机拍照分析（优先使用当前选中的图片，否则使用最新）"""
        try:
            from datetime import datetime
            
            # 检查是否有当前选中的图片（通过 Alt+C 切换的）
            if hasattr(self, 'current_image_path') and self.current_image_path:
                # 验证文件是否存在
                if os.path.exists(self.current_image_path):
                    image_path = self.current_image_path
                    print(f"📱 使用当前选中的图片: {os.path.basename(image_path)}")
                else:
                    print(f"⚠️ 当前选中的图片不存在，重新获取最新图片")
                    self.current_image_path = None
                    image_path = self._get_latest_phone_photo_path()
                    if not image_path:
                        return
            else:
                # 获取最新的图片
                image_path = self._get_latest_phone_photo_path()
                if not image_path:
                    return
            
            print(f"📱 开始分析: {os.path.basename(image_path)}")
            
            # 发送LLM开始状态
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:LLM分析中]", silent=True)
            
            # 调用 Kimi 分析
            self.start_kimi_analysis(image_path)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 手机拍照分析失败: {e}")
            print(f"错误详情:\n{error_detail}")
            self.statusBar().showMessage(f"手机拍照分析失败: {str(e)}")
    
    def _get_latest_phone_photo_path(self):
        """获取最新的手机拍照图片路径（用于 Alt+Z/X 首次触发）"""
        try:
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                # 打包后：使用 exe 所在目录
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境：使用当前工作目录
                base_dir = os.getcwd()
            
            # 获取 phone_photo 目录
            phone_photo_dir = os.path.join(base_dir, 'phone_photo')
            
            if not os.path.exists(phone_photo_dir):
                print("⚠️ 手机拍照目录不存在！请先通过手机 WebSocket 连接发送图片。")
                self.statusBar().showMessage("⚠️ 手机拍照目录不存在，已自动切换为 PC 截图模式", 3000)
                # 自动切换回 PC 截图模式
                self.pc_screenshot_radio.setChecked(True)
                self.phone_photo_radio.setChecked(False)
                self.image_source_status_label.setText("✅ 当前使用：PC屏幕截图")
                return None
            
            # 查找最新的图片文件夹
            folders = [f for f in os.listdir(phone_photo_dir) 
                      if os.path.isdir(os.path.join(phone_photo_dir, f))]
            
            if not folders:
                print("⚠️ 手机拍照目录为空！请先通过手机发送图片到 PC。")
                self.statusBar().showMessage("⚠️ 手机拍照目录为空，已自动切换为 PC 截图模式", 3000)
                # 自动切换回 PC 截图模式
                self.pc_screenshot_radio.setChecked(True)
                self.phone_photo_radio.setChecked(False)
                self.image_source_status_label.setText("✅ 当前使用：PC屏幕截图")
                return None
            
            # 按时间排序，获取最新的文件夹
            folders.sort(reverse=True)
            latest_folder = folders[0]
            folder_path = os.path.join(phone_photo_dir, latest_folder)
            
            # 查找文件夹中的图片文件
            image_files = [f for f in os.listdir(folder_path) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            
            if not image_files:
                print(f"⚠️ 文件夹 '{latest_folder}' 中没有图片文件！")
                self.statusBar().showMessage(f"⚠️ 文件夹 '{latest_folder}' 中没有图片文件", 3000)
                return None
            
            # 按文件名排序，获取第一张图片（通常是 1.png）
            image_files.sort()
            latest_image = image_files[0]
            image_path = os.path.join(folder_path, latest_image)
            
            return image_path
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 获取手机拍照路径失败: {e}")
            print(f"错误详情:\n{error_detail}")
            return None
    
    @Slot()
    def start_ocr(self):
        """开始 OCR 识别 - 静默处理错误"""
        if not self.current_image_path:
            print("⚠️ 请先进行截图！")
            self.statusBar().showMessage("⚠️ 请先进行截图！")
            return
        
        if not os.path.exists(self.current_image_path):
            print(f"⚠️ 截图文件不存在: {self.current_image_path}")
            self.statusBar().showMessage("⚠️ 截图文件不存在！")
            return
        
        # 禁用按钮
        self.btn_ocr.setEnabled(False)
        self.btn_ocr.setText("识别中...")
        
        # 发送OCR开始状态到手机（静默）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message("[STATUS:OCR分析中]", silent=True)
        
        # 创建并启动 OCR 工作线程
        siliconflow_key = self.backup_api_key_input.text().strip()
        self.ocr_worker = OCRWorker(self.current_image_path, siliconflow_api_key=siliconflow_key)
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
        
        # 【关键】发送 OCR 完成状态到手机（通知手机端可以切换到 LLM 分析）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message(f"[STATUS:OCR已完成] [ELAPSED:{elapsed_time:.2f}]", silent=True)
        
        # 如果启用了自动 LLM
        if self.auto_llm_check.isChecked():
            self.start_llm()
    
    @Slot()
    def start_llm(self):
        """开始 LLM 分析 - 静默处理错误"""
        if not self.ocr_result:
            print("⚠️ 请先进行 OCR 识别！")
            self.statusBar().showMessage("⚠️ 请先进行 OCR 识别！")
            return
        
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        
        # 【修改】优先使用共享提示词，如果没有则使用主页提示词
        prompt = ""
        if hasattr(self, 'shared_prompt_input') and self.shared_prompt_input:
            prompt = self.shared_prompt_input.toPlainText().strip()
        elif hasattr(self, 'main_prompt_input') and self.main_prompt_input:
            prompt = self.main_prompt_input.toPlainText().strip()
        
        if not api_key or not model or not prompt:
            print("⚠️ 请填写完整的 LLM 配置！")
            self.statusBar().showMessage("⚠️ 请填写完整的 LLM 配置！")
            return
        # 【关键】如果已有 LLM 任务在运行，先中断
        if self.llm_worker and self.llm_worker.isRunning():
            print("⚠️ 检测到正在运行的 LLM 任务，先中断...")
            try:
                self.llm_worker.interrupt()
                self.llm_worker.terminate()
                self.llm_worker.wait(500)
            except Exception as e:
                print(f"⚠️ LLM 任务中断异常: {e}")
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
        self.llm_result_timestamp = time.time()  # 【关键】记录时间戳
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
        """开始 Kimi 图片分析（支持 DeepSeek-OCR + EasyOCR 降级）"""
        try:
            # 【修改】优先使用共享提示词，如果没有则使用主页提示词
            prompt = ""
            if hasattr(self, 'shared_prompt_input') and self.shared_prompt_input:
                prompt = self.shared_prompt_input.toPlainText().strip()
            elif hasattr(self, 'main_prompt_input') and self.main_prompt_input:
                prompt = self.main_prompt_input.toPlainText().strip()
            else:
                # 默认提示词
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
            
            # 从 UI 获取 Kimi API Key
            api_key = self.kimi_api_key_input.text().strip()
            if not api_key:
                print("⚠️ 请先在 Case2 标签页中填写 Kimi API Key！")
                self.statusBar().showMessage("⚠️ 请先填写 Kimi API Key！")
                return
            
            # 获取 SiliconFlow API Key（用于备选模型）
            siliconflow_key = self.backup_api_key_input.text().strip()
            
            print(f"🤖 开始 Kimi 分析...")
            self.statusBar().showMessage("正在调用 Kimi 分析图片...")
            
            # 【关键】发送 LLM 开始状态到手机
            if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
                self.websocket_worker.send_message("[STATUS:LLM分析中]", silent=True)
            
            # 【关键】如果已有 Kimi 任务在运行，先中断
            if self.kimi_worker and self.kimi_worker.isRunning():
                print("⚠️ 检测到正在运行的 Kimi 任务，先中断...")
                try:
                    self.kimi_worker.interrupt()
                    self.kimi_worker.terminate()
                    self.kimi_worker.wait(500)
                except Exception as e:
                    print(f"⚠️ Kimi 任务中断异常: {e}")
            
            # 创建并启动 Kimi 工作线程
            self.kimi_worker = KimiWorker(api_key, image_path, prompt, siliconflow_api_key=siliconflow_key)
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
        self.kimi_result_timestamp = time.time()  # 【关键】记录时间戳
        
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
        """发送结果到手机 - 静默处理错误"""
        if not self.websocket_worker or not self.websocket_worker.is_running:
            print("⚠️ WebSocket 服务未启动！")
            self.statusBar().showMessage("⚠️ WebSocket 服务未启动！")
            return
        
        if not self.llm_result:
            print("⚠️ 没有可发送的结果！")
            self.statusBar().showMessage("⚠️ 没有可发送的结果！")
            return
        
        # 构建发送消息（只发送 LLM 分析结果）
        message = f"""🤖 LLM 智能分析结果

{self.llm_result}

⏰ {self.get_current_time()}"""
        
        # 发送消息
        self.websocket_worker.send_message(message)
    
    @Slot(str)
    def on_error(self, error_msg):
        """错误处理回调 - 静默处理，仅显示在状态栏"""
        print(f"❌ 错误: {error_msg}")
        self.statusBar().showMessage(f"错误: {error_msg}")
        
        # 同步到 WebSocket（如果已连接）
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
            self.websocket_worker.send_message(f"[ERROR:{error_msg}]", silent=True)
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_prompt_config(self):
        """保存提示词配置（主页）- 同步到共享提示词"""
        try:
            prompt_text = self.main_prompt_input.toPlainText()
            
            # 保存到文件
            config_file = "prompt_config.json"
            import json
            
            config_data = {
                "shared_prompt": prompt_text,  # 【修改】使用 shared_prompt 键
                "last_modified": self.get_current_time()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 同步更新到共享提示词输入框
            if hasattr(self, 'shared_prompt_input') and self.shared_prompt_input:
                self.shared_prompt_input.setText(prompt_text)
            
            print(f"💾 提示词已保存到 {config_file}")
            self.statusBar().showMessage("✅ 提示词配置已保存", 3000)
            
        except Exception as e:
            print(f"❌ 保存提示词失败: {e}")
            self.statusBar().showMessage(f"❌ 保存失败: {str(e)}")
    
    def _on_api_key_changed(self):
        """API Key 变更时自动保存配置"""
        # 使用防抖定时器，避免频繁写入
        if not hasattr(self, '_api_key_save_timer'):
            self._api_key_save_timer = QTimer()
            self._api_key_save_timer.setSingleShot(True)
            self._api_key_save_timer.setInterval(1000)  # 1秒防抖
            self._api_key_save_timer.timeout.connect(self.save_api_keys_config)
        self._api_key_save_timer.start()
    
    def _copy_api_url(self, url, name):
        """复制 API Key 获取链接到剪贴板"""
        from PySide6.QtWidgets import QApplication as QtApp
        clipboard = QtApp.clipboard()
        clipboard.setText(url)
        self.statusBar().showMessage(f"✅ {name} API Key 获取地址已复制到剪贴板", 3000)
        # 给点击的按钮临时反馈
        btn = self.sender()
        if btn:
            original_text = btn.text()
            btn.setText("✅ 已复制")
            QTimer.singleShot(2000, lambda: btn.setText(original_text))
    
    def save_api_keys_config(self):
        """保存 API Keys 到配置文件（持久化）"""
        try:
            import json
            
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            
            config_data = {
                'longcat_api_key': self.api_key_input.text().strip(),
                'kimi_api_key': self.kimi_api_key_input.text().strip(),
                'siliconflow_api_key': self.backup_api_key_input.text().strip(),
            }
            
            config_file = os.path.join(base_dir, 'api_keys_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 API Keys 配置已保存: {config_file}")
            
        except Exception as e:
            print(f"❌ 保存 API Keys 配置失败: {e}")
    
    def load_api_keys_config(self):
        """从配置文件加载 API Keys（持久化）"""
        try:
            import json
            
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            
            config_file = os.path.join(base_dir, 'api_keys_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if config_data.get('longcat_api_key'):
                    self.api_key_input.setText(config_data['longcat_api_key'])
                if config_data.get('kimi_api_key'):
                    self.kimi_api_key_input.setText(config_data['kimi_api_key'])
                if config_data.get('siliconflow_api_key'):
                    self.backup_api_key_input.setText(config_data['siliconflow_api_key'])
                
                print(f"✅ 已加载 API Keys 配置")
            else:
                print("ℹ️ 未找到 API Keys 配置文件，请手动填写")
                
        except Exception as e:
            print(f"⚠️ 加载 API Keys 配置失败: {e}")
    
    def load_saved_config(self):
        """加载保存的配置"""
        try:
            import json
            import os
            
            # 加载 API Keys 配置
            self.load_api_keys_config()
            
            config_file = "prompt_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 【修改】优先加载 shared_prompt，兼容旧的 main_prompt
                saved_prompt = None
                if "shared_prompt" in config_data:
                    saved_prompt = config_data["shared_prompt"]
                elif "main_prompt" in config_data:
                    saved_prompt = config_data["main_prompt"]
                
                if saved_prompt:
                    # 更新共享提示词（优先级最高）
                    if hasattr(self, 'shared_prompt_input') and self.shared_prompt_input:
                        self.shared_prompt_input.setText(saved_prompt)
                    
                    # 更新主页提示词
                    if hasattr(self, 'main_prompt_input') and self.main_prompt_input:
                        self.main_prompt_input.setText(saved_prompt)
                    
                    print(f"✅ 已加载保存的提示词配置 (修改时间: {config_data.get('last_modified', '未知')})")
                else:
                    print("⚠️ 配置文件无提示词数据")
            else:
                print("ℹ️ 未找到保存的配置文件，使用默认配置")
                
        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        # 加载 Case3 配置
        if hasattr(self, 'load_case3_config'):
            self.load_case3_config()
        
        # 加载全局配置（图片来源）
        self.load_global_config()
    
    def on_image_source_changed(self, source_type):
        """图片来源切换回调"""
        if source_type == 'pc':
            self.image_source_status_label.setText("✅ 当前使用：PC屏幕截图")
            self.image_source_status_label.setStyleSheet("color: #4ecca3; font-weight: bold; font-size: 12px;")
            print("📸 图片来源已切换为：PC屏幕截图")
        elif source_type == 'phone':
            self.image_source_status_label.setText("✅ 当前使用：手机物理拍照")
            self.image_source_status_label.setStyleSheet("color: #4ecca3; font-weight: bold; font-size: 12px;")
            print("📱 图片来源已切换为：手机物理拍照")
    
    def save_global_config(self):
        """保存全局配置（图片来源等）"""
        try:
            import json
            
            # 确定图片来源
            if self.pc_screenshot_radio.isChecked():
                image_source = 'pc'
            else:
                image_source = 'phone'
            
            config_data = {
                'image_source': image_source,
                'last_modified': self.get_current_time()
            }
            
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            
            # 保存到文件
            config_file = os.path.join(base_dir, 'global_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 全局配置已保存: {config_file}")
            print(f"   - 图片来源: {image_source}")
            
            self.statusBar().showMessage("✅ 全局配置已保存！", 3000)
            
        except Exception as e:
            print(f"❌ 保存全局配置失败: {e}")
            self.statusBar().showMessage(f"❌ 保存配置失败: {str(e)}")
    
    def load_global_config(self):
        """加载全局配置（图片来源等）"""
        try:
            import json
            
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            
            config_file = os.path.join(base_dir, 'global_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载图片来源设置
                if 'image_source' in config_data:
                    image_source = config_data['image_source']
                    
                    if image_source == 'pc':
                        self.pc_screenshot_radio.setChecked(True)
                        self.phone_photo_radio.setChecked(False)
                        self.image_source_status_label.setText("✅ 当前使用：PC屏幕截图")
                    elif image_source == 'phone':
                        self.pc_screenshot_radio.setChecked(False)
                        self.phone_photo_radio.setChecked(True)
                        self.image_source_status_label.setText("✅ 当前使用：手机物理拍照")
                    
                    print(f"✅ 已加载全局配置 - 图片来源: {image_source} (修改时间: {config_data.get('last_modified', '未知')})")
                else:
                    print("⚠️ 全局配置文件无图片来源数据，使用默认值")
            else:
                print("ℹ️ 未找到全局配置文件，使用默认配置（PC屏幕截图）")
                
        except Exception as e:
            print(f"⚠️ 加载全局配置失败: {e}，使用默认配置")
    
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
            print("⚠️ IP 地址尚未加载完成！")
            self.statusBar().showMessage("⚠️ IP 地址尚未加载完成！")
    
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
    
    def add_autostart_control_to_statusbar(self):
        """在状态栏添加自启控制"""
        status_bar = self.statusBar()
        
        # 创建自启状态标签
        self.statusbar_autostart_label = QLabel()
        self.update_statusbar_autostart()
        
        # 添加到状态栏永久部件
        status_bar.addPermanentWidget(self.statusbar_autostart_label)
    
    def update_statusbar_autostart(self):
        """更新状态栏自启状态显示"""
        if hasattr(self, 'statusbar_autostart_label'):
            is_enabled = self.autostart_manager.is_enabled()
            if is_enabled:
                self.statusbar_autostart_label.setText("🔄 自启: 已启用")
                self.statusbar_autostart_label.setStyleSheet("color: #4ecca3;")
            else:
                self.statusbar_autostart_label.setText("🔄 自启: 未启用")
                self.statusbar_autostart_label.setStyleSheet("color: #999;")
    
    def update_autostart_status(self):
        """更新自启状态显示"""
        is_enabled = self.autostart_manager.is_enabled()
        if is_enabled:
            self.autostart_status_label.setText("✅ 开机自启已启用")
            self.autostart_status_label.setStyleSheet("color: #4ecca3; font-weight: bold;")
            self.btn_toggle_autostart.setText("禁用开机自启")
        else:
            self.autostart_status_label.setText("❌ 开机自启未启用")
            self.autostart_status_label.setStyleSheet("color: #e94560; font-weight: bold;")
            self.btn_toggle_autostart.setText("启用开机自启")
        
        # 同时更新状态栏
        self.update_statusbar_autostart()
    
    @Slot()
    def toggle_autostart(self):
        """切换开机自启状态 - 静默处理"""
        success, message = self.autostart_manager.toggle_startup()
        
        if success:
            self.update_autostart_status()
            print(f"✅ {message}")
            self.statusBar().showMessage(message, 3000)
        else:
            print(f"❌ 操作失败: {message}")
            self.statusBar().showMessage(f"❌ 操作失败: {message}")
    
    @Slot()
    def open_guardian_script(self):
        """打开守护启动脚本 - 静默处理"""
        script_path = os.path.abspath("start_with_guardian.bat")
        if os.path.exists(script_path):
            os.startfile(script_path)
            self.statusBar().showMessage(f"已启动守护脚本: {script_path}")
        else:
            print(f"⚠️ 找不到启动脚本: {script_path}")
            self.statusBar().showMessage(f"⚠️ 找不到启动脚本")
    
    @Slot()
    def open_guardian_log(self):
        """打开守护日志文件 - 静默处理"""
        log_path = os.path.abspath("guardian.log")
        if os.path.exists(log_path):
            os.startfile(log_path)
            self.statusBar().showMessage(f"已打开日志文件: {log_path}")
        else:
            print(f"ℹ️ 日志文件尚不存在: {log_path}")
            self.statusBar().showMessage(f"ℹ️ 日志文件尚不存在")
    
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
    
    @Slot()
    def install_windows_service(self):
        """安装 Windows 系统服务 - 静默处理"""
        print("⚠️ 重要提示：此操作需要管理员权限！")
        print("将安装 AceInterview 为 Windows 计划任务。")
        print("✅ 登录时自动启动 | ✅ 崩溃后自动重启（最多10次） | ✅ 系统级保护")
        
        try:
            success, message = self.service_manager.install_as_service(
                max_restarts=10,
                restart_delay=3
            )
            
            if success:
                print(f"✅ {message}")
                self.statusBar().showMessage(message, 3000)
                self.check_service_status()
            else:
                print(f"❌ {message}")
                self.statusBar().showMessage(f"❌ {message}", 5000)
        except Exception as e:
            error_msg = f"安装失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.statusBar().showMessage(f"❌ {error_msg}", 5000)
    
    @Slot()
    def uninstall_windows_service(self):
        """卸载 Windows 系统服务 - 静默处理"""
        print("⚠️ 将卸载 AceInterview 的 Windows 计划任务")
        print("程序将不再自动启动和重启。")
        
        try:
            success, message = self.service_manager.uninstall_service()
            
            if success:
                print(f"✅ {message}")
                self.statusBar().showMessage(message, 3000)
                self.check_service_status()
            else:
                print(f"❌ {message}")
                self.statusBar().showMessage(f"❌ {message}", 5000)
        except Exception as e:
            error_msg = f"卸载失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.statusBar().showMessage(f"❌ {error_msg}", 5000)
    
    @Slot()
    def check_service_status(self):
        """检查 Windows 服务状态"""
        try:
            status = self.service_manager.get_service_status()
            
            if not status['installed']:
                self.service_status_label.setText("⚪ 未安装")
                self.btn_install_service.setEnabled(True)
                self.btn_uninstall_service.setEnabled(False)
            else:
                if status['running']:
                    status_text = "🟢 运行中"
                else:
                    status_text = "🔴 已停止"
                
                self.service_status_label.setText(f"{status_text} (已安装)")
                self.btn_install_service.setEnabled(False)
                self.btn_uninstall_service.setEnabled(True)
                
                # 显示详细信息
                if status.get('last_run'):
                    print(f"上次运行: {status['last_run']}")
                if status.get('next_run'):
                    print(f"下次运行: {status['next_run']}")
        except Exception as e:
            self.service_status_label.setText(f"❌ 检查失败: {str(e)}")
    
    @Slot()
    def open_guardian_log(self):
        """打开守护日志文件 - 静默处理"""
        log_path = os.path.abspath("guardian.log")
        if os.path.exists(log_path):
            os.startfile(log_path)
            self.statusBar().showMessage(f"已打开日志文件: {log_path}")
        else:
            print(f"ℹ️ 日志文件不存在: {log_path}")
            self.statusBar().showMessage(f"ℹ️ 日志文件不存在")
    
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
        
        # 停止模型切换监听器
        if hasattr(self, 'model_toggle_listener') and self.model_toggle_listener:
            try:
                print("⏳ 正在停止模型切换监听...")
                self.model_toggle_listener.stop()
                print("✅ 模型切换监听已停止")
            except:
                pass
        
        # 停止 Kimi 模型切换监听器
        if hasattr(self, 'kimi_model_toggle_listener') and self.kimi_model_toggle_listener:
            try:
                print("⏳ 正在停止 Kimi 模型切换监听...")
                self.kimi_model_toggle_listener.stop()
                print("✅ Kimi 模型切换监听已停止")
            except:
                pass
        
        # 停止后备模型监听器
        if hasattr(self, 'backup_model_listener') and self.backup_model_listener:
            try:
                print("⏳ 正在停止后备模型监听...")
                self.backup_model_listener.stop()
                print("✅ 后备模型监听已停止")
            except:
                pass
        
        # 【新增】清理 OCR 引擎单例，释放内存
        try:
            OCRWorker.cleanup_reader()
            print("✅ OCR 引擎已清理")
        except Exception as e:
            print(f"⚠️ OCR 引擎清理失败: {e}")
        
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
        
        # 停止模型切换监听器
        if hasattr(self, 'model_toggle_listener') and self.model_toggle_listener:
            try:
                print("⏳ 正在停止模型切换监听...")
                self.model_toggle_listener.stop()
                print("✅ 模型切换监听已停止")
            except:
                pass
        
        # 停止 Kimi 模型切换监听器
        if hasattr(self, 'kimi_model_toggle_listener') and self.kimi_model_toggle_listener:
            try:
                print("⏳ 正在停止 Kimi 模型切换监听...")
                self.kimi_model_toggle_listener.stop()
                print("✅ Kimi 模型切换监听已停止")
            except:
                pass
        
        # 停止后备模型监听器
        if hasattr(self, 'backup_model_listener') and self.backup_model_listener:
            try:
                print("⏳ 正在停止后备模型监听...")
                self.backup_model_listener.stop()
                print("✅ 后备模型监听已停止")
            except:
                pass
        
        # 停止自动写入监听器
        if hasattr(self, 'auto_type_listener') and self.auto_type_listener:
            try:
                print("⏳ 正在停止自动写入监听...")
                self.auto_type_listener.stop()
                print("✅ 自动写入监听已停止")
            except:
                pass
        
        # 停止代码整理Worker
        if self.code_organize_worker and self.code_organize_worker.isRunning():
            print("⏳ 正在停止代码整理...")
            self.code_organize_worker.interrupt()
            self.code_organize_worker.terminate()
            self.code_organize_worker.wait(1000)
            print("✅ 代码整理已停止")
        
        # 停止自动写入Worker
        if self.auto_type_worker and self.auto_type_worker.isRunning():
            print("⏳ 正在停止自动写入...")
            self.auto_type_worker.stop_typing()
            self.auto_type_worker.terminate()
            self.auto_type_worker.wait(1000)
            print("✅ 自动写入已停止")
        
        # 【新增】清理 OCR 引擎单例，释放内存
        try:
            OCRWorker.cleanup_reader()
            print("✅ OCR 引擎已清理")
        except Exception as e:
            print(f"⚠️ OCR 引擎清理失败: {e}")
        
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
