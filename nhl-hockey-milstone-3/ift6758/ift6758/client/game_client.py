import os
import sys
import requests
from tidy_features import TidyData
import pickle
import logging
from typing import List, Dict, Tuple
logger = logging.getLogger(__name__)

def getRepositoryRoot():
                 stream = os.popen("git rev-parse --absolute-git-dir")
                 output = stream.read()
                 ''' Read entire output string except last 6 characters : /.git\n '''
                 project_root_directory = output[:-6]
                 #print("Project root directory : ", project_root_directory)
                 return project_root_directory



class gameClient():

    def __init__(self):
        logger.info("/GAME_CLIENT: Game client Initialsed")
        self.game_tracker = {}
        self.features = TidyData()
        self.advanced_features = ['Shot Type','Last event type','Period', 'X-Coordinate', 'Y-Coordinate', 'Was Net Empty',
                                   'Game Seconds', 'Shot Distance', 'Shot Angle', 'Last X', 'Last Y', 'Time from last event', 'Rebound', 
                                   'Distance from last event', 'Speed', 'Change in shot angle','Time since Powerplay', 'Friendly skaters', 'Non Friendly Skaters']
        # param_directory = getRepositoryRoot()+"/ift6758/ift6758/client/"+"param_dict.pkl"
        param_directory = "/code/"+"param_dict.pkl"
        # param_directory = "param_dict.pkl"
        # print(train_file_directory)
        with open(param_directory, "rb") as f:
            self.param_encoder = pickle.load(f)
        self.test_batch = 40

    def process_data(self, data: Dict, game_id: str, last_idx: int) -> Tuple:
        '''

        :param data: The data acquired with game id
        :param gameID: string gameID = 10 digits
        :param last_idx: The number memorizing the event number processed before
        :return: Tuple of below structure:

        {"<Team_Name_1>" : {"features" : csv of new shot goal (processed)features,
                            "real_features" : csv of new shot and goal features,
                                "goals", Int: No of new goals by team}
        "<Team_Name_2>" : {"features" : csv of new shot goal (processed)features,
                            "real_features" : csv of new shot and goal features,
                         "goals", Int: No of new goals by team}

        "period": Int:  period value
        "period_time_remaining": str: period time remaining in format mm:ss

        '''
        
        response_dict = {}

        current_event = data["liveData"]["plays"]["allPlays"][-1]["about"]
        period = current_event["period"]
        period_time_remaining = current_event["periodTimeRemaining"]

        tidy_data = self.features.process_json(data, game_id)
        # separate teams
        team_names = tidy_data["Event Team Name"].unique()

        # check if new events since last_idx
        tidy_data = tidy_data.loc[tidy_data["eventIdx"] > last_idx]

        # if no, new events, return some information and current period values
        if tidy_data.shape[0] == 0:
            return {"No more"}, period, period_time_remaining

        shot_type_encoding = self.param_encoder["shot_type_encoding"]
        last_event_encoding = self.param_encoder["last_event_encoding"]
        features_norm_encoding = self.param_encoder["norm_encoding"]
        # preprocessing the features
        for team in team_names:
            response_dict[team] = {}
            response_dict[team]["goals"] = tidy_data.loc[(tidy_data["Event"] == "Goal") & (tidy_data["Event Team Name"] == team)].shape[0]

            shot_data = tidy_data[tidy_data["Event Team Name"] == team]
            shot_data = shot_data.loc[(shot_data["Event"] == 'Shot') | (shot_data['Event'] == 'Goal')]
            response_dict[team]['real_features'] = shot_data
            shot_data = shot_data[self.advanced_features]
            shot_data = shot_data.dropna()
            
            shot_data['Was Net Empty'] = shot_data['Was Net Empty'].apply(lambda x: 1 if x == True else 0)
            shot_data['Rebound'] = shot_data['Rebound'].apply(lambda x: 1 if x == True else 0)

            shot_data['Shot Type'] = shot_data['Shot Type'].apply(lambda x: shot_type_encoding.get(x, 0))
            shot_data['Last event type'] = shot_data['Last event type'].apply(lambda x: last_event_encoding.get(x, 0))

            numerical_columns = shot_data.columns[2:]
            for column in numerical_columns:
                shot_data[column] = (shot_data[column] - features_norm_encoding[column][0])/features_norm_encoding[column][1]

            response_dict[team]["features"] = shot_data
            # response_dict[team]['real_features'] = tidy_data.loc[(tidy_data["Event"] in accept_type) & (tidy_data["Event Team Name"] == team)]

        return response_dict, period, period_time_remaining

    def ping_game(self, gameID: str, test_mode: bool = False) -> Tuple:
        '''

        :param gameID: string gameID = 10 digits
        :param test_mode: If True, simulates a live game, by retrieving events data in batches of 50 events
        :return: Tuple of below structure:

        {"<Team_Name_1>" : {"features" : csv of new shot and goal (processed)features,
                                "real_features" : csv of new shot and goal features,
                                "goals", Int: No of new goals by team}
        "<Team_Name_2>" : {"features" : csv of new shot goal (processed)features,
                            "real_features" : csv of new shot and goal features,
                         "goals", Int: No of new goals by team}

        "period": Int:  period value
        "period_time_remaining": str: period time remaining in format mm:ss

        '''

        if len(gameID) != 10:
            logger.info("/GAME_CLIENT: Invalid GameID encountered: {} Exiting ...".format(gameID))
            return None, None, None

        resp = requests.get(f"https://statsapi.web.nhl.com/api/v1/game/{gameID}/feed/live")
        if resp.status_code != 200:
            logger.info("/GAME_CLIENT: NHL API fetch failed with status: {} for gameID: {}".format(resp.status_code, gameID))
            return {'Wrong'},'x','xx'
        game_data = resp.json()
        game_status = game_data['gameData']['status']['abstractGameState']

        if test_mode:
            if gameID not in self.game_tracker.keys():
                self.test_batch = 40
            game_data["liveData"]["plays"]["allPlays"] = game_data["liveData"]["plays"]["allPlays"][:self.test_batch]
            if self.test_batch  > len(game_data["liveData"]["plays"]["allPlays"]):
                game_status = "Final"
            else:
                game_status = 'run'
            self.test_batch += 10

        # print("tracker",self.game_tracker)
        if gameID in self.game_tracker.keys():
            logger.info("/GAME_CLIENT: Pinging previously seen gameID:{}".format(gameID))
            if game_status == 'Final' and self.game_tracker[gameID] == -1:
                logger.info("/GAME_CLIENT: game ID {} is over".format(gameID))
                return {'Over'},'x','xxx'
            elif game_status == 'Final' and self.game_tracker[gameID] != -1:
                logger.info("/GAME_CLIENT: gameID {} is about to end".format(gameID))
                last_idx = self.game_tracker[gameID]
                team_processed_data, period, period_time_left = self.process_data(game_data, gameID, last_idx)
                last_idx = len(game_data["liveData"]["plays"]["allPlays"]) - 1
                self.game_tracker[gameID] = -1
                return team_processed_data, 'x','xxx'
               
            elif game_status == 'Preview':
                logger.info("/GAME_CLIENT: gameID {} is on the way.".format(gameID))
                return {"Preview"},'x','xxx'
            else:
                last_idx = self.game_tracker[gameID]
                team_processed_data, period, period_time_left = self.process_data(game_data, gameID, last_idx)
                last_idx = len(game_data["liveData"]["plays"]["allPlays"]) - 1
                self.game_tracker[gameID] = last_idx
                return team_processed_data, period, period_time_left
        else:
            logger.info("/GAME_CLIENT: NHL API fetch new gameID: {} ".format(gameID))
            if game_status == 'Final':
                logger.info("/GAME_CLIENT: gameID {} is over".format(gameID))
                last_idx = 0
                team_processed_data, period, period_time_left = self.process_data(game_data, gameID, last_idx)
                self.game_tracker[gameID] = -1
                return team_processed_data, 'x', 'xxx'
            elif game_status == 'Preview':
                logger.info("/GAME_CLIENT: gameID {} is on the way.".format(gameID))
                self.game_tracker[gameID] = 0
                return {"Preview"},'x','xxx'
            else:
                last_idx = 0
                team_processed_data, period, period_time_left = self.process_data(game_data, gameID, last_idx)
                last_idx = len(game_data["liveData"]["plays"]["allPlays"]) - 1
                self.game_tracker[gameID] = last_idx
                return team_processed_data, period, period_time_left
                
if __name__ == "__main__":
    import json
    import numpy as np
    from serving_client import ServingClient

    gameid = "2022020510"
    game_client = gameClient()
    #serving_client = ServingClient(ip="127.0.0.1", port=5000)
    serving_client = ServingClient(ip="127.0.0.2", port=8083)
    team_stats = {}

    ## This loop on num_pings is a test code : not required in actual streamlit
    for num_pings in range(1, 4):
        print("PING - {}".format(num_pings))

        # CAUTION: SET TEST MODE = False, WHILE USING IN STREAMLIT
        team_data, period, period_time_left = game_client.ping_game(gameid, test_mode=True)
        if team_data == {}:
            print("TWO POSSIBILITIES: EITHER GAME IS YET TO START, OR NO NEW EVENTS are there in the game(game is already finished)")
            """
            In both cases team_data returns a empty dict, differentiate between these two cases
            Note to Yizhao and Parag: Handle these case here, i didnt have time to finish this. 
                1. If game is yet to start --> display team names only and keep the  no goals/expected goals blank
                2. If game has no new events(or game has already finished), display old values of team names, expected goals/true goals.
            """
            continue

        elif team_data is None:
            print("Invalid Game ID receieved, please check for valid 10 digit gameid")
            continue

        for team_name in team_data.keys():
            if team_name not in team_stats.keys():
                team_stats[team_name] = {"exp": 0,
                                         "actual": 0}

            shot_events = team_data[team_name]["features"]
            goal_pred = None
            actual_goals = None
            print("len of shot events:", len(shot_events))
            if len(shot_events) == 0:
                print("len of shot events:", len(shot_events))
                goal_pred = 0
                actual_goals = 0
            else:
                    pred_df = serving_client.predict(shot_events)
                    
                    print("Prediction df :")
                    print(pred_df.columns)
                    pred = np.array(pred_df["Exp_Goal"].values)
                    # sum the expected goal values for all shots
                    goal_pred = np.sum(pred)
                    actual_goals = team_data[team_name]["goals"]


            team_stats[team_name]["exp"] += goal_pred
            team_stats[team_name]["actual"] += actual_goals

            print("Team : {} Expected Goals : {} Actual Goals: {}".format(team_name, team_stats[team_name]["exp"],
                                                                          team_stats[team_name]["actual"]))

        print("------------------------")






