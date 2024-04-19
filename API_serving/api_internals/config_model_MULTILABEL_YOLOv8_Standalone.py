import cv2
from pathlib import Path

import numpy as np

import onnxruntime as rt
from ultralytics import YOLO


class MultiLabel_YOLOv8_Standalone:

    def __init__(self, model_path):

        print("init_YOLO", model_path)

        self.model_path = model_path
        self.model_name = Path(model_path).name
        self.input_size = (640, 640) # W, H

        self.model = YOLO(model_path)
        self.class_names = self.model.names

    def predict(self, filtered_files, *args, **kwargs):
        print("infer_YOLO")

        # -- Prepare images
        preprocessed_data = [self.__preprocessing(x) for x in filtered_files]
        preprocessed_files, original_ratios = list(map(list, zip(*preprocessed_data)))

        # -- Infer
        results = self.model.predict(
            preprocessed_files, conf=0.25, agnostic_nms=True
        )  # TODO not sure we need agnostic_nms with Yolo v8

        return self.__format_results(results, original_ratios)

    def __preprocessing(self, file):

        nparr = file['buffer'] # nparr = np.frombuffer(file.read(), np.uint8)
        image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        resized = cv2.resize(
            image_bytes, self.input_size, interpolation=cv2.INTER_LINEAR
        )

        ratioW = image_bytes.shape[0] / self.input_size[0]
        ratioH = image_bytes.shape[1] / self.input_size[1]

        return resized, (ratioW, ratioH)

    def __format_results(self, results, original_ratios):
        print("format_results_YOLO")

        images = []
        for i, r in enumerate(results):
            detects = []

            for box in r.boxes:

                coords_ratio = box.xyxy[0].tolist()
                coords_ratio[0] *= original_ratios[i][1]
                coords_ratio[1] *= original_ratios[i][0]
                coords_ratio[2] *= original_ratios[i][1]
                coords_ratio[3] *= original_ratios[i][0]

                detect = {
                    # get box coordinates in (top, left, bottom, right) format
                    "coords": coords_ratio,
                    "type": self.class_names[int(box.cls)],
                    "probability": float(box.conf[0]),
                }
                detects.append(detect)

            images.append(detects)

        return images


# The YOLOv8 ONNX format has known issues:
# https://github.com/ultralytics/ultralytics/issues/1856
#
# class MultiLabel_YOLOv8_Standalone_ONNX:
# 
#     def __init__(self, model_path):
# 
#         print("init_YOLO_ONNX", model_path)
# 
#         self.model_path = model_path
#         self.model_name = Path(model_path).name
#         self.input_size = (640, 640) # W, H
# 
#         print("ONNX:", rt.get_device())
# 
#         providers = [
#             # "TensorrtExecutionProvider",
#             # "CUDAExecutionProvider",
#             "CPUExecutionProvider",
#         ]
# 
#         self.model = rt.InferenceSession(
#             str(model_path), providers=providers
#         )
# 
# 
#         self.input_name = self.model.get_inputs()[0].name
#         self.output_name = self.model.get_outputs()[0].name
# 
#         # props = { p.key : p.value for p in self.model.metadata_props }
#         # props = { p.key : p.value for p in self.model._model_meta }
#         # if 'names' in props:
#         # self.class_names = ast.literal_eval(props['names'])
#         # self.class_names = props['names']
#         # self.class_names = ['spatter', 'irregular_bead', 'slag', 'start_stop_overlap','porosity_burn_through']
#         # List of classes where the index match the class id in the ONNX network
#         # model = Path(model_path)
#         # self.class_names = model.parent.joinpath("classes.names").read_text().split("\n")
#         # print(self.class_names)
# 
#     def predict(self, filtered_files):
#         print("infer_YOLO_ONNX")
# 
#         # -- Prepare images
#         preprocessed_data = [self.__preprocessing(x) for x in filtered_files]
#         preprocessed_files, original_ratios = list(map(list, zip(*preprocessed_data)))
#         preprocessed_files = np.transpose(preprocessed_files, [0, 3, 1, 2])
# 
#         # -- Infer
#         print("SHAPE:",preprocessed_files.shape)
#         results = self.model.run([self.output_name], {self.input_name: preprocessed_files})[0]
#         print("TEST:", len(results))
# 
#         return self.__format_results(results, original_ratios)
# 
# 
#     def __preprocessing(self, file):
# 
#         nparr = file['buffer'] # nparr = np.frombuffer(file.read(), np.uint8)
#         image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
# 
#         resized = cv2.resize(
#             image_bytes, self.input_size, interpolation=cv2.INTER_LINEAR
#         ).astype(np.float32)
#         # ).astype(np.float16)
#         # print(resized.shape)
#         # resized = np.moveaxis(resized, -1, 0)
#         # print(resized.shape)
# 
# 
#         ratioW = image_bytes.shape[0] / self.input_size[0]
#         ratioH = image_bytes.shape[1] / self.input_size[1]
# 
#         return resized, (ratioW, ratioH)
# 
# 
#     def __parse_row(self, row):
# 
#         print("PARSE_ROW")
#         print(len(row))
# 
#         img_width = self.input_size[0]
#         img_height = self.input_size[1]
#         threshold = 0.5
# 
#         # Filter out object confidence scores below threshold
#         predictions = np.squeeze(row[0]).T
#         scores = np.max(predictions[:, 4:], axis=1)
#         predictions = predictions[scores > threshold, :]
#         scores = scores[scores > self.conf_threshold]
# 
#         print("scores:", scores)
#         print("predictions:", predictions)
# 
#         # xc,yc,w,h = row[:4]
#         # x1 = (xc-w/2)/640*img_width
#         # y1 = (yc-h/2)/640*img_height
#         # x2 = (xc+w/2)/640*img_width
#         # y2 = (yc+h/2)/640*img_height
#         # prob = row[4:].max()
#         # class_id = row[4:].argmax()
#         # #label = yolo_classes[class_id]
#         # return [x1,y1,x2,y2,class_id,prob]
# 
# 
#     def __format_results(self, results, original_ratios):
#         print("format_results_YOLO_ONNX")
# 
#         images = []
#         for i, r in enumerate(results):
#             detects = []
# 
#             print("r.attributs:", r)
#             print("LEN R:", len(r))
#             boxes = [row for row in [self.__parse_row(row) for row in r] if row[5]>0.5]
#             print("LEN BOXES:", len(boxes))
# 
# 
#             for box in boxes:
# 
#                 coords_ratio = box[0:4]
#                 coords_ratio[0] *= original_ratios[i][1]
#                 coords_ratio[1] *= original_ratios[i][0]
#                 coords_ratio[2] *= original_ratios[i][1]
#                 coords_ratio[3] *= original_ratios[i][0]
# 
#                 detect = {
#                     # get box coordinates in (top, left, bottom, right) format
#                     "coords": coords_ratio,
#                     "type": self.class_names[int(box[4])],
#                     "probability": float(box[5]),
#                 }
#                 detects.append(detect)
# 
#             images.append(detects)
# 
#         return images
