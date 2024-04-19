import io
from pathlib import Path

import onnxruntime as rt
import numpy as np
import cv2
from PIL import Image


class MultiLabel_MobileNet:

    def __init__(self, model_path):

        print("init_MOBILENET", model_path)

        self.model_path = model_path
        self.model_name = Path(model_path).name
        self.input_size = (224, 224) # W, H

        print("ONNX:", rt.get_device())

        providers = [
            # "TensorrtExecutionProvider",
            # "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]

        self.model = rt.InferenceSession(
            str(model_path), providers=providers
        )

        self.input_name = self.model.get_inputs()[0].name
        self.output_name = self.model.get_outputs()[0].name
        self.class_names = [
                'spatter',
                'irregular_bead',
                'slag',
                'start_stop_overlap',
                'porosity_burn_through'
        ]

    def predict(self, filtered_files, pred_threshold = 0.3):
        print("infer_MOBILENET ", pred_threshold)


        # -- Prepare images
        preprocessed_data = [self.__preprocessing(x) for x in filtered_files]
        preprocessed_files, original_ratios = list(map(list, zip(*preprocessed_data)))


        # img = load_and_prep_image(filename)
        # img_expanded = np.expand_dims(img, axis=0).astype(np.float32)  # ONNX expects float32 type

        # Use ONNX Runtime for prediction
        # input_name = session.get_inputs()[0].name
        # output_name = session.get_outputs()[0].name
        # Model_Predictions_Prob = session.run([output_name], {input_name: img_expanded})[0]

        # -- Infer
        results = self.model.run([self.output_name], {self.input_name: preprocessed_files})[0]

        return self.__format_results(results, original_ratios, pred_threshold)


    def __preprocessing(self, file, img_shape=224):

        # -- Read image using PIL (from buffer)
        nparr = file['buffer'] # np.frombuffer(file.read(), np.uint8)
        image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        resized = cv2.resize(
            image_bytes, self.input_size, interpolation=cv2.INTER_LINEAR
        )

        ratioW = image_bytes.shape[0] / self.input_size[0]
        ratioH = image_bytes.shape[1] / self.input_size[1]

        return resized, (ratioW, ratioH)

        # img = cv2.imread(filename)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img = cv2.resize(img, (img_shape, img_shape))
        # img = img / 255.0
        # img_expanded = np.expand_dims(img, axis=0).astype(np.float32)  # ONNX expects float32 type
        # return img_expanded

    def __format_results(self, results, original_ratios, threshold):
        print("format_results_MOBILENET")

        images = []

        for i, result in enumerate(results):
            detects = []

            predictions = [ 1 if x > threshold else 0 for x in result ]
            probabilities = [ x for x in result ]
            classes = [x for i, x in enumerate(self.class_names) if predictions[i] == 1]

            for j, defect in enumerate(classes):
                detect = {
                    # get box coordinates in (top, left, bottom, right) format
                    # "coords": [],
                    "type": classes[j],
                    "probability": float(probabilities[j]),
                }
                detects.append(detect)

            images.append(detects)

        return images
