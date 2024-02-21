"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:
    
    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
import os
from flask import Flask, jsonify, request, abort
from comet_ml import API
import logging
# import ift6758
import pandas as pd
from project_constants import ROOT_DIR, LOG_FILE, MODELS_DIR, \
    COMET_API_KEY, DEFAULT_MODEL, DEFAULT_MODEL_NAME, fileHandler

app = Flask(__name__)
api = API(api_key=COMET_API_KEY)
loaded_model = None
loaded_model_name = None

feature_dict = {"xgboost-hyper": [],
                "best-model": [],
                "lr-binnedbydistance": ["Shot Distance"]}


def download_comet_model(workspace: str, model: str, version: str):
    try:
        model_details = api.get_registry_model_details(workspace, model, version)
        filename = model_details['assets'][0]['fileName']
        api.download_registry_model(workspace, model, version, output_path=os.path.join(ROOT_DIR,MODELS_DIR), expand=True)
        model = pd.read_pickle(f"{ROOT_DIR}/{MODELS_DIR}/{filename}")
        return model
    except Exception as e:
        logging.error(e)
        return None

@app.before_first_request
def before_first_request():
    """
    Hook to handle any initialization before the first request (e.g. load model,
    setup logging handler, etc.)
    """
    # setup basic logging configuration
    # fileHandler = logging.FileHandler(os.path.join(ROOT_DIR, LOG_FILE))
    # fileHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(levelname)s]-[%(filename)s]: %(message)s'))
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(fileHandler)

    # any other initialization before the first request (e.g. load default model)
    global loaded_model, loaded_model_name
    try:
        default_path = os.path.join(ROOT_DIR, "models", DEFAULT_MODEL + ".pkl")
        loaded_model = pd.read_pickle(default_path)
        loaded_model_name = DEFAULT_MODEL_NAME
        app.logger.info("/INIT: Default model loaded: {}".format(DEFAULT_MODEL))
    except Exception as e:
        app.logger.exception(e)


@app.route("/logs", methods=["GET"])
def logs():
    """Reads data from the log file and returns them as the response"""

    app.logger.info("/LOG: Returning logs ...")
    with open(os.path.join(ROOT_DIR, LOG_FILE), "rb") as f:
        file = f.read()

    return jsonify(file)  # response must be json serializable!


@app.route("/download_registry_model", methods=["POST"])
def download_registry_model():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

    The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

    Recommend (but not required) json with the schema:

        {
            workspace: (required),
            model: (required),
            version: (required)
        }
    
    """
    global loaded_model, loaded_model_name
    # Get POST json data
    json = request.get_json()
    app.logger.info("/DOWNLOAD: model : {}".format(json.get("model")))

    # Check to see if the model you are querying for is already downloaded
    model_details = api.get_registry_model_details(json.get("workspace"), json.get("model"), json.get("version"))
    filename = model_details['assets'][0]['fileName']
    filepath = os.path.join(ROOT_DIR, "models", filename + ".pkl")

    # If yes, load that model and write to the log about the model change.
    load_success = False
    if os.path.exists(filepath):
        app.logger.info("/DOWNLOAD: Model: {} exists in download cache".format(filename))
        try:
            loaded_model = pd.read_pickle(filepath)
            loaded_model_name = json.get("model")
            app.logger.info("/DOWNLOAD: Model : {} load success")
            load_success = True
        except Exception as e:
            app.logger.error(e)
            app.logger.info("/DOWNLOAD: Read from cache failed, downloading model from comet instead")
    
    # If not available, try downloading the model: if it succeeds, load that model and write to the log
    if not load_success:
        new_model = download_comet_model(json.get("workspace"), json.get("model"), json.get("version"))
        if new_model is not None:
            loaded_model = new_model
            loaded_model_name = json.get("model")
            app.logger.info("/DOWNLOAD: Model switch SUCCESS, New model : {}".format(filename))
            load_success = True
        else:
            app.logger.info("/DOWNLOAD: Model switch FAILURE, retaining existing model")

    response = "SUCCESS" if load_success else "FAIL"
    return jsonify(response)  # response must be json serializable!


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    # Get POST json data
    json = request.get_json()
    global loaded_model, loaded_model_name

    pred = []
    success = False
    try:
        df = pd.DataFrame(json)
        len_df = df.shape[0]
        app.logger.info("/PREDICT: input receieved of len : {}".format(len_df))

        if len_df:
            feature_names = feature_dict.get(loaded_model_name, [])
            if feature_names:
                pred = loaded_model.predict_proba(df[feature_names].values)
                # get goal probability only
                pred = pred[:, 1]
            else:
                pred = loaded_model.predict_proba(df.values)
                pred = pred[:, 1]
            success = True

    except Exception as e:
        app.logger.exception(e)

    app.logger.info("/PREDICT: Status : {}, Output Len: {}".format(success, len(pred)))
    return jsonify(pred.tolist())  # response must be json serializable!
    
    
@app.route("/parag")
def parag():
        return "Parag, you are on the right path. Keep moving forward."
