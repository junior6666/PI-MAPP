from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import hashlib

# # 导入并应用 ReportLab 兼容性补丁
# try:
#     from reportlab_patch import apply_reportlab_patch
#     apply_reportlab_patch()
# except ImportError:
#     print("警告: 无法导入 reportlab_patch，将使用内置补丁")
#     # 内置补丁
#     try:
#         import reportlab.pdfbase.pdfdoc as pdfdoc
#         def compatible_md5(data=None):
#             if data:
#                 return hashlib.md5(data.encode('utf-8') if isinstance(data, str) else data)
#             else:
#                 return hashlib.md5()
#         pdfdoc.md5 = compatible_md5
#     except Exception as e:
#         print(f"应用内置补丁失败: {e}")
pdfmetrics.registerFont(TTFont('MSYH',  r'H:\pycharm_project\PI-MAPP\project\polpy_detect\font\msyh.ttc'))      # 正文细体
pdfmetrics.registerFont(TTFont('MSYH-B', r'H:\pycharm_project\PI-MAPP\project\polpy_detect\font\msyhbd.ttc'))   # 粗体
class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='MSYH-B'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue,
            fontName='MSYH-B'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            fontName='MSYH'
        ))

        self.styles.add(ParagraphStyle(
            name='TableTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue,
            fontName='MSYH-B'
        ))
    
    def generate_detection_report(self, patient_info, detection_results, source_path, result_path, output_path):
        """生成检测报告"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # 报告标题
            title = Paragraph("息肉智能检测报告", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # 报告信息
            report_info = [
                ["报告编号", f"RPT{datetime.now().strftime('%Y%m%d%H%M%S')}"],
                ["生成时间", datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')],
                ["检测系统", "息肉智能检测系统"]
            ]
            
            report_table = Table(report_info, colWidths=[2*inch, 4*inch])
            report_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'MSYH'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(report_table)
            story.append(Spacer(1, 20))
            
            # 患者信息
            patient_title = Paragraph("患者信息", self.styles['CustomSubtitle'])
            story.append(patient_title)
            
            patient_data = [
                ["患者姓名", patient_info.get('name', '')],
                ["性别", patient_info.get('gender', '')],
                ["年龄", str(patient_info.get('age', ''))],
                ["病历号", patient_info.get('medical_record_number', '')],
                ["联系电话", patient_info.get('phone', '')],
                ["诊断医生", patient_info.get('doctor', '')],
                ["检测日期", datetime.now().strftime('%Y年%m月%d日')]
            ]
            
            patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'MSYH'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(patient_table)
            story.append(Spacer(1, 20))
            
            # 检测结果
            if detection_results:
                results_title = Paragraph("检测结果", self.styles['CustomSubtitle'])
                story.append(results_title)
                
                # 检测结果表格
                results_data = [["序号", "息肉类型", "置信度", "位置坐标"]]
                for i, result in enumerate(detection_results, 1):
                    results_data.append([
                        str(i),
                        result.get('class', ''),
                        f"{result.get('confidence', 0):.2%}",
                        result.get('coordinates', '')
                    ])
                
                results_table = Table(results_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 2*inch])
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'MSYH'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(results_table)
                story.append(Spacer(1, 20))
            
            # 图像信息
            if source_path and os.path.exists(source_path):
                image_title = Paragraph("检测图像", self.styles['CustomSubtitle'])
                story.append(image_title)
                
                # 添加原图
                if os.path.exists(source_path):
                    try:
                        img = Image(source_path, width=3*inch, height=2*inch)
                        story.append(img)
                        story.append(Spacer(1, 10))
                    except Exception as e:
                        story.append(Paragraph(f"原图加载失败: {str(e)}", self.styles['CustomBody']))
                
                # 添加结果图
                if result_path and os.path.exists(result_path):
                    try:
                        result_img = Image(result_path, width=3*inch, height=2*inch)
                        story.append(result_img)
                        story.append(Spacer(1, 10))
                    except Exception as e:
                        story.append(Paragraph(f"结果图加载失败: {str(e)}", self.styles['CustomBody']))
            
            # 统计信息
            if detection_results:
                stats_title = Paragraph("统计信息", self.styles['CustomSubtitle'])
                story.append(stats_title)
                
                total_polyps = len(detection_results)
                hyperplastic_count = sum(1 for r in detection_results if '增生性' in r.get('class', ''))
                adenoma_count = sum(1 for r in detection_results if '腺瘤性' in r.get('class', ''))
                
                stats_data = [
                    ["检测总数", str(total_polyps)],
                    ["增生性息肉", str(hyperplastic_count)],
                    ["腺瘤性息肉", str(adenoma_count)],
                    ["平均置信度", f"{sum(r.get('confidence', 0) for r in detection_results) / len(detection_results):.2%}"]
                ]
                
                stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'MSYH'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(stats_table)
                story.append(Spacer(1, 20))
            
            # 结论和建议
            conclusion_title = Paragraph("结论与建议", self.styles['CustomSubtitle'])
            story.append(conclusion_title)
            
            if detection_results:
                conclusion_text = f"""
                本次检测共发现{len(detection_results)}个息肉。建议根据检测结果进行进一步诊断和治疗。
                请咨询专业医生获取详细的医疗建议。
                """
            else:
                conclusion_text = "本次检测未发现息肉。建议定期进行健康检查。"
            
            conclusion_para = Paragraph(conclusion_text, self.styles['CustomBody'])
            story.append(conclusion_para)
            story.append(Spacer(1, 20))
            
            # 注意事项
            notes_title = Paragraph("注意事项", self.styles['CustomSubtitle'])
            story.append(notes_title)
            
            notes_text = """
            1. 本报告仅供参考，不能替代专业医生的诊断。
            2. 如发现异常，请及时就医。
            3. 建议定期进行健康检查。
            4. 本系统检测结果可能存在误差，请以医生诊断为准。
            """
            
            notes_para = Paragraph(notes_text, self.styles['CustomBody'])
            story.append(notes_para)
            story.append(Spacer(1, 20))
            
            # 页脚
            footer = Paragraph(
                f"报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')} | "
                "基于YOLO+PySide6+MySQL的息肉智能检测系统 v1.0",
                self.styles['CustomBody']
            )
            story.append(footer)
            
            # 生成PDF
            doc.build(story)
            
        except Exception as e:
            raise Exception(f"生成PDF报告时出错: {str(e)}")
    
    def generate_summary_report(self, statistics, output_path):
        """生成统计报告"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # 报告标题
        title = Paragraph("息肉检测统计报告", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # 总体统计
        summary_title = Paragraph("总体统计", self.styles['CustomSubtitle'])
        story.append(summary_title)
        
        summary_data = [
            ["总检测次数", str(statistics.get('total_detections', 0))],
            ["今日检测次数", str(statistics.get('today_detections', 0))],
            ["平均处理时间(ms)", f"{statistics.get('avg_processing_time', 0):.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'MSYH'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # 息肉类型统计
        polyp_title = Paragraph("息肉类型统计", self.styles['CustomSubtitle'])
        story.append(polyp_title)
        
        polyp_stats = statistics.get('polyp_statistics', [])
        if polyp_stats:
            polyp_data = [["息肉类型", "检测数量"]]
            for stat in polyp_stats:
                polyp_data.append([stat['polyp_type'], str(stat['count'])])
            
            polyp_table = Table(polyp_data, colWidths=[3*inch, 3*inch])
            polyp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'MSYH-B'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white)
            ]))
            story.append(polyp_table)
        else:
            no_polyp = Paragraph("暂无息肉检测数据", self.styles['CustomBody'])
            story.append(no_polyp)
        
        story.append(Spacer(1, 20))
        
        # 生成时间
        time_text = f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
        time_para = Paragraph(time_text, self.styles['CustomBody'])
        story.append(time_para)
        
        # 生成PDF
        doc.build(story)
        return output_path 