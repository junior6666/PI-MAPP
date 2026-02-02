import cv2
import nibabel as nib
import numpy as np
from ultralytics import YOLO
import os
import time
from dataclasses import dataclass
from typing import Tuple, Optional, List


# ----------------------------
# 配置和数据结构
# ----------------------------
@dataclass
class Config:
    model_path: str = r'H:\pycharm_project\PI-MAPP\project\detection_train\tumor\runs\detect\train_yolo12_try_owndata2\weights\best.pt'
    nii_path: str = r'H:\data\QSM\SCA3_Data_raw\anat_niigz\SCA3_0001\SCA3_0001.nii.gz'
    output_project: str = '../best_slices_results_test/SCA3_0001'
    conf: float = 0.65

    # 优化参数配置
    AXIAL_SAMPLING_STEP: int = 2
    SAGITTAL_SAMPLING_STEP: int = 2
    CORONAL_SAMPLING_STEP: int = 2
    SLICE_THRESHOLD: float = 0.05
    STD_THRESHOLD: float = 5.0
    REFINE_RADIUS: int = 1
    HIGH_CONF_FOR_OTHER_AXES: float = 0.92


@dataclass
class SearchResult:
    success: bool
    best_slice_idx: Optional[int] = None
    best_axis: Optional[str] = None
    max_area: float = 0.0
    processing_time: float = 0.0
    slices_processed: int = 0
    slices_skipped: int = 0
    has_tumor: bool = True
    message: str = ""


# ----------------------------
# 全局变量和初始化
# ----------------------------
config = Config()
model = None
data = None
I, J, K = 0, 0, 0
spacing = None


def initialize_system():
    """初始化模型和数据处理系统"""
    global model, data, I, J, K, spacing

    print("🔄 Loading model and data...")

    # 加载模型
    if model is None:
        try:
            model = YOLO(config.model_path)
            print("✅ Model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    # 加载数据
    if data is None:
        try:
            img = nib.load(config.nii_path)
            data_raw = img.get_fdata()
            spacing = img.header.get_zooms()

            # 归一化到 uint8
            if data_raw.dtype != np.uint8:
                data_raw = np.clip(data_raw, 0, np.percentile(data_raw, 99))
                data_raw = ((data_raw - data_raw.min()) / (data_raw.max() - data_raw.min()) * 255).astype(np.uint8)

            data = data_raw
            I, J, K = data.shape
            os.makedirs(config.output_project, exist_ok=True)

            print(f"✅ Data loaded: shape={data.shape}, spacing={spacing}")
        except Exception as e:
            raise RuntimeError(f"Failed to load NIfTI data: {e}")


# ----------------------------
# 工具函数
# ----------------------------
def pre_filter_slice(slice_2d, non_zero_thresh=config.SLICE_THRESHOLD, std_thresh=config.STD_THRESHOLD):
    """预过滤切片：基于非零比例和标准差"""
    non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size
    if non_zero_ratio < non_zero_thresh:
        return False
    slice_std = np.std(slice_2d)
    if slice_std < std_thresh:
        return False
    return True


def run_inference_on_slice(slice_2d, conf_threshold):
    """在单个切片上运行推理"""
    slice_rgb = np.stack([slice_2d] * 3, axis=-1)
    results = model.predict(source=slice_rgb, conf=conf_threshold, verbose=False, device=None, save=False)
    max_area = 0
    best_box = None
    for result in results:
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xywh.cpu().numpy()
            areas = boxes[:, 2] * boxes[:, 3]
            max_idx = areas.argmax()
            if areas[max_idx] > max_area:
                max_area = areas[max_idx]
                best_box = boxes[max_idx]
    return max_area, best_box


def extract_slice(axis: str, index: int) -> np.ndarray:
    """根据轴和索引提取切片"""
    if axis == 'axial':
        return data[:, :, index]
    elif axis == 'sagittal':
        return data[index, :, :]
    elif axis == 'coronal':
        return data[:, index, :]
    else:
        raise ValueError(f"Invalid axis: {axis}")


# ==========================================
# 优化的检测方法（支持无肿瘤情况）
# ==========================================
def optimized_search_with_no_tumor_detection() -> SearchResult:
    """优化的搜索方法，包含无肿瘤检测"""
    start_time = time.time()
    total_processed = 0
    total_skipped = 0

    # 步骤1: 轴向粗搜索 + 精修
    print("🔍 Starting axial coarse search...")
    max_area_coarse = -1
    best_idx_coarse = -1
    skipped = 0
    processed = 0

    # 先进行小范围采样检查是否有肿瘤迹象
    sample_indices = list(range(0, K, config.AXIAL_SAMPLING_STEP))
    sample_areas = []

    for idx in sample_indices:
        slice_2d = extract_slice('axial', idx)
        if not pre_filter_slice(slice_2d):
            skipped += 1
            continue

        processed += 1
        area, _ = run_inference_on_slice(slice_2d, config.conf)
        sample_areas.append(area)

        if area > max_area_coarse:
            max_area_coarse = area
            best_idx_coarse = idx

    # 判断是否存在肿瘤
    if max_area_coarse <= 0 or (len(sample_areas) > 5 and np.mean(sample_areas) < 100):
        return SearchResult(
            success=True,
            has_tumor=False,
            processing_time=time.time() - start_time,
            slices_processed=processed,
            slices_skipped=skipped,
            message="No significant tumor detected in axial view"
        )

    # 存在肿瘤，继续精修
    print(f"🎯 Tumor candidate found at axial slice {best_idx_coarse}, refining...")
    fine_range = list(range(max(0, best_idx_coarse - config.REFINE_RADIUS),
                            min(K, best_idx_coarse + config.REFINE_RADIUS + 1)))

    best_k = best_idx_coarse
    max_area_k = max_area_coarse

    for idx in fine_range:
        area, _ = run_inference_on_slice(extract_slice('axial', idx), config.conf)
        if area > max_area_k:
            max_area_k = area
            best_k = idx

    total_processed += processed + len(fine_range)
    total_skipped += skipped

    # 获取中心点和ROI
    _, best_box = run_inference_on_slice(data[:, :, best_k], config.conf)
    if best_box is None:
        return SearchResult(
            success=False,
            has_tumor=False,
            processing_time=time.time() - start_time,
            message="No clear tumor bounding box found"
        )

    cx, cy, w, h = best_box
    i_center = int(round(cy))
    j_center = int(round(cx))

    # 计算搜索半径
    physical_width_mm = w * spacing[1]
    physical_height_mm = h * spacing[0]
    search_radius_i_vox = max(1, int(np.ceil((physical_height_mm / 3.0) / spacing[0])))
    search_radius_j_vox = max(1, int(np.ceil((physical_width_mm / 3.0) / spacing[1])))

    i_start = max(0, i_center - search_radius_i_vox)
    i_end = min(I, i_center + search_radius_i_vox + 1)
    j_start = max(0, j_center - search_radius_j_vox)
    j_end = min(J, j_center + search_radius_j_vox + 1)

    # 步骤2: 矢状面搜索
    print("🔍 Searching sagittal plane...")
    max_area_sag = -1
    best_i = -1
    sag_processed = 0
    sag_skipped = 0

    for idx in range(i_start, i_end, config.SAGITTAL_SAMPLING_STEP):
        slice_2d = extract_slice('sagittal', idx)
        if not pre_filter_slice(slice_2d):
            sag_skipped += 1
            continue
        sag_processed += 1
        area, _ = run_inference_on_slice(slice_2d, config.HIGH_CONF_FOR_OTHER_AXES)
        if area > max_area_sag:
            max_area_sag = area
            best_i = idx

    fine_sag = list(range(max(i_start, best_i - config.REFINE_RADIUS),
                          min(i_end, best_i + config.REFINE_RADIUS + 1)))
    for idx in fine_sag:
        area, _ = run_inference_on_slice(extract_slice('sagittal', idx), config.HIGH_CONF_FOR_OTHER_AXES)
        if area > max_area_sag:
            max_area_sag = area
            best_i = idx

    total_processed += sag_processed + len(fine_sag)
    total_skipped += sag_skipped

    # 步骤3: 冠状面搜索
    print("🔍 Searching coronal plane...")
    max_area_cor = -1
    best_j = -1
    cor_processed = 0
    cor_skipped = 0

    for idx in range(j_start, j_end, config.CORONAL_SAMPLING_STEP):
        slice_2d = extract_slice('coronal', idx)
        if not pre_filter_slice(slice_2d):
            cor_skipped += 1
            continue
        cor_processed += 1
        area, _ = run_inference_on_slice(slice_2d, config.HIGH_CONF_FOR_OTHER_AXES)
        if area > max_area_cor:
            max_area_cor = area
            best_j = idx

    fine_cor = list(range(max(j_start, best_j - config.REFINE_RADIUS),
                          min(j_end, best_j + config.REFINE_RADIUS + 1)))
    for idx in fine_cor:
        area, _ = run_inference_on_slice(extract_slice('coronal', idx), config.HIGH_CONF_FOR_OTHER_AXES)
        if area > max_area_cor:
            max_area_cor = area
            best_j = idx

    total_processed += cor_processed + len(fine_cor)
    total_skipped += cor_skipped

    # 确定最佳切片
    final_max_area = max(max_area_k, max_area_sag, max_area_cor)
    best_axis = 'axial'
    best_slice_idx = best_k

    if max_area_sag > final_max_area:
        final_max_area = max_area_sag
        best_axis = 'sagittal'
        best_slice_idx = best_i
    if max_area_cor > final_max_area:
        final_max_area = max_area_cor
        best_axis = 'coronal'
        best_slice_idx = best_j

    processing_time = time.time() - start_time

    return SearchResult(
        success=True,
        has_tumor=True,
        best_axis=best_axis,
        best_slice_idx=best_slice_idx,
        max_area=final_max_area,
        processing_time=processing_time,
        slices_processed=total_processed,
        slices_skipped=total_skipped,
        message=f"Best slice found: {best_axis} slice {best_slice_idx}"
    )


# ==========================================
# 全轴遍历方法（支持无肿瘤检测）
# ==========================================
def full_search_with_no_tumor_detection() -> SearchResult:
    """全轴暴力搜索方法，包含无肿瘤检测"""
    start_time = time.time()
    total_processed = 0
    all_areas = []

    best_area = -1
    best_slice_info = None

    # 轴向搜索
    print("💥 Full axial search...")
    for k in range(K):
        area, _ = run_inference_on_slice(extract_slice('axial', k), config.conf)
        total_processed += 1
        all_areas.append(area)
        if area > best_area:
            best_area = area
            best_slice_info = ('axial', k)

    # 矢状面搜索
    print("💥 Full sagittal search...")
    for i in range(I):
        area, _ = run_inference_on_slice(extract_slice('sagittal', i), config.HIGH_CONF_FOR_OTHER_AXES)
        total_processed += 1
        all_areas.append(area)
        if area > best_area:
            best_area = area
            best_slice_info = ('sagittal', i)

    # 冠状面搜索
    print("💥 Full coronal search...")
    for j in range(J):
        area, _ = run_inference_on_slice(extract_slice('coronal', j), config.HIGH_CONF_FOR_OTHER_AXES)
        total_processed += 1
        all_areas.append(area)
        if area > best_area:
            best_area = area
            best_slice_info = ('coronal', j)

    processing_time = time.time() - start_time

    # 判断是否存在肿瘤
    has_tumor = best_area > 100  # 阈值可根据实际情况调整

    return SearchResult(
        success=True,
        has_tumor=has_tumor,
        best_axis=best_slice_info[0] if best_slice_info else None,
        best_slice_idx=best_slice_info[1] if best_slice_info else None,
        max_area=best_area if best_area > 0 else 0,
        processing_time=processing_time,
        slices_processed=total_processed,
        slices_skipped=0,
        message="Full search completed" + (" - No tumor detected" if not has_tumor else "")
    )


# ==========================================
# 报告生成
# ==========================================
def generate_comparison_report(opt_result: SearchResult, full_result: SearchResult):
    """生成详细的对比报告"""

    # 计算节省
    time_saved = full_result.processing_time - opt_result.processing_time
    time_saved_percent = (time_saved / full_result.processing_time) * 100 if full_result.processing_time > 0 else 0
    proc_saved = full_result.slices_processed - opt_result.slices_processed
    proc_saved_percent = (proc_saved / full_result.slices_processed) * 100 if full_result.slices_processed > 0 else 0

    # 生成报告
    report = f"""MRI Best Slice Detection: Optimized vs Full Search Comparison
==================================================================
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

Dataset: {config.nii_path}
Model: {config.model_path}
Data shape: {data.shape if data is not None else 'N/A'}
Spacing: {spacing if spacing is not None else 'N/A'}

--- Full Exhaustive Search ---
Status: {'Tumor detected' if full_result.has_tumor else 'No tumor detected'}
Total slices processed: {full_result.slices_processed}
Total time: {full_result.processing_time:.2f} seconds
Message: {full_result.message}

--- Optimized Search (Coarse + Refine + Local ROI) ---
Status: {'Tumor detected' if opt_result.has_tumor else 'No tumor detected'}
Total slices processed: {opt_result.slices_processed}
Skipped slices: {opt_result.slices_skipped}
Total time: {opt_result.processing_time:.2f} seconds
Message: {opt_result.message}

--- Performance Comparison ---
Time saved: {time_saved:.2f} s ({time_saved_percent:.1f}% reduction)
Inference calls saved: {proc_saved} ({proc_saved_percent:.1f}% reduction)
Speedup factor: {full_result.processing_time / max(opt_result.processing_time, 0.001):.2f}x

--- Tumor Detection Details ---
Optimized method best: {opt_result.best_axis} slice {opt_result.best_slice_idx} (area: {opt_result.max_area:.1f})
Full search best: {full_result.best_axis} slice {full_result.best_slice_idx} (area: {full_result.max_area:.1f})

Configuration:
- Axial sampling step: {config.AXIAL_SAMPLING_STEP}
- Sagittal/Coronal sampling step: {config.SAGITTAL_SAMPLING_STEP}/{config.CORONAL_SAMPLING_STEP}
- Pre-filter thresholds: non-zero={config.SLICE_THRESHOLD}, std={config.STD_THRESHOLD}
- Refinement radius: {config.REFINE_RADIUS}

Note:
- Both methods now include no-tumor detection capabilities
- Optimized method uses adaptive sampling and early termination for negative cases
- Full search provides ground truth comparison but is computationally expensive
"""
    return report


# ==========================================
# 主程序
# ==========================================
def main():
    try:
        # 初始化系统
        initialize_system()

        # 运行优化搜索
        print("\n🚀 Running optimized search with no-tumor detection...")
        opt_result = optimized_search_with_no_tumor_detection()

        # 运行全搜索
        print("\n💥 Running full exhaustive search with no-tumor detection...")
        full_result = full_search_with_no_tumor_detection()

        # 生成并保存报告
        report = generate_comparison_report(opt_result, full_result)
        output_file = os.path.join(config.output_project, 'comparison_results.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ Comparison report saved to: {output_file}")
        print("\n" + "=" * 50)
        print(report)

        # 输出简要总结
        print("\n📊 SUMMARY:")
        print(f"  Tumor detected: Optimized={opt_result.has_tumor}, Full={full_result.has_tumor}")
        print(f"  Time savings: {full_result.processing_time - opt_result.processing_time:.2f}s "
              f"({((full_result.processing_time - opt_result.processing_time) / full_result.processing_time) * 100:.1f}%)")
        print(f"  Processing savings: {full_result.slices_processed - opt_result.slices_processed} slices")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()