import cv2
import nibabel as nib
import numpy as np
from ultralytics import YOLO
import os

# ----------------------------
# 配置
# ----------------------------
model_path = r'../pt_models/best.pt'
nii_path = '../data_test/MRBrainTumor2.nii.gz'
output_project = '../best_slices_results_test12'
os.makedirs(output_project, exist_ok=True)
conf = 0.65

# 优化参数配置
AXIAL_SAMPLING_STEP = 2  # 轴向全局搜索时的跳帧步长
SAGITTAL_SAMPLING_STEP = 2  # 矢状面粗搜索步长
CORONAL_SAMPLING_STEP = 2  # 冠状面粗搜索步长
SLICE_THRESHOLD = 0.05  # 非零像素比例阈值 (0-1)
STD_THRESHOLD = 5.0  # 标准差阈值，可选
REFINE_RADIUS = 1  # 精细搜索半径（前后各1片）

model = YOLO(model_path)
img = nib.load(nii_path)
data = img.get_fdata()

# 获取体素间距
spacing = img.header.get_zooms()
print(f"📏 Voxel spacing (mm): {spacing}")

# 归一化到 uint8
if data.dtype != np.uint8:
    data = np.clip(data, 0, np.percentile(data, 99))
    data = ((data - data.min()) / (data.max() - data.min()) * 255).astype(np.uint8)

I, J, K = data.shape


# ==========================================
# 预筛选函数
# ==========================================
def pre_filter_slice(slice_2d, non_zero_thresh=SLICE_THRESHOLD, std_thresh=STD_THRESHOLD):
    """
    预筛选切片：检查切片是否值得推理
    返回: True表示需要推理，False表示跳过
    """
    # 方法1: 非零像素比例
    non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size

    # 方法2: 标准差（可选）
    slice_std = np.std(slice_2d)

    # 如果非零像素比例过低，则跳过
    if non_zero_ratio < non_zero_thresh:
        return False

    # 如果标准差过低（图像变化小），也跳过（可选）
    if slice_std < std_thresh:
        return False

    return True


# ==========================================
# 搜索函数：执行粗搜索和精细搜索
# ==========================================
def search_with_refinement(data_axis, axis_type, slice_indices, sampling_step,
                           search_range_name="", conf_threshold=conf):
    """
    在指定轴上执行粗搜索和精细搜索

    参数:
    - data_axis: 生成切片的函数，接受切片索引参数
    - axis_type: 轴类型，用于日志输出
    - slice_indices: 切片索引范围
    - sampling_step: 粗搜索步长
    - search_range_name: 搜索范围名称
    - conf_threshold: 置信度阈值

    返回:
    - best_index: 最佳切片索引
    - max_area: 最大检测面积
    - processed_slices: 处理的切片数
    - skipped_slices: 跳过的切片数
    """
    start_idx, end_idx = slice_indices
    print(f"🔍 {axis_type}搜索 ({search_range_name}): 范围 [{start_idx}, {end_idx})")

    # 阶段1: 粗搜索
    max_area_coarse = -1
    best_idx_coarse = -1
    best_box_coarse = None
    skipped_slices = 0
    processed_coarse = 0

    for idx in range(start_idx, end_idx, sampling_step):
        slice_2d = data_axis(idx)

        # 预筛选
        if not pre_filter_slice(slice_2d):
            skipped_slices += 1
            continue

        processed_coarse += 1
        slice_rgb = np.stack([slice_2d] * 3, axis=-1)
        results = model.predict(source=slice_rgb, conf=conf_threshold,
                                verbose=False, device=None, save=False)

        current_max_area = 0
        best_box = None
        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xywh.cpu().numpy()
                areas = boxes[:, 2] * boxes[:, 3]
                max_idx = areas.argmax()
                if areas[max_idx] > current_max_area:
                    current_max_area = areas[max_idx]
                    best_box = boxes[max_idx]

        if current_max_area > max_area_coarse:
            max_area_coarse = current_max_area
            best_idx_coarse = idx
            best_box_coarse = best_box

    print(f"✅ {axis_type}粗搜索: 最佳切片 (idx={best_idx_coarse}), 最大面积: {max_area_coarse:.2f}")
    print(f"⏭️  跳过 {skipped_slices}/{len(range(start_idx, end_idx, sampling_step))} 切片")

    # 如果粗搜索没找到目标，直接返回
    if max_area_coarse <= 0:
        return -1, 0, processed_coarse, skipped_slices

    # 阶段2: 精细搜索
    print(f"🔍 {axis_type}精细搜索...")
    max_area_fine = -1
    best_idx_fine = -1
    best_box_fine = None

    # 确定精细搜索范围
    fine_search_range = []
    for offset in range(-REFINE_RADIUS, REFINE_RADIUS + 1):
        fine_idx = best_idx_coarse + offset
        if start_idx <= fine_idx < end_idx:
            fine_search_range.append(fine_idx)

    # 确保包含粗搜索的最佳切片
    if best_idx_coarse not in fine_search_range:
        fine_search_range.append(best_idx_coarse)

    # 移除重复索引并排序
    fine_search_range = sorted(set(fine_search_range))
    print(f"🔍 精细搜索范围: {fine_search_range}")

    for fine_idx in fine_search_range:
        # 精细搜索中不进行预筛选
        slice_2d = data_axis(fine_idx)
        slice_rgb = np.stack([slice_2d] * 3, axis=-1)
        results = model.predict(source=slice_rgb, conf=conf_threshold,
                                verbose=False, device=None, save=False)

        current_max_area = 0
        best_box = None
        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xywh.cpu().numpy()
                areas = boxes[:, 2] * boxes[:, 3]
                max_idx = areas.argmax()
                if areas[max_idx] > current_max_area:
                    current_max_area = areas[max_idx]
                    best_box = boxes[max_idx]

        if current_max_area > max_area_fine:
            max_area_fine = current_max_area
            best_idx_fine = fine_idx
            best_box_fine = best_box

    print(f"✅ {axis_type}精细搜索: 最佳切片 (idx={best_idx_fine}), 最大面积: {max_area_fine:.2f}")

    # 如果精细搜索没有找到，回退到粗搜索结果
    if best_box_fine is None:
        if best_box_coarse is None:
            return -1, 0, processed_coarse + len(fine_search_range), skipped_slices
        else:
            print(f"⚠️  {axis_type}精细搜索未找到目标，使用粗搜索结果")
            best_idx_fine = best_idx_coarse
            best_box_fine = best_box_coarse
            max_area_fine = max_area_coarse

    return best_idx_fine, max_area_fine, processed_coarse + len(fine_search_range), skipped_slices


# ==========================================
# Step 1: 沿 axis=2（axial）找最大目标切片（优化版）
# ==========================================
print("🔍 Step 1: Searching along axis=2 (axial slices) with optimization...")


# 定义轴向切片获取函数
def get_axial_slice(k):
    return data[:, :, k]


best_k_fine, max_area_k_fine, axial_processed, axial_skipped = search_with_refinement(
    data_axis=get_axial_slice,
    axis_type="轴向",
    slice_indices=(0, K),
    sampling_step=AXIAL_SAMPLING_STEP,
    search_range_name="全局"
)

if best_k_fine == -1:
    raise RuntimeError("No tumor detected in any axial slice!")

# 获取最佳轴向切片的检测框
print("🔍 获取最佳轴向切片的检测框...")
slice_2d = data[:, :, best_k_fine]
slice_rgb = np.stack([slice_2d] * 3, axis=-1)
results = model.predict(source=slice_rgb, conf=conf, verbose=False, device=None, save=False)

best_box_axial = None
max_area_axial = 0
for result in results:
    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes.xywh.cpu().numpy()
        areas = boxes[:, 2] * boxes[:, 3]
        max_idx = areas.argmax()
        if areas[max_idx] > max_area_axial:
            max_area_axial = areas[max_idx]
            best_box_axial = boxes[max_idx]

if best_box_axial is None:
    raise RuntimeError("No tumor detected in the best axial slice!")

cx, cy, w, h = best_box_axial
i_center = int(round(cy))
j_center = int(round(cx))
k_center = best_k_fine

print(f"🎯 Tumor center at volume index: (i={i_center}, j={j_center}, k={k_center})")

# ==============================
# 计算物理尺寸和搜索半径
# ==============================
physical_width_mm = w * spacing[1]
physical_height_mm = h * spacing[0]

search_radius_mm_i = physical_height_mm / 3.0
search_radius_mm_j = physical_width_mm / 3.0

search_radius_i_vox = int(np.ceil(search_radius_mm_i / spacing[0]))
search_radius_j_vox = int(np.ceil(search_radius_mm_j / spacing[1]))

search_radius_i_vox = max(1, search_radius_i_vox)
search_radius_j_vox = max(1, search_radius_j_vox)

i_start = max(0, i_center - search_radius_i_vox)
i_end = min(I, i_center + search_radius_i_vox + 1)
j_start = max(0, j_center - search_radius_j_vox)
j_end = min(J, j_center + search_radius_j_vox + 1)

print(f"📏 Using spacing {spacing} → search radii: "
      f"axis0={search_radius_i_vox} vox, axis1={search_radius_j_vox} vox")
print(f"🔍 Search sagittal (i) in [{i_start}, {i_end})")
print(f"🔍 Search coronal  (j) in [{j_start}, {j_end})")

# ==========================================
# Step 2: 在 axis=0（sagittal）局部搜索（带粗搜索和精细搜索）
# ==========================================
print("\n" + "=" * 50)
print("Step 2: Searching sagittal slices with coarse and fine search...")


# 定义矢状面切片获取函数
def get_sagittal_slice(i):
    return data[i, :, :]


best_i_fine, max_area_i_fine, sagittal_processed, sagittal_skipped = search_with_refinement(
    data_axis=get_sagittal_slice,
    axis_type="矢状面",
    slice_indices=(i_start, i_end),
    sampling_step=SAGITTAL_SAMPLING_STEP,
    search_range_name=f"局部[{i_start}, {i_end})",
    conf_threshold=0.92
)

# ==========================================
# Step 3: 在 axis=1（coronal）局部搜索（带粗搜索和精细搜索）
# ==========================================
print("\n" + "=" * 50)
print("Step 3: Searching coronal slices with coarse and fine search...")


# 定义冠状面切片获取函数
def get_coronal_slice(j):
    return data[:, j, :]


best_j_fine, max_area_j_fine, coronal_processed, coronal_skipped = search_with_refinement(
    data_axis=get_coronal_slice,
    axis_type="冠状面",
    slice_indices=(j_start, j_end),
    sampling_step=CORONAL_SAMPLING_STEP,
    search_range_name=f"局部[{j_start}, {j_end})",
    conf_threshold=0.92
)

# ==========================================
# Step 4: 保存结果
# ==========================================
print("\n" + "=" * 50)
print("Step 4: Saving results...")

best_indices = {0: best_i_fine if best_i_fine != -1 else i_center,
                1: best_j_fine if best_j_fine != -1 else j_center,
                2: k_center}
plane_names = ['sagittal', 'coronal', 'axial']
detection_status = ['未检测到', '检测成功']

for axis, idx in best_indices.items():
    if axis == 0:
        slice_2d = data[idx, :, :]
    elif axis == 1:
        slice_2d = data[:, idx, :]
    else:
        slice_2d = data[:, :, idx]

    slice_rgb = np.stack([slice_2d] * 3, axis=-1)
    slice_rgb = np.ascontiguousarray(slice_rgb)

    results = model.predict(
        source=slice_rgb,
        conf=conf,
        save=False,
        verbose=False,
        device=None
    )

    plotted_img = results[0].plot()
    output_dir = os.path.join(output_project, f"best_{plane_names[axis]}_slice_{idx:04d}")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "image.jpg")
    cv2.imwrite(output_path, plotted_img)

# ==========================================
# 性能统计
# ==========================================
print("\n" + "=" * 60)
print("📊 优化效果统计:")
print("=" * 60)

# 计算原始需要处理的切片数量（无优化）
axial_original = K  # 轴向全搜索
sagittal_original = i_end - i_start  # 矢状面全范围
coronal_original = j_end - j_start  # 冠状面全范围
total_original = axial_original + sagittal_original + coronal_original

# 优化后处理的切片数量
axial_processed_total = axial_processed
sagittal_processed_total = sagittal_processed
coronal_processed_total = coronal_processed
total_processed = axial_processed_total + sagittal_processed_total + coronal_processed_total

# 跳过的切片数量
axial_skipped_total = axial_skipped
sagittal_skipped_total = sagittal_skipped
coronal_skipped_total = coronal_skipped
total_skipped = axial_skipped_total + sagittal_skipped_total + coronal_skipped_total

# 加速比
speedup_ratio = total_original / total_processed if total_processed > 0 else 1

print(f"{'方向':<10} {'原始切片数':<12} {'处理切片数':<12} {'跳过切片数':<12} {'检测状态':<12}")
print(f"{'-' * 60}")
print(f"{'轴向':<10} {axial_original:<12} {axial_processed_total:<12} {axial_skipped_total:<12} {'✓ 成功':<12}")
print(
    f"{'矢状面':<10} {sagittal_original:<12} {sagittal_processed_total:<12} {sagittal_skipped_total:<12} {detection_status[best_i_fine != -1]:<12}")
print(
    f"{'冠状面':<10} {coronal_original:<12} {coronal_processed_total:<12} {coronal_skipped_total:<12} {detection_status[best_j_fine != -1]:<12}")
print(f"{'-' * 60}")
print(f"{'总计':<10} {total_original:<12} {total_processed:<12} {total_skipped:<12}")
print(f"{'加速比':<10} {speedup_ratio:.2f}x")

print(f"\n📍 最佳切片索引:")
print(f"  轴向 (k): {k_center}")
print(f"  矢状面 (i): {best_i_fine if best_i_fine != -1 else '未检测到'}")
print(f"  冠状面 (j): {best_j_fine if best_j_fine != -1 else '未检测到'}")

print(f"\n📈 检测面积统计:")
print(f"  轴向最大面积: {max_area_k_fine:.2f}")
sagittal_area_str = f"{max_area_i_fine:.2f}" if best_i_fine != -1 else "N/A"
coronal_area_str = f"{max_area_j_fine:.2f}" if best_j_fine != -1 else "N/A"

print(f"  矢状面最大面积: {sagittal_area_str}")
print(f"  冠状面最大面积: {coronal_area_str}")

print("=" * 60)
print(f"\n✅ 所有最佳切片已保存，带优化.")
print(f"结果保存在: {os.path.abspath(output_project)}")