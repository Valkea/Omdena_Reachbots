"""
Description: This script provides a streamlit interface connecting to the inference API (API_serving) to get defects from image(s) and video.
Author: Letremble Emmanuel (emmanuel+code@shedge.com)
Command: streamlit run app.py
"""

import os
import io
import requests

from PIL import Image
import cv2

import streamlit as st

# ===== VARIABLES =====

DEFAULT_URL = "http://0.0.0.0:5000"

os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "10000"

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


# ===== FUNCTIONS =====


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
    URL = st.session_state["API_URL"] + "/get_available_models"
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
    # sending get request
    URL = st.session_state["API_URL"] + "/predict_defects"

    r = requests.post(
        URL,
        files=files,
        data={"selected_model": selected_model},
    )

    # extracting data in json format
    data = r.json()
    return data


def submit_images(files, selected_model, show_labels, show_jsons, show_json):
    """
    Prepare the UploadedFiles for the 'predict_draw_defects' function

    Parameters
    ----------
    files : list
        A list of files to use for prediction and drawing.
    selected_model : str
        The model_id of the model to use for inference.
    show_labels : boolean
        An option to display defect labels on the images.
    show_jsons : boolean
        An option to display defect characteristics next to each image.
    show_json : boolean
        An option to display the JSON returned by the API at the end of the call.
    """

    if len(files) > 0:
        predict_draw_defects(
            files,
            selected_model,
            show_labels,
            show_jsons,
            show_json,
        )


def submit_video(
    video_file, selected_model, show_labels, show_jsons, show_json, show_stream, cps
):
    """
    Prepare the uploaded video for the 'predict_draw_defects' function

    Parameters
    ----------
    video_file : UploadedFile
        A video file to use for prediction and drawing.
    selected_model : str
        The model_id of the model to use for inference.
    show_labels : boolean
        An option to display defect labels on the images.
    show_jsons : boolean
        An option to display defect characteristics next to each image.
    show_json : boolean
        An option to display the JSON returned by the API at the end of the call.
    show_stream: boolean
        An option to display all the images in the same container (the new image replace the older)
    cps : int
        An option to define the number of captures per second
    """

    # --- CAPTURE VIDEO STREAM ---

    vid = video_file.name
    with open(vid, mode="wb") as f:
        f.write(video_file.read())  # save video to disk

    vidcap = cv2.VideoCapture(vid)  # load video from disk

    # --- LOOP OVER CAPTURED FRAMES ---

    if show_stream:
        st.write("Capture stream")
        vid_div = st.empty()
        st.divider()

    cur_frame = 0
    capt_count = 0
    captured_files = []

    # -- Calculate and set the skip rate
    skip_rate = 1
    video_fps = vidcap.get(cv2.CAP_PROP_FPS)
    if video_fps > cps:
        skip_rate = round(video_fps / cps)

    while True:
        # success, frame = vidcap.read()  # get next frame
        success = vidcap.grab()
        if not success:
            break

        cur_frame += 1
        if cur_frame % skip_rate == 0:  # Processing frame
            capt_count += 1
            st.write(f"Capture {capt_count}")

            # pil_img = Image.fromarray(frame) # convert cv2 frame to PIL Image
            status, frame = vidcap.retrieve()  # Decode processing frame with .grab()

            is_success, buffer = cv2.imencode(".png", frame)
            io_buf = io.BytesIO(buffer)
            io_buf.name = f"capture{cur_frame}.png"

            captured_files.append(io_buf)

            drawn_img = predict_draw_defects(
                captured_files, selected_model, show_labels, show_jsons, show_json
            )
            captured_files = []

            if show_stream:
                vid_div.image(drawn_img)
                # vid_div.image(io_buf.getvalue())

    # --- RELEASE VIDEO ---

    vidcap.release()


def predict_draw_defects(files, selected_model, show_labels, show_jsons, show_json):
    """
    Predict defects using the provided images and parameters

    Parameters
    ----------
    files : list
        A list of files to use for prediction and drawing.
    selected_model : str
        The model_id of the model to use for inference.
    show_labels : boolean
        An option to display defect labels on the images.
    show_jsons : boolean
        An option to display defect characteristics next to each image.
    show_json : boolean
        An option to display the JSON returned by the API at the end of the call.

    Returns
    -------
    str
        The last drawn image.
    """
    json = post_images(files, selected_model)
    results = json["images"]

    for file in files:
        image = Image.open(file)
        image = image.convert("RGB")  # remove alpha if any
        image = image.save("img.jpg")

        # Reading an image in default mode
        image = cv2.imread("img.jpg")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Window name in which image is displayed
        window_name = "Image"

        # Line thickness of 2 px
        thickness = 3
        font_scale = 1.5

        infos_str = {}

        for result in results:

            if file.name != result["file"]:
                continue

            infos_str = {k: v for k, v in result.items() if k in ["file", "has_defect", "probability", "score", "defect_list"]}
            # if result['has_defect'] is True:
            #    infos_str['defect_list'] = []

            if 'defect_list' not in result.keys():
                continue


            defect_list = result['defect_list']
            count = 0

            for defect in defect_list:

                if type(defect) == str:
                    continue

                if 'coords' not in defect.keys():
                    continue

                # defects_str.append((defect["type"], defect["probability"]))
                # infos_str['defect_list'].append(
                #    {k: v for k, v in defect.items() if k in ["type", "probability"]} # coords
                # )

                # Get defect coords
                x, y, w, h = defect["coords"]

                # Blue color in BGR
                dtype = defect["type"]
                color = hex_to_rgb(colors[dtype]) # color = (255, 0, 0)

                # Start coordinate (the top left corner of rectangle)
                start_point = (int(x), int(y))

                # Ending coordinate (represents the bottom right corner of rectangle)
                end_point = (int(w), int(h))

                # Draw rectangle around the defect
                image = cv2.rectangle(image, start_point, end_point, color, thickness)

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
                    font_scale=font_scale,
                    font_thickness=thickness,
                    text_color=color,
                    text_color_bg=(255, 255, 255),
                )

                count += 1

        st.image(image)
        defects_expander = st.expander("Defects", expanded=show_jsons)
        defects_expander.write(infos_str)

    st.write(
        "**Used model(s):**",
        json["defect_models"],
        "||",
        "**Total inference time:**",
        json["inference_time"],
        " || ",
        "**Mean inference time:**",
        json["mean_inference_time"],
    )

    json_expander = st.expander("Returned JSON", expanded=show_json)
    json_expander.write(json)

    return image


# ===== LAYOUTS =====


def init():
    """
    Display a layout to request the base API URL
    """

    def go(base_url):
        available_models, current_index = get_available_models()
        main(base_url, available_models, current_index)

    if "API_URL" in st.session_state:
        go(st.session_state["API_URL"])

    else:
        form_div = st.empty()
        form = form_div.form("url_form")
        base_url = form.text_input("**Base URL:**", DEFAULT_URL)
        submitted = form.form_submit_button("Submit")

        if submitted and base_url != "":
            try:
                st.session_state["API_URL"] = base_url
                go(base_url)
                form_div.empty()
            except Exception:
                st.write("Invalid URL:", base_url)
                del st.session_state["API_URL"]


def main(base_url, available_models, current_index):
    """
    Display a layout to actually select medias, send them to the API and display the results
    """

    st.sidebar.write("API_URL:", st.session_state["API_URL"])

    form = st.sidebar.form("pred_form")

    # --- FORM OPTIONS ---

    model_id = form.selectbox(
        label="Select a model",
        options=available_models,
        index=current_index,
    )

    show_labels = form.checkbox("Show labels on pictures", False)
    show_jsons = form.checkbox("Show defait details", False)
    show_json = form.checkbox("Show the whole JSON", False)

    # --- FORM TABS ---

    tabs = form.tabs(["Use Image(s)", "Use Video"])

    uploaded_files = tabs[0].file_uploader(
        "Choose image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )
    submitted_i = tabs[0].form_submit_button("Submit image(s)")

    show_stream = tabs[1].checkbox("Show stream", False)
    fps = tabs[1].slider("Capture per second", 1, 5, 1)
    uploaded_video = tabs[1].file_uploader("Choose video", type=["mp4", "mov"])
    submitted_v = tabs[1].form_submit_button("Submit video")

    # --- FORM SUBMITS ---

    if submitted_i:
        submit_images(
            uploaded_files,
            available_models[model_id],
            show_labels,
            show_jsons,
            show_json,
        )

    if submitted_v:
        if uploaded_video is not None:
            submit_video(
                uploaded_video,
                available_models[model_id],
                show_labels,
                show_jsons,
                show_json,
                show_stream,
                fps,
            )


if __name__ == "__main__":
    init()
