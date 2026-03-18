
import os
import time
from ultralytics import YOLO

# 配置参数
DATA_YAML = "data.yaml"
IMG_SIZE = 512
BATCH_SIZE = 16
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.7

# 模型权重文件路径
MODEL_WEIGHTS = [
    "runs/detect/train_yolov8n/weights/best.pt",
    "runs/detect/train_yolov9t/weights/best.pt",
    "runs/detect/train_yolov10n/weights/best.pt",
    "runs/detect/train_yolo11n/weights/best.pt",
    "runs/detect/train_yolo26n/weights/best.pt",
]

# 验证设备配置
DEVICE_CONFIGS = [
    {"device": "0", "name": "GPU"},
    {"device": "cpu", "name": "CPU"},
]


def validate_model(model_path, device_config):
    """验证单个模型在指定设备上的性能"""
    print(f"\n{'=' * 60}")
    print(f"验证模型：{model_path}")
    print(f"设备：{device_config['name']} ({device_config['device']})")
    print(f"{'=' * 60}")

    try:
        # 加载模型
        print("正在加载模型...")
        model = YOLO(model_path)

        # 开始验证
        print("开始验证...")
        start_time = time.time()

        metrics = model.val(
            data=DATA_YAML,
            imgsz=IMG_SIZE,
            batch=BATCH_SIZE,
            conf=CONF_THRESHOLD,
            iou=IOU_THRESHOLD,
            device=device_config['device']
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        # 输出结果
        print(f"\n验证完成！耗时：{elapsed_time:.2f}秒")
        print(f"\n验证结果:")
        print(f"  - mAP50: {metrics.box.map50:.4f}")
        print(f"  - mAP50-95: {metrics.box.map:.4f}")
        print(f"  - Precision: {metrics.box.mp:.4f}")
        print(f"  - Recall: {metrics.box.mr:.4f}")

        return {
            'model': model_path,
            'device': device_config['name'],
            'map50': metrics.box.map50,
            'map': metrics.box.map,
            'precision': metrics.box.mp,
            'recall': metrics.box.mr,
            'time': elapsed_time
        }

    except Exception as e:
        print(f"验证失败：{str(e)}")
        return None


def main():
    """主函数：批量验证所有模型"""
    print("开始批量验证模型")
    print(f"数据集：{DATA_YAML}")
    print(f"图像尺寸：{IMG_SIZE}")
    print(f"批次大小：{BATCH_SIZE}")
    print(f"置信度阈值：{CONF_THRESHOLD}")
    print(f"IoU 阈值：{IOU_THRESHOLD}")

    results = []

    # 遍历所有设备配置
    for device_config in DEVICE_CONFIGS:
        print(f"\n\n{'#' * 70}")
        print(f"# 在 {device_config['name']} 设备上验证所有模型")
        print(f"{'#' * 70}")

        # 遍历所有模型
        for model_path in MODEL_WEIGHTS:
            if not os.path.exists(model_path):
                print(f"\n⚠️  警告：模型文件不存在 - {model_path}")
                continue

            result = validate_model(model_path, device_config)
            if result:
                results.append(result)

    # 输出汇总结果
    print(f"\n\n{'=' * 80}")
    print("验证结果汇总")
    print(f"{'=' * 80}")

    # 按设备分组显示结果
    for device_name in ["GPU", "CPU"]:
        device_results = [r for r in results if r['device'] == device_name]

        if device_results:
            print(f"\n{device_name} 设备结果:")
            print(f"{'模型':<50} {'mAP50':<10} {'mAP50-95':<10} {'耗时 (s)':<10}")
            print("-" * 80)

            for r in device_results:
                model_name = os.path.basename(os.path.dirname(r['model']))
                print(f"{model_name:<50} {r['map50']:<10.4f} {r['map']:<10.4f} {r['time']:<10.2f}")

    # 保存结果到文件
    output_file = "validation_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("模型验证结果汇总\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"数据集：{DATA_YAML}\n")
        f.write(f"图像尺寸：{IMG_SIZE}, 批次大小：{BATCH_SIZE}\n")
        f.write(f"置信度阈值：{CONF_THRESHOLD}, IoU 阈值：{IOU_THRESHOLD}\n\n")

        for device_name in ["GPU", "CPU"]:
            device_results = [r for r in results if r['device'] == device_name]
            if device_results:
                f.write(f"\n{device_name} 设备:\n")
                f.write("-" * 80 + "\n")
                for r in device_results:
                    model_name = os.path.basename(os.path.dirname(r['model']))
                    f.write(f"{model_name}:\n")
                    f.write(f"  mAP50: {r['map50']:.4f}\n")
                    f.write(f"  mAP50-95: {r['map']:.4f}\n")
                    f.write(f"  Precision: {r['precision']:.4f}\n")
                    f.write(f"  Recall: {r['recall']:.4f}\n")
                    f.write(f"  耗时：{r['time']:.2f}秒\n\n")

    print(f"\n结果已保存到：{output_file}")
    print("批量验证完成！")


if __name__ == "__main__":
    main()