import streamlit as st
import pandas as pd
import numpy as np
import os

import sys
# sys.path.append('ift6758/ift6758/client/')

from serving_client import ServingClient
from game_client import gameClient
import json

# Store the initial value of widgets in session state. 
if 'serving_client' not in st.session_state:
    # st.session_state.serving_client = ServingClient(ip='127.0.0.2', port=8083)
    st.session_state.serving_client = ServingClient(ip='flask-service', port=8083)

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
if "disabled" not in st.session_state:
    st.session_state.disabled = False
if "model_option" not in st.session_state:
    st.session_state.model_option = None
if "version_option" not in st.session_state:
    st.session_state.version_option = None

if 'client' not in st.session_state:
	st.session_state.client = gameClient()
if "team_stats"not in st.session_state:
    st.session_state.team_stats = {}
if 'home_team_name' not in st.session_state:
    st.session_state.home_team_name = str("AAA")
if 'away_team_name' not in st.session_state:
    st.session_state.away_team_name = str("BBB")
if 'home_predict_score' not in st.session_state:
    st.session_state.home_predict_score = 0
if 'home_real_score' not in st.session_state:
    st.session_state.home_real_score = 0
if 'away_predict_score' not in st.session_state:
    st.session_state.away_predict_score = 0
if 'away_real_score' not in st.session_state:
    st.session_state.away_real_score = 0
if 'period' not in st.session_state:
    st.session_state.period = 'x'
if 'period_time_left' not in st.session_state:
    st.session_state.period_time_left = 'xxx'
if 'home_team_data' not in st.session_state:
    st.session_state.home_team_data = None
if 'away_team_data' not in st.session_state:
    st.session_state.away_team_data = None
if 'team_data' not in st.session_state:
    st.session_state.team_data = None


def download_registry_model(workspace: str, model: str, version: str):
    return st.session_state.serving_client.download_registry_model(workspace,model,version)


# Control the sidebar on the left of the interface, choose the workspace, model, and version here.
with st.sidebar:
    workspace_option = st.selectbox(
        "Workspace",
        ("brucewang",),
        #label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,)
        
    model_option = st.selectbox(
        "Model",
        ("xgboost-hyper", "best-model"),
        #label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,)
        
    version_option = st.selectbox(
        "Version",
        ("1.0.0", "2.0.0", "3.0.0"),
        #label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,)
    select_sign = False
    
    # Some versions don't work, give the notification
    if model_option == 'xgboost-hyper' and (version_option == '1.0.0' or version_option == '2.0.0'):
        st.error("Please use version 3.0.0")
        select_sign = False
    elif model_option == 'best-model' and (version_option == '2.0.0' or version_option == '3.0.0'):
        st.error("Please use version 1.0.0")
        select_sign = False
    else:
        select_sign = True
  
    if st.button('Get model') and select_sign:
        registry_model_result = download_registry_model(workspace_option, model_option, version_option) # Comet_model should be changed as the download form of the model in Comet
        st.warning(registry_model_result )
        if str(registry_model_result) == "SUCCESS":
            st.session_state.model_option = model_option
            st.session_state.version_option = version_option


# showing the main content on the right of the interface
st.title('Hockey Visualization App')



gameid_input = st.text_input(
    "Game ID",
    #label_visibility=st.session_state.visibility,
    disabled=st.session_state.disabled,
    #placeholder=st.session_state.placeholder,
)


# Process all of the situations when click the button
if st.button('Ping game'):
    #If no model is chosen or choose the wrong model, we will use the default model"""
    if st.session_state.model_option == None :
        st.write("Didn't choose the write model. Using the default model:")
        st.write('The model: {} , The version: {}'.format("xgboost-hyper", '3.0.0')) # should be changed into the connection with flask app 
    else:
        st.write('The model: {} , The version: {}'.format(st.session_state.model_option,st.session_state.version_option))
    #processing the gameID, test mode is used to simulate the live game with finished game"""
    st.session_state.team_data, st.session_state.period, st.session_state.period_time_left = st.session_state.client.ping_game(gameid_input, test_mode=False)

    if st.session_state.team_data == {"Wrong"}:
        #If the gameID is wrong or not this id
        st.error("Invalid Game ID receieved, please check for valid 10 digit gameid")
        st.session_state.away_team_name = str("BBB")
        st.session_state.home_team_name = str("AAA")
        st.session_state.home_predict_score = 0
        st.session_state.home_real_score = 0
        st.session_state.away_predict_score = 0
        st.session_state.away_real_score = 0
        st.session_state.period = 'x'
        st.session_state.period_time_left = 'xxx'
        st.session_state.home_team_data = None
        st.session_state.away_team_data = None
        st.session_state.team_data = None


    elif st.session_state.team_data == {"Over"}:
        #If the game is over"""
        st.write("Game is over!")
        st.session_state.home_team_name, st.session_state.away_team_name =  st.session_state.team_stats[gameid_input]
        st.session_state.home_predict_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["exp"]
        st.session_state.home_real_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["actual"]
        st.session_state.away_predict_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["exp"]
        st.session_state.away_real_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["actual"]
        st.session_state.home_team_data =  st.session_state.team_stats[gameid_input][st.session_state.home_team_name]['features']
        st.session_state.away_team_data = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]['features']
    
    elif st.session_state.team_data == {"No more"}:
        #If the game is pinged  before , now ping again, but no more shot event """
        st.write("No more shot yet!")
        st.session_state.home_team_name, st.session_state.away_team_name =  st.session_state.team_stats[gameid_input]
        st.session_state.home_predict_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["exp"]
        st.session_state.home_real_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["actual"]
        st.session_state.away_predict_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["exp"]
        st.session_state.away_real_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["actual"]
        st.session_state.home_team_data =  st.session_state.team_stats[gameid_input][st.session_state.home_team_name]['features']
        st.session_state.away_team_data = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]['features']


    elif st.session_state.team_data == {"Preview"}:
        #If the game is going to be happen"""
        st.write("Game is not yet to start!")
        st.session_state.away_team_name = str("BBB")
        st.session_state.home_team_name = str("AAA")
        st.session_state.home_predict_score = 0
        st.session_state.home_real_score = 0
        st.session_state.away_predict_score = 0
        st.session_state.away_real_score = 0
        st.session_state.period = 'x'
        st.session_state.period_time_left = 'xxx'
        st.session_state.home_team_data = None
        st.session_state.away_team_data = None
        st.session_state.team_data = None

    elif st.session_state.team_data is None:
        #If the length of the gameID is not 10, wrong ID"""
        st.error("Invalid Game ID receieved, please check for valid 10 digit gameid")

    else:

        if st.session_state.team_data == {}  :
            st.error("Wrong case!")

        else:
            if gameid_input not in st.session_state.team_stats.keys():
                #If we haven't seen this gameID before"""
                st.session_state.team_stats[gameid_input] = {}

            for team_name in st.session_state.team_data.keys():
                #Process the event data we get from the client"""
                shot_events = st.session_state.team_data[team_name]["features"]
                # print(shot_events)
                goal_pred = None
                actual_goals = None
                
                if len(shot_events) == 0:
                    #if one of the team doesn't have new shot or goal"""
                    # print("len of shot events",len(shot_events))
                    goal_pred = 0
                    actual_goals = 0

                else:
                    #predict the goal probability"""
                    pred_df = st.session_state.serving_client.predict(shot_events)
                    pred = np.array(pred_df["Exp_Goal"].values)
                    # sum the expected goal values for all shots
                    goal_pred = np.sum(pred)
                    actual_goals = st.session_state.team_data[team_name]["goals"]
                    st.session_state.team_data[team_name]["real_features"]['Model output'] = pred_df["Exp_Goal"]

                if gameid_input in st.session_state.team_stats.keys() and team_name in st.session_state.team_stats[gameid_input]:
                    #if the gameID and this team we processed before, we concatenate the new events with what we already processed"""
                    st.session_state.team_stats[gameid_input][team_name]['features'] = pd.concat([st.session_state.team_stats[gameid_input][team_name]['features'],st.session_state.team_data[team_name]["real_features"]],ignore_index=True)
                else:
                    #If the gameID or the team in this gameID we didn't seen before"""
                    st.session_state.team_stats[gameid_input][team_name] = {}
                    st.session_state.team_stats[gameid_input][team_name]['features'] = st.session_state.team_data[team_name]["real_features"]
                    st.session_state.team_stats[gameid_input][team_name]["exp"] = 0
                    st.session_state.team_stats[gameid_input][team_name]["actual"] = 0

                st.session_state.team_stats[gameid_input][team_name]["exp"] += goal_pred
                st.session_state.team_stats[gameid_input][team_name]["actual"] += actual_goals
            if len(st.session_state.team_data.keys()) !=2:
                # if game just started and only one team has shot event
                if len(st.session_state.team_stats[gameid_input]) == 1:
                    st.session_state.home_team_name = list(st.session_state.team_data)[0]
                    st.session_state.home_predict_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["exp"]
                    st.session_state.home_real_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["actual"]
                    st.session_state.away_predict_score = 0
                    st.session_state.away_real_score = 0
                    st.session_state.home_team_data =  st.session_state.team_stats[gameid_input][st.session_state.home_team_name]['features']
                    st.session_state.away_team_data = None
                else:
                    # if only one team has new shot event, but two teams already has old shot events
                    st.session_state.home_team_name,st.session_state.away_team_name = st.session_state.team_stats[gameid_input].keys()
                    st.session_state.home_predict_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["exp"]
                    st.session_state.home_real_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["actual"]
                    st.session_state.away_predict_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["exp"]
                    st.session_state.away_real_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["actual"]
                    st.session_state.home_team_data =  st.session_state.team_stats[gameid_input][st.session_state.home_team_name]['features']
                    st.session_state.away_team_data = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]['features']

            else:
                st.session_state.home_team_name, st.session_state.away_team_name = st.session_state.team_data.keys()

                st.session_state.home_predict_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["exp"]
                st.session_state.home_real_score = st.session_state.team_stats[gameid_input][st.session_state.home_team_name]["actual"]
                st.session_state.away_predict_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["exp"]
                st.session_state.away_real_score = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]["actual"]
                st.session_state.home_team_data =  st.session_state.team_stats[gameid_input][st.session_state.home_team_name]['features']
                st.session_state.away_team_data = st.session_state.team_stats[gameid_input][st.session_state.away_team_name]['features']

# Show the exact content.
st.header("Game ID:{}".format(gameid_input))
st.header("{} vs {}".format(st.session_state.home_team_name,st.session_state.away_team_name))
st.text("Period{}: {} left".format(st.session_state.period,st.session_state.period_time_left))

# Show the score
home_team, away_team = st.columns(2)
home_team.metric(label=f"{st.session_state.home_team_name} xG(actual)", value=f"{round(st.session_state.home_predict_score,1)}({st.session_state.home_real_score})", delta=round(st.session_state.home_real_score-st.session_state.home_predict_score,1),delta_color="inverse")
away_team.metric(label=f"{st.session_state.away_team_name} xG(actual)", value=f"{round(st.session_state.away_predict_score,1)}({st.session_state.away_real_score})", delta=round(st.session_state.away_real_score-st.session_state.away_predict_score,1),delta_color="inverse")

# Show the raw feature of each team
st.header(f"Data for {st.session_state.home_team_name}")
st.dataframe(st.session_state.home_team_data)
st.header(f"Data for {st.session_state.away_team_name}")
st.dataframe(st.session_state.away_team_data)

    
#https://statsapi.web.nhl.com/api/v1/game/2022020510/feed/live
#waitress-serve --listen=127.0.0.2:8083 app:app

#https://statsapi.web.nhl.com/api/v1/game/2022020528/feed/live
# the last eventIdx time is not 0:0