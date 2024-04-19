#! /usr/bin/env python3
# coding: utf-8

import io
import json
import base64

from flask import request

from PIL import Image
import cv2
import numpy as np

from api_internals.config_model_MULTILABEL_YOLOv8_Standalone import *
from api_internals.config_model_MULTILABEL_YOLOv8_SAHI import *
from api_internals.config_model_MULTILABEL_MobileNet import *
from api_internals.config_model_laser_MULTICLASS_MobileNet import *


ALLOWED_EXTENSIONS = {
    "bmp",
    "dng",
    "jpeg",
    "jpg",
    "mpo",
    "png",
    "tif",
    "tiff",
    "webp",
    "pfm",  # images
    # "asf",
    # "avi",
    # "gif",
    # "m4v",
    # "mkv",
    # "mov",
    # "mp4",
    # "mpeg",
    # "mpg",
    # "ts",
    # "wmv",
    # "webm",  # videos
}

# --- DEFINE FUNCTIONS


def allowed_file(filename):
    """
    Check if a file is allowed based on its extension.

    Parameters
    ----------
    filename : str
        The name of the file to check.

    Returns
    -------
    bool
        True if the file extension is allowed, False otherwise.
    """

    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def filter_images(f):
    """
    Check weither or not the provided file is compatible with the models.

    Parameters
    ----------
    f : file object
        A file object of an image to be filtered.

    Returns
    -------
    bool
        True if the file extension is allowed, False otherwise.
    """

    return allowed_file(f.filename)


def check_uploaded_files(request: request) -> list:
    """
    Check if files were uploaded properly and if they have compatible formats.

    Parameters
    ----------
    request : request
        The Flask request object containing the files to check.

    Returns
    -------
    list
        A list of file objects that have a compatible format.

    Raises
    ------
    BadRequest
        If the 'file' form-data field is missing or contains no data.
    BadRequest
        If none of the uploaded files have a compatible format.
    """

    # --- CHECK IF THE POST REQUEST HAS THE FILE PART

    if "file" not in request.files:
        print("No file part")
        abort(400, description="The 'file' form-data field is missing in the request.")

    # --- CHECK IF THE FILEPART CONTAINS DATA

    files = request.files.getlist("file")
    if len(files) == 1 and files[0].filename == "":
        print("No data into the filepart")
        abort(400, description="There is no data in the 'file' form-data field.")
    else:
        print(f"There are {len(files)} files in the filepart")

    # --- CHECK IF THERE IS AT LEAST ONE FILE WITH A COMPATIBLE FORMAT

    filtered_files = list(filter(filter_images, files))
    if len(filtered_files) == 0:
        print("The provided format is not supported")
        abort(400, description="The provided file(s) format is not supported.")

    return filtered_files


def perenize_buffers(filtered_files):
    """
    Save the uploaded files buffers to a new structure so that we can use them with several models
    (Otherwise the FileBuffer is consumed/deleted after the first read)

    Parameters
    ----------
    filtered_files : list of str
        A list of file paths of images to be preprocessed.

    Returns
    -------
    list of dictionaries
        each dictionary containing tww keys:
        - "buffer" the file buffer
        - "filename" the file name
    """
    return [{'buffer':np.frombuffer(f.read(), np.uint8), 'filename':f.filename} for f in filtered_files]



def convertImageToDataUri(imagePath):
    encoded = base64.b64encode(open(imagePath, "rb").read())
    return 'data:image/gif;base64,{}'.format(encoded)

def make_gif(filtered_files):

    # frames = [Image.open(image) for image in glob.glob(f"{frame_folder}/*.JPG")]
    frames = []
    for file in filtered_files:
        image_bytes = Image.open(io.BytesIO(file['buffer']))
        # nparr = file['buffer'] # np.frombuffer(file.read(), np.uint8)
        # image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        frames.append(image_bytes)

    frame_one = frames[0]
    frame_one.save(f"laser.gif", format="GIF", append_images=frames, save_all=True, duration=250, loop=0)


    img = Image.open('laser.gif')
    data_url = convertImageToDataUri('laser.gif')
    return data_url


# def preprocess_image(file, height, width):
#     """
#     Preprocess an image file.
# 
#     Parameters
#     ----------
#     file : file object
#         A file object of an image to be preprocessed.
#     height : int
#         The vertical size of the image expected by the model
#     width : int
#         The horizontal size of the image expected by the model
# 
#     Returns
#     -------
#     tuple of (ndarray, tuple)
#         A tuple containing two elements:
#         - resized (ndarray): A preprocessed image.
#         - ratioW, ratioH (tuple): A tuple of ratios for the original image.
#     """
# 
#     # Open POST file with PIL
#     # image_bytes = Image.open(io.BytesIO(file.read()))
# 
#     # Open POST file with CV2
#     nparr = np.frombuffer(file.read(), np.uint8)
#     image_bytes = Image.open(io.BytesIO(nparr))
# 
#     # nparr = np.frombuffer(file.read(), np.uint8)
#     # print(nparr)
#     # image_bytes = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
# 
#     newSizeH = height # 1920
#     newSizeW = width # 1080 
#     resized = cv2.resize(
#         image_bytes, (newSizeH, newSizeW), interpolation=cv2.INTER_LINEAR
#     )
# 
#     ratioW = image_bytes.shape[0] / newSizeW
#     ratioH = image_bytes.shape[1] / newSizeH
# 
#     return resized, (ratioW, ratioH)
# 
# 
# def prepare_images(filtered_files, height, width):
#     """
#     Preprocess a batch of images.
# 
#     Parameters
#     ----------
#     filtered_files : list of str
#         A list of file paths of images to be preprocessed.
#     height : int
#         The vertical size of the image expected by the model
#     width : int
#         The horizontal size of the image expected by the model
# 
#     Returns
#     -------
#     tuple of (list, list)
#         A tuple containing two lists:
#         - preprocessed_files (list): A list of preprocessed image files.
#         - original_ratios (list): A list of image ratios to recover the original positions/sizes.
#     """
# 
#     print(filtered_files)
# 
#     preprocessed_data = [preprocess_image(x, height, width) for x in filtered_files]
#     preprocessed_data = list(map(list, zip(*preprocessed_data)))
# 
#     preprocessed_files, original_ratios = preprocessed_data[0], preprocessed_data[1]
# 
#     return preprocessed_files, original_ratios

# --- SELECT MODEL

# models = {}
# with open("models.json") as json_file:
#     models = json.load(json_file)

class ModelSelector:

    def __init__(self, category, current_model_id=None):

        self.models= {}

        with open("models.json") as json_file:
            models_json = json.load(json_file)
            models_def = {}

            for m_id in models_json:
                if models_json[m_id]['category'] == category:
                    models_def[m_id] = models_json[m_id]

        self.models_def = models_def
        self.last_model_id = None
        self.set_current_model_id(current_model_id)

    def get_models(self):
        return {x: self.models_def[x]["label"] for x in self.models_def}

    def set_current_model_id(self, model_id):
        if model_id is None:
            model_id = list(self.models_def.keys())[-1]

        self.current_model_id = model_id

    def get_current_model_id(self):
        return self.current_model_id

    def get_current_model(self):
        if self.current_model_id not in self.models:
            self.models[self.current_model_id] = eval(f"{self.models_def[self.current_model_id]['class']}('models/{self.current_model_id}')")

        return self.models[self.current_model_id]


    def predict_current(self, filtered_files, *args, **kwargs):

        defect_model = self.get_current_model()
        return defect_model.predict(filtered_files, *args, **kwargs)
