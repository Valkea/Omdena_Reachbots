# from ultralytics import YOLO

import io
from pathlib import Path

import onnxruntime as rt
import numpy as np

from torchvision import transforms
from PIL import Image


class BinaryClassifier():

    def __init__(self, model_path):

        print("init_BINARY", model_path)

        self.model_path = model_path
        self.model_name = Path(model_path).name

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

    def __transform_image_from_bytes(self, file):

        # -- Read image using PIL (from buffer)
        nparr = file['buffer'] # np.frombuffer(file.read(), np.uint8)
        img = Image.open(io.BytesIO(nparr))

        # -- Define PyTorch transformations
        transform = transforms.Compose([
            transforms.Resize((580, 580)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # -- Apply transformations
        img = transform(img)

        return img

    # def __transform_image_from_path(self, image_path):
    # 
    #     # -- Read image using PIL
    #     img = Image.open(str(image_path)).convert('RGB')
    # 
    #     # -- Define PyTorch transformations
    #     transform = transforms.Compose([
    #         transforms.Resize((580, 580)),
    #         transforms.ToTensor(),
    #         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    #     ])
    # 
    #     # -- Apply transformations
    #     img = transform(img)
    #     img = img.unsqueeze(0)  # Add a batch dimension
    # 
    #     return img

    def predict(self, filtered_files, pred_threshold = 0.5):
        print("infer_BINARY_CLASSIFIER ", pred_threshold)

        # -- Prepare images
        preprocessed_files = [self.__transform_image_from_bytes(x) for x in filtered_files]

        # -- Infer
        results = self.model.run([self.output_name], {self.input_name: preprocessed_files})[0]

        return self.__format_results(results, filtered_files, pred_threshold)

    def __format_results(self, results, filtered_files, threshold):
        print("format_results_BINARY_CLASSIFIER")

        predictions = np.where(results > threshold, 1, 0)
        # print("PREDS:", predictions)
        # labels = np.where(predictions == 0, "Defect", "No defect" )
        # print("LABELS:", labels)

        images = []
        defect_indexes = []
        for i, r in enumerate(results):

            has_defect = not bool(predictions[i])
            if has_defect:
                defect_indexes.append(i)

            binary_score = prob = r[0]
            if predictions[i] == 0: # Defect
                prob = 1.0 - prob

            defect = {
                'file': filtered_files[i]['filename'],
                'has_defect': has_defect,
                'score': float(binary_score),
                'probability': float(prob),
            }
            images.append(defect)

        return images, defect_indexes
