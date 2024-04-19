import json
import time

from api_internals.config_model_laser_BINARY import LaserBinaryClassifier
from api_internals.utils import perenize_buffers, ModelSelector, make_gif

laser_model_selector = ModelSelector(category='laser')


# --- MAIN FUNCTION

def predict_defects_laser(
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
    results_json = []

    if len(filtered_files) < 10:
        raise Exception("The Laser pipeline need batches with at least 10 images")

    # --- CAST EXTRA INFO TO THE EXPECTED FORMAT

    slide_step = extra_info['slide_step']
    slide_step = int(slide_step) if slide_step else 3

    min_defects = extra_info['min_defects']
    min_defects = int(min_defects) if min_defects else 1

    binary_threshold = extra_info['binary_threshold']
    binary_threshold = float(binary_threshold) if binary_threshold else 0.5

    multi_threshold = extra_info['multi_threshold']
    multi_threshold = float(multi_threshold) if multi_threshold else 0.4

    # --- PERENIZE THE UPLOADED FILES SO THAT WE CAN APPLY SEVERAL MODELS

    images_bytes = perenize_buffers(filtered_files)

    # --- USE BINARY MODEL

    bc = LaserBinaryClassifier(
            'models/laser_binary_classifier.onnx',
            'models/laser_binary_classifier_metadata.json'
            )

    results_binary, defect_indexes = bc.predict(images_bytes, pred_threshold=binary_threshold)
    used_models = [bc.model_name]


    # --- LOAD THE SELECTED MULTICLASS MODEL AND INFER

    used_models.append(extra_info['selected_model'])
    laser_model_selector.set_current_model_id(extra_info["selected_model"])
    results_multi = laser_model_selector.predict_current(
            images_bytes,
            defect_indexes,
            slide_step = slide_step,
            defects_threshold = min_defects,
            pred_threshold = multi_threshold,
    )

    for i, result_multi in enumerate(results_multi):


        batch_index_l, *_, batch_index_r = result_multi['indexes']

        # gif = make_gif([x for j, x in enumerate(images_bytes) if j in result_multi['indexes']])
        # result_multi['gif'] = gif

        node = {
            "binary_results": results_binary[batch_index_l:batch_index_r+1],
            "multi_results": result_multi,
        }

        results_json.append(node)

    inference_time = time.time() - start_time
    return results_json, inference_time, used_models
