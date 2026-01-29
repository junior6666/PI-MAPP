import cv2
import nibabel as nib
import numpy as np
from ultralytics import YOLO
import os
import time

# ----------------------------
# 配置
# ----------------------------
model_path = r'H:\pycharm_project\PI-MAPP\project\detection_train\tumor\runs\detect\train_yolo12_try_owndata2\weights\best.pt'
nii_path = '../data_test/MRBrainTumor2.nii.gz'
output_project = '../best_slices_results_test'
os.makedirs(output_project, exist_ok=True)
conf = 0.65

# 优化参数配置
AXIAL_SAMPLING_STEP = 2
SAGITTAL_SAMPLING_STEP = 2
CORONAL_SAMPLING_STEP = 2
SLICE_THRESHOLD = 0.05
STD_THRESHOLD = 5.0
REFINE_RADIUS = 1

# 全局变量用于模型和数据（避免重复加载）
model = None
data = None
I, J, K = 0, 0, 0
spacing = None


def load_model_and_data():
    global model, data, I, J, K, spacing
    if model is None:
        model = YOLO(model_path)
    if data is None:
        img = nib.load(nii_path)
        data_raw = img.get_fdata()
        spacing = img.header.get_zooms()

        # 归一化到 uint8
        if data_raw.dtype != np.uint8:
            data_raw = np.clip(data_raw, 0, np.percentile(data_raw, 99))
            data_raw = ((data_raw - data_raw.min()) / (data_raw.max() - data_raw.min()) * 255).astype(np.uint8)
        data = data_raw
        I, J, K = data.shape


def pre_filter_slice(slice_2d, non_zero_thresh=SLICE_THRESHOLD, std_thresh=STD_THRESHOLD):
    non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size
    if non_zero_ratio < non_zero_thresh:
        return False
    slice_std = np.std(slice_2d)
    if slice_std < std_thresh:
        return False
    return True


def run_inference_on_slice(slice_2d, conf_threshold=conf):
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


# ==========================================
# 优化方法（你原来的流程）
# ==========================================
def optimized_search():
    start_time = time.time()
    total_processed = 0
    total_skipped = 0

    # Step 1: Axial coarse + refine
    def get_axial_slice(k):
        return data[:, :, k]

    max_area_coarse = -1
    best_idx_coarse = -1
    skipped = 0
    processed = 0
    for idx in range(0, K, AXIAL_SAMPLING_STEP):
        slice_2d = get_axial_slice(idx)
        if not pre_filter_slice(slice_2d):
            skipped += 1
            continue
        processed += 1
        area, _ = run_inference_on_slice(slice_2d, conf)
        if area > max_area_coarse:
            max_area_coarse = area
            best_idx_coarse = idx

    if max_area_coarse <= 0:
        raise RuntimeError("No tumor in axial")

    fine_range = list(range(max(0, best_idx_coarse - REFINE_RADIUS), min(K, best_idx_coarse + REFINE_RADIUS + 1)))
    best_k = best_idx_coarse
    max_area_k = max_area_coarse
    for idx in fine_range:
        area, _ = run_inference_on_slice(get_axial_slice(idx), conf)
        if area > max_area_k:
            max_area_k = area
            best_k = idx

    total_processed += processed + len(fine_range)
    total_skipped += skipped

    # Get center
    _, best_box = run_inference_on_slice(data[:, :, best_k], conf)
    if best_box is None:
        raise RuntimeError("No box in best axial")
    cx, cy, w, h = best_box
    i_center = int(round(cy))
    j_center = int(round(cx))

    # Compute search radii
    physical_width_mm = w * spacing[1]
    physical_height_mm = h * spacing[0]
    search_radius_i_vox = max(1, int(np.ceil((physical_height_mm / 3.0) / spacing[0])))
    search_radius_j_vox = max(1, int(np.ceil((physical_width_mm / 3.0) / spacing[1])))
    i_start = max(0, i_center - search_radius_i_vox)
    i_end = min(I, i_center + search_radius_i_vox + 1)
    j_start = max(0, j_center - search_radius_j_vox)
    j_end = min(J, j_center + search_radius_j_vox + 1)

    # Step 2: Sagittal
    def get_sagittal_slice(i):
        return data[i, :, :]

    max_area_sag = -1
    best_i = -1
    sag_processed = 0
    sag_skipped = 0
    for idx in range(i_start, i_end, SAGITTAL_SAMPLING_STEP):
        slice_2d = get_sagittal_slice(idx)
        if not pre_filter_slice(slice_2d):
            sag_skipped += 1
            continue
        sag_processed += 1
        area, _ = run_inference_on_slice(slice_2d, 0.92)
        if area > max_area_sag:
            max_area_sag = area
            best_i = idx

    fine_sag = list(range(max(i_start, best_i - REFINE_RADIUS), min(i_end, best_i + REFINE_RADIUS + 1)))
    for idx in fine_sag:
        area, _ = run_inference_on_slice(get_sagittal_slice(idx), 0.92)
        if area > max_area_sag:
            max_area_sag = area
            best_i = idx

    total_processed += sag_processed + len(fine_sag)
    total_skipped += sag_skipped

    # Step 3: Coronal
    def get_coronal_slice(j):
        return data[:, j, :]

    max_area_cor = -1
    best_j = -1
    cor_processed = 0
    cor_skipped = 0
    for idx in range(j_start, j_end, CORONAL_SAMPLING_STEP):
        slice_2d = get_coronal_slice(idx)
        if not pre_filter_slice(slice_2d):
            cor_skipped += 1
            continue
        cor_processed += 1
        area, _ = run_inference_on_slice(slice_2d, 0.92)
        if area > max_area_cor:
            max_area_cor = area
            best_j = idx

    fine_cor = list(range(max(j_start, best_j - REFINE_RADIUS), min(j_end, best_j + REFINE_RADIUS + 1)))
    for idx in fine_cor:
        area, _ = run_inference_on_slice(get_coronal_slice(idx), 0.92)
        if area > max_area_cor:
            max_area_cor = area
            best_j = idx

    total_processed += cor_processed + len(fine_cor)
    total_skipped += cor_skipped

    end_time = time.time()
    return end_time - start_time, total_processed, total_skipped


# ==========================================
# 全轴遍历方法（暴力法）
# ==========================================
def full_search():
    start_time = time.time()
    total_processed = 0

    best_area = -1
    best_slice_info = None  # (axis, idx)

    # Axial (axis=2)
    for k in range(K):
        area, _ = run_inference_on_slice(data[:, :, k], conf)
        total_processed += 1
        if area > best_area:
            best_area = area
            best_slice_info = ('axial', k)

    # Sagittal (axis=0)
    for i in range(I):
        area, _ = run_inference_on_slice(data[i, :, :], 0.92)
        total_processed += 1
        if area > best_area:
            best_area = area
            best_slice_info = ('sagittal', i)

    # Coronal (axis=1)
    for j in range(J):
        area, _ = run_inference_on_slice(data[:, j, :], 0.92)
        total_processed += 1
        if area > best_area:
            best_area = area
            best_slice_info = ('coronal', j)

    end_time = time.time()
    return end_time - start_time, total_processed, 0  # skipped = 0


# ==========================================
# 主程序：运行对比并保存结果
# ==========================================
def main():
    print("🔄 Loading model and data...")
    load_model_and_data()
    print(f"Data shape: {data.shape}, spacing: {spacing}")

    print("\n🚀 Running optimized search...")
    time_opt, proc_opt, skip_opt = optimized_search()

    print("\n💥 Running full exhaustive search...")
    time_full, proc_full, _ = full_search()

    # 计算节省
    time_saved = time_full - time_opt
    time_saved_percent = (time_saved / time_full) * 100 if time_full > 0 else 0
    proc_saved = proc_full - proc_opt
    proc_saved_percent = (proc_saved / proc_full) * 100 if proc_full > 0 else 0

    # 生成报告
    report = f"""MRI Best Slice Detection: Optimized vs Full Search Comparison
==================================================================

Dataset: {nii_path}
Model: {model_path}

--- Full Exhaustive Search ---
Total slices processed: {proc_full}
Total time: {time_full:.2f} seconds

--- Optimized Search (Coarse + Refine + Local ROI) ---
Total slices processed: {proc_opt}
Skipped slices: {skip_opt}
Total time: {time_opt:.2f} seconds

--- Savings ---
Time saved: {time_saved:.2f} s ({time_saved_percent:.1f}% reduction)
Inference calls saved: {proc_saved} ({proc_saved_percent:.1f}% reduction)

Note:
- Optimized method uses axial coarse sampling (step={AXIAL_SAMPLING_STEP}),
  local sagittal/coronal search around tumor ROI,
  and pre-filtering based on non-zero ratio & std.
- Full search runs inference on every single slice in all 3 axes.
"""
    # 保存到文件
    output_file = os.path.join(output_project, 'comparison_results.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Comparison report saved to: {output_file}")
    print(report)


if __name__ == "__main__":
    main()