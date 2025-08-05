import os
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw


def generate_test_image(path, width=100, height=100):
    """生成测试图像"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 90, 90], outline='red', width=2)
    img.save(path)
    return path


def get_detection_report_test_data():
    """生成检测报告测试数据"""
    # 创建临时图像
    with tempfile.TemporaryDirectory() as temp_dir:
        source_img = generate_test_image(os.path.join(temp_dir, "source.jpg"))
        result_img = generate_test_image(os.path.join(temp_dir, "result.jpg"))

        # 患者信息
        patient_info = {
            'name': '张三',
            'gender': '男',
            'age': 45,
            'medical_record_number': 'MR20230815001',
            'phone': '13800138000',
            'doctor': '李医生'
        }

        # 检测结果
        detection_results = [
            {'class': '增生性息肉', 'confidence': 0.92, 'coordinates': '(120, 80, 150, 110)'},
            {'class': '腺瘤性息肉', 'confidence': 0.87, 'coordinates': '(200, 150, 230, 180)'},
            {'class': '增生性息肉', 'confidence': 0.78, 'coordinates': '(300, 200, 330, 230)'}
        ]

        # 空检测结果
        empty_detection_results = []

        return {
            'patient_info': patient_info,
            'detection_results': detection_results,
            'empty_detection_results': empty_detection_results,
            'source_path': source_img,
            'result_path': result_img,
            'temp_dir': temp_dir
        }


def get_summary_report_test_data():
    """生成统计报告测试数据"""
    return {
        'statistics': {
            'total_detections': 128,
            'today_detections': 8,
            'avg_processing_time': 345.67,
            'polyp_statistics': [
                {'polyp_type': '增生性息肉', 'count': 76},
                {'polyp_type': '腺瘤性息肉', 'count': 42},
                {'polyp_type': '其他类型', 'count': 10}
            ]
        },
        'empty_statistics': {
            'total_detections': 0,
            'today_detections': 0,
            'avg_processing_time': 0,
            'polyp_statistics': []
        }
    }