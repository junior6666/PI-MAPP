#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制面板组件
包含播放控制、帧导航、速度控制、显示选项等功能
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QPushButton, QSlider, QLabel, QComboBox, QCheckBox,
                               QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon


class ControlPanelWidget(QWidget):
    """控制面板组件"""
    
    # 信号定义
    play_pause_clicked = Signal()
    stop_clicked = Signal()
    frame_changed = Signal(int)
    speed_changed = Signal(float)
    joint_visibility_changed = Signal(str, bool)
    data_type_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.current_frame = 0
        self.max_frame = 0
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 播放控制组
        playback_group = self.create_playback_controls()
        layout.addWidget(playback_group)
        
        # 帧控制组
        frame_group = self.create_frame_controls()
        layout.addWidget(frame_group)
        
        # 显示选项组
        display_group = self.create_display_options()
        layout.addWidget(display_group)
        
        # 分析选项组
        analysis_group = self.create_analysis_options()
        layout.addWidget(analysis_group)
        
        # 添加弹性空间
        layout.addStretch()
    
    def create_playback_controls(self):
        """创建播放控制组"""
        group = QGroupBox("播放控制")
        layout = QVBoxLayout(group)
        
        # 播放按钮行
        button_layout = QHBoxLayout()
        
        # 播放/暂停按钮
        self.play_pause_btn = QPushButton("▶ 播放")
        self.play_pause_btn.setMinimumHeight(40)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: 2px solid #45a049;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #55b059);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3CAF40, stop:1 #359039);
            }
        """)
        button_layout.addWidget(self.play_pause_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f44336, stop:1 #d32f2f);
                border: 2px solid #d32f2f;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f55346, stop:1 #e33f3f);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e43326, stop:1 #c31f1f);
            }
        """)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # 播放速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("播放速度:"))
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x", "3.0x"])
        self.speed_combo.setCurrentText("1.0x")
        speed_layout.addWidget(self.speed_combo)
        
        layout.addLayout(speed_layout)
        
        return group
    
    def create_frame_controls(self):
        """创建帧控制组"""
        group = QGroupBox("帧控制")
        layout = QVBoxLayout(group)
        
        # 帧信息显示
        self.frame_info_label = QLabel("帧: 0 / 0")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #66bb6a;
                padding: 5px;
                background: rgba(102, 187, 106, 0.1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.frame_info_label)
        
        # 帧滑块
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)
        layout.addWidget(self.frame_slider)
        
        # 精确帧控制
        frame_control_layout = QHBoxLayout()
        
        # 上一帧按钮
        prev_frame_btn = QPushButton("◀")
        prev_frame_btn.setMaximumWidth(40)
        prev_frame_btn.clicked.connect(self.prev_frame)
        frame_control_layout.addWidget(prev_frame_btn)
        
        # 帧数输入框
        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setMinimum(0)
        self.frame_spinbox.setMaximum(0)
        frame_control_layout.addWidget(self.frame_spinbox)
        
        # 下一帧按钮
        next_frame_btn = QPushButton("▶")
        next_frame_btn.setMaximumWidth(40)
        next_frame_btn.clicked.connect(self.next_frame)
        frame_control_layout.addWidget(next_frame_btn)
        
        layout.addLayout(frame_control_layout)
        
        return group
    
    def create_display_options(self):
        """创建显示选项组"""
        group = QGroupBox("显示选项")
        layout = QVBoxLayout(group)
        
        # 关节显示选择
        joints_layout = QVBoxLayout()
        joints_layout.addWidget(QLabel("显示关节:"))
        
        self.joint_checkboxes = {}
        joint_names = [
            ("hip", "髋关节"),
            ("knee", "膝关节"),
            ("ankle", "踝关节"),
            ("trunk", "躯干摆动"),
            ("shoulder", "肩关节"),
            ("elbow", "肘关节")
        ]
        
        for joint_key, joint_name in joint_names:
            checkbox = QCheckBox(joint_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda state, key=joint_key: self.on_joint_visibility_changed(key, state == Qt.Checked)
            )
            self.joint_checkboxes[joint_key] = checkbox
            joints_layout.addWidget(checkbox)
        
        layout.addLayout(joints_layout)
        
        # 数据类型选择
        data_type_layout = QHBoxLayout()
        data_type_layout.addWidget(QLabel("数据类型:"))
        
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["原始数据", "平滑数据"])
        self.data_type_combo.setCurrentText("平滑数据")
        data_type_layout.addWidget(self.data_type_combo)
        
        layout.addLayout(data_type_layout)
        
        return group
    
    def create_analysis_options(self):
        """创建分析选项组"""
        group = QGroupBox("分析选项")
        layout = QVBoxLayout(group)
        
        # 平滑参数
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(QLabel("平滑强度:"))
        
        self.smooth_spinbox = QDoubleSpinBox()
        self.smooth_spinbox.setMinimum(0.1)
        self.smooth_spinbox.setMaximum(10.0)
        self.smooth_spinbox.setValue(2.0)
        self.smooth_spinbox.setSingleStep(0.1)
        smooth_layout.addWidget(self.smooth_spinbox)
        
        layout.addLayout(smooth_layout)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("检测阈值:"))
        
        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setMinimum(0.1)
        self.threshold_spinbox.setMaximum(1.0)
        self.threshold_spinbox.setValue(0.5)
        self.threshold_spinbox.setSingleStep(0.05)
        threshold_layout.addWidget(self.threshold_spinbox)
        
        layout.addLayout(threshold_layout)
        
        # 显示支撑相
        self.show_support_phase = QCheckBox("显示支撑相标记")
        self.show_support_phase.setChecked(True)
        layout.addWidget(self.show_support_phase)
        
        # 显示步态周期
        self.show_gait_cycle = QCheckBox("显示步态周期")
        self.show_gait_cycle.setChecked(True)
        layout.addWidget(self.show_gait_cycle)
        
        return group
    
    def setup_connections(self):
        """设置信号连接"""
        # 播放控制
        self.play_pause_btn.clicked.connect(self.on_play_pause_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        
        # 帧控制
        self.frame_slider.valueChanged.connect(self.on_frame_slider_changed)
        self.frame_spinbox.valueChanged.connect(self.on_frame_spinbox_changed)
        
        # 播放速度
        self.speed_combo.currentTextChanged.connect(self.on_speed_changed)
        
        # 数据类型
        self.data_type_combo.currentTextChanged.connect(self.on_data_type_changed)
    
    def on_play_pause_clicked(self):
        """播放/暂停按钮点击"""
        self.play_pause_clicked.emit()
    
    def on_stop_clicked(self):
        """停止按钮点击"""
        self.stop_clicked.emit()
    
    def on_frame_slider_changed(self, value):
        """帧滑块值变化"""
        if value != self.current_frame:
            self.current_frame = value
            self.frame_spinbox.blockSignals(True)
            self.frame_spinbox.setValue(value)
            self.frame_spinbox.blockSignals(False)
            self.update_frame_info()
            self.frame_changed.emit(value)
    
    def on_frame_spinbox_changed(self, value):
        """帧数输入框值变化"""
        if value != self.current_frame:
            self.current_frame = value
            self.frame_slider.blockSignals(True)
            self.frame_slider.setValue(value)
            self.frame_slider.blockSignals(False)
            self.update_frame_info()
            self.frame_changed.emit(value)
    
    def on_speed_changed(self, text):
        """播放速度变化"""
        try:
            speed = float(text.replace('x', ''))
            self.speed_changed.emit(speed)
        except ValueError:
            pass
    
    def on_joint_visibility_changed(self, joint_key, visible):
        """关节显示状态变化"""
        self.joint_visibility_changed.emit(joint_key, visible)
    
    def on_data_type_changed(self, text):
        """数据类型变化"""
        data_type = "smoothed" if text == "平滑数据" else "raw"
        self.data_type_changed.emit(data_type)
    
    def prev_frame(self):
        """上一帧"""
        if self.current_frame > 0:
            self.set_current_frame(self.current_frame - 1)
    
    def next_frame(self):
        """下一帧"""
        if self.current_frame < self.max_frame:
            self.set_current_frame(self.current_frame + 1)
    
    def set_frame_range(self, min_frame, max_frame):
        """设置帧范围"""
        self.max_frame = max_frame
        
        self.frame_slider.setMinimum(min_frame)
        self.frame_slider.setMaximum(max_frame)
        
        self.frame_spinbox.setMinimum(min_frame)
        self.frame_spinbox.setMaximum(max_frame)
        
        self.update_frame_info()
    
    def set_current_frame(self, frame):
        """设置当前帧"""
        if frame != self.current_frame:
            self.current_frame = frame
            
            # 更新控件
            self.frame_slider.blockSignals(True)
            self.frame_slider.setValue(frame)
            self.frame_slider.blockSignals(False)
            
            self.frame_spinbox.blockSignals(True)
            self.frame_spinbox.setValue(frame)
            self.frame_spinbox.blockSignals(False)
            
            self.update_frame_info()
    
    def update_frame_info(self):
        """更新帧信息显示"""
        self.frame_info_label.setText(f"帧: {self.current_frame} / {self.max_frame}")
    
    def update_play_button(self, is_playing):
        """更新播放按钮状态"""
        self.is_playing = is_playing
        if is_playing:
            self.play_pause_btn.setText("⏸ 暂停")
            self.play_pause_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12pt;
                    font-weight: bold;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FF9800, stop:1 #F57C00);
                    border: 2px solid #F57C00;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FFA800, stop:1 #F58C00);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #E88800, stop:1 #E56C00);
                }
            """)
        else:
            self.play_pause_btn.setText("▶ 播放")
            self.play_pause_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12pt;
                    font-weight: bold;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    border: 2px solid #45a049;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5CBF60, stop:1 #55b059);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3CAF40, stop:1 #359039);
                }
            """)
    
    def get_joint_visibility(self):
        """获取关节显示状态"""
        return {key: checkbox.isChecked() for key, checkbox in self.joint_checkboxes.items()}
    
    def get_data_type(self):
        """获取数据类型"""
        return "smoothed" if self.data_type_combo.currentText() == "平滑数据" else "raw"
    
    def get_smooth_strength(self):
        """获取平滑强度"""
        return self.smooth_spinbox.value()
    
    def get_threshold(self):
        """获取检测阈值"""
        return self.threshold_spinbox.value()
    
    def is_support_phase_visible(self):
        """是否显示支撑相"""
        return self.show_support_phase.isChecked()
    
    def is_gait_cycle_visible(self):
        """是否显示步态周期"""
        return self.show_gait_cycle.isChecked()