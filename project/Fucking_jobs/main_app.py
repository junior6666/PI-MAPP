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
                                QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QFont, QTextCursor, QIcon

# 导入工作线程类
from workers import (ScreenshotWorker, OCRWorker, LLMWorker, KimiWorker, WebSocketServerWorker)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📸 截图 OCR LLM 分析工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
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
        
        # 延迟启动截图监听（等待 UI 完全加载）
        QTimer.singleShot(500, self.auto_start_screenshot)
        
        # 延迟启动快速分析快捷键（Alt+Z）
        QTimer.singleShot(1000, self.start_quick_analysis_hotkey)
        
        # 延迟启动 WebSocket 服务
        QTimer.singleShot(1500, self.auto_start_websocket)
        
        # 初始化系统托盘
        self.init_system_tray()
        
    def init_ui(self):
        """初始化用户界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, stretch=1)
        
        # 右侧结果显示区
        right_panel = self.create_result_panel()
        main_layout.addWidget(right_panel, stretch=2)
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # ===== 截图控制组 =====
        screenshot_group = QGroupBox("📸 截图设置")
        screenshot_layout = QFormLayout()
        
        self.hotkey_input = QLineEdit("<alt>+x")
        self.hotkey_input.setPlaceholderText("例如: <ctrl>+<shift>+s")
        screenshot_layout.addRow("热键组合:", self.hotkey_input)
        
        self.save_dir_input = QLineEdit("./screenshots")
        self.save_dir_input.setReadOnly(True)
        screenshot_layout.addRow("保存目录:", self.save_dir_input)
        
        self.btn_toggle_screenshot = QPushButton("停止截图监听")
        self.btn_toggle_screenshot.setCheckable(True)
        self.btn_toggle_screenshot.setChecked(True)  # 默认选中
        self.btn_toggle_screenshot.clicked.connect(self.toggle_screenshot)
        screenshot_layout.addRow(self.btn_toggle_screenshot)
        
        screenshot_group.setLayout(screenshot_layout)
        layout.addWidget(screenshot_group)
        
        # ===== OCR 控制组 =====
        ocr_group = QGroupBox("🔍 OCR 文字识别")
        ocr_layout = QVBoxLayout()
        
        self.btn_ocr = QPushButton("开始 OCR 识别")
        self.btn_ocr.setEnabled(False)
        self.btn_ocr.clicked.connect(self.start_ocr)
        ocr_layout.addWidget(self.btn_ocr)
        
        self.auto_ocr_check = QCheckBox("截图后自动进行 OCR")
        ocr_layout.addWidget(self.auto_ocr_check)
        
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # ===== LLM 控制组 =====
        llm_group = QGroupBox("🤖 LLM 智能分析")
        llm_layout = QFormLayout()
        
        self.api_key_input = QLineEdit("ak_2Fw1hL0xA8H33yj1wn4pW8ag0w84y")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        llm_layout.addRow("API Key:", self.api_key_input)
        
        self.model_input = QLineEdit("LongCat-Flash-Chat")
        llm_layout.addRow("模型名称:", self.model_input)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入提示词...")
        self.prompt_input.setMaximumHeight(80)
        self.prompt_input.setText("""你是一位专业的面试助手。请分析屏幕截图中的内容，识别出面试题目并给出专业回答。

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
        
        # ===== WebSocket 控制组 =====
        ws_group = QGroupBox("📡 WebSocket 服务器")
        ws_layout = QFormLayout()
        
        self.ws_port_input = QSpinBox()
        self.ws_port_input.setRange(1024, 65535)
        self.ws_port_input.setValue(8765)
        ws_layout.addRow("端口号:", self.ws_port_input)
        
        self.ws_status_label = QLabel("未启动")
        ws_layout.addRow("状态:", self.ws_status_label)
        
        self.btn_toggle_ws = QPushButton("启动 WebSocket 服务")
        self.btn_toggle_ws.setCheckable(True)
        self.btn_toggle_ws.clicked.connect(self.toggle_websocket)
        ws_layout.addRow(self.btn_toggle_ws)
        
        self.btn_send_to_phone = QPushButton("发送结果到手机")
        self.btn_send_to_phone.setEnabled(False)
        self.btn_send_to_phone.clicked.connect(self.send_to_phone)
        ws_layout.addRow(self.btn_send_to_phone)
        
        ws_group.setLayout(ws_layout)
        layout.addWidget(ws_group)
        
        # 弹簧
        layout.addStretch()
        
        return panel
    
    def create_result_panel(self):
        """创建右侧结果显示区"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
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
        self.ocr_time_label.setStyleSheet("color: #888; font-size: 11px; padding: 2px 4px;")
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
        self.llm_time_label.setStyleSheet("color: #888; font-size: 11px; padding: 2px 4px;")
        llm_timing_layout.addWidget(self.llm_time_label)
        llm_result_layout.addLayout(llm_timing_layout)
        
        llm_result_group.setLayout(llm_result_layout)
        layout.addWidget(llm_result_group)
        
        return panel
    
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
            hotkey = self.hotkey_input.text().strip()
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
        
        # 如果启用了自动 OCR
        if self.auto_ocr_check.isChecked():
            self.start_ocr()
    
    def on_quick_analysis_triggered(self):
        """快速分析快捷键触发（Alt+Z）"""
        print("🚀 快速分析流程启动...")
        
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
        
        # 在 LLM 结果区显示（因为是分析结果）
        self.llm_result_text.setText(kimi_text)
        self.llm_elapsed = elapsed_time
        
        # 显示 Kimi 耗时
        self.llm_time_label.setText(f"⏱️ {elapsed_time:.2f}s (Kimi)")
        
        # 计算整体耗时
        total_elapsed = 0.0
        if self.screenshot_timestamp:
            total_elapsed = time.time() - self.screenshot_timestamp
        
        print(f"✅ Kimi 分析完成 (耗时: {elapsed_time:.2f}s)")
        
        # 如果 WebSocket 已启动且有客户端连接，自动发送结果
        if self.websocket_worker and self.websocket_worker.is_running and self.websocket_worker.has_clients:
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
    
    def init_system_tray(self):
        """初始化系统托盘"""
        # 检查系统是否支持托盘图标
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ 系统不支持托盘图标")
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标（使用 icon.ico）
        if os.path.exists("icon.ico"):
            self.tray_icon.setIcon(QIcon("icon.ico"))
        
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
            self.screenshot_worker.stop()
            self.screenshot_worker.wait(2000)  # 最多等待2秒
        
        if self.kimi_worker and self.kimi_worker.isRunning():
            self.kimi_worker.terminate()
            self.kimi_worker.wait(1000)
        
        # 先停止 WebSocket 服务（需要等待异步任务清理）
        if self.websocket_worker:
            print("⏳ 正在停止 WebSocket 服务...")
            self.websocket_worker.stop()
            self.websocket_worker.wait(5000)  # 等待最多5秒让异步任务清理
            print("✅ WebSocket 服务已停止")
        
        # 停止快速分析监听器
        if hasattr(self, 'quick_analysis_listener') and self.quick_analysis_listener:
            try:
                self.quick_analysis_listener.stop()
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
        # 停止所有工作线程
        if self.screenshot_worker:
            self.screenshot_worker.stop()
            self.screenshot_worker.wait()
        
        if self.kimi_worker:
            self.kimi_worker.terminate()
            self.kimi_worker.wait()
        
        if self.websocket_worker:
            self.websocket_worker.stop()
            self.websocket_worker.wait()
        
        # 停止快速分析监听器
        if hasattr(self, 'quick_analysis_listener') and self.quick_analysis_listener:
            self.quick_analysis_listener.stop()
        
        # 移除托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 默认隐藏窗口，只显示托盘图标
    window.hide()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
