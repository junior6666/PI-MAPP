#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表显示组件
使用pyqtgraph显示关节角度特征曲线和步态分析结果
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class ChartDisplayWidget(QWidget):
    """图表显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame = 0
        self.angle_data = {}
        self.joint_visibility = {
            'hip': True,
            'knee': True,
            'ankle': True,
            'trunk': True,
            'shoulder': True,
            'elbow': True
        }
        self.data_type = 'smoothed'  # 'raw' or 'smoothed'
        
        # 颜色配置
        self.colors = {
            'left_hip': '#E91E63',     # 粉红
            'right_hip': '#F44336',    # 红色
            'left_knee': '#9C27B0',    # 紫色
            'right_knee': '#673AB7',   # 深紫
            'left_ankle': '#3F51B5',   # 靛蓝
            'right_ankle': '#2196F3',  # 蓝色
            'trunk_sway': '#00BCD4',   # 青色
            'left_shoulder': '#4CAF50', # 绿色
            'right_shoulder': '#8BC34A', # 浅绿
            'left_elbow': '#FFEB3B',   # 黄色
            'right_elbow': '#FF9800',  # 橙色
        }
        
        self.init_ui()
        self.setup_plots()
    
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
                padding: 8px 16px;
                margin-right: 2px;
                color: #cccccc;
                font-weight: bold;
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
        
        # 关节角度图表标签页
        self.angles_tab = QWidget()
        self.create_angles_tab()
        self.tab_widget.addTab(self.angles_tab, "关节角度")
        
        # 步态周期图表标签页
        self.cycles_tab = QWidget()
        self.create_cycles_tab()
        self.tab_widget.addTab(self.cycles_tab, "步态周期")
        
        # 支撑相分析标签页
        self.phases_tab = QWidget()
        self.create_phases_tab()
        self.tab_widget.addTab(self.phases_tab, "支撑相分析")
        
        layout.addWidget(self.tab_widget)
    
    def create_angles_tab(self):
        """创建关节角度标签页"""
        layout = QVBoxLayout(self.angles_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分 - 腿部关节
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        
        # 髋关节图表
        self.hip_plot = self.create_plot_widget("髋关节角度", "角度 (度)")
        upper_layout.addWidget(self.hip_plot)
        
        # 膝关节图表
        self.knee_plot = self.create_plot_widget("膝关节角度", "角度 (度)")
        upper_layout.addWidget(self.knee_plot)
        
        # 踝关节图表
        self.ankle_plot = self.create_plot_widget("踝关节角度", "角度 (度)")
        upper_layout.addWidget(self.ankle_plot)
        
        splitter.addWidget(upper_widget)
        
        # 下半部分 - 躯干和上肢
        lower_widget = QWidget()
        lower_layout = QHBoxLayout(lower_widget)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        
        # 躯干摆动图表
        self.trunk_plot = self.create_plot_widget("躯干摆动", "角度 (度)")
        lower_layout.addWidget(self.trunk_plot)
        
        # 肩关节图表
        self.shoulder_plot = self.create_plot_widget("肩关节角度", "角度 (度)")
        lower_layout.addWidget(self.shoulder_plot)
        
        splitter.addWidget(lower_widget)
        splitter.setSizes([300, 200])
        
        layout.addWidget(splitter)
    
    def create_cycles_tab(self):
        """创建步态周期标签页"""
        layout = QVBoxLayout(self.cycles_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 步态周期总览图表
        self.cycle_overview_plot = self.create_plot_widget("步态周期总览", "归一化时间 (%)")
        layout.addWidget(self.cycle_overview_plot)
        
        # 左右对比图表
        comparison_widget = QWidget()
        comparison_layout = QHBoxLayout(comparison_widget)
        comparison_layout.setContentsMargins(0, 0, 0, 0)
        
        self.left_cycle_plot = self.create_plot_widget("左侧步态周期", "归一化时间 (%)")
        comparison_layout.addWidget(self.left_cycle_plot)
        
        self.right_cycle_plot = self.create_plot_widget("右侧步态周期", "归一化时间 (%)")
        comparison_layout.addWidget(self.right_cycle_plot)
        
        layout.addWidget(comparison_widget)
    
    def create_phases_tab(self):
        """创建支撑相分析标签页"""
        layout = QVBoxLayout(self.phases_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 支撑相时序图
        self.phase_timeline_plot = self.create_plot_widget("支撑相时序", "时间 (帧)")
        layout.addWidget(self.phase_timeline_plot)
        
        # 支撑相统计图表
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.support_ratio_plot = self.create_plot_widget("支撑相比例", "百分比 (%)")
        stats_layout.addWidget(self.support_ratio_plot)
        
        self.swing_ratio_plot = self.create_plot_widget("摆动相比例", "百分比 (%)")
        stats_layout.addWidget(self.swing_ratio_plot)
        
        layout.addWidget(stats_widget)
    
    def create_plot_widget(self, title, y_label):
        """创建单个图表组件"""
        plot_widget = pg.PlotWidget(title=title)
        
        # 设置样式
        plot_widget.setBackground('#2b2b2b')
        plot_widget.getAxis('left').setPen(pg.mkPen(color='#cccccc', width=1))
        plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#cccccc', width=1))
        plot_widget.getAxis('left').setTextPen(pg.mkPen(color='#cccccc'))
        plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='#cccccc'))
        
        # 设置标签
        plot_widget.setLabel('left', y_label, color='#cccccc', size='10pt')
        plot_widget.setLabel('bottom', '帧数', color='#cccccc', size='10pt')
        
        # 设置网格
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 设置标题样式
        plot_widget.setTitle(title, color='#ffffff', size='12pt')
        
        # 添加图例
        plot_widget.addLegend(offset=(10, 10))
        
        return plot_widget
    
    def setup_plots(self):
        """设置图表"""
        # 存储图表引用
        self.plots = {
            'hip': self.hip_plot,
            'knee': self.knee_plot,
            'ankle': self.ankle_plot,
            'trunk': self.trunk_plot,
            'shoulder': self.shoulder_plot,
        }
        
        # 存储当前帧线
        self.current_frame_lines = {}
        
        # 为每个图表添加当前帧指示线
        for plot_name, plot_widget in self.plots.items():
            line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color='yellow', width=2, style=Qt.DashLine))
            plot_widget.addItem(line)
            self.current_frame_lines[plot_name] = line
    
    def update_data(self, analysis_results):
        """更新图表数据"""
        if not analysis_results:
            return
        
        self.angle_data = analysis_results.get('angles', {})
        raw_angles = analysis_results.get('raw_angles', {})
        smoothed_angles = analysis_results.get('smoothed_angles', {})
        
        # 更新关节角度图表
        self.update_angle_plots(raw_angles, smoothed_angles)
        
        # 更新步态周期图表
        if 'gait_cycles' in analysis_results:
            self.update_cycle_plots(analysis_results['gait_cycles'])
        
        # 更新支撑相图表
        if 'phase_analysis' in analysis_results:
            self.update_phase_plots(analysis_results['phase_analysis'])
    
    def update_angle_plots(self, raw_angles, smoothed_angles):
        """更新关节角度图表"""
        # 清除现有曲线
        for plot_widget in self.plots.values():
            plot_widget.clear()
            
        # 重新添加当前帧线
        for plot_name, plot_widget in self.plots.items():
            line = pg.InfiniteLine(pos=self.current_frame, angle=90, 
                                 pen=pg.mkPen(color='yellow', width=2, style=Qt.DashLine))
            plot_widget.addItem(line)
            self.current_frame_lines[plot_name] = line
        
        # 选择数据源
        angles_data = smoothed_angles if self.data_type == 'smoothed' else raw_angles
        
        if not angles_data:
            return
        
        frames = list(range(len(list(angles_data.values())[0])))
        
        # 髋关节
        if self.joint_visibility.get('hip', True):
            if 'left_hip' in angles_data:
                self.hip_plot.plot(frames, angles_data['left_hip'], 
                                 pen=pg.mkPen(color=self.colors['left_hip'], width=2),
                                 name='左髋关节')
            if 'right_hip' in angles_data:
                self.hip_plot.plot(frames, angles_data['right_hip'], 
                                 pen=pg.mkPen(color=self.colors['right_hip'], width=2),
                                 name='右髋关节')
        
        # 膝关节
        if self.joint_visibility.get('knee', True):
            if 'left_knee' in angles_data:
                self.knee_plot.plot(frames, angles_data['left_knee'], 
                                  pen=pg.mkPen(color=self.colors['left_knee'], width=2),
                                  name='左膝关节')
            if 'right_knee' in angles_data:
                self.knee_plot.plot(frames, angles_data['right_knee'], 
                                  pen=pg.mkPen(color=self.colors['right_knee'], width=2),
                                  name='右膝关节')
        
        # 踝关节
        if self.joint_visibility.get('ankle', True):
            if 'left_ankle' in angles_data:
                self.ankle_plot.plot(frames, angles_data['left_ankle'], 
                                   pen=pg.mkPen(color=self.colors['left_ankle'], width=2),
                                   name='左踝关节')
            if 'right_ankle' in angles_data:
                self.ankle_plot.plot(frames, angles_data['right_ankle'], 
                                   pen=pg.mkPen(color=self.colors['right_ankle'], width=2),
                                   name='右踝关节')
        
        # 躯干摆动
        if self.joint_visibility.get('trunk', True):
            if 'trunk_sway' in angles_data:
                self.trunk_plot.plot(frames, angles_data['trunk_sway'], 
                                   pen=pg.mkPen(color=self.colors['trunk_sway'], width=2),
                                   name='躯干摆动')
        
        # 肩关节
        if self.joint_visibility.get('shoulder', True):
            if 'left_shoulder' in angles_data:
                self.shoulder_plot.plot(frames, angles_data['left_shoulder'], 
                                      pen=pg.mkPen(color=self.colors['left_shoulder'], width=2),
                                      name='左肩关节')
            if 'right_shoulder' in angles_data:
                self.shoulder_plot.plot(frames, angles_data['right_shoulder'], 
                                      pen=pg.mkPen(color=self.colors['right_shoulder'], width=2),
                                      name='右肩关节')
    
    def update_cycle_plots(self, cycle_data):
        """更新步态周期图表"""
        self.cycle_overview_plot.clear()
        self.left_cycle_plot.clear()
        self.right_cycle_plot.clear()
        
        # 步态周期总览
        if 'normalized_cycles' in cycle_data:
            for i, cycle in enumerate(cycle_data['normalized_cycles']):
                if cycle.get('side') == 'left':
                    color = self.colors['left_knee']
                    name = f'左侧周期 {i+1}'
                else:
                    color = self.colors['right_knee']
                    name = f'右侧周期 {i+1}'
                
                normalized_time = np.linspace(0, 100, len(cycle['angles']))
                self.cycle_overview_plot.plot(normalized_time, cycle['angles'],
                                            pen=pg.mkPen(color=color, width=2),
                                            name=name)
        
        # 左右对比
        if 'left_cycles' in cycle_data:
            for i, cycle in enumerate(cycle_data['left_cycles']):
                normalized_time = np.linspace(0, 100, len(cycle))
                self.left_cycle_plot.plot(normalized_time, cycle,
                                        pen=pg.mkPen(color=self.colors['left_knee'], width=2),
                                        name=f'周期 {i+1}')
        
        if 'right_cycles' in cycle_data:
            for i, cycle in enumerate(cycle_data['right_cycles']):
                normalized_time = np.linspace(0, 100, len(cycle))
                self.right_cycle_plot.plot(normalized_time, cycle,
                                         pen=pg.mkPen(color=self.colors['right_knee'], width=2),
                                         name=f'周期 {i+1}')
    
    def update_phase_plots(self, phase_data):
        """更新支撑相图表"""
        self.phase_timeline_plot.clear()
        self.support_ratio_plot.clear()
        self.swing_ratio_plot.clear()
        
        # 支撑相时序图
        if 'timeline' in phase_data:
            timeline = phase_data['timeline']
            
            # 绘制支撑相区间
            for phase in timeline:
                if phase['type'] == 'support':
                    y_pos = 1 if phase['side'] == 'left' else 0
                    color = self.colors['left_hip'] if phase['side'] == 'left' else self.colors['right_hip']
                    
                    # 绘制支撑相矩形
                    x = [phase['start'], phase['end'], phase['end'], phase['start'], phase['start']]
                    y = [y_pos-0.1, y_pos-0.1, y_pos+0.1, y_pos+0.1, y_pos-0.1]
                    
                    self.phase_timeline_plot.plot(x, y, fillLevel=y_pos-0.1,
                                                brush=pg.mkBrush(color=color, alpha=128))
        
        # 支撑相比例图
        if 'support_ratios' in phase_data:
            cycles = list(range(1, len(phase_data['support_ratios']) + 1))
            self.support_ratio_plot.plot(cycles, [r*100 for r in phase_data['support_ratios']],
                                       pen=pg.mkPen(color=self.colors['left_hip'], width=3),
                                       symbol='o', symbolSize=8,
                                       name='支撑相比例')
        
        # 摆动相比例图
        if 'swing_ratios' in phase_data:
            cycles = list(range(1, len(phase_data['swing_ratios']) + 1))
            self.swing_ratio_plot.plot(cycles, [r*100 for r in phase_data['swing_ratios']],
                                     pen=pg.mkPen(color=self.colors['right_hip'], width=3),
                                     symbol='s', symbolSize=8,
                                     name='摆动相比例')
    
    def set_current_frame(self, frame):
        """设置当前帧位置"""
        self.current_frame = frame
        
        # 更新所有图表中的当前帧线
        for line in self.current_frame_lines.values():
            line.setPos(frame)
    
    def set_joint_visibility(self, joint, visible):
        """设置关节显示状态"""
        self.joint_visibility[joint] = visible
        # 重新绘制图表
        if hasattr(self, 'angle_data') and self.angle_data:
            raw_angles = self.angle_data.get('raw_angles', {})
            smoothed_angles = self.angle_data.get('smoothed_angles', {})
            self.update_angle_plots(raw_angles, smoothed_angles)
    
    def set_data_type(self, data_type):
        """设置数据类型"""
        self.data_type = data_type
        # 重新绘制图表
        if hasattr(self, 'angle_data') and self.angle_data:
            raw_angles = self.angle_data.get('raw_angles', {})
            smoothed_angles = self.angle_data.get('smoothed_angles', {})
            self.update_angle_plots(raw_angles, smoothed_angles)
    
    def export_charts(self, file_path):
        """导出图表"""
        try:
            # 获取当前显示的图表
            current_tab = self.tab_widget.currentWidget()
            
            if file_path.endswith('.png'):
                # 导出为PNG图片
                exporter = pg.exporters.ImageExporter(current_tab)
                exporter.export(file_path)
            elif file_path.endswith('.pdf'):
                # 导出为PDF
                exporter = pg.exporters.PDFExporter(current_tab)
                exporter.export(file_path)
            else:
                raise ValueError("不支持的文件格式")
                
        except Exception as e:
            raise Exception(f"导出图表失败: {str(e)}")
    
    def clear_all_plots(self):
        """清除所有图表"""
        for plot_widget in self.plots.values():
            plot_widget.clear()
        
        self.cycle_overview_plot.clear()
        self.left_cycle_plot.clear()
        self.right_cycle_plot.clear()
        self.phase_timeline_plot.clear()
        self.support_ratio_plot.clear()
        self.swing_ratio_plot.clear()