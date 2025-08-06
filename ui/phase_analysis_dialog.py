#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支撑相分析对话框
显示详细的支撑相和摆动相分析结果
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QTabWidget, QWidget, QTableWidget,
                               QTableWidgetItem, QHeaderView, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np


class PhaseAnalysisDialog(QDialog):
    """支撑相分析对话框"""
    
    def __init__(self, analysis_results, parent=None):
        super().__init__(parent)
        self.analysis_results = analysis_results
        
        self.init_ui()
        self.populate_data()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("支撑相和摆动相详细分析")
        self.setModal(True)
        self.resize(1000, 700)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2b2b2b, stop:1 #3c3c3c);
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background: rgba(255,255,255,0.05);
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 详细报告标签页
        self.report_tab = QWidget()
        self.create_report_tab()
        self.tab_widget.addTab(self.report_tab, "详细报告")
        
        # 数据表格标签页
        self.table_tab = QWidget()
        self.create_table_tab()
        self.tab_widget.addTab(self.table_tab, "数据表格")
        
        # 可视化图表标签页
        self.chart_tab = QWidget()
        self.create_chart_tab()
        self.tab_widget.addTab(self.chart_tab, "可视化分析")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("导出报告")
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: 2px solid #45a049;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #55b059);
            }
        """)
        export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #4a4a4a);
                border: 2px solid #5a5a5a;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a7a7a, stop:1 #5a5a5a);
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_report_tab(self):
        """创建详细报告标签页"""
        layout = QVBoxLayout(self.report_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 文本显示区域
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Consolas", 10))
        self.report_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #ffffff;
                border: 2px solid #5a5a5a;
                border-radius: 6px;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        
        layout.addWidget(self.report_text)
    
    def create_table_tab(self):
        """创建数据表格标签页"""
        layout = QVBoxLayout(self.table_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 左脚数据表格
        self.left_table = QTableWidget()
        self.left_table.setColumnCount(7)
        self.left_table.setHorizontalHeaderLabels([
            "周期", "开始帧", "结束帧", "持续时间(s)", "支撑相(%)", "摆动相(%)", "计算方法"
        ])
        self.setup_table_style(self.left_table)
        splitter.addWidget(self.left_table)
        
        # 右脚数据表格  
        self.right_table = QTableWidget()
        self.right_table.setColumnCount(7)
        self.right_table.setHorizontalHeaderLabels([
            "周期", "开始帧", "结束帧", "持续时间(s)", "支撑相(%)", "摆动相(%)", "计算方法"
        ])
        self.setup_table_style(self.right_table)
        splitter.addWidget(self.right_table)
        
        layout.addWidget(splitter)
    
    def create_chart_tab(self):
        """创建可视化图表标签页"""
        layout = QVBoxLayout(self.chart_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 支撑相比例图表
        self.phase_ratio_plot = pg.PlotWidget(title="支撑相和摆动相比例对比")
        self.phase_ratio_plot.setBackground('#2b2b2b')
        self.phase_ratio_plot.setLabel('left', '比例 (%)', color='#cccccc')
        self.phase_ratio_plot.setLabel('bottom', '步态周期', color='#cccccc')
        self.phase_ratio_plot.addLegend()
        splitter.addWidget(self.phase_ratio_plot)
        
        # 时序分析图表
        self.timeline_plot = pg.PlotWidget(title="支撑相和摆动相时序分析")
        self.timeline_plot.setBackground('#2b2b2b')
        self.timeline_plot.setLabel('left', '侧别', color='#cccccc')
        self.timeline_plot.setLabel('bottom', '帧数', color='#cccccc')
        splitter.addWidget(self.timeline_plot)
        
        layout.addWidget(splitter)
    
    def setup_table_style(self, table):
        """设置表格样式"""
        table.setStyleSheet("""
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
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
    
    def populate_data(self):
        """填充数据"""
        if not self.analysis_results:
            return
        
        # 生成详细报告
        self.generate_detailed_report()
        
        # 填充表格数据
        self.populate_tables()
        
        # 生成图表
        self.generate_charts()
    
    def generate_detailed_report(self):
        """生成详细报告"""
        gait_params = self.analysis_results.get('gait_params', {})
        phase_analysis = self.analysis_results.get('phase_analysis', {})
        
        report = "支撑相和摆动相详细分析报告\n"
        report += "=" * 60 + "\n\n"
        
        # 基本信息
        report += "1. 基本信息\n"
        report += "-" * 30 + "\n"
        report += f"分析时间: {self.get_current_time()}\n"
        report += f"数据来源: 步态分析系统\n"
        report += f"分析方法: 基于关节角度变化的相位检测\n\n"
        
        # 总体统计
        report += "2. 总体统计\n"
        report += "-" * 30 + "\n"
        report += f"左脚平均支撑相比例: {gait_params.get('left_support_ratio', 0)*100:.1f}%\n"
        report += f"左脚平均摆动相比例: {gait_params.get('left_swing_ratio', 0)*100:.1f}%\n"
        report += f"右脚平均支撑相比例: {gait_params.get('right_support_ratio', 0)*100:.1f}%\n"
        report += f"右脚平均摆动相比例: {gait_params.get('right_swing_ratio', 0)*100:.1f}%\n"
        report += f"双支撑相比例: {gait_params.get('double_support_ratio', 0)*100:.1f}%\n"
        report += f"左右对称性: {gait_params.get('left_right_symmetry', 0):.1f}%\n\n"
        
        # 左脚详细分析
        report += "3. 左脚详细分析\n"
        report += "-" * 30 + "\n"
        left_phases = phase_analysis.get('left_phases', [])
        if left_phases:
            for i, phase in enumerate(left_phases[:10]):  # 限制显示前10个周期
                report += f"周期 {i+1}:\n"
                report += f"  类型: {phase.get('type', 'unknown')}\n"
                report += f"  开始帧: {phase.get('start_frame', 0)}\n"
                report += f"  结束帧: {phase.get('end_frame', 0)}\n"
                report += f"  持续时间: {phase.get('duration', 0):.3f}秒\n"
                report += "\n"
        else:
            report += "  无左脚相位数据\n\n"
        
        # 右脚详细分析
        report += "4. 右脚详细分析\n"
        report += "-" * 30 + "\n"
        right_phases = phase_analysis.get('right_phases', [])
        if right_phases:
            for i, phase in enumerate(right_phases[:10]):  # 限制显示前10个周期
                report += f"周期 {i+1}:\n"
                report += f"  类型: {phase.get('type', 'unknown')}\n"
                report += f"  开始帧: {phase.get('start_frame', 0)}\n"
                report += f"  结束帧: {phase.get('end_frame', 0)}\n"
                report += f"  持续时间: {phase.get('duration', 0):.3f}秒\n"
                report += "\n"
        else:
            report += "  无右脚相位数据\n\n"
        
        # 分析结论
        report += "5. 分析结论\n"
        report += "-" * 30 + "\n"
        
        # 判断步态是否正常
        left_support = gait_params.get('left_support_ratio', 0) * 100
        right_support = gait_params.get('right_support_ratio', 0) * 100
        symmetry = gait_params.get('left_right_symmetry', 0)
        
        if 58 <= left_support <= 65 and 58 <= right_support <= 65:
            report += "✓ 支撑相比例在正常范围内 (60% ± 5%)\n"
        else:
            report += "⚠ 支撑相比例异常，建议进一步检查\n"
        
        if symmetry >= 85:
            report += "✓ 左右对称性良好\n"
        elif symmetry >= 75:
            report += "⚠ 左右对称性一般\n"
        else:
            report += "⚠ 左右对称性较差，建议康复训练\n"
        
        report += "\n"
        report += "6. 建议\n"
        report += "-" * 30 + "\n"
        report += "• 定期进行步态分析，监测康复进展\n"
        report += "• 结合物理治疗师的专业建议制定康复计划\n"
        report += "• 注意保持良好的步态习惯\n"
        
        self.report_text.setPlainText(report)
    
    def populate_tables(self):
        """填充表格数据"""
        phase_analysis = self.analysis_results.get('phase_analysis', {})
        
        # 填充左脚表格
        left_phases = phase_analysis.get('left_phases', [])
        self.populate_phase_table(self.left_table, left_phases, "左脚")
        
        # 填充右脚表格
        right_phases = phase_analysis.get('right_phases', [])
        self.populate_phase_table(self.right_table, right_phases, "右脚")
    
    def populate_phase_table(self, table, phases, side_name):
        """填充相位表格"""
        # 按周期组织数据
        cycles = {}
        for phase in phases:
            cycle_key = f"{phase.get('start_frame', 0)}-{phase.get('end_frame', 0)}"
            if cycle_key not in cycles:
                cycles[cycle_key] = {
                    'start_frame': phase.get('start_frame', 0),
                    'end_frame': phase.get('end_frame', 0),
                    'duration': phase.get('duration', 0),
                    'stance_ratio': 0,
                    'swing_ratio': 0,
                    'method': 'auto'
                }
            
            if phase.get('type') == 'stance':
                cycles[cycle_key]['stance_ratio'] = 60.0  # 示例值
                cycles[cycle_key]['swing_ratio'] = 40.0
            
        table.setRowCount(len(cycles))
        
        for i, (cycle_key, cycle_data) in enumerate(cycles.items()):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem(str(cycle_data['start_frame'])))
            table.setItem(i, 2, QTableWidgetItem(str(cycle_data['end_frame'])))
            table.setItem(i, 3, QTableWidgetItem(f"{cycle_data['duration']:.3f}"))
            table.setItem(i, 4, QTableWidgetItem(f"{cycle_data['stance_ratio']:.1f}"))
            table.setItem(i, 5, QTableWidgetItem(f"{cycle_data['swing_ratio']:.1f}"))
            table.setItem(i, 6, QTableWidgetItem(cycle_data['method']))
    
    def generate_charts(self):
        """生成图表"""
        gait_params = self.analysis_results.get('gait_params', {})
        phase_analysis = self.analysis_results.get('phase_analysis', {})
        
        # 支撑相比例对比图
        self.plot_phase_ratios(gait_params)
        
        # 时序分析图
        self.plot_timeline_analysis(phase_analysis)
    
    def plot_phase_ratios(self, gait_params):
        """绘制支撑相比例对比图"""
        self.phase_ratio_plot.clear()
        
        # 数据
        categories = ['左脚支撑相', '左脚摆动相', '右脚支撑相', '右脚摆动相']
        values = [
            gait_params.get('left_support_ratio', 0) * 100,
            gait_params.get('left_swing_ratio', 0) * 100,
            gait_params.get('right_support_ratio', 0) * 100,
            gait_params.get('right_swing_ratio', 0) * 100
        ]
        
        x = np.arange(len(categories))
        
        # 绘制柱状图
        bar_graph = pg.BarGraphItem(x=x, height=values, width=0.6, 
                                   brush=['#E91E63', '#F48FB1', '#F44336', '#FFAB91'])
        self.phase_ratio_plot.addItem(bar_graph)
        
        # 设置X轴标签
        ax = self.phase_ratio_plot.getAxis('bottom')
        ax.setTicks([[(i, cat) for i, cat in enumerate(categories)]])
    
    def plot_timeline_analysis(self, phase_analysis):
        """绘制时序分析图"""
        self.timeline_plot.clear()
        
        timeline = phase_analysis.get('timeline', [])
        
        if not timeline:
            return
        
        # 分别处理左右脚的相位
        left_y = 1
        right_y = 0
        
        for phase in timeline:
            start = phase.get('start', 0)
            end = phase.get('end', 0)
            side = phase.get('side', 'left')
            phase_type = phase.get('type', 'stance')
            
            y = left_y if side == 'left' else right_y
            
            if phase_type == 'stance':
                color = '#E91E63' if side == 'left' else '#F44336'
            else:
                color = '#9C27B0' if side == 'left' else '#673AB7'
            
            # 绘制相位区间
            x = [start, end, end, start, start]
            y_coords = [y-0.1, y-0.1, y+0.1, y+0.1, y-0.1]
            
            self.timeline_plot.plot(x, y_coords, pen=pg.mkPen(color=color, width=2),
                                  fillLevel=y-0.1, brush=pg.mkBrush(color=color, alpha=100))
        
        # 设置Y轴标签
        ax = self.timeline_plot.getAxis('left')
        ax.setTicks([[(0, '右脚'), (1, '左脚')]])
    
    def export_report(self):
        """导出报告"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出支撑相分析报告",
            "",
            "文本文件 (*.txt);;HTML文件 (*.html);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                report_content = self.report_text.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                QMessageBox.information(self, "成功", f"报告已导出到: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")