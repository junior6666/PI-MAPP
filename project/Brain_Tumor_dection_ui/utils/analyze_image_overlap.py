import os
import csv
from collections import defaultdict

def get_image_files_from_directory(dir_path):
    """从目录中获取所有图片文件名（不包括子目录）"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    image_files = set()
    
    if not os.path.exists(dir_path):
        print(f"警告：目录不存在 - {dir_path}")
        return image_files
    
    for file in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, file)):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.add(file)
    
    return image_files

def main():
    # 定义路径
    path1 = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE_3\Train\images"
    path2 = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE\Train\Glioma\images"
    path3 = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE\Train\Meningioma\images"
    path4 = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE\Train\Pituitary\images"
    
    # 获取所有图片文件
    print("正在扫描图片文件...")
    images_path1 = get_image_files_from_directory(path1)
    images_path2 = get_image_files_from_directory(path2)
    images_path3 = get_image_files_from_directory(path3)
    images_path4 = get_image_files_from_directory(path4)
    
    print(f"路径 1 (MRI_2D_DATA_USE_3): {len(images_path1)} 张图片")
    print(f"路径 2 (Glioma): {len(images_path2)} 张图片")
    print(f"路径 3 (Meningioma): {len(images_path3)} 张图片")
    print(f"路径 4 (Pituitary): {len(images_path4)} 张图片")
    print()
    
    # 将三个子类型路径合并
    images_use = images_path2 | images_path3 | images_path4
    
    # 计算交集和差集
    common_images = images_path1 & images_use
    only_in_path1 = images_path1 - images_use
    only_in_use = images_use - images_path1
    
    # 详细分析三个子类型
    only_in_glioma = images_path2 - images_path1
    only_in_meningioma = images_path3 - images_path1
    only_in_pituitary = images_path4 - images_path1
    
    # 打印报告
    print("=" * 80)
    print("分析报告")
    print("=" * 80)
    print(f"\n共有图片数量：{len(common_images)}")
    print(f"仅在 MRI_2D_DATA_USE_3 中的图片：{len(only_in_path1)}")
    print(f"仅在 MRI_2D_DATA_USE (三个子类型) 中的图片：{len(only_in_use)}")
    print()
    print("详细分布:")
    print(f"  - 仅在 Glioma 中：{len(only_in_glioma)}")
    print(f"  - 仅在 Meningioma 中：{len(only_in_meningioma)}")
    print(f"  - 仅在 Pituitary 中：{len(only_in_pituitary)}")
    print()
    
    # 计算重叠率
    if images_path1:
        overlap_rate_path1 = len(common_images) / len(images_path1) * 100
        print(f"MRI_2D_DATA_USE_3 的重叠率：{overlap_rate_path1:.2f}%")
    
    if images_use:
        overlap_rate_use = len(common_images) / len(images_use) * 100
        print(f"MRI_2D_DATA_USE 的重叠率：{overlap_rate_use:.2f}%")
    
    print("=" * 80)
    
    # 保存为 CSV
    output_csv = r"H:\pycharm_project\github_projects\PI-MAPP\project\Brain_Tumor_dection_ui\utils\image_analysis_report.csv"
    
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['分类', '文件名', '数量'])
        
        # 共有图片
        writer.writerow(['共有图片', '', len(common_images)])
        for img in sorted(common_images):
            writer.writerow(['共有图片', img, ''])
        
        writer.writerow([])
        
        # 仅在 path1 中
        writer.writerow(['仅在 MRI_2D_DATA_USE_3', '', len(only_in_path1)])
        for img in sorted(only_in_path1):
            writer.writerow(['仅在 MRI_2D_DATA_USE_3', img, ''])
        
        writer.writerow([])
        
        # 仅在 use 中
        writer.writerow(['仅在 MRI_2D_DATA_USE', '', len(only_in_use)])
        for img in sorted(only_in_use):
            writer.writerow(['仅在 MRI_2D_DATA_USE', img, ''])
        
        writer.writerow([])
        
        # 详细子类型
        writer.writerow(['仅在 Glioma', '', len(only_in_glioma)])
        for img in sorted(only_in_glioma):
            writer.writerow(['仅在 Glioma', img, ''])
        
        writer.writerow([])
        
        writer.writerow(['仅在 Meningioma', '', len(only_in_meningioma)])
        for img in sorted(only_in_meningioma):
            writer.writerow(['仅在 Meningioma', img, ''])
        
        writer.writerow([])
        
        writer.writerow(['仅在 Pituitary', '', len(only_in_pituitary)])
        for img in sorted(only_in_pituitary):
            writer.writerow(['仅在 Pituitary', img, ''])
    
    print(f"\n统计报告已保存至：{output_csv}")
    
    # 显示前 10 个共有和不同的图片示例
    if common_images:
        print(f"\n共有图片示例 (前 10 个): {list(sorted(common_images))[:10]}")
    
    if only_in_path1:
        print(f"仅在 MRI_2D_DATA_USE_3 中的图片示例 (前 10 个): {list(sorted(only_in_path1))[:10]}")
    
    if only_in_use:
        print(f"仅在 MRI_2D_DATA_USE 中的图片示例 (前 10 个): {list(sorted(only_in_use))[:10]}")

if __name__ == "__main__":
    main()
