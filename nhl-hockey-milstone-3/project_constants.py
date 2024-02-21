import logging
import os
from dotenv import load_dotenv
load_dotenv('.env')

ROOT_DIR = os.path.dirname((os.path.abspath(__file__)))
LOG_FILE = "app.log"

MODELS_DIR = "models/"
COMET_WORKSPACE="brucewang"
COMET_API_KEY = os.getenv('COMET_API_KEY')
DEFAULT_MODEL = "XGBoost_hyper"
DEFAULT_MODEL_NAME = "xgboost-hyper"

fileHandler = logging.FileHandler(os.path.join(ROOT_DIR, LOG_FILE))
fileHandler.setFormatter(logging.Formatter('[%(asctime)s]-[%(levelname)s]-[%(filename)s]: %(message)s'))