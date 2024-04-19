# from ultralytics import YOLO
import io
from pathlib import Path
from typing import Union, Optional
from importlib.util import find_spec

import albumentations as A
import numpy as np

# import onnxruntime as rt
from openvino.runtime import Core

# from anomalib.data.utils import get_image_filenames
from anomalib.deploy.inferencers.base_inferencer import Inferencer
from anomalib.data.utils import read_image
# from anomalib.post_processing import Visualizer
# from anomalib.post_processing import ImageResult

from api_internals.LaserProfileTransformation import transform_frame

from PIL import Image


class LaserBinaryClassifier(Inferencer):

    def __init__(self, model_path, metadata_path) -> None:

        print("init_laserBINARY", model_path)

        self.model_path = model_path
        self.model_name = Path(model_path).name

        self.device = 'CPU'

        self.input_name, self.output_name, self.model = self.load_model(model_path)
        self.metadata = super()._load_metadata(metadata_path)

    def load_model(self, path: Union[str, Path]):

        # -- Define and load model
        ie_core = Core()
        model = ie_core.read_model(path)
        compile_model = ie_core.compile_model(model=model, device_name=self.device)

        # -- Create cache folder
        # cache_folder = Path("cache")
        # cache_folder.mkdir(exist_ok=True)
        # ie_core.set_property({"CACHE_DIR": cache_folder})

        # -- Return in/out layers blobs and model
        input_blob = compile_model.input(0)
        output_blob = compile_model.output(0)
        return input_blob, output_blob, compile_model

    def pre_process(self, image: np.ndarray) -> np.ndarray:

        image = transform_frame(image) # needed for extra processing

        transform = A.from_dict(self.metadata["transform"])
        processed_image = transform(image=image)["image"]

        if len(processed_image.shape) == 3:
            processed_image = np.expand_dims(processed_image, axis=0)

        if processed_image.shape[-1] == 3:
            processed_image = processed_image.transpose(0, 3, 1, 2)

        processed_image = np.repeat(processed_image, 3, axis=1) # needed for extra processing
        return processed_image

    def forward(self, image: np.ndarray) -> np.ndarray:
        return self.model(image)

    def post_process(self, predictions: np.ndarray):

        predictions = predictions[self.output_name]

        # -- Initialize the result variables.

        anomaly_map = None
        pred_label = None
        pred_score = None

        if len(predictions.shape) > 1:
            anomaly_map = predictions.squeeze()
            pred_score = anomaly_map.reshape(-1).max()
        if "image_threshold" in self.metadata:
            pred_label = pred_score >= self.metadata["image_threshold"]
            anomaly_map, pred_score = self._normalize(pred_scores=pred_score,
                                                      anomaly_maps=anomaly_map,
                                                      metadata=self.metadata)
            assert anomaly_map is not None

        return {
            "anomaly_map": anomaly_map,
            "pred_label": pred_label,
            "pred_score": pred_score,
        }

    def predict(self, filtered_files, pred_threshold = 0.5):
        print("infer_laser_BINARY_CLASSIFIER", pred_threshold)

        results = []
        for file in filtered_files:
            image_arr = np.array(file['buffer'])
            img = Image.open(io.BytesIO(image_arr))
            # img = img.convert('RGB')
            image_arr = np.array(img)
            # self.metadata["image_shape"] = image_arr.shape[:2]

            processed_image = self.pre_process(image_arr)
            predictions = self.forward(processed_image)
            output = self.post_process(predictions)

            results.append(output['pred_score'])

        results = np.array(results)
        return self.__format_results(results, filtered_files, pred_threshold)

    def __format_results(self, results, filtered_files, pred_threshold):
        print("format_results_laser_BINARY_CLASSIFIER", pred_threshold)

        predictions = np.where(results > pred_threshold, 0, 1)
        # print("PREDS:", predictions)
        # labels = np.where(predictions == 0, "Defect", "No defect" )
        # print("LABELS:", labels)

        images = []
        defect_indexes = []
        for i, r in enumerate(results):

            has_defect = not bool(predictions[i])
            if has_defect:
                defect_indexes.append(i)

            binary_score = prob = r
            if predictions[i] == 1: # Defect
                prob = 1.0 - prob

            defect = {
                "file": filtered_files[i]['filename'],
                "has_defect": has_defect,
                "score": float(binary_score),
                "probability": float(prob),
            }
            images.append(defect)

        return images, defect_indexes
