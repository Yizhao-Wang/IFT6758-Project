import json
import requests
import pandas as pd
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ServingClient:
    def __init__(self, ip: str = "0.0.0.0", port: int = 5000):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the inputs into an appropriate payload for a POST request, and queries the
        prediction service. Retrieves the response from the server, and processes it back into a
        dataframe that corresponds index-wise to the input dataframe.
        
        Args:
            X (Dataframe): Input dataframe to submit to the prediction service.
        """

        if X.shape[0] > 0:
            pred = requests.post(f"{self.base_url}/predict", json=json.loads(X.to_json()))
            if pred.status_code != 200:
                logger.info("/Serving Client: Error in Prediction service with status code: {}".format(pred.status_code))
                return X
            else:
                resp_df = X.copy()
                resp_df["Exp_Goal"] = np.array(pred.json())
                return resp_df
        else:
            logger.info("/Serving Client: Invalid input dataframe encountered, returning input")
            return X


    def logs(self) -> dict:
        """Get server logs"""

        resp = requests.get(f"{self.base_url}/logs")
        if resp.status_code != 200:
                 logger.info("/Serving Client: Error in Logs service with status code: {}".format(resp.status_code))
                 return "/Serving Client: Error in Logs service with status code: "+str(resp.status_code)
        else:
                return resp.json()


    def download_registry_model(self, workspace: str, model: str, version: str) -> dict:
        """
        Triggers a "model swap" in the service; the workspace, model, and model version are
        specified and the service looks for this model in the model registry and tries to
        download it. 

        See more here:

            https://www.comet.ml/docs/python-sdk/API/#apidownload_registry_model
        
        Args:
            workspace (str): The Comet ML workspace
            model (str): The model in the Comet ML registry to download
            version (str): The model version to download
        """
        payload = {"workspace": workspace,
                   "model": model,
                   "version": version}
        resp = requests.post(f"{self.base_url}/download_registry_model", json=payload)
        if resp.status_code != 200:
                logger.info("/Serving Client: Error in Download Model service with status code: {}".format(resp.status_code))
                return "/Serving Client: Error in Download Model service with status code: "+str(resp.status_code)
        else:
                return resp.json()
