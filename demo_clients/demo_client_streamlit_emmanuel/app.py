import requests

import streamlit as st
from streamlit_option_menu import option_menu

BASE_URL = "http://0.0.0.0:5000"


def get_available_models():

    # sending get request
    URL = BASE_URL+"/get_available_models"
    r = requests.get(url = URL)

    # extracting data in json format
    data = r.json()
    models = data['available_models']

    # get current index
    current_index = list(models.keys()).index(data['current_model'])

    # inverse mapping
    models = {f"{v} [{k}]": k for k, v in models.items()}

    return models, current_index

def post_images(uploaded_files, selected_model):

    # prepare data with multiple files
    files = [('file',x) for x in uploaded_files]

    # sending get request
    URL = BASE_URL+"/predict_defects"

    r = requests.post(
        URL,
        files=files,
        data={'selected_model': selected_model},
    )

    # extracting data in json format
    data = r.json()
    return data


def main():
    print("Hello World")

    available_models, current_index = get_available_models()


    # --- Side bar ---

    option = st.sidebar.selectbox(
        label = 'Select a model',
        options=available_models,
        index=current_index,
    )

    uploaded_files = st.sidebar.file_uploader("Choose a CSV file", accept_multiple_files=True)
    json = ""
    if len(uploaded_files) > 0:
        json = post_images(uploaded_files, available_models[option])


    # --- Center ---
    st.text("Coucou")
    st.write('You selected:', available_models[option])
    st.write('JSON', json)




if __name__ == "__main__":
    main()
