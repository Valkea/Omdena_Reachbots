#! /usr/bin/env python3
# coding: utf-8

import os
from flask import Flask, request, redirect, jsonify, url_for, session, abort
from flask_cors import CORS
from apiflask import APIFlask

from json2html import json2html

from api_internals.config_apiflask import (
    ModelsFullOut,
    PhotoDefectsIn,
    PhotoDefectsFullOut,
    LaserDefectsIn,
    LaserDefectsFullOut,
)
from api_internals.predict_defects_photo import predict_defects_photo, photo_model_selector
from api_internals.predict_defects_laser import predict_defects_laser, laser_model_selector
from api_internals.utils import check_uploaded_files


# --- API Flask app ---
# app = Flask(__name__)
app = APIFlask(__name__, title="Omdena Reachbots - Inference API")
app.secret_key = "super secret key"
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 200

CORS(app)


# ########## API ENTRY POINTS (BACKEND) ##########

# ----- GET AVAILABLE MODELS -----


@app.route("/get_available_photo_models", methods=["GET"])
@app.output(ModelsFullOut)
def route_get_photo_models():
    """
    Define the API endpoint to get the models available to detect defect from a photography.
    This entrypoint awaits a GET request and returns a JSON object.

    Returns
    -------
    jsonify(json_dict) : JSON object
        A JSON object containing the availabe models along with the current model id.
    """

    models = photo_model_selector.get_models()
    current = photo_model_selector.get_current_model_id()
    json_dict = {"available_models": models, "current_model": current}

    return jsonify(json_dict)

@app.route("/get_available_laser_models", methods=["GET"])
@app.output(ModelsFullOut)
def route_get_laser_models():
    """
    Define the API endpoint to get the models available to detect defect(s) from a laser cut image.
    This entrypoint awaits a GET request and returns a JSON object.

    Returns
    -------
    jsonify(json_dict) : JSON object
        A JSON object containing the availabe models along with the current model id.
    """

    models = laser_model_selector.get_models()
    current = laser_model_selector.get_current_model_id()
    json_dict = {"available_models": models, "current_model": current}

    return jsonify(json_dict)

# ----- PREDICT DEFECTS -----

@app.route("/predict_photo_defects", methods=["POST"])
@app.input(PhotoDefectsIn, location="files")
@app.output(PhotoDefectsFullOut)
def route_predict_photo_defects(files_data):
    """
    Define the API endpoint to get defect predictions from one or more images.
    This entrypoint awaits a POST request along with a 'file' parameter
    containing image(s) and returns a JSON object.

    Parameters
    ----------
    request : request
        The Flask request object containing the files and optional parameters.

    Returns
    -------
    jsonify(json_dict) : JSON object
        A JSON object containing the predicted defects along with several other information.
    """

    # --- CHECK FILES
    filtered_files = check_uploaded_files(request)

    # --- GATHER EXTRA INFORMATION
    p_selected_model = request.form.get("selected_model")
    p_binary_threshold = request.form.get("binary_threshold")
    p_multi_threshold = request.form.get("multi_threshold")

    extra_info = {
        "selected_model": p_selected_model,
        "binary_threshold": p_binary_threshold,
        "multi_threshold": p_multi_threshold,
    }

    print("params:", extra_info)

    # --- PREDICT
    try:
        json_defects, inference_time, used_models = predict_defects_photo(filtered_files, extra_info)
        json_dict = {
            "defect_models": used_models,
            "inference_time": f"{round(inference_time,2)}s",
            "mean_inference_time": f"{round(inference_time/len(filtered_files),2)}s",
            "results": json_defects,
        }
    except Exception as e:
        json_dict = {
            "error_msg": str(e)
        }

    print("OUTPUT:\n", json_dict)

    # --- RETURN ANSWER
    args = request.args
    if args.get("isfrontend") is None:
        print(jsonify(json_dict))
        return jsonify(json_dict)

    else:
        session["json2html"] = json2html.convert(json_dict)
        return redirect(url_for("upload_defects"))

@app.route("/predict_laser_defects", methods=["POST"])
@app.input(LaserDefectsIn, location="files")
@app.output(LaserDefectsFullOut)
def route_predict_defects(files_data):
    """
    Define the API endpoint to get defect predictions from one or more images.
    This entrypoint awaits a POST request along with a 'file' parameter
    containing image(s) and returns a JSON object.

    Parameters
    ----------
    request : request
        The Flask request object containing the files and optional parameters.

    Returns
    -------
    jsonify(json_dict) : JSON object
        A JSON object containing the predicted defects along with several other information.
    """

    # --- CHECK FILES
    filtered_files = check_uploaded_files(request)

    # --- GATHER EXTRA INFORMATION
    p_selected_model = request.form.get("selected_model")
    p_slide_step = request.form.get("slide_step")
    p_min_defects = request.form.get("min_defects")
    p_binary_threshold = request.form.get("binary_threshold")
    p_multi_threshold = request.form.get("multi_threshold")

    extra_info = {
        "selected_model": p_selected_model,
        "slide_step": p_slide_step,
        "min_defects": p_min_defects,
        "binary_threshold": p_binary_threshold,
        "multi_threshold": p_multi_threshold,
    }

    print("params:", extra_info)

    # --- PREDICT
    try:
        json_defects, inference_time, used_models = predict_defects_laser(filtered_files, extra_info)
        json_dict = {
            "defect_models": used_models,
            "inference_time": f"{round(inference_time,2)}s",
            "mean_inference_time": f"{round(inference_time/len(json_defects),2)}s",
            "results": json_defects,
        }
    except Exception as e:
        # raise e
        if str(e) == "image must be numpy array type":
            e = "The provided image(s) are not laser images"

        json_dict = {
            "error_msg": str(e)
        }


    print("OUTPUT:\n", json_dict)

    # --- RETURN ANSWER
    args = request.args
    if args.get("isfrontend") is None:
        print(jsonify(json_dict))
        return jsonify(json_dict)

    else:
        session["json2html"] = json2html.convert(json_dict)
        return redirect(url_for("upload_defects"))


# ########## DEMO FRONTEND ##########
# This could be a different Flask script totally independant from the API!


@app.route("/")
# @app.doc(hide=True)
def index():
    """Define the content of the main fontend page of the API server"""

    url = url_for('static', filename='index.html')

    return f"""
    <h1>The 'Reachbots Inference API' server is up.</h1>
    <ul>
        <li>You can use the included <strong><a href='{url}' target='_self'>simple HTML/js demo frontend</a></strong></li>
        <li>You can query the entry points to get JSON answers (see the <strong><a href='/docs' target='_self'>API documentation</a></strong>) using cURL, Postman, the streamlit client etc.</li>
    </ul>
    """

# ########## START BOTH API & FRONTEND ##########

if __name__ == "__main__":
    current_port = int(os.environ.get("PORT") or 5000)
    app.run(debug=True, host="0.0.0.0", port=current_port, threaded=True)
