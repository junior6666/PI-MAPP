import sys
import os
import cv2
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from ultralytics import YOLO
from database_setup import DatabaseManager
from database_operations import DatabaseOperations
from report_generator import ReportGenerator
import json
import traceback
import traceback
from functools import partial

class FluentStyle:
    """Fluent Design 样式定义"""
    # 颜色定义
    BACKGROUND_DARK = "#1E1E1E"
    BACKGROUND_LIGHT = "#2D2D2D"
    PRIMARY_COLOR = "#0078D7"
    TEXT_COLOR = "#FFFFFF"
    BORDER_COLOR = "#404040"
    
    # 样式表
    MAIN_STYLE = f"""
    QMainWindow {{
        background-color: {BACKGROUND_DARK};
        color: {TEXT_COLOR};
        font-family: "Segoe UI";
    }}
    
    QWidget {{
        background-color: {BACKGROUND_DARK};
        color: {TEXT_COLOR};
        font-family: "Segoe UI";
    }}
    
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: #106EBE;
    }}
    
    QPushButton:pressed {{
        background-color: #005A9E;
    }}
    
    QPushButton:disabled {{
        background-color: #666666;
        color: #999999;
    }}
    
    QLabel {{
        color: {TEXT_COLOR};
        font-size: 14px;
    }}
    
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {BACKGROUND_LIGHT};
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
        padding: 6px;
        font-size: 14px;
    }}
    
    QTableWidget {{
        background-color: {BACKGROUND_LIGHT};
        color: {TEXT_COLOR};
        gridline-color: {BORDER_COLOR};
        border: 1px solid {BORDER_COLOR};
    }}
    
    QTableWidget::item {{
        padding: 8px;
    }}
    
    QHeaderView::section {{
        background-color: {BACKGROUND_DARK};
        color: {TEXT_COLOR};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {BORDER_COLOR};
        background-color: {BACKGROUND_DARK};
    }}
    
    QTabBar::tab {{
        background-color: {BACKGROUND_LIGHT};
        color: {TEXT_COLOR};
        padding: 12px 24px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {PRIMARY_COLOR};
    }}
    
    QScrollBar:vertical {{
        background-color: {BACKGROUND_LIGHT};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {BORDER_COLOR};
        border-radius: 6px;
        min-height: 20px;
    }}
    """

class DetectionWidget(QWidget):
    """检测结果显示组件"""
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setMaximumHeight(30)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 2px;")
        layout.addWidget(title_label)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setMinimumSize(360, 450)
        self.image_label.setStyleSheet(f"border: 2px solid {FluentStyle.BORDER_COLOR}; border-radius: 8px;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("等待图像...")
        layout.addWidget(self.image_label)
        
        self.setLayout(layout)
    
    def set_image(self, image_path):
        """设置显示的图像"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("图像加载失败")

class DetailsWidget(QWidget):
    """详细信息显示组件"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🔍 检测详情")
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            margin-bottom: 15px;
            color: #0078D7;
            padding: 12px;
            border-bottom: 2px solid #0078D7;
            background-color: #2D2D2D;
            border-radius: 8px;
        """)
        layout.addWidget(title_label)
        
        # 创建2列5行的网格布局
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        
        # 定义5行显示的项目
        self.detail_items = [
            ("🎯 检测目标", "未检测"),
            ("📊 置信度", "0%"),
            ("📍 坐标位置", "未定位"),
            ("⏱️ 处理时间", "0ms"),
            ("📈 检测数量", "0个")
        ]
        
        # 创建标签和值显示
        self.name_labels = []
        self.value_labels = []
        
        for i, (name, default_value) in enumerate(self.detail_items):
            # 创建名称标签（第一列）
            name_label = QLabel(name)
            name_label.setStyleSheet("""
                font-size: 14px;
                font-weight: 600;
                color: #E0E0E0;
                padding: 10px 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2D2D2D, stop:1 #3D3D3D);
                border-radius: 8px;
                border-left: 4px solid #0078D7;
                margin-right: 8px;
            """)
            name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_label.setMinimumHeight(45)
            name_label.setMinimumWidth(120)

            # 创建值标签（第二列）
            value_label = QLabel(default_value)
            value_label.setStyleSheet("""
                font-size: 13px;
                color: #FFFFFF;
                padding: 10px 15px;
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #404040;
                font-weight: 500;
            """)
            value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value_label.setMinimumHeight(45)
            value_label.setMinimumWidth(150)
            value_label.setWordWrap(True)
            
            # 添加到网格布局
            self.grid_layout.addWidget(name_label, i, 0)
            self.grid_layout.addWidget(value_label, i, 1)
            
            # 保存引用
            self.name_labels.append(name_label)
            self.value_labels.append(value_label)
        
        # 设置列宽比例
        self.grid_layout.setColumnStretch(0, 1)  # 名称列
        self.grid_layout.setColumnStretch(1, 2)  # 值列
        
        layout.addLayout(self.grid_layout)
        layout.addStretch()  # 添加弹性空间
        
        self.setLayout(layout)
    
    def update_details(self, detection_results):
        """更新检测详情"""
        if not detection_results:
            # 重置为默认值
            self.value_labels[0].setText("未检测")
            self.value_labels[1].setText("0%")
            self.value_labels[2].setText("未定位")
            self.value_labels[3].setText("0ms")
            self.value_labels[4].setText("0个")
            return
        
        # 计算统计信息
        total_count = len(detection_results)
        avg_confidence = sum(result.get('confidence', 0) for result in detection_results) / total_count if total_count > 0 else 0
        total_time = sum(result.get('time_ms', 0) for result in detection_results)
        
        # 获取第一个检测结果的坐标作为示例
        first_coordinates = detection_results[0].get('coordinates', '未定位') if detection_results else '未定位'
        
        # 类别英文到中文的映射
        class_map = {
            "Hyperplastic_polyps": "增生性息肉",
            "Adenoma polyps": "腺瘤息肉",
            "增生性息肉": "增生性息肉",  # 兼容中文
            "腺瘤息肉": "腺瘤息肉"
        }
        
        # 收集当前帧检测到的类别
        if detection_results:
            class_names = set()
            for result in detection_results:
                class_name = result.get('class', '')
                if class_name in class_map:
                    class_names.add(class_map[class_name])
            
            if class_names:
                # 显示检测到的类别（当前帧）
                detected_classes = list(class_names)
                self.value_labels[0].setText(detected_classes[0])  # 只显示第一个类别，不用逗号分隔
            else:
                self.value_labels[0].setText("未知类别")
        else:
            self.value_labels[0].setText("未检测")
        
        # 更新其他显示
        self.value_labels[1].setText(f"{avg_confidence:.1%}")
        self.value_labels[2].setText(str(first_coordinates))
        self.value_labels[3].setText(f"{total_time}ms")
        self.value_labels[4].setText(f"{total_count}个")
        
        # 根据检测结果更新样式
        if total_count > 0:
            self.value_labels[0].setStyleSheet("""
                font-size: 13px;
                color: #4CAF50;
                padding: 10px 15px;
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #4CAF50;
                font-weight: 600;
            """)
        else:
            self.value_labels[0].setStyleSheet("""
                font-size: 13px;
                color: #FF6B6B;
                padding: 10px 15px;
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #FF6B6B;
            """)

class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("参数设置")
        self.setModal(True)
        self.setFixedSize(400, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 模型参数设置
        model_group = QGroupBox("模型参数")
        model_layout = QFormLayout()
        
        self.iou_slider = QSlider(Qt.Horizontal)
        self.iou_slider.setRange(0, 100)
        self.iou_slider.setValue(50)
        self.iou_label = QLabel("0.50")
        self.iou_slider.valueChanged.connect(lambda v: self.iou_label.setText(f"{v/100:.2f}"))
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(50)
        self.confidence_label = QLabel("0.50")
        self.confidence_slider.valueChanged.connect(lambda v: self.confidence_label.setText(f"{v/100:.2f}"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["pt_models/polpy_best.pt"])
        
        model_layout.addRow("IOU阈值:", self.iou_slider)
        model_layout.addRow("", self.iou_label)
        model_layout.addRow("置信度阈值:", self.confidence_slider)
        model_layout.addRow("", self.confidence_label)
        model_layout.addRow("模型权重:", self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 数据库配置
        db_group = QGroupBox("数据库配置")
        db_layout = QFormLayout()
        
        self.db_host = QLineEdit("localhost")
        self.db_port = QLineEdit("3306")
        self.db_user = QLineEdit("root")
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.Password)
        self.db_name = QLineEdit("polyp_detection")
        
        db_layout.addRow("主机:", self.db_host)
        db_layout.addRow("端口:", self.db_port)
        db_layout.addRow("用户名:", self.db_user)
        db_layout.addRow("密码:", self.db_password)
        db_layout.addRow("数据库:", self.db_name)
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_database_connection)
        db_layout.addRow("", test_btn)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def test_database_connection(self):
        """测试数据库连接"""
        try:
            db_manager = DatabaseManager(
                host=self.db_host.text(),
                port=int(self.db_port.text()),
                user=self.db_user.text(),
                password=self.db_password.text(),
                database=self.db_name.text()
            )
            
            if db_manager.test_connection():
                QMessageBox.information(self, "连接成功", "数据库连接测试成功！")
            else:
                QMessageBox.warning(self, "连接失败", "数据库连接测试失败！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接测试出错: {str(e)}")

class PatientInfoDialog(QDialog):
    """患者信息对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("患者信息")
        self.setModal(True)
        self.setFixedSize(400, 500)
        self.patient_info = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit('张三')
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        self.age_edit = QLineEdit("30")
        self.medical_record_edit = QLineEdit("666")
        self.phone_edit = QLineEdit("120120120120120")
        self.doctor_edit = QLineEdit("王医生")
        self.notes_edit = QTextEdit('这里是备注！')
        self.notes_edit.setMaximumHeight(100)
        
        form_layout.addRow("患者姓名:", self.name_edit)
        form_layout.addRow("性别:", self.gender_combo)
        form_layout.addRow("年龄:", self.age_edit)
        form_layout.addRow("病历号:", self.medical_record_edit)
        form_layout.addRow("联系电话:", self.phone_edit)
        form_layout.addRow("诊断医生:", self.doctor_edit)
        form_layout.addRow("备注:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        save_btn.clicked.connect(self.save_patient_info)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_patient_info(self):
        """保存患者信息"""
        # 数据验证
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "患者姓名不能为空")
            return
        
        try:
            age = int(self.age_edit.text()) if self.age_edit.text().isdigit() else 30
            if age < 0 or age > 150:
                QMessageBox.warning(self, "验证失败", "年龄必须在0-150之间")
                return
        except ValueError:
            QMessageBox.warning(self, "验证失败", "年龄必须是数字")
            return
        
        self.patient_info = {
            'name': self.name_edit.text().strip(),
            'gender': self.gender_combo.currentText(),
            'age': age,
            'medical_record_number': self.medical_record_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'doctor': self.doctor_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        self.accept()

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("息肉智能检测系统")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(FluentStyle.MAIN_STYLE)
        
        # 设置应用图标
        self.set_app_icon()
        
        # 初始化变量
        self.model = None
        self.current_source = None
        self.detection_results = []
        self.current_result_path = None
        self.db_manager = None
        self.db_operations = None
        self.report_generator = ReportGenerator()
        
        # 分页相关变量
        self.current_page = 1
        self.total_pages = 1
        self.page_size = 10
        self.total_records = 0
        
        # 分页相关变量
        self.current_page = 1
        self.total_pages = 1
        self.page_size = 10
        self.total_records = 0
        
        self.init_ui()
        self.init_database()
        
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 导航条
        self.create_navigation_bar()
        main_layout.addWidget(self.nav_bar)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.create_main_tab()
        self.create_history_tab()
        main_layout.addWidget(self.tab_widget)
        
        central_widget.setLayout(main_layout)
        
    def create_navigation_bar(self):
        """创建导航条"""
        self.nav_bar = QWidget()
        self.nav_bar.setFixedHeight(60)
        self.nav_bar.setStyleSheet(f"background-color: {FluentStyle.BACKGROUND_LIGHT}; border-bottom: 1px solid {FluentStyle.BORDER_COLOR};")
        
        layout = QHBoxLayout()
        layout.addStretch()

        # 系统名称
        title_label = QLabel("基于YOLO+PySide6+MySQL的息肉智能检测系统")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 导航标签
        self.home_btn = QPushButton("主页")
        self.history_btn = QPushButton("历史记录")
        
        self.home_btn.setCheckable(True)
        self.history_btn.setCheckable(True)
        self.home_btn.setChecked(True)
        
        self.home_btn.clicked.connect(lambda: self.switch_tab(0))
        self.history_btn.clicked.connect(lambda: self.switch_tab(1))
        
        layout.addWidget(self.home_btn)
        layout.addWidget(self.history_btn)
        
        # 用户头像
        user_btn = QPushButton("👨‍⚕️")
        user_btn.setFixedSize(40, 40)
        user_btn.clicked.connect(self.show_user_menu)
        layout.addWidget(user_btn)
        
        self.nav_bar.setLayout(layout)
    
    def create_main_tab(self):
        """创建主页面"""
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 左侧：设置按钮
        settings_btn = QPushButton("⚙️ 参数设置")
        settings_btn.setFixedSize(120, 40)
        settings_btn.clicked.connect(self.show_settings)
        top_layout.addWidget(settings_btn)
        
        # top_layout.addStretch()
        
        # 右侧：保存和导出按钮
        self.save_btn = QPushButton("💾 保存结果")
        self.export_btn = QPushButton("📄 导出报告")
        
        self.save_btn.setFixedSize(120, 40)
        self.export_btn.setFixedSize(120, 40)
        
        self.save_btn.clicked.connect(self.save_result)
        self.export_btn.clicked.connect(self.export_report)
        
        # 初始状态
        self.save_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.select_file_btn = QPushButton("📁 选择文件")
        self.camera_btn = QPushButton("📷 加载摄像头")

        self.select_file_btn.clicked.connect(self.select_file)
        self.camera_btn.clicked.connect(self.toggle_camera)
        top_layout.addWidget(self.select_file_btn)
        top_layout.addWidget(self.camera_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.save_btn)
        top_layout.addWidget(self.export_btn)


        layout.addLayout(top_layout)
        
        # 中间显示区域：左右两个窗口 + 检测详情
        display_layout = QHBoxLayout()
        
        # 左侧：两个显示窗口（左右布局）
        left_display_layout = QHBoxLayout()
        self.source_widget = DetectionWidget("源图像/视频")
        self.result_widget = DetectionWidget("检测结果")
        left_display_layout.addWidget(self.source_widget)
        left_display_layout.addWidget(self.result_widget)

        
        display_layout.addLayout(left_display_layout)
        
        # 右侧：检测详情区域
        self.details_widget = DetailsWidget()
        self.details_widget.setFixedWidth(300)  # 设置固定宽度
        display_layout.addWidget(self.details_widget)
        
        layout.addLayout(display_layout)
        
        # 底部操作按钮栏
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ 开始检测")
        self.pause_btn = QPushButton("⏸️ 暂停检测")
        self.stop_btn = QPushButton("⏹️ 结束检测")
        
        # 连接信号
        self.start_btn.clicked.connect(self.start_detection)
        self.pause_btn.clicked.connect(self.pause_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        
        # 初始状态
        # self.pause_btn.setEnabled(False)
        # self.stop_btn.setEnabled(False)
        
        buttons = [ self.start_btn,
                  self.pause_btn, self.stop_btn]
        button_layout.addStretch()
        for btn in buttons:
            button_layout.addWidget(btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        
        main_widget.setLayout(layout)
        self.tab_widget.addTab(main_widget, "主页")
        
        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("系统就绪")
    
    def create_history_tab(self):
        """创建历史记录页面"""
        history_widget = QWidget()
        layout = QVBoxLayout()
        
        # 查询区域
        query_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入搜索关键词...")
        self.search_edit.returnPressed.connect(self.search_history)
        
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["患者信息", "医生信息", "类别", "日期"])
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        
        search_btn = QPushButton("🔍 查询")
        search_btn.clicked.connect(self.search_history)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_search)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_history)
        
        query_layout.addWidget(QLabel("搜索:"))
        query_layout.addWidget(self.search_edit)
        query_layout.addWidget(QLabel("字段:"))
        query_layout.addWidget(self.search_field_combo)
        query_layout.addWidget(QLabel("日期范围:"))
        query_layout.addWidget(self.date_from)
        query_layout.addWidget(QLabel("至"))
        query_layout.addWidget(self.date_to)
        query_layout.addWidget(search_btn)
        query_layout.addWidget(clear_btn)
        query_layout.addWidget(refresh_btn)
        query_layout.addStretch()
        
        layout.addLayout(query_layout)
        
        # 历史记录显示区域
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels(["患者姓名", "医生", "类别", "检测类型", "检测日期", "耗时(ms)", "状态", "操作"])
        self.history_table.setColumnWidth(4, 120)
        self.history_table.setColumnWidth(6, 500)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        # # 假设第 3 列（下标 3）要占满剩余宽度
        # header = self.history_table.horizontalHeader()
        # header.setStretchLastSection(False)  # 先关闭默认的“最后一列拉伸”
        # header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.MultiSelection)
        
        # 设置表格行高，确保按钮正常显示
        self.history_table.verticalHeader().setMinimumSectionSize(35)
        
        # 启用右键菜单
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.history_table)
        
        # 批量操作按钮
        batch_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("全选")
        self.deselect_all_btn = QPushButton("取消全选")
        self.batch_delete_btn = QPushButton("批量删除")
        self.export_selected_btn = QPushButton("导出选中")
        self.export_all_btn = QPushButton("导出全部")
        
        self.select_all_btn.clicked.connect(self.select_all_records)
        self.deselect_all_btn.clicked.connect(self.deselect_all_records)
        self.batch_delete_btn.clicked.connect(self.batch_delete_records)
        self.export_selected_btn.clicked.connect(self.export_selected_records)
        self.export_all_btn.clicked.connect(self.export_all_records)
        
        batch_layout.addWidget(self.select_all_btn)
        batch_layout.addWidget(self.deselect_all_btn)
        batch_layout.addWidget(self.batch_delete_btn)
        batch_layout.addWidget(self.export_selected_btn)
        batch_layout.addWidget(self.export_all_btn)
        batch_layout.addStretch()
        
        layout.addLayout(batch_layout)
        
        # 翻页控件
        page_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_edit = QLineEdit("1")
        self.page_edit.setFixedWidth(50)
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100"])
        self.page_size_combo.setCurrentText("10")
        
        # 状态标签
        self.status_label = QLabel("共 0 条记录")
        
        page_layout.addWidget(QLabel("每页条数:"))
        page_layout.addWidget(self.page_size_combo)
        page_layout.addStretch()
        page_layout.addWidget(self.status_label)
        page_layout.addStretch()
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(QLabel("第"))
        page_layout.addWidget(self.page_edit)
        page_layout.addWidget(QLabel("页"))
        page_layout.addWidget(self.next_btn)
        
        layout.addLayout(page_layout)
        
        history_widget.setLayout(layout)
        self.tab_widget.addTab(history_widget, "历史记录")
        
        # 连接翻页信号
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        self.page_edit.returnPressed.connect(self.on_page_changed)
    
    def set_app_icon(self):
        """设置应用图标"""
        try:
            icon_path = "icon_img/app_icon.png"
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # 如果图标文件不存在，创建一个简单的图标
                self.create_simple_icon()
        except Exception as e:
            print(f"设置图标失败: {e}")
    
    def create_simple_icon(self):
        """创建简单的应用图标"""
        try:
            # 创建一个简单的图标
            icon = QPixmap(64, 64)
            icon.fill(Qt.transparent)
            
            painter = QPainter(icon)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制圆形背景
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 56, 56)
            
            # 绘制医疗十字
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(28, 20, 8, 24)  # 垂直条
            painter.drawRect(20, 28, 24, 8)  # 水平条
            
            painter.end()
            
            self.setWindowIcon(QIcon(icon))
        except Exception as e:
            print(f"创建简单图标失败: {e}")
    
    def init_database(self):
        """初始化数据库"""
        try:
            self.db_manager = DatabaseManager()
            if self.db_manager.test_connection():
                self.db_operations = DatabaseOperations(self.db_manager)
                print("数据库连接成功")
                # 延迟加载历史记录，确保UI完全初始化
                QTimer.singleShot(500, self.load_history)
            else:
                QMessageBox.warning(self, "数据库连接", "无法连接到数据库，请检查配置。")
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"数据库初始化失败: {str(e)}")
    
    def switch_tab(self, index):
        """切换标签页"""
        self.tab_widget.setCurrentIndex(index)
        self.home_btn.setChecked(index == 0)
        self.history_btn.setChecked(index == 1)
        
        # 切换到历史记录页面时自动刷新
        if index == 1:
            self.load_history()
    
    def show_user_menu(self):
        """显示用户菜单"""
        menu = QMenu(self)
        menu.addAction("设置")
        menu.addAction("关于")
        menu.addSeparator()
        menu.addAction("退出")
        menu.exec(QCursor.pos())
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # 保存设置
            pass
    
    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "图像文件 (*.jpg *.jpeg *.png *.bmp);;视频文件 (*.mp4 *.avi *.mov)"
        )
        if file_path:
            self.current_source = file_path
            self.source_widget.set_image(file_path)
            self.start_btn.setEnabled(True)
    
    def toggle_camera(self):
        """切换摄像头"""
        if not hasattr(self, 'camera_active') or not self.camera_active:
            try:
                # 检查摄像头是否可用
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    QMessageBox.warning(self, "摄像头错误", "未检测到可用的摄像头设备，请检查摄像头连接后重试。")
                    return
                
                # 尝试读取一帧以验证摄像头是否真正可用
                ret, frame = cap.read()
                if not ret:
                    QMessageBox.warning(self, "摄像头错误", "摄像头无法读取图像，请检查摄像头是否被其他程序占用或设备是否正常工作。")
                    cap.release()
                    return
                
                # 释放摄像头资源
                cap.release()
                
                # 启动摄像头
                self.camera_active = True
                self.camera_btn.setText("📹 关闭摄像头")
                QMessageBox.information(self, "摄像头状态", "摄像头已成功启动！")
                # 这里需要实现摄像头逻辑
                
            except Exception as e:
                QMessageBox.critical(self, "摄像头错误", f"摄像头检测过程中出现错误: {str(e)}")
                return
        else:
            # 关闭摄像头
            self.camera_active = False
            self.camera_btn.setText("📹 加载摄像头")
            QMessageBox.information(self, "摄像头状态", "摄像头已关闭。")
    
    def start_detection(self):
        """开始检测"""
        # 检查是否有可用的检测源
        if not self.current_source and not (hasattr(self, 'camera_active') and self.camera_active):
            QMessageBox.warning(self, "警告", "请先选择源文件或启动摄像头")
            return
        
        try:
            # 加载模型
            if not self.model:
                model_path = "pt_models/polpy_best.pt"
                if os.path.exists(model_path):
                    self.model = YOLO(model_path)
                else:
                    QMessageBox.critical(self, "错误", "模型文件不存在")
                    return
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 确定检测源
            detection_source = self.current_source
            if hasattr(self, 'camera_active') and self.camera_active:
                # 如果是摄像头模式，使用摄像头作为检测源
                detection_source = 0  # OpenCV摄像头索引
            
            # 执行检测
            results = self.model(detection_source)
            
            # 计算耗时
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000  # 转换为毫秒
            
            # 处理结果
            self.process_detection_results(results, processing_time)
            
            # 更新UI状态
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "检测错误", f"检测过程中出现错误: {str(e)}")
    
    def process_detection_results(self, results, processing_time=0):
        """处理检测结果"""
        self.detection_results = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    # 获取坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    coordinates = f"({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})"
                    
                    # 获取置信度
                    confidence = float(box.conf[0])
                    
                    # 获取类别
                    class_id = int(box.cls[0])
                    class_names = ["增生性息肉", "腺瘤息肉"]
                    class_name = class_names[class_id] if class_id < len(class_names) else "未知"
                    
                    self.detection_results.append({
                        'class': class_name,
                        'coordinates': coordinates,
                        'confidence': confidence,
                        'time_ms': int(processing_time)  # 使用实际检测耗时
                    })
        
        # 更新详情表格
        self.details_widget.update_details(self.detection_results)
        
        # 显示结果图像并保存到指定目录
        if hasattr(results[0], 'save'):
            # 生成结果图像文件名
            result_filename = self.generate_result_filename()
            result_path = os.path.join("data", "results", result_filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            
            # 保存结果图像
            results[0].save(result_path)
            self.result_widget.set_image(result_path)
            
            # 保存结果路径供后续使用
            self.current_result_path = result_path
    
    def generate_result_filename(self):
        """根据源文件生成结果文件名"""
        if not self.current_source:
            # 如果没有源文件（如摄像头），使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"camera_result_{timestamp}.jpg"
        
        # 获取源文件名（不含路径）
        source_filename = os.path.basename(self.current_source)
        name, ext = os.path.splitext(source_filename)
        
        # 生成结果文件名：原文件名_result.jpg
        result_filename = f"{name}_result.jpg"
        return result_filename
    
    def copy_source_to_data_directory(self):
        """将源文件复制到data/sources目录"""
        if not self.current_source or not os.path.exists(self.current_source):
            return None
        
        try:
            # 获取源文件名
            source_filename = os.path.basename(self.current_source)
            
            # 目标路径
            target_path = os.path.join("data", "sources", source_filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(self.current_source, target_path)
            
            return target_path
        except Exception as e:
            print(f"复制源文件失败: {str(e)}")
            return None
    
    def pause_detection(self):
        """暂停检测"""
        self.pause_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
    
    def stop_detection(self):
        """结束检测"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
    
    def save_result(self):
        """保存结果"""
        if not self.detection_results:
            QMessageBox.warning(self, "警告", "没有检测结果可保存")
            return
        
        dialog = PatientInfoDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # 保存到数据库
            self.save_to_database(dialog.patient_info)
    
    def save_to_database(self, patient_info):
        """保存到数据库"""
        if not self.db_operations:
            QMessageBox.warning(self, "保存错误", "数据库未连接")
            return
        
        try:
            # 数据验证
            if not patient_info.get('name', '').strip():
                QMessageBox.warning(self, "验证失败", "患者姓名不能为空")
                return
            
            if not self.detection_results:
                QMessageBox.warning(self, "验证失败", "没有检测结果可保存")
                return
            
            # 复制源文件到data/sources目录
            source_path = self.copy_source_to_data_directory()
            
            # 保存检测记录到数据库
            result_path = self.current_result_path if self.current_result_path else ""
            
            # 计算总处理时间
            total_time = sum(result.get('time_ms', 0) for result in self.detection_results)
            
            # 确定检测类型
            detection_type = "图片"
            if self.current_source and self.current_source.lower().endswith(('.mp4', '.avi', '.mov')):
                detection_type = "视频"
            elif hasattr(self, 'camera_active') and self.camera_active:
                detection_type = "摄像头"
            
            success = self.db_operations.save_detection_record(
                patient_info, 
                self.detection_results, 
                source_path if source_path else self.current_source, 
                result_path,
                detection_type
            )
            
            if success:
                QMessageBox.information(self, "保存成功", "检测结果已保存到数据库")
                # 刷新历史记录
                if self.tab_widget.currentIndex() == 1:
                    self.load_history()
            else:
                QMessageBox.warning(self, "保存失败", "保存到数据库失败")
                
        except Exception as e:
            error_msg = f"保存到数据库失败: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "保存错误", error_msg)
    
    def export_report(self):
        """导出报告"""
        if not self.detection_results:
            QMessageBox.warning(self, "警告", "没有检测结果可导出")
            return
        
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存报告", f"detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                "PDF文件 (*.pdf)"
            )
            
            if not file_path:
                return
            
            # 创建患者信息（这里使用默认值，实际应该从保存的患者信息中获取）
            patient_info = {
                'name': '患者姓名',
                'gender': '男',
                'age': 30,
                'medical_record_number': '666',
                'phone': '120120120120120',
                'doctor': '王医生',
                'notes': ''
            }
            
            # 生成PDF报告
            result_path = self.current_result_path if self.current_result_path else ""
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            
            self.report_generator.generate_detection_report(
                patient_info,
                self.detection_results,
                self.current_source,
                result_path,
                file_path
            )
            
            QMessageBox.information(self, "导出成功", f"报告已导出到: {file_path}")
            
        except Exception as e:
            error_msg = f"生成报告失败: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "导出错误", error_msg)
    
    def search_history(self):
        """搜索历史记录"""
        self.current_page = 1
        self.page_edit.setText("1")
        self.load_history()
    
    def clear_search(self):
        """清空搜索条件"""
        self.search_edit.clear()
        self.search_field_combo.setCurrentText("患者信息")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.current_page = 1
        self.page_edit.setText("1")
        self.load_history()
    
    def refresh_history(self):
        """刷新历史记录"""
        try:
            # 显示刷新状态
            self.status_label.setText("正在刷新...")
            QApplication.processEvents()  # 立即更新UI
            
            # 重新加载历史记录
            self.load_history()
            
            # 显示刷新完成状态
            QTimer.singleShot(1000, lambda: self.status_label.setText(f"共 {self.total_records} 条记录，第 {self.current_page}/{max(1, self.total_pages)} 页"))
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 刷新错误", f"刷新历史记录失败:\n{str(e)}")
    
    def load_history(self):
        """加载历史记录"""
        if not self.db_operations:
            return
        
        try:
            # 更新状态栏
            self.statusBar.showMessage("正在加载历史记录...")
            QApplication.processEvents()
            
            # 获取查询参数
            search_keyword = self.search_edit.text().strip()
            search_field = self.search_field_combo.currentText()
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
            page = self.current_page
            page_size = int(self.page_size_combo.currentText())
            
            # 获取历史记录
            records, total_count = self.db_operations.get_detection_history(
                search_keyword, search_field, date_from, date_to, page, page_size
            )
            # # -------------- 打印参数 --------------
            # print("=== 查询参数 ===")
            # print(f"search_keyword : {search_keyword!r}")
            # print(f"search_field   : {search_field!r}")
            # print(f"date_from      : {date_from!r}")
            # print(f"date_to        : {date_to!r}")
            # print(f"page           : {page}")
            # print(f"page_size      : {page_size}")
            # print()
            #
            # # -------------- 打印结果 --------------
            # print("=== 查询结果 ===")
            # print(f"total_count    : {total_count}")
            # print("records (前 5 条预览):")
            # for idx, rec in enumerate(records[:5], 1):
            #     print(f"  [{idx}] {rec}")
            # if len(records) > 5:
            #     print(f"  ... 还有 {len(records) - 5} 条未展示 ...")
            # print("=" * 40)

            
            # 更新分页信息
            self.total_records = total_count
            self.total_pages = (total_count + page_size - 1) // page_size
            
            # 更新状态标签
            self.status_label.setText(f"共 {total_count} 条记录，第 {page}/{max(1, self.total_pages)} 页")
            
            # 更新状态栏
            self.statusBar.showMessage(f"已加载 {len(records)} 条记录，共 {total_count} 条")
            
            # 更新按钮状态
            self.prev_btn.setEnabled(page > 1)
            self.next_btn.setEnabled(page < self.total_pages)
            
            # 更新表格
            self.history_table.setRowCount(len(records))
            
            for i, record in enumerate(records):
                record_id = record.get('id', 0)
                
                # 患者姓名
                self.history_table.setItem(i, 0, QTableWidgetItem(record.get('patient_name', '')))
                
                # 医生姓名
                doctor_name = record.get('doctor_name', '')
                doctor_dept = record.get('doctor_department', '')
                doctor_display = f"{doctor_name}" if not doctor_dept else f"{doctor_name}({doctor_dept})"
                self.history_table.setItem(i, 1, QTableWidgetItem(doctor_display))
                
                # 息肉类型
                polyp_types = record.get('polyp_types', '')
                self.history_table.setItem(i, 2, QTableWidgetItem(polyp_types))
                
                # 检测类型
                detection_type = record.get('detection_type', '')
                self.history_table.setItem(i, 3, QTableWidgetItem(detection_type))
                
                # 检测日期
                detection_date = record.get('detection_date', '')
                if detection_date:
                    if isinstance(detection_date, str):
                        date_str = detection_date
                    else:
                        date_str = detection_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date_str = ""
                self.history_table.setItem(i, 4, QTableWidgetItem(date_str))
                
                # 处理时间
                processing_time = record.get('processing_time_ms', 0)
                time_display = f"{processing_time}ms" if processing_time > 0 else "未记录"
                self.history_table.setItem(i, 5, QTableWidgetItem(time_display))
                
                # 状态（根据检测结果判断）
                detection_count = record.get('detection_count', 0)
                avg_confidence = record.get('avg_confidence', 0)
                
                if detection_count > 0:
                    status = f"已检测({detection_count}个)"
                    if avg_confidence:
                        status += f", 平均置信度: {avg_confidence:.1%}"
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(QBrush(QColor(0, 255, 0)))  # 绿色
                else:
                    status = "无检测结果"
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(QBrush(QColor(255, 0, 0)))  # 红色
                
                self.history_table.setItem(i, 6, status_item)
                
                # 操作按钮
                button_widget = QWidget()
                button_layout = QHBoxLayout()
                button_layout.setContentsMargins(2, 2, 2, 2)
                button_layout.setSpacing(10)
                
                view_btn = QPushButton("查看")
                view_btn.setFixedSize(50, 15)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0078D7;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0px 2px; 
                    }
                    QPushButton:hover {
                        background-color: #106EBE;
                    }
                    QPushButton:pressed {
                        background-color: #005A9E;
                    }
                """)
                # 将record_id存储到按钮的属性中
                view_btn.setProperty("record_id", record_id)
                view_btn.clicked.connect(partial(self.on_view_button_clicked, record_id))

                delete_btn = QPushButton("删除")
                delete_btn.setFixedSize(50, 15)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d9534f;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0px 2px; 
                    }
                    QPushButton:hover {
                        background-color: #c9302c;
                    }
                    QPushButton:pressed {
                        background-color: #ac2925;
                    }
                """)
                # 将record_id存储到按钮的属性中
                delete_btn.setProperty("record_id", record_id)
                delete_btn.clicked.connect(partial(self.on_delete_button_clicked, record_id))
                
                font = delete_btn.font()  # 拿到当前字体
                font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)  # 1.2 px 额外间距
                delete_btn.setFont(font)
                font = view_btn.font()  # 拿到当前字体
                font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)  # 1.2 px 额外间距
                view_btn.setFont(font)
                
                button_layout.addStretch()
                button_layout.addWidget(view_btn)
                button_layout.addWidget(delete_btn)
                button_layout.addStretch()
                # button_widget.setStyleSheet("""
                #     QWidget {
                #         background: #f5f5f5;   /* 背景色 */
                #         border: 1px solid #ccc;
                #         border-radius: 4px;
                #     }
                # """)
                button_widget.setStyleSheet("background: transparent;")
                button_widget.setAutoFillBackground(True)  # 让 QWidget 主动绘制背景
                button_widget.setLayout(button_layout)
                
                # 将record_id存储到widget的属性中，方便后续获取
                button_widget.setProperty("record_id", record_id)
                button_layout_1 = QHBoxLayout(button_widget)
                button_layout_1.setContentsMargins(4, 4, 4, 4)  # 左 4、上 2、右 4、下 2
                self.history_table.setCellWidget(i, 7, button_widget)

            
        except Exception as e:
            error_msg = f"加载历史记录失败: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "加载错误", error_msg)
    
    def view_record_details(self, record_id):
        """查看记录详情"""
        if not self.db_operations:
            return
        
        try:
            # 获取检测详情
            details = self.db_operations.get_detection_details(record_id)
            patient_info = self.db_operations.get_patient_info(record_id)
            paths = self.db_operations.get_record_paths(record_id)
            patient_info.update(paths)
            # print("=== 调试打印 ===")
            # print("record_id:", record_id)
            # print("patient_info:")
            # for k, v in patient_info.items():
            #     print(f"  {k}: {v}")
            # print("details (共 {} 条):".format(len(details)))
            # for idx, d in enumerate(details, 1):
            #     print(f"  [{idx}] {d}")
            
            # 显示详情对话框
            self.show_record_details_dialog(patient_info, details)
            
        except Exception as e:
            QMessageBox.critical(self, "查看错误", f"获取记录详情失败: {str(e)}")
    
    def delete_record(self, record_id):
        """删除记录"""
        # 获取记录信息用于确认
        try:
            patient_info = self.db_operations.get_patient_info(record_id)
            patient_name = patient_info.get('name', '未知患者')
            detection_date = patient_info.get('detection_date', '')
            if detection_date:
                if isinstance(detection_date, str):
                    date_str = detection_date
                else:
                    date_str = detection_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                date_str = "未知时间"
            
            confirm_msg = f"确定要删除以下检测记录吗？\n\n患者姓名: {patient_name}\n检测日期: {date_str}\n\n⚠️ 此操作不可恢复！"
        except Exception:
            confirm_msg = f"确定要删除这条检测记录吗？\n\n⚠️ 此操作不可恢复！"
        
        reply = QMessageBox.question(
            self, "🗑️ 确认删除", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 显示进度对话框
                progress = QProgressDialog("正在删除记录...", "取消", 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setAutoClose(True)
                progress.show()
                
                if self.db_operations.delete_detection_record(record_id):
                    progress.close()
                    QMessageBox.information(self, "✅ 删除成功", "检测记录已成功删除")
                    self.load_history()  # 刷新列表
                else:
                    progress.close()
                    QMessageBox.warning(self, "❌ 删除失败", "删除记录失败，请检查数据库连接")
            except Exception as e:
                QMessageBox.critical(self, "❌ 删除错误", f"删除记录时发生错误:\n{str(e)}")



    def show_record_details_dialog(self, patient_info, details):
        """
        新布局：
        第1行：源图(左) + 结果图(右)
        第2行：患者信息
        第3行：医生信息
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 检测记录详情")
        dialog.setModal(True)
        dialog.resize(900, 700)
        dialog.setStyleSheet(FluentStyle.MAIN_STYLE)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(10)

        # --------- 1. 左右图片布局 ---------
        img_row = QHBoxLayout()
        img_row.setSpacing(15)

        # 源图
        src_label = QLabel("源图")
        src_label.setAlignment(Qt.AlignCenter)
        src_label.setStyleSheet("font-weight:bold; font-size:15px;")
        src_pix = QPixmap(patient_info.get("source_file_path", ""))
        if not src_pix.isNull():
            src_pix = src_pix.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        src_img = QLabel()
        src_img.setPixmap(src_pix)
        src_img.setAlignment(Qt.AlignCenter)
        src_img.setStyleSheet("border:1px solid #555; border-radius:8px;")
        src_box = QVBoxLayout()
        src_box.addWidget(src_label)
        src_box.addWidget(src_img)

        # 结果图
        res_label = QLabel("处理后")
        res_label.setAlignment(Qt.AlignCenter)
        res_label.setStyleSheet("font-weight:bold; font-size:15px;")
        res_pix = QPixmap(patient_info.get("result_file_path", ""))
        if not res_pix.isNull():
            res_pix = res_pix.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        res_img = QLabel()
        res_img.setPixmap(res_pix)
        res_img.setAlignment(Qt.AlignCenter)
        res_img.setStyleSheet("border:1px solid #555; border-radius:8px;")
        res_box = QVBoxLayout()
        res_box.addWidget(res_label)
        res_box.addWidget(res_img)

        img_row.addLayout(src_box)
        img_row.addLayout(res_box)
        root.addLayout(img_row)

        # --------- 2. 患者信息 ---------
        patient_lbl = QLabel("患者信息")
        patient_lbl.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        patient_lbl.setStyleSheet("color:#0078D7; margin-top:10px;")
        root.addWidget(patient_lbl)

        patient_text = (
            f"姓名：{patient_info.get('name', '')}\n"
            f"性别：{patient_info.get('gender', '')} | 年龄：{patient_info.get('age', '')}\n"
            f"病历号：{patient_info.get('medical_record_number', '')}\n"
            f"联系电话：{patient_info.get('phone', '')}\n"
            f"检测日期：{patient_info.get('detection_date', '')}\n"
            f"检测类型：{patient_info.get('detection_type', '')}\n"
            f"处理耗时：{patient_info.get('processing_time_ms', 0)} ms\n"
            f"备注：{patient_info.get('notes', '')}"
        )
        patient_info_lbl = QLabel(patient_text)
        patient_info_lbl.setStyleSheet("background:#2D2D2D; padding:10px; border-radius:8px;")
        patient_info_lbl.setWordWrap(True)
        root.addWidget(patient_info_lbl)

        # --------- 3. 医生信息 ---------
        doctor_lbl = QLabel("医生信息")
        doctor_lbl.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        doctor_lbl.setStyleSheet("color:#0078D7; margin-top:10px;")
        root.addWidget(doctor_lbl)

        doctor_text = (
            f"医生：{patient_info.get('doctor_name', '')}\n"
            f"科室：{patient_info.get('department', '')}\n"
            f"职称：{patient_info.get('title', '')}"
        )
        doctor_info_lbl = QLabel(doctor_text)
        doctor_info_lbl.setStyleSheet("background:#2D2D2D; padding:10px; border-radius:8px;")
        doctor_info_lbl.setWordWrap(True)
        root.addWidget(doctor_info_lbl)

        # --------- 4. 关闭按钮 ---------
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(100, 30)
        close_btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        root.addLayout(btn_layout)

        dialog.exec()
    
    def on_page_size_changed(self):
        """页面大小改变"""
        self.page_size = int(self.page_size_combo.currentText())
        self.current_page = 1
        self.page_edit.setText("1")
        self.load_history()
    
    def on_page_changed(self):
        """页码改变"""
        try:
            new_page = int(self.page_edit.text())
            if 1 <= new_page <= self.total_pages:
                self.current_page = new_page
                self.load_history()
            else:
                self.page_edit.setText(str(self.current_page))
        except ValueError:
            self.page_edit.setText(str(self.current_page))
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.page_edit.setText(str(self.current_page))
            self.load_history()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_edit.setText(str(self.current_page))
            self.load_history()
    
    def select_all_records(self):
        """全选记录"""
        for i in range(self.history_table.rowCount()):
            self.history_table.selectRow(i)
    
    def deselect_all_records(self):
        """取消全选记录"""
        self.history_table.clearSelection()
    
    def get_selected_record_ids(self):
        """获取选中的记录ID"""
        selected_ids = []
        for row in range(self.history_table.rowCount()):
            if self.history_table.isRowSelected(row):
                # 从按钮组件中获取记录ID
                button_widget = self.history_table.cellWidget(row, 7)
                if button_widget:
                    record_id = button_widget.property("record_id")
                    if record_id is not None:
                        selected_ids.append(record_id)
        return selected_ids
    
    def batch_delete_records(self):
        """批量删除记录"""
        selected_ids = self.get_selected_record_ids()
        if not selected_ids:
            QMessageBox.warning(self, "⚠️ 警告", "请先选择要删除的记录")
            return
        
        # 获取选中记录的详细信息
        selected_info = []
        try:
            for record_id in selected_ids[:5]:  # 只显示前5条记录的信息
                patient_info = self.db_operations.get_patient_info(record_id)
                patient_name = patient_info.get('name', '未知患者')
                detection_date = patient_info.get('detection_date', '')
                if detection_date:
                    if isinstance(detection_date, str):
                        date_str = detection_date
                    else:
                        date_str = detection_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date_str = "未知时间"
                selected_info.append(f"• {patient_name} ({date_str})")
            
            if len(selected_ids) > 5:
                selected_info.append(f"... 还有 {len(selected_ids) - 5} 条记录")
        except Exception:
            selected_info = [f"• 记录ID: {rid}" for rid in selected_ids[:5]]
            if len(selected_ids) > 5:
                selected_info.append(f"... 还有 {len(selected_ids) - 5} 条记录")
        
        confirm_msg = f"确定要删除以下 {len(selected_ids)} 条检测记录吗？\n\n" + "\n".join(selected_info) + "\n\n⚠️ 此操作不可恢复！"
        
        reply = QMessageBox.question(
            self, "🗑️ 确认批量删除", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 显示进度对话框
                progress = QProgressDialog("正在批量删除记录...", "取消", 0, len(selected_ids), self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setAutoClose(True)
                progress.show()
                
                if self.db_operations.batch_delete_records(selected_ids):
                    progress.close()
                    QMessageBox.information(self, "✅ 删除成功", f"成功删除 {len(selected_ids)} 条检测记录")
                    self.load_history()  # 刷新列表
                else:
                    progress.close()
                    QMessageBox.warning(self, "❌ 删除失败", "批量删除记录失败，请检查数据库连接")
            except Exception as e:
                QMessageBox.critical(self, "❌ 删除错误", f"批量删除记录时发生错误:\n{str(e)}")
    
    def export_selected_records(self):
        """导出选中的记录"""
        selected_ids = self.get_selected_record_ids()
        if not selected_ids:
            QMessageBox.warning(self, "⚠️ 警告", "请先选择要导出的记录")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存导出文件", f"selected_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                # 显示进度对话框
                progress = QProgressDialog("正在导出选中记录...", "取消", 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setAutoClose(True)
                progress.show()
                
                if self.db_operations.export_records_to_json(selected_ids, file_path):
                    progress.close()
                    QMessageBox.information(self, "✅ 导出成功", f"成功导出 {len(selected_ids)} 条记录到:\n{file_path}")
                else:
                    progress.close()
                    QMessageBox.warning(self, "❌ 导出失败", "导出记录失败，请检查文件权限和磁盘空间")
            except Exception as e:
                QMessageBox.critical(self, "❌ 导出错误", f"导出记录时发生错误:\n{str(e)}")
    
    def export_all_records(self):
        """导出所有记录"""
        # 先获取总记录数
        try:
            records, total_count = self.db_operations.get_detection_history(page=1, page_size=1)
            if total_count == 0:
                QMessageBox.information(self, "ℹ️ 提示", "当前没有可导出的记录")
                return
        except Exception as e:
            QMessageBox.critical(self, "❌ 错误", f"无法获取记录数量:\n{str(e)}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存导出文件", f"all_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                # 显示进度对话框
                progress = QProgressDialog(f"正在导出所有记录 ({total_count} 条)...", "取消", 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setAutoClose(True)
                progress.show()
                
                if self.db_operations.export_records_to_json(None, file_path):
                    progress.close()
                    QMessageBox.information(self, "✅ 导出成功", f"成功导出 {total_count} 条记录到:\n{file_path}")
                else:
                    progress.close()
                    QMessageBox.warning(self, "❌ 导出失败", "导出记录失败，请检查文件权限和磁盘空间")
            except Exception as e:
                QMessageBox.critical(self, "❌ 导出错误", f"导出记录时发生错误:\n{str(e)}")
    
    def export_record_details(self, patient_info, details):
        """导出记录详情"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存详情文件", f"record_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                # 准备导出数据
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'patient_info': patient_info,
                    'detection_details': details,
                    'summary': {
                        'total_detections': len(details),
                        'avg_confidence': sum(d.get('confidence', 0) for d in details) / len(details) if details else 0,
                        'total_time': sum(d.get('detection_time_ms', 0) for d in details),
                        'polyp_types': list(set(d.get('polyp_type', '') for d in details))
                    }
                }
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
                
                QMessageBox.information(self, "导出成功", f"记录详情已导出到: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出记录详情失败: {str(e)}")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取点击的行
        row = self.history_table.rowAt(position.y())
        if row < 0:
            return
        
        # 获取记录ID
        button_widget = self.history_table.cellWidget(row, 7)
        if not button_widget:
            return
        
        record_id = button_widget.property("record_id")
        if record_id is None:
            return
        
        # 创建右键菜单
        menu = QMenu(self)
        menu.setStyleSheet(FluentStyle.MAIN_STYLE)
        
        # 查看详情
        view_action = menu.addAction("👁️ 查看详情")
        view_action.triggered.connect(partial(self.on_view_button_clicked, record_id))
        
        # 导出详情
        export_action = menu.addAction("📄 导出详情")
        export_action.triggered.connect(partial(self.export_single_record_details, record_id))
        
        menu.addSeparator()
        
        # 删除记录
        delete_action = menu.addAction("🗑️ 删除记录")
        delete_action.triggered.connect(partial(self.on_delete_button_clicked, record_id))
        
        # 显示菜单
        menu.exec(self.history_table.mapToGlobal(position))
    
    def export_single_record_details(self, record_id):
        """导出单条记录详情"""
        try:
            # 获取记录详情
            details = self.db_operations.get_detection_details(record_id)
            patient_info = self.db_operations.get_patient_info(record_id)
            
            if not patient_info:
                QMessageBox.warning(self, "⚠️ 警告", "无法获取记录信息")
                return
            
            # 调用导出详情方法
            self.export_record_details(patient_info, details)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 导出错误", f"导出记录详情失败:\n{str(e)}")
    
    def on_view_button_clicked(self, record_id):
        """查看按钮点击处理"""
        self.view_record_details(record_id)
    
    def on_delete_button_clicked(self, record_id):
        """删除按钮点击处理"""
        self.delete_record(record_id)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式以获得更好的跨平台体验
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 