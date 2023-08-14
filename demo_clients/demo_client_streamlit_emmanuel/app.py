import os
import io
import requests
import numpy as np

from PIL import Image
import cv2

import streamlit as st
from streamlit_option_menu import option_menu

DEFAULT_URL = "http://0.0.0.0:5000"

os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = "10000"

colors = {
    "spatter": "FF0000",  # 921619 ~RED
    "porosity": "FFEC00",  # c6b80c ~YELLOW
    "irregular_bead": "0000FF",  # 095d87 ~BLUE
    "burn_through": "00BC5D",  # 09703c ~GREEN
    "undercut": "99B410",  # 7f8d36 ~YELLOW/GREEN
    "slag": "00FFFF",  # 99b410 ~CYAN
    "arc_strike": "C631C9",  # c631c9 ~MAGENTA
    "cracks": "C4ACB4",  # c4acb4 ~GREY
    "start_stop": "E6A22A",  # 917b54 ~GOLD
    "start_stop_overlap": "E6A22A",  # 917b54 ~GOLD /!\ OLD Label
    "overlap": "0B6B5F",  # 09443d ~DARK GREEN
    "gap": "0B6B5F",  # 09443d ~DARK GREEN /!\ OLD Label
    "others_not_classified": "0B6B5F",  # 0b6b5f ~ORANGE
    "toe_angle": "327A71",  # 09443d ~DARK GREEN
}


def hex_to_rgb(hex):
    """
    Convert hexadecimal color to RGB tuple

    Parameters
    ----------
    hex : str
        An hexadecimal color

    Returns
    -------
    tuple(int, int, int)
        A tuple with RED, GREEN and BLUE color values.
    """
    return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))


def draw_text(
    img,
    text,
    font=cv2.FONT_HERSHEY_PLAIN,
    pos=(0, 0),
    font_scale=3,
    font_thickness=2,
    text_color=(0, 255, 0),
    text_color_bg=(0, 0, 0),
):
    """
    Draw text with a background color

    Parameters
    ----------
    img : numpy.ndarray
        A cv2 source image
    text : str
        The text to write on the image
    pos : tuple(int, int)
        The starting position of the background (bottom, left)
    font_scale : int
        The text size
    font_thickness : int
        The text thickness
    text_color : tuple(int, int, int)
        The RGB values for the font color
    text_color_bg : tuple(int, int, int)
        The RGB valies for the background color

    Returns
    -------
    numpy.ndarray
        The original image modified with the text and background
    """

    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(img, pos, (x + text_w, y - text_h), text_color_bg, -1)
    cv2.putText(img, text, (x, y), font, font_scale, text_color, font_thickness)

    return img


def get_available_models():
    """
    Fetch the models available on the API

    Returns
    -------
    tuple of (dict, int)
        A tuple containing:
        - a dictionnary with the labels as key and the keys as values.
        - an integer corresponding to the index of the currently selected model (on API side).
    """

    # sending get request
    URL = st.session_state['API_URL'] + "/get_available_models"
    r = requests.get(url=URL)

    # extracting data in json format
    data = r.json()
    models = data["available_models"]

    # get current index
    current_index = list(models.keys()).index(data["current_model"])

    # inverse mapping
    models = {f"{v} [{k}]": k for k, v in models.items()}

    return models, current_index


def post_images(uploaded_files, selected_model):
    """
    Send the selected files to the API /predict_defects endpoint

    Parameters
    ----------
    uploaded_files : list of UploadedFile
        A list with the uploaded image files as UploadedFile objects.
    selected_model : str
        The model_id of the model to use for inference.

    Returns
    -------
    str
        A JSON string with the API answer.
    """

    # prepare data with multiple files
    files = [("file", x) for x in uploaded_files]
    print(files)

    # sending get request
    URL = st.session_state['API_URL'] + "/predict_defects"

    r = requests.post(
        URL,
        files=files,
        data={"selected_model": selected_model},
    )

    # extracting data in json format
    data = r.json()
    return data


def init():
    """
    Request the API base url
    """

    def go(base_url):
        available_models, current_index = get_available_models()
        main(base_url, available_models, current_index)

    if 'API_URL' in st.session_state:
        go(st.session_state['API_URL'])

    else:
        form_div = st.empty()
        form = form_div.form("url_form")
        base_url = form.text_input("**Base URL:**", DEFAULT_URL)
        submitted = form.form_submit_button("Submit")

        if submitted and base_url != "":
            try:
                st.session_state['API_URL'] = base_url
                go(base_url)
                form_div.empty()
            except Exception:
                st.write("Invalid URL:", base_url)
                del st.session_state["API_URL"]


def main(base_url, available_models, current_index):
    """
    Define the streamlit app layout and base actions
    """

    st.sidebar.write("API_URL:", st.session_state['API_URL'])

    # --- Side bar ---

    form = st.sidebar.form("pred_form")

    option = form.selectbox(
        label="Select a model",
        options=available_models,
        index=current_index,
    )

    show_labels = form.checkbox("Show labels on pictures", True)
    show_jsons = form.checkbox("Show defait details", False)
    show_json = form.checkbox("Show the whole JSON", False)

    uploaded_files = form.file_uploader("Choose image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    submitted = form.form_submit_button("Submit")

    if submitted:
        if len(uploaded_files) > 0:
            for uploaded_file in uploaded_files:
                print("TYPE:", uploaded_file.type)
            predict_and_draw(uploaded_files, available_models[option], show_labels, show_jsons, show_json)

    # --------------------

    form_v = st.sidebar.form("pred_formi_video")
    uploaded_video = form_v.file_uploader("Choose video", type=["mp4", "mov"])
    submitted_v = form_v.form_submit_button("Submit")
    frame_skip = 300 # display every 300 frames

    if submitted_v and uploaded_video is not None: # run only when user uploads video
        vid = uploaded_video.name
        with open(vid, mode='wb') as f:
            f.write(uploaded_video.read()) # save video to disk
    
        st.markdown(f"""
        ### Files
        - {vid}
        """,
        unsafe_allow_html=True) # display file name
    
        vidcap = cv2.VideoCapture(vid) # load video from disk
        cur_frame = 0
        success = True

        vid_div = st.empty()
    
        while success:
            success, frame = vidcap.read() # get next frame from video
            if cur_frame % frame_skip == 0: # only analyze every n=300 frames
                print('frame: {}'.format(cur_frame))
                # pil_img = Image.fromarray(frame) # convert opencv frame (with type()==numpy) into PIL Image

                is_success, buffer = cv2.imencode(".jpg", frame)
                io_buf = io.BytesIO(buffer)
                io_buf.name = "Blop2.png"

                #with open("Blop.png", "wb") as f:
                #    f.write(io_buf.getvalue())

                ups = [io_buf]
                predict_and_draw(ups, available_models[option], show_labels, show_jsons, show_json)
                # vid_div.image(pil_img)
                # vid_div.image(io_buf.getvalue())
            cur_frame += 1

    # --- Center ---
    # st.text("Hello world")


def predict_and_draw(uploaded_files, selected_model, show_labels, show_jsons, show_json):

    json = post_images(uploaded_files, selected_model)
    print(json)
    defects = json["defects"]
    
    for file in uploaded_files:
        print("D01", type(file))
        image = Image.open(file)
        image = image.save("img.jpg")
        print("D02", type(file))
    
        # Reading an image in default mode
        image = cv2.imread("img.jpg")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
        # Window name in which image is displayed
        window_name = "Image"
    
        # Line thickness of 2 px
        thickness = 1
    
        defects_str = []
        count = 0
        for defect in defects:
            if file.name != defect["file"]:
                continue
    
            # defects_str.append((defect["type"], defect["probability"]))
            defects_str.append({ k:v for k, v in defect.items() if k in ['type', 'probability']})
    
            # Get defect coords
            x, y, w, h = defect["coords"]
    
            # Blue color in BGR
            dtype = defect["type"]
            color = hex_to_rgb(colors[dtype])
            # color = (255, 0, 0)
    
            # Start coordinate (the top left corner of rectangle)
            start_point = (int(x), int(y))
    
            # Ending coordinate (represents the bottom right corner of rectangle)
            end_point = (int(w), int(h))
    
            # Draw rectangle around the defect
            image = cv2.rectangle(
                image, start_point, end_point, color, thickness
            )
    
            # Add label next to the defect
            if show_labels:
                txt = f"{count} {dtype}"
            else:
                txt = f"{count}"
    
            image = draw_text(
                image,
                txt,
                font=cv2.FONT_HERSHEY_DUPLEX,
                pos=start_point,
                font_scale=0.6,
                font_thickness=thickness,
                text_color=color,
                text_color_bg=(255, 255, 255),
            )
    
            count +=1
    
        st.image(image)
        # st.json(defects_str, expanded=False)
        if show_jsons:
            st.write(defects_str)

    st.write("**Model used:**", json["defect_model"], "||", "**Total inference time:**", json["inference_time"], " || ", "**Mean inference time:**", json["mean_inference_time"])
    if show_json:
        st.write("JSON", json)

if __name__ == "__main__":
    init()
