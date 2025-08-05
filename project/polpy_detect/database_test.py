#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库功能测试脚本
"""

import sys
import os
from datetime import datetime
from database_setup import DatabaseManager
from database_operations import DatabaseOperations

def test_database_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    db_manager = DatabaseManager()
    
    if db_manager.test_connection():
        print("✅ 数据库连接成功")
        return db_manager
    else:
        print("❌ 数据库连接失败")
        return None

def test_save_detection_record(db_operations):
    """测试保存检测记录"""
    print("\n=== 测试保存检测记录 ===")
    
    # 模拟患者信息
    patient_info = {
        'name': '测试患者',
        'gender': '男',
        'age': 35,
        'medical_record_number': 'TEST001',
        'phone': '13800138000',
        'doctor': '张医生',
        'notes': '测试检测记录'
    }
    
    # 模拟检测结果
    detection_results = [
        {
            'class': '增生性息肉',
            'coordinates': '(100.5, 200.3, 300.7, 400.9)',
            'confidence': 0.85,
            'time_ms': 150
        },
        {
            'class': '腺瘤息肉',
            'coordinates': '(150.2, 250.8, 350.4, 450.1)',
            'confidence': 0.92,
            'time_ms': 200
        }
    ]
    
    success = db_operations.save_detection_record(
        patient_info, 
        detection_results, 
        'test_source.jpg', 
        'test_result.jpg',
        '图片'
    )
    
    if success:
        print("✅ 检测记录保存成功")
    else:
        print("❌ 检测记录保存失败")

def test_get_history(db_operations):
    """测试获取历史记录"""
    print("\n=== 测试获取历史记录 ===")
    
    records, total_count = db_operations.get_detection_history(
        search_keyword="", 
        search_field="患者信息", 
        date_from=None, 
        date_to=None, 
        page=1, 
        page_size=10
    )
    
    print(f"总记录数: {total_count}")
    print(f"当前页记录数: {len(records)}")
    
    if records:
        print("前3条记录:")
        for i, record in enumerate(records[:3]):
            print(f"  {i+1}. 患者: {record.get('patient_name', 'N/A')}, "
                  f"医生: {record.get('doctor_name', 'N/A')}, "
                  f"检测日期: {record.get('detection_date', 'N/A')}")
    else:
        print("没有找到记录")

def test_get_statistics(db_operations):
    """测试获取统计信息"""
    print("\n=== 测试获取统计信息 ===")
    
    stats = db_operations.get_statistics()
    
    print(f"总检测次数: {stats.get('total_detections', 0)}")
    print(f"今日检测次数: {stats.get('today_detections', 0)}")
    print(f"平均处理时间: {stats.get('avg_processing_time', 0):.2f}ms")
    
    polyp_stats = stats.get('polyp_statistics', [])
    if polyp_stats:
        print("息肉类型统计:")
        for stat in polyp_stats:
            print(f"  {stat['polyp_type']}: {stat['count']}个")
    
    type_stats = stats.get('type_statistics', [])
    if type_stats:
        print("检测类型统计:")
        for stat in type_stats:
            print(f"  {stat['detection_type']}: {stat['count']}次")

def test_export_records(db_operations):
    """测试导出记录"""
    print("\n=== 测试导出记录 ===")
    
    output_file = "test_export.json"
    success = db_operations.export_records_to_json(None, output_file)
    
    if success:
        print(f"✅ 记录导出成功: {output_file}")
        # 检查文件是否存在
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"文件大小: {file_size} 字节")
        else:
            print("❌ 导出文件不存在")
    else:
        print("❌ 记录导出失败")

def main():
    """主测试函数"""
    print("开始数据库功能测试...")
    
    # 测试数据库连接
    db_manager = test_database_connection()
    if not db_manager:
        print("数据库连接失败，无法继续测试")
        return
    
    # 创建数据库操作对象
    db_operations = DatabaseOperations(db_manager)
    
    # 测试保存检测记录
    test_save_detection_record(db_operations)
    
    # 测试获取历史记录
    test_get_history(db_operations)
    
    # 测试获取统计信息
    test_get_statistics(db_operations)
    
    # 测试导出记录
    test_export_records(db_operations)
    
    print("\n=== 测试完成 ===")
    
    # 关闭数据库连接
    db_manager.close()

if __name__ == "__main__":
    main() 