#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数显示组件
显示步态分析的数值参数、统计信息和分析结果
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QTableWidget, QTableWidgetItem, QTabWidget,
                               QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ParameterDisplayWidget(QWidget):
    """参数显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_results = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.05), stop:1 rgba(255,255,255,0.02));
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                border: 2px solid #5a5a5a;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 6px 12px;
                margin-right: 2px;
                color: #cccccc;
                font-weight: bold;
                font-size: 9pt;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #4caf50);
                color: white;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
        """)
        
        # 基本参数标签页
        self.basic_tab = QWidget()
        self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本参数")
        
        # 步态周期标签页
        self.cycles_tab = QWidget()
        self.create_cycles_tab()
        self.tab_widget.addTab(self.cycles_tab, "步态周期")
        
        # 支撑相分析标签页
        self.phases_tab = QWidget()
        self.create_phases_tab()
        self.tab_widget.addTab(self.phases_tab, "相位分析")
        
        # 统计信息标签页
        self.stats_tab = QWidget()
        self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "统计信息")
        
        layout.addWidget(self.tab_widget)
    
    def create_basic_tab(self):
        """创建基本参数标签页"""
        layout = QVBoxLayout(self.basic_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 步长参数组
        stride_group = QGroupBox("步长参数")
        stride_layout = QVBoxLayout(stride_group)
        
        self.stride_length_label = self.create_parameter_label("平均步长", "-- cm")
        stride_layout.addWidget(self.stride_length_label)
        
        self.step_width_label = self.create_parameter_label("步宽", "-- cm")
        stride_layout.addWidget(self.step_width_label)
        
        self.step_frequency_label = self.create_parameter_label("步频", "-- 步/分")
        stride_layout.addWidget(self.step_frequency_label)
        
        layout.addWidget(stride_group)
        
        # 时间参数组
        timing_group = QGroupBox("时间参数")
        timing_layout = QVBoxLayout(timing_group)
        
        self.cycle_duration_label = self.create_parameter_label("步态周期时长", "-- s")
        timing_layout.addWidget(self.cycle_duration_label)
        
        self.stance_time_label = self.create_parameter_label("支撑相时间", "-- s")
        timing_layout.addWidget(self.stance_time_label)
        
        self.swing_time_label = self.create_parameter_label("摆动相时间", "-- s")
        timing_layout.addWidget(self.swing_time_label)
        
        layout.addWidget(timing_group)
        
        # 对称性参数组
        symmetry_group = QGroupBox("对称性参数")
        symmetry_layout = QVBoxLayout(symmetry_group)
        
        self.left_right_symmetry_label = self.create_parameter_label("左右对称性", "-- %")
        symmetry_layout.addWidget(self.left_right_symmetry_label)
        
        self.temporal_symmetry_label = self.create_parameter_label("时间对称性", "-- %")
        symmetry_layout.addWidget(self.temporal_symmetry_label)
        
        self.spatial_symmetry_label = self.create_parameter_label("空间对称性", "-- %")
        symmetry_layout.addWidget(self.spatial_symmetry_label)
        
        layout.addWidget(symmetry_group)
        
        layout.addStretch()
    
    def create_cycles_tab(self):
        """创建步态周期标签页"""
        layout = QVBoxLayout(self.cycles_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 步态周期表格
        self.cycles_table = QTableWidget()
        self.cycles_table.setColumnCount(6)
        self.cycles_table.setHorizontalHeaderLabels([
            "周期", "侧别", "起始帧", "结束帧", "持续时间(s)", "步长(cm)"
        ])
        
        # 设置表格样式
        self.cycles_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #5a5a5a;
                background-color: #2b2b2b;
                alternate-background-color: #3a3a3a;
                selection-background-color: #4caf50;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 5px;
                font-weight: bold;
            }
        """)
        
        self.cycles_table.setAlternatingRowColors(True)
        self.cycles_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.cycles_table)
    
    def create_phases_tab(self):
        """创建相位分析标签页"""
        layout = QVBoxLayout(self.phases_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 支撑相统计组
        support_group = QGroupBox("支撑相统计")
        support_layout = QVBoxLayout(support_group)
        
        self.left_support_ratio_label = self.create_parameter_label("左脚支撑相比例", "-- %")
        support_layout.addWidget(self.left_support_ratio_label)
        
        self.right_support_ratio_label = self.create_parameter_label("右脚支撑相比例", "-- %")
        support_layout.addWidget(self.right_support_ratio_label)
        
        self.double_support_ratio_label = self.create_parameter_label("双支撑相比例", "-- %")
        support_layout.addWidget(self.double_support_ratio_label)
        
        layout.addWidget(support_group)
        
        # 摆动相统计组
        swing_group = QGroupBox("摆动相统计")
        swing_layout = QVBoxLayout(swing_group)
        
        self.left_swing_ratio_label = self.create_parameter_label("左脚摆动相比例", "-- %")
        swing_layout.addWidget(self.left_swing_ratio_label)
        
        self.right_swing_ratio_label = self.create_parameter_label("右脚摆动相比例", "-- %")
        swing_layout.addWidget(self.right_swing_ratio_label)
        
        layout.addWidget(swing_group)
        
        # 相位表格
        self.phases_table = QTableWidget()
        self.phases_table.setColumnCount(5)
        self.phases_table.setHorizontalHeaderLabels([
            "周期", "侧别", "支撑相(%)", "摆动相(%)", "双支撑(%)"
        ])
        
        # 设置表格样式
        self.phases_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #5a5a5a;
                background-color: #2b2b2b;
                alternate-background-color: #3a3a3a;
                selection-background-color: #4caf50;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 5px;
                font-weight: bold;
            }
        """)
        
        self.phases_table.setAlternatingRowColors(True)
        self.phases_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.phases_table)
    
    def create_stats_tab(self):
        """创建统计信息标签页"""
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 角度统计组
        angles_group = QGroupBox("关节角度统计")
        angles_layout = QVBoxLayout(angles_group)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 存储角度统计标签
        self.angle_stats_labels = {}
        
        joint_names = [
            ("left_hip", "左髋关节"),
            ("right_hip", "右髋关节"),
            ("left_knee", "左膝关节"),
            ("right_knee", "右膝关节"),
            ("left_ankle", "左踝关节"),
            ("right_ankle", "右踝关节"),
            ("trunk_sway", "躯干摆动")
        ]
        
        for joint_key, joint_name in joint_names:
            joint_frame = QFrame()
            joint_frame.setFrameStyle(QFrame.Box)
            joint_frame.setStyleSheet("""
                QFrame {
                    border: 1px solid #5a5a5a;
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.05);
                    margin: 2px;
                    padding: 5px;
                }
            """)
            
            joint_layout = QVBoxLayout(joint_frame)
            joint_layout.setContentsMargins(10, 5, 10, 5)
            
            # 关节名称
            title_label = QLabel(joint_name)
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 11pt;
                    color: #66bb6a;
                    border: none;
                    margin-bottom: 5px;
                }
            """)
            joint_layout.addWidget(title_label)
            
            # 统计信息
            stats_layout = QHBoxLayout()
            
            mean_label = QLabel("平均值: --°")
            mean_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
            stats_layout.addWidget(mean_label)
            
            std_label = QLabel("标准差: --°")
            std_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
            stats_layout.addWidget(std_label)
            
            range_label = QLabel("范围: --°")
            range_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
            stats_layout.addWidget(range_label)
            
            joint_layout.addLayout(stats_layout)
            
            self.angle_stats_labels[joint_key] = {
                'mean': mean_label,
                'std': std_label,
                'range': range_label
            }
            
            scroll_layout.addWidget(joint_frame)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        angles_layout.addWidget(scroll_area)
        layout.addWidget(angles_group)
        
        # 数据质量组
        quality_group = QGroupBox("数据质量")
        quality_layout = QVBoxLayout(quality_group)
        
        self.data_completeness_label = self.create_parameter_label("数据完整性", "-- %")
        quality_layout.addWidget(self.data_completeness_label)
        
        self.detection_confidence_label = self.create_parameter_label("检测置信度", "-- %")
        quality_layout.addWidget(self.detection_confidence_label)
        
        self.smoothing_quality_label = self.create_parameter_label("平滑质量", "-- %")
        quality_layout.addWidget(self.smoothing_quality_label)
        
        layout.addWidget(quality_group)
        
        layout.addStretch()
    
    def create_parameter_label(self, name, value):
        """创建参数显示标签"""
        container = QFrame()
        container.setFrameStyle(QFrame.NoFrame)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        
        name_label = QLabel(name + ":")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #cccccc;
                min-width: 120px;
            }
        """)
        layout.addWidget(name_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                font-weight: bold;
                color: #66bb6a;
                background: rgba(102, 187, 106, 0.1);
                padding: 3px 8px;
                border-radius: 3px;
                min-width: 80px;
            }
        """)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        # 存储值标签的引用以便更新
        container.value_label = value_label
        
        return container
    
    def update_parameters(self, analysis_results):
        """更新参数显示"""
        if not analysis_results:
            return
        
        self.analysis_results = analysis_results
        
        # 更新基本参数
        self.update_basic_parameters(analysis_results)
        
        # 更新步态周期表格
        self.update_cycles_table(analysis_results)
        
        # 更新相位分析
        self.update_phases_parameters(analysis_results)
        
        # 更新统计信息
        self.update_statistics(analysis_results)
    
    def update_basic_parameters(self, results):
        """更新基本参数"""
        gait_params = results.get('gait_params', {})
        
        # 步长参数
        stride_length = gait_params.get('avg_stride_length', 0)
        self.stride_length_label.value_label.setText(f"{stride_length:.1f} cm")
        
        step_width = gait_params.get('avg_step_width', 0)
        self.step_width_label.value_label.setText(f"{step_width:.1f} cm")
        
        step_frequency = gait_params.get('step_frequency', 0)
        self.step_frequency_label.value_label.setText(f"{step_frequency:.1f} 步/分")
        
        # 时间参数
        cycle_duration = gait_params.get('avg_cycle_duration', 0)
        self.cycle_duration_label.value_label.setText(f"{cycle_duration:.2f} s")
        
        stance_time = gait_params.get('avg_stance_time', 0)
        self.stance_time_label.value_label.setText(f"{stance_time:.2f} s")
        
        swing_time = gait_params.get('avg_swing_time', 0)
        self.swing_time_label.value_label.setText(f"{swing_time:.2f} s")
        
        # 对称性参数
        lr_symmetry = gait_params.get('left_right_symmetry', 0)
        self.left_right_symmetry_label.value_label.setText(f"{lr_symmetry:.1f} %")
        
        temporal_symmetry = gait_params.get('temporal_symmetry', 0)
        self.temporal_symmetry_label.value_label.setText(f"{temporal_symmetry:.1f} %")
        
        spatial_symmetry = gait_params.get('spatial_symmetry', 0)
        self.spatial_symmetry_label.value_label.setText(f"{spatial_symmetry:.1f} %")
    
    def update_cycles_table(self, results):
        """更新步态周期表格"""
        cycles_data = results.get('gait_cycles', [])
        
        self.cycles_table.setRowCount(len(cycles_data))
        
        for i, cycle in enumerate(cycles_data):
            # 周期编号
            self.cycles_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # 侧别
            side = "左" if cycle.get('side') == 'left' else "右"
            self.cycles_table.setItem(i, 1, QTableWidgetItem(side))
            
            # 起始帧
            start_frame = cycle.get('start_frame', 0)
            self.cycles_table.setItem(i, 2, QTableWidgetItem(str(start_frame)))
            
            # 结束帧
            end_frame = cycle.get('end_frame', 0)
            self.cycles_table.setItem(i, 3, QTableWidgetItem(str(end_frame)))
            
            # 持续时间
            duration = cycle.get('duration', 0)
            self.cycles_table.setItem(i, 4, QTableWidgetItem(f"{duration:.2f}"))
            
            # 步长
            stride_length = cycle.get('stride_length', 0)
            self.cycles_table.setItem(i, 5, QTableWidgetItem(f"{stride_length:.1f}"))
    
    def update_phases_parameters(self, results):
        """更新相位分析参数"""
        gait_params = results.get('gait_params', {})
        
        # 支撑相比例
        left_support = gait_params.get('left_support_ratio', 0) * 100
        self.left_support_ratio_label.value_label.setText(f"{left_support:.1f} %")
        
        right_support = gait_params.get('right_support_ratio', 0) * 100
        self.right_support_ratio_label.value_label.setText(f"{right_support:.1f} %")
        
        double_support = gait_params.get('double_support_ratio', 0) * 100
        self.double_support_ratio_label.value_label.setText(f"{double_support:.1f} %")
        
        # 摆动相比例
        left_swing = gait_params.get('left_swing_ratio', 0) * 100
        self.left_swing_ratio_label.value_label.setText(f"{left_swing:.1f} %")
        
        right_swing = gait_params.get('right_swing_ratio', 0) * 100
        self.right_swing_ratio_label.value_label.setText(f"{right_swing:.1f} %")
        
        # 更新相位表格
        phase_details = gait_params.get('phase_details', [])
        self.phases_table.setRowCount(len(phase_details))
        
        for i, phase in enumerate(phase_details):
            # 周期编号
            self.phases_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # 侧别
            side = "左" if phase.get('side') == 'left' else "右"
            self.phases_table.setItem(i, 1, QTableWidgetItem(side))
            
            # 支撑相比例
            support_ratio = phase.get('support_ratio', 0) * 100
            self.phases_table.setItem(i, 2, QTableWidgetItem(f"{support_ratio:.1f}"))
            
            # 摆动相比例
            swing_ratio = phase.get('swing_ratio', 0) * 100
            self.phases_table.setItem(i, 3, QTableWidgetItem(f"{swing_ratio:.1f}"))
            
            # 双支撑比例
            double_support_ratio = phase.get('double_support_ratio', 0) * 100
            self.phases_table.setItem(i, 4, QTableWidgetItem(f"{double_support_ratio:.1f}"))
    
    def update_statistics(self, results):
        """更新统计信息"""
        import numpy as np
        
        # 更新关节角度统计
        smoothed_angles = results.get('smoothed_angles', {})
        
        for joint_key, labels in self.angle_stats_labels.items():
            if joint_key in smoothed_angles:
                angles = smoothed_angles[joint_key]
                if len(angles) > 0:
                    angles_array = np.array(angles)
                    
                    # 计算统计值
                    mean_val = np.mean(angles_array)
                    std_val = np.std(angles_array)
                    min_val = np.min(angles_array)
                    max_val = np.max(angles_array)
                    
                    # 更新标签
                    labels['mean'].setText(f"平均值: {mean_val:.1f}°")
                    labels['std'].setText(f"标准差: {std_val:.1f}°")
                    labels['range'].setText(f"范围: {min_val:.1f}° - {max_val:.1f}°")
        
        # 更新数据质量信息
        quality_info = results.get('quality_info', {})
        
        completeness = quality_info.get('data_completeness', 0) * 100
        self.data_completeness_label.value_label.setText(f"{completeness:.1f} %")
        
        confidence = quality_info.get('detection_confidence', 0) * 100
        self.detection_confidence_label.value_label.setText(f"{confidence:.1f} %")
        
        smoothing_quality = quality_info.get('smoothing_quality', 0) * 100
        self.smoothing_quality_label.value_label.setText(f"{smoothing_quality:.1f} %")
    
    def clear_parameters(self):
        """清除所有参数显示"""
        # 重置基本参数
        self.stride_length_label.value_label.setText("-- cm")
        self.step_width_label.value_label.setText("-- cm")
        self.step_frequency_label.value_label.setText("-- 步/分")
        self.cycle_duration_label.value_label.setText("-- s")
        self.stance_time_label.value_label.setText("-- s")
        self.swing_time_label.value_label.setText("-- s")
        self.left_right_symmetry_label.value_label.setText("-- %")
        self.temporal_symmetry_label.value_label.setText("-- %")
        self.spatial_symmetry_label.value_label.setText("-- %")
        
        # 清空表格
        self.cycles_table.setRowCount(0)
        self.phases_table.setRowCount(0)
        
        # 重置角度统计
        for labels in self.angle_stats_labels.values():
            labels['mean'].setText("平均值: --°")
            labels['std'].setText("标准差: --°")
            labels['range'].setText("范围: --°")
        
        # 重置数据质量
        self.data_completeness_label.value_label.setText("-- %")
        self.detection_confidence_label.value_label.setText("-- %")
        self.smoothing_quality_label.value_label.setText("-- %")