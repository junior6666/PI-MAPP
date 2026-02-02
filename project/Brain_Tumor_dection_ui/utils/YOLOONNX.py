# visualize_onnx_yolo.py

import cv2
import matplotlib.pyplot as plt

# 假设 YOLOONNX 类已定义（可放在同一文件或导入）
# 这里为方便，直接内联你之前的 YOLOONNX 类（实际项目中建议拆分到单独模块）
# >>>>>>>>>>>> [开始：YOLOONNX 类定义] <<<<<<<<<<<<
import numpy as np
import onnxruntime as ort
import urllib.request
from pathlib import Path


class YOLOONNX:
    def __init__(self, model_path, class_names=None, conf_thres=0.25, iou_thres=0.45, input_size=640):
        self.model_path = model_path
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.input_size = input_size

        # 默认类别名（根据你的 Brain Tumor 数据集调整！）
        self.names = class_names or ['tumor']  # ⚠️ 重要：替换成你的真实类别！

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if ort.get_device() == 'GPU' else [
            'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def _load_image(self, source):
        if isinstance(source, np.ndarray):
            return source.copy()
        elif isinstance(source, str):
            if source.startswith('http'):
                req = urllib.request.urlopen(source)
                arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1)
            else:
                img = cv2.imread(source)
            if img is None:
                raise ValueError(f"Failed to load image from {source}")
            return img
        else:
            raise TypeError("Source must be a file path, URL, or numpy array")

    def _preprocess(self, img):
        h, w = img.shape[:2]
        scale = self.input_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (new_w, new_h))
        padded = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        padded[:new_h, :new_w] = resized
        input_tensor = padded.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        return input_tensor, (h, w)

    def _nms(self, detections, iou_thres):
        if len(detections) == 0:
            return detections
        x1, y1, x2, y2, scores = detections[:, 0], detections[:, 1], detections[:, 2], detections[:, 3], detections[:,
                                                                                                         4]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(iou <= iou_thres)[0]
            order = order[inds + 1]
        return detections[keep]

    def _postprocess(self, outputs, orig_shape):
        pred = outputs[0]
        boxes = pred[0, :4, :]
        scores = pred[0, 4:, :]
        num_boxes = boxes.shape[1]
        detections = np.zeros((num_boxes, 6), dtype=np.float32)
        detections[:, :4] = boxes.T
        detections[:, 4] = np.max(scores, axis=0)
        detections[:, 5] = np.argmax(scores, axis=0)
        conf_mask = detections[:, 4] >= self.conf_thres
        detections = detections[conf_mask]
        if len(detections) == 0:
            return np.empty((0, 6))
        xywh = detections[:, :4]
        xyxy = np.copy(xywh)
        xyxy[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
        xyxy[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
        xyxy[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
        xyxy[:, 3] = xywh[:, 1] + xywh[:, 3] / 2
        orig_h, orig_w = orig_shape
        xyxy[:, [0, 2]] = xyxy[:, [0, 2]] / self.input_size * orig_w
        xyxy[:, [1, 3]] = xyxy[:, [1, 3]] / self.input_size * orig_h
        detections[:, :4] = xyxy
        return self._nms(detections, self.iou_thres)

    def __call__(self, source, conf=None, verbose=False):
        if conf is not None:
            self.conf_thres = conf
        img = self._load_image(source)
        input_tensor, orig_shape = self._preprocess(img)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        detections = self._postprocess(outputs, orig_shape)
        return [YOOLOResult(img, detections, self.names)]


class YOOLOResult:
    def __init__(self, orig_img, detections, names):
        self.orig_img = orig_img.copy()
        self.detections = detections
        self.names = {i: name for i, name in enumerate(names)}

    @property
    def boxes(self):
        return BoxList(self.detections)

    def plot(self):
        plotted_img = self.orig_img.copy()
        for det in self.detections:
            x1, y1, x2, y2 = map(int, det[:4])
            conf = det[4]
            cls_id = int(det[5])
            label = f"{self.names[cls_id]} {conf:.2f}"
            cv2.rectangle(plotted_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(plotted_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return plotted_img


class BoxList:
    def __init__(self, detections):
        self.detections = detections

    @property
    def xyxy(self):
        return self.detections[:, :4] if len(self.detections) > 0 else np.empty((0, 4))

    @property
    def conf(self):
        return self.detections[:, 4] if len(self.detections) > 0 else np.empty(0)

    @property
    def cls(self):
        return self.detections[:, 5].astype(int) if len(self.detections) > 0 else np.empty(0, dtype=int)


# <<<<<<<<<<<< [结束：YOLOONNX 类定义] >>>>>>>>>>>>

if __name__ == '__main__':
    # 配置路径
    model_path = r"H:\pycharm_project\github_projects\PI-MAPP\project\Brain_Tumor_dection_ui\onnx_models\Brain_Tumor.onnx"
    image_path = r"H:\YOLO_Datasets\BrainTumor\BrainTumorYolov8_copy\test\images\10_jpg.rf.efaf1af26de11dabdda3214f4457c931.jpg"

    # 初始化模型（注意：替换为你真实的类别名！）
    yolo = YOLOONNX(model_path, class_names=[
        'glioma', 'meningioma', 'pituitary'
    ], conf_thres=0.5)

    # 推理
    results = yolo(image_path, conf=0.5)
    result = results[0]
    result_img = result.plot()

    # === 可视化方式 1：用 OpenCV 显示（按任意键关闭）===
    cv2.imshow("Brain Tumor Detection (ONNX)", result_img)
    print("按任意键关闭窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # === 可视化方式 2：用 Matplotlib 显示（适合 Jupyter 或无 GUI 环境）===
    # plt.figure(figsize=(12, 8))
    # plt.imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    # plt.axis('off')
    # plt.title("Brain Tumor Detection (ONNX)")
    # plt.show()

    # === 可选：保存结果图像 ===
    output_path = "detected_brain_tumor.jpg"
    cv2.imwrite(output_path, result_img)
    print(f"检测结果已保存至: {output_path}")

    # 打印检测信息
    xyxy = result.boxes.xyxy
    conf = result.boxes.conf
    cls_ids = result.boxes.cls
    names = [result.names[cls.item()] for cls in cls_ids]
    print("\n检测结果:")
    for i in range(len(xyxy)):
        print(f"  {names[i]} | 置信度: {conf[i]:.2f} | 框: {xyxy[i]}")
