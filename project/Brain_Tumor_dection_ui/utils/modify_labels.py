"""
标签文件类别编号修改脚本
将 Pituitary 类别的标签从 3 改为 2
"""

import os
from pathlib import Path


def modify_label_files(label_dir, old_class_id=3, new_class_id=2):
    """
    修改指定目录下所有标签文件中的类别编号
    
    Args:
        label_dir: 标签文件目录路径
        old_class_id: 原始类别编号
        new_class_id: 新的类别编号
    """
    label_path = Path(label_dir)
    
    if not label_path.exists():
        print(f"错误：目录不存在 - {label_dir}")
        return
    
    # 获取所有txt 文件
    txt_files = list(label_path.glob("*.txt"))
    
    if not txt_files:
        print(f"警告：在 {label_dir} 下未找到 txt 文件")
        return
    
    modified_count = 0
    total_count = len(txt_files)
    
    print(f"找到 {total_count} 个标签文件")
    print(f"开始修改：类别 {old_class_id} -> {new_class_id}")
    print("-" * 50)
    
    for txt_file in txt_files:
        try:
            # 读取文件内容
            with open(txt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified_lines = []
            file_modified = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    
                    # 如果匹配到目标类别编号，则修改
                    if class_id == old_class_id:
                        parts[0] = str(new_class_id)
                        file_modified = True
                    
                    # 重新组合行
                    modified_line = ' '.join(parts)
                    modified_lines.append(modified_line)
                else:
                    # 保持原样
                    modified_lines.append(line)
            
            # 如果文件有修改，则写回
            if file_modified:
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(modified_lines) + '\n')
                modified_count += 1
                print(f"✓ 已修改：{txt_file.name}")
            else:
                print(f"- 无需修改：{txt_file.name}")
                
        except Exception as e:
            print(f"✗ 处理失败 {txt_file.name}: {str(e)}")
    
    print("-" * 50)
    print(f"完成！共 {total_count} 个文件，已修改 {modified_count} 个文件")


def main():
    # 配置路径
    # label_directory = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE\Train\Pituitary\labels"
    label_directory = r"H:\YOLO_Datasets\BrainTumor\MRI_2D_DATA_USE\Val\Pituitary\labels"

    # 验证路径是否存在
    if not os.path.exists(label_directory):
        print(f"错误：标签目录不存在！")
        print(f"路径：{label_directory}")
        print("\n请确认路径是否正确，或修改脚本中的 label_directory 变量")
        return
    
    print("=" * 50)
    print("脑肿瘤标签类别编号修改工具")
    print("=" * 50)
    print(f"\n目标目录：{label_directory}")
    print(f"修改内容：类别 3 (Pituitary) -> 类别 2")
    print()
    
    # 执行修改
    modify_label_files(label_directory, old_class_id=3, new_class_id=2)
    
    print("\n提示：修改完成后，请检查 data.yaml 中的配置是否正确")
    print("当前配置：nc: 3, names: [glioma, meningioma, pituitary]")


if __name__ == "__main__":
    main()
