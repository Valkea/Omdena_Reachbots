import io
from pathlib import Path

import onnxruntime as rt
import numpy as np
import cv2
from PIL import Image

from api_internals.LaserProfileTransformation import transform_frame


class Laser_Multiclass_MobileNet:

    def __init__(self, model_path):

        print("init_laser_MOBILENET", model_path)

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
        self.class_names = ['Irregular_Bead', 'Porosity_Burn_Through', 'Start_Stop_Overlap']

    def predict(self, filtered_files, binary_defect_indexes, slide_step=3, defects_threshold=1, pred_threshold=0.5):
        print("infer_laser_MOBILENET", defects_threshold, pred_threshold)

        if len(filtered_files) < 10:
            return []

        # -- Pre process all images
        preprocessed_files_all = []
        for filtered_img in filtered_files:
            preprocessed_files_all.append(self.__preprocessing(filtered_img))

        # -- Prepare batches of 10 images
        preprocessed_batch = []
        batch_indexes = []

        binary_defect_bools = [1 if x in binary_defect_indexes else 0 for x in range(len(filtered_files))]
        i = 0
        while i+10 <= len(filtered_files):

            binary_defect_values = binary_defect_bools[i:i+10]
            num_defects_in_batch = np.array(binary_defect_values).sum()
            print("NUM_DEFECTS_IN_BATCH:", num_defects_in_batch)

            indexes = []

            if num_defects_in_batch >= defects_threshold:
                selected_files = []
                for j, processed_img in enumerate(preprocessed_files_all):

                    if processed_img is not None:
                        selected_files.append(processed_img)
                        indexes.append(i+j)
                    if len(selected_files) == 10:
                        break

                preprocessed_batch.append(selected_files)
                batch_indexes.append(indexes)

            else:
                preprocessed_batch.append([])

            i += slide_step

        # print("PREPROCESSED_BATCH:", preprocessed_batch)

        # -- Infer
        preprocessed = [x for x in preprocessed_batch if len(x) > 0]
        results = []
        if len(preprocessed) > 0:
            results = self.model.run([self.output_name], {self.input_name: preprocessed})[0]

        # -- Prepare results
        r = [results[j] if len(x) > 0 else None for j, x in enumerate(preprocessed_batch)]

        print("RESULTS:", r)
        return self.__format_results(r, batch_indexes, pred_threshold)


    def __preprocessing(self, file, img_shape=224):

        nparr = file['buffer'] # np.frombuffer(file.read(), np.uint8)
        image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        #///img = cv2.imread(img_path)

        gray_frame = cv2.cvtColor(image_bytes, cv2.COLOR_BGR2GRAY)
        gray_transformed_frame = transform_frame(gray_frame)
        # gray_transformed_frame = transform_frame(image_bytes)

        if gray_transformed_frame is None:
            return None
        #     frames_passed += 1
        #     continue

        rgb_transformed_frame = cv2.cvtColor(gray_transformed_frame, cv2.COLOR_GRAY2RGB)

        # Resize the Frame to fixed Dimensions.
        resized_frame = cv2.resize(rgb_transformed_frame, self.input_size)

        # Normalize the resized frame
        normalized_frame = resized_frame / 255.0
        return normalized_frame


        # -- Read image using PIL (from buffer)
        # nparr = file['buffer'] # np.frombuffer(file.read(), np.uint8)
        # image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # resized = cv2.resize(
        #     image_bytes, self.input_size, interpolation=cv2.INTER_LINEAR
        # ).astype(np.float32)

        # return resized


    def __format_results(self, results, batch_indexes, pred_threshold):
        print("format_results_laser_MOBILENET")

        images = []

        for i, result in enumerate(results):
            image_names = []
            batch_index = batch_indexes[i] if len(batch_indexes) > 0 else (0,0,0)

            defect = {
                'indexes': batch_index,
                'has_defect': None,
                'type': None,
                'probability': None,
                'score': None,
            }

            if result is None:
                defect['type'] = 'no_pred'
            else:
                probabilities = np.array(result)
                max_value = np.max(probabilities)
                max_index = np.argmax(probabilities)

                if max_value > pred_threshold:
                    defect['type'] = self.class_names[max_index]
                    defect['has_defect'] = True
                else:
                    defect['type'] = 'no_defect_found'
                    defect['has_defect'] = False

                proba = float(probabilities[max_index])
                defect['score'] = proba

                if defect['has_defect']:
                    defect['probability'] = proba
                else:
                    defect['probability'] = 1.0 - proba

            images.append(defect)

        print("IMAGES:", images)
        return images
