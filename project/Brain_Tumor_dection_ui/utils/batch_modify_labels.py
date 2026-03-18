"""
批量修改 YOLO 格式标签文件
功能：删除所有类别编号为 3 的标注数据
目标目录：H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE_3\Train\labels
"""

import os
from pathlib import Path


def modify_label_file(file_path):
    """
    修改单个标签文件，删除类别编号为 3 的行
    
    Args:
        file_path: 标签文件路径
        
    Returns:
        tuple: (修改前的行数，修改后的行数，是否被修改)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_count = len(lines)
        
        # 过滤掉类别编号为 3 的行
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:  # 跳过空行
                continue
            
            parts = line.split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                if class_id != 3:  # 保留不是类别 3 的数据
                    filtered_lines.append(line)
        
        modified_count = len(filtered_lines)
        
        # 如果有删除的行，则写回文件
        if modified_count < original_count:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(filtered_lines))
                if filtered_lines:  # 如果还有内容，末尾添加换行符
                    f.write('\n')
            
            return original_count, modified_count, True
        else:
            return original_count, modified_count, False
            
    except Exception as e:
        print(f"处理文件 {file_path} 时出错：{e}")
        return 0, 0, False


def batch_modify_labels(labels_dir):
    """
    批量修改目录下所有标签文件
    
    Args:
        labels_dir: 标签目录路径
    """
    labels_path = Path(labels_dir)
    
    if not labels_path.exists():
        print(f"错误：目录不存在 - {labels_dir}")
        return
    
    # 获取所有 txt 文件
    txt_files = list(labels_path.glob('*.txt'))
    total_files = len(txt_files)
    
    print(f"找到 {total_files} 个标签文件")
    print(f"开始处理目录：{labels_dir}")
    print("-" * 60)
    
    modified_files = 0
    total_removed_annotations = 0
    
    for idx, txt_file in enumerate(txt_files, 1):
        original_count, modified_count, is_modified = modify_label_file(txt_file)
        
        if is_modified:
            modified_files += 1
            removed_count = original_count - modified_count
            total_removed_annotations += removed_count
            print(f"[{idx}/{total_files}] 已修改：{txt_file.name} - 删除 {removed_count} 条类别 3 的标注 "
                  f"(剩余：{modified_count} 条)")
        else:
            print(f"[{idx}/{total_files}] 无需修改：{txt_file.name} (无类别 3 的标注)")
    
    print("-" * 60)
    print(f"处理完成！")
    print(f"总文件数：{total_files}")
    print(f"已修改文件数：{modified_files}")
    print(f"未修改文件数：{total_files - modified_files}")
    print(f"删除的标注总数：{total_removed_annotations}")


if __name__ == "__main__":
    # 指定标签目录
    labels_directory = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE_3\Val\labels"
    
    print("=" * 60)
    print("YOLO 标签批量修改工具")
    print("功能：删除所有类别编号为 3 的标注数据")
    print("=" * 60)
    
    batch_modify_labels(labels_directory)
    
    print("\n按 Enter 键退出...")
    input()
