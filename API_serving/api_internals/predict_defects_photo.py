import json
import time

from api_internals.config_model_BINARY import BinaryClassifier
from api_internals.utils import perenize_buffers, ModelSelector

photo_model_selector = ModelSelector(category='photo')


# --- MAIN FUNCTION

def predict_defects_photo(
    filtered_files: list,
    extra_info: dict,
) -> list:
    """
    Predicts defects and their probability levels for given preprocessed files.

    Parameters
    ----------
    filtered_files: list
        A list of the filtered files so that we can return the name of the original files.
    extra_info: dict
        A dictionary containing extra information useful for the prediction.

    Returns
    -------
    list
        A list of predicted defects, where each item is a dictionary containing the following information:
            - type: (str) The type of defect.
            - coords: (list) The coordinates of the defect in (top, left, bottom, right) format.
            - file: (str) The name of the file the defect was predicted from.
            - probable_duplicate: (bool) True if the predicted defect for a given class
            already reached the limit in the BATCH of images (they are ordered by probability score)
    """

    start_time = time.time()

    # --- CAST EXTRA INFO TO THE EXPECTED FORMAT

    binary_threshold = extra_info['binary_threshold']
    binary_threshold = float(binary_threshold) if binary_threshold else 0.5

    multi_threshold = extra_info['multi_threshold']
    multi_threshold = float(multi_threshold) if multi_threshold else 0.5

    # --- PERENIZE THE UPLOADED FILES SO THAT WE CAN APPLY SEVERAL MODELS

    images_bytes = perenize_buffers(filtered_files)

    # --- USE BINARY MODEL

    bc = BinaryClassifier('models/binary_classifier.onnx')
    results_binary, defect_indexes = bc.predict(images_bytes, pred_threshold=binary_threshold)
    used_models = [bc.model_name]

    if len(defect_indexes) > 0 :

        used_models.append(extra_info['selected_model'])

        # --- SELECT THE IMAGES CONTAINING DEFECT AS PER THE BINARY CLASSIFIER

        sub_filtered_files = [images_bytes[x] for x in defect_indexes]

        # --- LOAD THE SELECTED MULTILLABEL MODEL AND INFER

        photo_model_selector.set_current_model_id(extra_info["selected_model"])
        results_multi = photo_model_selector.predict_current(sub_filtered_files, pred_threshold=multi_threshold)

        for i, result_multi in enumerate(results_multi):

            if len(result_multi) == 0:
                value = "NO defect found with the MULTILABEL model"
            else:
                value = result_multi

            results_binary[defect_indexes[i]]['defect_list'] = value

    inference_time = time.time() - start_time
    return results_binary, inference_time, used_models
