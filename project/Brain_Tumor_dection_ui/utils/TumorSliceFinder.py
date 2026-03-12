import cv2
import nibabel as nib
import numpy as np
from ultralytics import YOLO
import os
from typing import Tuple, Optional, Dict, List


class TumorSliceFinder:
    def __init__(self, model_path: str, nii_path: str, output_project: str,
                 conf: float = 0.65, voxel_spacing: Optional[Tuple[float, float, float]] = None):
        """
        初始化肿瘤切片查找器

        Args:
            model_path: YOLO模型路径
            nii_path: NIfTI文件路径
            output_project: 输出目录
            conf: 置信度阈值
            voxel_spacing: 体素间距(mm)，如果为None则从文件读取
        """
        self.model_path = model_path
        self.nii_path = nii_path
        self.output_project = output_project
        self.conf = conf
        self.voxel_spacing = voxel_spacing

        # 优化参数配置
        self.AXIAL_SAMPLING_STEP = 2
        self.SAGITTAL_SAMPLING_STEP = 2
        self.CORONAL_SAMPLING_STEP = 2
        self.SLICE_THRESHOLD = 0.05
        self.STD_THRESHOLD = 5.0
        self.REFINE_RADIUS = 1

        # 初始化模型和加载数据
        self._initialize_model()
        self._load_data()

        # 创建输出目录
        os.makedirs(self.output_project, exist_ok=True)

        print(f"📏 Voxel spacing (mm): {self.spacing}")

    def _initialize_model(self):
        """初始化YOLO模型"""
        self.model = YOLO(self.model_path)

    def _load_data(self):
        """加载NIfTI数据"""
        img = nib.load(self.nii_path)
        self.data = img.get_fdata()

        # 获取或设置体素间距
        if self.voxel_spacing is None:
            self.spacing = img.header.get_zooms()
        else:
            self.spacing = self.voxel_spacing

        self.I, self.J, self.K = self.data.shape

        # 归一化到uint8
        if self.data.dtype != np.uint8:
            self.data = np.clip(self.data, 0, np.percentile(self.data, 99))
            self.data = ((self.data - self.data.min()) / (self.data.max() - self.data.min()) * 255).astype(np.uint8)

    def get_units(self) -> Dict[str, str]:
        """
        获取各轴的单位信息

        Returns:
            包含各轴单位和转换信息的字典
        """
        units = {
            'axial': {
                'pixel_unit': 'pixel',
                'physical_unit': 'mm',
                'conversion_factor': self.spacing[2],  # k轴间距
                'description': f'轴向切片索引 -> 物理位置: 索引 × {self.spacing[2]:.3f} mm'
            },
            'sagittal': {
                'pixel_unit': 'pixel',
                'physical_unit': 'mm',
                'conversion_factor': self.spacing[0],  # i轴间距
                'description': f'矢状面切片索引 -> 物理位置: 索引 × {self.spacing[0]:.3f} mm'
            },
            'coronal': {
                'pixel_unit': 'pixel',
                'physical_unit': 'mm',
                'conversion_factor': self.spacing[1],  # j轴间距
                'description': f'冠状面切片索引 -> 物理位置: 索引 × {self.spacing[1]:.3f} mm'
            }
        }
        return units

    @staticmethod
    def pre_filter_slice(slice_2d, non_zero_thresh=0.05, std_thresh=5.0):
        """
        预筛选切片：检查切片是否值得推理

        Returns: True表示需要推理，False表示跳过
        """
        # 方法1: 非零像素比例
        non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size

        # 方法2: 标准差
        slice_std = np.std(slice_2d)

        # 如果非零像素比例过低，则跳过
        if non_zero_ratio < non_zero_thresh:
            return False

        # 如果标准差过低（图像变化小），也跳过
        if slice_std < std_thresh:
            return False

        return True

    def search_with_refinement(self, data_axis, axis_type, slice_indices, sampling_step,
                               search_range_name="", conf_threshold=None):
        """
        在指定轴上执行粗搜索和精细搜索

        Returns:
            best_index: 最佳切片索引, max_area: 最大检测面积,
            processed_slices: 处理的切片数, skipped_slices: 跳过的切片数
        """
        if conf_threshold is None:
            conf_threshold = self.conf

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
            if not self.pre_filter_slice(slice_2d):
                skipped_slices += 1
                continue

            processed_coarse += 1
            slice_rgb = np.stack([slice_2d] * 3, axis=-1)
            results = self.model.predict(source=slice_rgb, conf=conf_threshold,
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
        for offset in range(-self.REFINE_RADIUS, self.REFINE_RADIUS + 1):
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
            slice_2d = data_axis(fine_idx)
            slice_rgb = np.stack([slice_2d] * 3, axis=-1)
            results = self.model.predict(source=slice_rgb, conf=conf_threshold,
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

    def find_best_slices(self) -> Dict:
        """
        主函数：查找最佳切片

        Returns:
            包含结果的字典
        """
        # Step 1: 沿axis=2（axial）找最大目标切片
        print("🔍 Step 1: Searching along axis=2 (axial slices) with optimization...")

        def get_axial_slice(k):
            return self.data[:, :, k]

        best_k_fine, max_area_k_fine, axial_processed, axial_skipped = self.search_with_refinement(
            data_axis=get_axial_slice,
            axis_type="轴向",
            slice_indices=(0, self.K),
            sampling_step=self.AXIAL_SAMPLING_STEP,
            search_range_name="全局"
        )

        # 如果没有检测到肿瘤，返回每个轴的中间切片
        if best_k_fine == -1:
            print("❌ 未检测到肿瘤，返回每个轴的中间切片")
            return {
                'has_tumor': False,
                'axial_slice': self.K // 2,
                'sagittal_slice': self.I // 2,
                'coronal_slice': self.J // 2,
                'tumor_center': None,
                'units': self.get_units(),
                'statistics': None
            }

        # 获取最佳轴向切片的检测框
        print("🔍 获取最佳轴向切片的检测框...")
        slice_2d = self.data[:, :, best_k_fine]
        slice_rgb = np.stack([slice_2d] * 3, axis=-1)
        results = self.model.predict(source=slice_rgb, conf=self.conf, verbose=False, device=None, save=False)

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

        # 计算物理尺寸和搜索半径
        physical_width_mm = w * self.spacing[1]
        physical_height_mm = h * self.spacing[0]

        search_radius_mm_i = physical_height_mm / 3.0
        search_radius_mm_j = physical_width_mm / 3.0

        search_radius_i_vox = int(np.ceil(search_radius_mm_i / self.spacing[0]))
        search_radius_j_vox = int(np.ceil(search_radius_mm_j / self.spacing[1]))

        search_radius_i_vox = max(1, search_radius_i_vox)
        search_radius_j_vox = max(1, search_radius_j_vox)

        i_start = max(0, i_center - search_radius_i_vox)
        i_end = min(self.I, i_center + search_radius_i_vox + 1)
        j_start = max(0, j_center - search_radius_j_vox)
        j_end = min(self.J, j_center + search_radius_j_vox + 1)

        print(f"📏 Using spacing {self.spacing} → search radii: "
              f"axis0={search_radius_i_vox} vox, axis1={search_radius_j_vox} vox")
        print(f"🔍 Search sagittal (i) in [{i_start}, {i_end})")
        print(f"🔍 Search coronal  (j) in [{j_start}, {j_end})")

        # Step 2: 在axis=0（sagittal）局部搜索
        print("\n" + "=" * 50)
        print("Step 2: Searching sagittal slices with coarse and fine search...")

        def get_sagittal_slice(i):
            return self.data[i, :, :]

        best_i_fine, max_area_i_fine, sagittal_processed, sagittal_skipped = self.search_with_refinement(
            data_axis=get_sagittal_slice,
            axis_type="矢状面",
            slice_indices=(i_start, i_end),
            sampling_step=self.SAGITTAL_SAMPLING_STEP,
            search_range_name=f"局部[{i_start}, {i_end})",
            conf_threshold=0.92
        )

        # Step 3: 在axis=1（coronal）局部搜索
        print("\n" + "=" * 50)
        print("Step 3: Searching coronal slices with coarse and fine search...")

        def get_coronal_slice(j):
            return self.data[:, j, :]

        best_j_fine, max_area_j_fine, coronal_processed, coronal_skipped = self.search_with_refinement(
            data_axis=get_coronal_slice,
            axis_type="冠状面",
            slice_indices=(j_start, j_end),
            sampling_step=self.CORONAL_SAMPLING_STEP,
            search_range_name=f"局部[{j_start}, {j_end})",
            conf_threshold=0.92
        )
        return {
            'has_tumor': True,
            'axial_slice': k_center,
            'sagittal_slice': best_i_fine if best_i_fine != -1 else i_center,
            'coronal_slice': best_j_fine if best_j_fine != -1 else j_center,
            'tumor_center': (i_center, j_center, k_center),
            'detection_areas': {
                'axial': max_area_k_fine,
                'sagittal': max_area_i_fine if best_i_fine != -1 else None,
                'coronal': max_area_j_fine if best_j_fine != -1 else None
            },
            'units': self.get_units()
        }

# 使用示例
if __name__ == "__main__":
    # 配置
    model_path = r'H:\pycharm_project\PI-MAPP\project\detection_train\tumor\runs\detect\train_yolo12_try_owndata2\weights\best.pt'
    nii_path = '../data_test/MRBrainTumor2.nii.gz'
    output_project = '../best_slices_results_test2214'

    # 创建查找器实例
    finder = TumorSliceFinder(
        model_path=model_path,
        nii_path=nii_path,
        output_project=output_project,
        conf=0.65
    )

    # 获取单位信息
    units = finder.get_units()
    print("单位信息:")
    for axis, info in units.items():
        print(f"{axis}: {info['description']}")

    # 查找最佳切片
    results = finder.find_best_slices()

    # 输出结果
    if results['has_tumor']:
        print(f"\n🎯 检测到肿瘤!")
        print(
            f"最佳轴向切片: {results['axial_slice']} (物理位置: {results['axial_slice'] * results['units']['axial']['conversion_factor']:.2f} mm)")
        print(
            f"最佳矢状面切片: {results['sagittal_slice']} (物理位置: {results['sagittal_slice'] * results['units']['sagittal']['conversion_factor']:.2f} mm)")
        print(
            f"最佳冠状面切片: {results['coronal_slice']} (物理位置: {results['coronal_slice'] * results['units']['coronal']['conversion_factor']:.2f} mm)")
        print(f"肿瘤中心: {results['tumor_center']}")
    else:
        print(f"\n❌ 未检测到肿瘤")
        print(
            f"返回中间切片 - 轴向: {results['axial_slice']}, 矢状面: {results['sagittal_slice']}, 冠状面: {results['coronal_slice']}")