import requests

import streamlit as st
from streamlit_option_menu import option_menu

BASE_URL = "http://0.0.0.0:5000"


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

    # --- Center ---
    st.text("Hello world")


if __name__ == "__main__":
    main()
