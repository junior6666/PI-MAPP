import os
import csv
from datetime import datetime
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("警告: 未安装ultralytics库，类别信息将无法获取")
    YOLO = None


def analyze_pt_files_simple(directory_path, output_file="YOLO_pt_files_report.csv"):
    """
    简化版本的PT文件分析
    """
    pt_files = list(Path(directory_path).rglob("*.pt"))

    if not pt_files:
        print(f"在目录 {directory_path} 中未找到任何.pt文件")
        return

    print(f"找到 {len(pt_files)} 个.pt文件")

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['文件名', '大小(MB)', '修改日期', '类别数量', '类别信息']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, pt_file in enumerate(pt_files, 1):
            print(f"正在处理 ({i}/{len(pt_files)}): {pt_file}")

            try:
                # 基本信息
                file_stat = os.stat(pt_file)
                file_size_mb = round(file_stat.st_size / (1024 * 1024), 2)
                mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                # 类别信息
                class_names = {}
                if YOLO is not None:
                    try:
                        model = YOLO(str(pt_file))
                        class_names = model.names
                    except Exception as e:
                        class_names = {"error": str(e)}

                # 写入CSV行
                writer.writerow({
                    '文件名': os.path.basename(pt_file),
                    '大小(MB)': file_size_mb,
                    '修改日期': mod_time,
                    '类别数量': len(class_names) if isinstance(class_names, dict) else 0,
                    '类别信息': str(class_names)
                })

            except Exception as e:
                print(f"处理文件 {pt_file} 时出错: {e}")
                writer.writerow({
                    '文件名': os.path.basename(pt_file),
                    '大小(MB)': 0,
                    '修改日期': 'N/A',
                    '类别数量': 0,
                    '类别信息': f"Error: {e}"
                })

    print(f"分析报告已保存到: {output_file}")


# 使用示例
if __name__ == "__main__":
    directory = r'H:\pycharm_project\github_projects\PI-MAPP\project\universal_object_detection_plus\YOLO_pt'
    analyze_pt_files_simple(directory)
    #https://github.com/JingW-ui/Pl-MAPP/releases/download/pt_download/
