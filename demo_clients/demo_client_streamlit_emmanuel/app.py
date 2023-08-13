import requests

from PIL import Image
import cv2

import streamlit as st
from streamlit_option_menu import option_menu

BASE_URL = "http://0.0.0.0:5000"


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
    URL = BASE_URL + "/get_available_models"
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
    URL = BASE_URL + "/predict_defects"

    r = requests.post(
        URL,
        files=files,
        data={"selected_model": selected_model},
    )

    # extracting data in json format
    data = r.json()
    return data


def main():
    available_models, current_index = get_available_models()

    # --- Side bar ---

    form = st.sidebar.form("pred_form")

    option = form.selectbox(
        label="Select a model",
        options=available_models,
        index=current_index,
    )

    uploaded_files = form.file_uploader("Choose file(s)", accept_multiple_files=True)
    submitted = form.form_submit_button("Submit")

    if submitted:
        st.write("You selected:", available_models[option])

        if len(uploaded_files) > 0:
            json = post_images(uploaded_files, available_models[option])
            st.write("JSON", json)
            defects = json["defects"]

            for file in uploaded_files:

                image = Image.open(file)
                image = image.save("img.jpg")

                # Reading an image in default mode
                image = cv2.imread("img.jpg")
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Window name in which image is displayed
                window_name = "Image"

                # Line thickness of 2 px
                thickness = 2

                for defect in defects:
                    if file.name != defect["file"]:
                        continue

                    # Get defect coords
                    x, y, w, h = defect["coords"]

                    # Blue color in BGR
                    t = defect["type"]
                    color = hex_to_rgb(colors[t])
                    # color = (255, 0, 0)

                    # Start coordinate (the top left corner of rectangle)
                    start_point = (int(x), int(y))

                    # Ending coordinate (represents the bottom right corner of rectangle)
                    end_point = (int(w), int(h))
                    image = cv2.rectangle(
                        image, start_point, end_point, color, thickness
                    )

                st.image(image)

    # --- Center ---
    st.text("Hello world")


if __name__ == "__main__":
    main()
