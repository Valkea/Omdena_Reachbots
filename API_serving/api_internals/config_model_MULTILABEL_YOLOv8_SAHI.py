import cv2
from pathlib import Path

from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction, predict

# import onnxruntime as rt
from ultralytics import YOLO


class MultiLabel_YOLOv8_SAHI:

    def __init__(self, model_path):

        print("init_YOLO_SAHI", model_path)

        self.model_path = model_path
        self.model_name = Path(model_path).name

        # self.input_size = (640, 540) # W, H
        # self.input_size = (1920, 1080) # W, H
        # print("ONNX:", rt.get_device())

        defect_model = YOLO(model_path)
        self.class_names = defect_model.names

        self.model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=model_path,
            confidence_threshold=0.3,
            device="cpu",  # or 'cuda:0'
        )

        # self.model.names = class_names

    def predict(self, filtered_files, *args, **kwargs):
        print("infer_YOLO SAHI")

        # -- Prepare images
        preprocessed_data = [self.__preprocessing(x) for x in filtered_files]
        preprocessed_files, original_ratios = list(map(list, zip(*preprocessed_data)))

        # -- Infer
        results = []
        for file in preprocessed_files:
            result = get_sliced_prediction(
                file,
                self.model,
                slice_height=512,
                slice_width=512,
                overlap_height_ratio=0.2,
                overlap_width_ratio=0.2,
            )
            results.append(result.object_prediction_list)

        return self.__format_results(results, original_ratios)

    def __preprocessing(self, file):

        nparr = file['buffer'] # nparr = np.frombuffer(file.read(), np.uint8)
        image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # resized = cv2.resize(
        #     image_bytes, self.input_size, interpolation=cv2.INTER_LINEAR
        # )

        # ratioW = image_bytes.shape[0] / self.input_size[1]
        # ratioH = image_bytes.shape[1] / self.input_size[0]

        resized = image_bytes
        ratioW = ratioH = 1.0

        return resized, (ratioW, ratioH)

    def __format_results(self, results, original_ratios):
        print("format_results_YOLO SAHI")

        images = []
        for i, r in enumerate(results):
            detects = []

            for box in r:

                coords_ratio = box.bbox.to_xyxy()
                coords_ratio[0] *= original_ratios[i][1]
                coords_ratio[1] *= original_ratios[i][0]
                coords_ratio[2] *= original_ratios[i][1]
                coords_ratio[3] *= original_ratios[i][0]

                detect = {
                    # get box coordinates in (top, left, bottom, right) format
                    "coords": coords_ratio,
                    "type": self.class_names[box.category.id],
                    "probability": float(box.score.value),
                }
                detects.append(detect)

            images.append(detects)

        return images


# The YOLOv8 ONNX format has known issues:
# https://github.com/ultralytics/ultralytics/issues/1856
# On our model we have [1,9, 3024].
# - 9 => 5 classes + 4 coords
# - 3024 => the three detection heads in YOLOv8 when the slice image size is 512
#
# class MultiLabel_YOLOv8_SAHI_ONNX(MultiLabel_YOLOv8_SAHI):
#     pass
