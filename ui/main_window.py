#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类
包含视频显示、特征曲线显示、控制面板等所有UI组件
"""

import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QSplitter, QMenuBar, QStatusBar, QLabel, QProgressBar,
                               QFileDialog, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QAction, QIcon

from .video_player import VideoPlayerWidget
from .chart_display import ChartDisplayWidget
from .control_panel import ControlPanelWidget
from .parameter_display import ParameterDisplayWidget
from core.gait_analyzer import GaitAnalyzer
from core.keypoint_generator import KeypointGenerator


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.gait_analyzer = None
        self.keypoint_generator = None
        self.current_video_path = None
        self.current_keypoints_path = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("步态分析可视化工具 v1.0")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 左侧区域 - 视频播放和控制
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 视频播放器
        self.video_player = VideoPlayerWidget()
        left_layout.addWidget(self.video_player, 3)
        
        # 控制面板
        self.control_panel = ControlPanelWidget()
        left_layout.addWidget(self.control_panel, 1)
        
        # 右侧区域 - 图表和参数显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 特征曲线显示
        self.chart_display = ChartDisplayWidget()
        right_layout.addWidget(self.chart_display, 2)
        
        # 参数显示
        self.parameter_display = ParameterDisplayWidget()
        right_layout.addWidget(self.parameter_display, 1)
        
        # 添加到分割器
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([800, 600])  # 设置初始大小比例
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开视频
        open_video_action = QAction("打开视频文件(&O)", self)
        open_video_action.setShortcut("Ctrl+O")
        open_video_action.setStatusTip("打开视频文件进行步态分析")
        open_video_action.triggered.connect(self.open_video_file)
        file_menu.addAction(open_video_action)
        
        # 打开关键点数据
        open_keypoints_action = QAction("打开关键点数据(&K)", self)
        open_keypoints_action.setShortcut("Ctrl+K")
        open_keypoints_action.setStatusTip("打开已有的关键点数据文件")
        open_keypoints_action.triggered.connect(self.open_keypoints_file)
        file_menu.addAction(open_keypoints_action)
        
        file_menu.addSeparator()
        
        # 保存分析结果
        save_results_action = QAction("保存分析结果(&S)", self)
        save_results_action.setShortcut("Ctrl+S")
        save_results_action.setStatusTip("保存步态分析结果")
        save_results_action.triggered.connect(self.save_analysis_results)
        save_results_action.setEnabled(False)
        self.save_results_action = save_results_action
        file_menu.addAction(save_results_action)
        
        # 导出图表
        export_charts_action = QAction("导出图表(&E)", self)
        export_charts_action.setShortcut("Ctrl+E")
        export_charts_action.setStatusTip("导出特征曲线图表")
        export_charts_action.triggered.connect(self.export_charts)
        export_charts_action.setEnabled(False)
        self.export_charts_action = export_charts_action
        file_menu.addAction(export_charts_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 分析菜单
        analysis_menu = menubar.addMenu("分析(&A)")
        
        # 开始分析
        start_analysis_action = QAction("开始分析(&S)", self)
        start_analysis_action.setShortcut("F5")
        start_analysis_action.setStatusTip("开始步态分析")
        start_analysis_action.triggered.connect(self.start_analysis)
        start_analysis_action.setEnabled(False)
        self.start_analysis_action = start_analysis_action
        analysis_menu.addAction(start_analysis_action)
        
        # 生成关键点
        generate_keypoints_action = QAction("生成关键点数据(&G)", self)
        generate_keypoints_action.setShortcut("F6")
        generate_keypoints_action.setStatusTip("使用YOLO模型生成关键点数据")
        generate_keypoints_action.triggered.connect(self.generate_keypoints)
        generate_keypoints_action.setEnabled(False)
        self.generate_keypoints_action = generate_keypoints_action
        analysis_menu.addAction(generate_keypoints_action)
        
        analysis_menu.addSeparator()
        
        # 显示支撑相分析
        phase_analysis_action = QAction("支撑相分析(&P)", self)
        phase_analysis_action.setStatusTip("显示详细的支撑相和摆动相分析")
        phase_analysis_action.triggered.connect(self.show_phase_analysis)
        phase_analysis_action.setEnabled(False)
        self.phase_analysis_action = phase_analysis_action
        analysis_menu.addAction(phase_analysis_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于步态分析工具")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 帧信息标签
        self.frame_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.frame_info_label)
    
    def setup_connections(self):
        """设置信号连接"""
        # 控制面板信号
        self.control_panel.play_pause_clicked.connect(self.toggle_playback)
        self.control_panel.stop_clicked.connect(self.stop_playback)
        self.control_panel.frame_changed.connect(self.on_frame_changed)
        self.control_panel.speed_changed.connect(self.video_player.set_playback_speed)
        self.control_panel.joint_visibility_changed.connect(self.chart_display.set_joint_visibility)
        self.control_panel.data_type_changed.connect(self.chart_display.set_data_type)
        
        # 视频播放器信号
        self.video_player.frame_changed.connect(self.on_video_frame_changed)
        self.video_player.playback_finished.connect(self.on_playback_finished)
    
    def open_video_file(self):
        """打开视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.load_video(file_path)
    
    def open_keypoints_file(self):
        """打开关键点数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择关键点数据文件",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_keypoints_path = file_path
            self.status_label.setText(f"已加载关键点数据: {os.path.basename(file_path)}")
            
            # 如果有视频文件，启用分析功能
            if self.current_video_path:
                self.start_analysis_action.setEnabled(True)
    
    def load_video(self, video_path):
        """加载视频文件"""
        try:
            self.current_video_path = video_path
            
            # 加载视频到播放器
            self.video_player.load_video(video_path)
            
            # 更新控制面板
            frame_count = self.video_player.get_frame_count()
            self.control_panel.set_frame_range(0, frame_count - 1)
            
            # 更新状态
            self.status_label.setText(f"已加载视频: {os.path.basename(video_path)}")
            
            # 启用生成关键点功能
            self.generate_keypoints_action.setEnabled(True)
            
            # 检查是否存在对应的关键点数据
            self.check_existing_keypoints(video_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载视频失败: {str(e)}")
    
    def check_existing_keypoints(self, video_path):
        """检查是否存在对应的关键点数据"""
        # 生成可能的关键点文件路径
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        video_dir = os.path.dirname(video_path)
        
        possible_paths = [
            os.path.join(video_dir, "output", video_name, "keypoints.json"),
            os.path.join(video_dir, f"{video_name}_keypoints.json"),
            os.path.join(video_dir, "keypoints.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.current_keypoints_path = path
                self.status_label.setText(f"已自动加载关键点数据: {os.path.basename(path)}")
                self.start_analysis_action.setEnabled(True)
                return
        
        # 未找到关键点数据，提示用户
        self.status_label.setText("未找到关键点数据，请生成或手动选择")
    
    def generate_keypoints(self):
        """生成关键点数据"""
        if not self.current_video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
        
        try:
            # 创建关键点生成器
            self.keypoint_generator = KeypointGenerator()
            
            # 显示进度
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.status_label.setText("正在生成关键点数据...")
            
            # 生成关键点（这里应该在子线程中执行）
            keypoints_path = self.keypoint_generator.generate_from_video(self.current_video_path)
            
            if keypoints_path:
                self.current_keypoints_path = keypoints_path
                self.status_label.setText(f"关键点数据生成完成: {os.path.basename(keypoints_path)}")
                self.start_analysis_action.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成关键点数据失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def start_analysis(self):
        """开始步态分析"""
        if not self.current_video_path or not self.current_keypoints_path:
            QMessageBox.warning(self, "警告", "请确保已加载视频文件和关键点数据")
            return
        
        try:
            # 创建步态分析器
            self.gait_analyzer = GaitAnalyzer()
            
            # 显示进度
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.status_label.setText("正在进行步态分析...")
            
            # 执行分析
            results = self.gait_analyzer.analyze(
                self.current_video_path, 
                self.current_keypoints_path,
                progress_callback=self.update_progress
            )
            
            if results:
                # 更新显示
                self.chart_display.update_data(results)
                self.parameter_display.update_parameters(results)
                self.video_player.set_keypoints_data(results.get('keypoints', []))
                
                # 启用相关功能
                self.save_results_action.setEnabled(True)
                self.export_charts_action.setEnabled(True)
                self.phase_analysis_action.setEnabled(True)
                
                self.status_label.setText("步态分析完成")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"步态分析失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(int(value))
        QApplication.processEvents()  # 保持界面响应
    
    def toggle_playback(self):
        """切换播放/暂停"""
        if self.video_player.is_playing():
            self.video_player.pause()
            self.control_panel.update_play_button(False)
        else:
            self.video_player.play()
            self.control_panel.update_play_button(True)
    
    def stop_playback(self):
        """停止播放"""
        self.video_player.stop()
        self.control_panel.update_play_button(False)
    
    def on_frame_changed(self, frame_number):
        """帧数变化处理"""
        self.video_player.seek_to_frame(frame_number)
        self.update_frame_info(frame_number)
        
        # 更新图表中的当前帧位置
        self.chart_display.set_current_frame(frame_number)
    
    def on_video_frame_changed(self, frame_number):
        """视频帧变化处理"""
        self.control_panel.set_current_frame(frame_number)
        self.update_frame_info(frame_number)
        
        # 更新图表中的当前帧位置
        self.chart_display.set_current_frame(frame_number)
    
    def update_frame_info(self, frame_number):
        """更新帧信息显示"""
        if self.video_player.video_loaded:
            total_frames = self.video_player.get_frame_count()
            fps = self.video_player.get_fps()
            current_time = frame_number / fps if fps > 0 else 0
            total_time = total_frames / fps if fps > 0 else 0
            
            self.frame_info_label.setText(
                f"帧: {frame_number}/{total_frames} | "
                f"时间: {current_time:.2f}s/{total_time:.2f}s"
            )
    
    def on_playback_finished(self):
        """播放完成处理"""
        self.control_panel.update_play_button(False)
    
    def save_analysis_results(self):
        """保存分析结果"""
        if not self.gait_analyzer or not hasattr(self.gait_analyzer, 'results'):
            QMessageBox.warning(self, "警告", "没有可保存的分析结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存分析结果",
            "",
            "JSON文件 (*.json);;Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.gait_analyzer.save_results(file_path)
                QMessageBox.information(self, "成功", f"分析结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def export_charts(self):
        """导出图表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图表",
            "",
            "PNG图片 (*.png);;PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.chart_display.export_charts(file_path)
                QMessageBox.information(self, "成功", f"图表已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def show_phase_analysis(self):
        """显示支撑相分析"""
        if not self.gait_analyzer or not hasattr(self.gait_analyzer, 'results'):
            QMessageBox.warning(self, "警告", "没有可显示的分析结果")
            return
        
        # 创建支撑相分析对话框（这里简化显示）
        from .phase_analysis_dialog import PhaseAnalysisDialog
        dialog = PhaseAnalysisDialog(self.gait_analyzer.results, self)
        dialog.exec()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于步态分析工具",
            """
            <h3>步态分析可视化工具 v1.0</h3>
            <p>基于PySide6和深度学习的步态分析工具</p>
            <p><b>主要功能：</b></p>
            <ul>
            <li>实时视频播放和骨骼点显示</li>
            <li>关节角度特征曲线分析</li>
            <li>支撑相和摆动相分析</li>
            <li>步态参数计算和可视化</li>
            <li>YOLO模型自动关键点检测</li>
            </ul>
            <p><b>技术栈：</b> PySide6, OpenCV, PyQtGraph, YOLO, NumPy</p>
            """
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止视频播放
        if hasattr(self, 'video_player'):
            self.video_player.stop()
        
        # 接受关闭事件
        event.accept()