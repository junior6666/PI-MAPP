# convert_pt_to_onnx.py

import os
from pathlib import Path
from ultralytics import YOLO

# 配置路径
PT_DIR = r"H:\pycharm_project\github_projects\PI-MAPP\project\Brain_Tumor_dection_ui\pt_models"
ONNX_DIR = r"H:\pycharm_project\github_projects\PI-MAPP\project\Brain_Tumor_dection_ui\onnx_models"

def main():
    pt_dir = Path(PT_DIR)
    onnx_dir = Path(ONNX_DIR)

    # 创建 ONNX 输出目录（如果不存在）
    onnx_dir.mkdir(parents=True, exist_ok=True)

    if not pt_dir.exists():
        print(f"错误：PT 模型目录不存在！{pt_dir}")
        return

    # 查找所有 .pt 或 .pth 文件
    pt_files = list(pt_dir.glob("*.pt")) + list(pt_dir.glob("*.pth"))
    if not pt_files:
        print(f"警告：在 {pt_dir} 中未找到任何 .pt 或 .pth 文件。")
        return

    print(f"发现 {len(pt_files)} 个模型文件，开始转换为 ONNX...")

    for pt_file in pt_files:
        try:
            print(f"\n正在加载模型: {pt_file.name}")
            model = YOLO(str(pt_file))

            # 构造输出 ONNX 路径
            onnx_file = onnx_dir / (pt_file.stem + ".onnx")

            print(f"正在导出为 ONNX: {onnx_file}")
            model.export(
                format="onnx",
                imgsz=640,          # 可根据你的模型调整
                dynamic=False,      # 如需动态输入尺寸，设为 True
                simplify=True,      # 启用 ONNX 简化（推荐）
                opset=12,           # 兼容性较好的 opset
                nms=False           # 若需要 NMS 后处理，可设为 True
            )

            # Ultralytics 默认会将 ONNX 保存在原模型同名路径下（如 yolov8n.onnx）
            # 所以我们需要将其移动到目标目录
            default_onnx = pt_file.with_suffix(".onnx")
            if default_onnx.exists():
                # 移动到目标目录（覆盖已存在文件）
                target_path = onnx_dir / default_onnx.name
                default_onnx.rename(target_path)
                print(f"✅ 已保存: {target_path}")
            else:
                print(f"⚠️  警告: 未找到生成的 ONNX 文件 ({default_onnx})")

        except Exception as e:
            print(f"❌ 转换失败 {pt_file.name}: {e}")

    print("\n✅ 所有模型转换完成！")

if __name__ == "__main__":
    main()