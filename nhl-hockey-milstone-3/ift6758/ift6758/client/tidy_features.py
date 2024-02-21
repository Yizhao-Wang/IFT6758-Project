import json
import pandas as pd
import os
from typing import Dict, Tuple
import numpy as np
from penalty_tracker import Penalty


class TidyData:

    def __init__(self):
        # each period is 20 minutes
        self.period_len = 1200
        self.penalty = Penalty()

    def get_game_seconds(self, period_num: int, period_time: str):
        minutes, sec = [int(x) for x in period_time.split(":")]
        time_in_seconds = (period_num-1)*self.period_len + minutes*60 + sec
        return time_in_seconds

    def get_shot_geometry(self, event_team, home_team, home_rink_side, period, coord_x, coord_y) -> Tuple:
        """Returns a tuple of :
        Euclidean distance between shot coordinates and goal post(assuming a point)
        Angle between shot coordinates and goal post center line
        """
        if None in [coord_x, coord_y]:
            return None, None, None

        goal_post_y_coordinate = 0
        if event_team == home_team:
            if home_rink_side == 'left':
                ''' Event team's goal post is ALSO on the LEFT side of the rink '''
                ''' Event team will have to hit on the opposite of home rink side goal post '''
                if period % 2 == 1:
                    ''' During the first and third period, event team will have to hit towards the goal post on the RIGHT side '''
                    goal_post_x_coordinate = 89
                else:
                    ''' During the second and fourth period, event team will have to hit towards the goal post on the LEFT side. '''
                    goal_post_x_coordinate = -89
            else:
                ''' Event team's goal post is ALSO on the RIGHT side of the rink '''
                ''' During the first and the third period, Event team will have to hit on the LEFT side goal post '''
                if period % 2 == 1:
                    goal_post_x_coordinate = -89
                else:
                    goal_post_x_coordinate = 89
        else:
            if home_rink_side == 'left':
                ''' Event team side is RIGHT '''
                ''' During the first and third period, event team has to take a shot on the left goal post '''
                if period % 2 == 1:
                    goal_post_x_coordinate = -89
                else:
                    ''' During the second and fourth period, event team has to take a shot on the right goal post '''
                    goal_post_x_coordinate = 89
            else:
                ''' Event team side is LEFT. '''
                ''' During the first and third period, event team has to take a shot on the right goal post '''
                if period % 2 == 1:
                    goal_post_x_coordinate = 89
                else:
                    ''' During the second and fourth period, event team has to take a shot on the left goal post '''
                    goal_post_x_coordinate = -89

        ''' Compute the distance : euclidean'''
        distance = ((coord_x - goal_post_x_coordinate) ** 2 + (coord_y - goal_post_y_coordinate) ** 2) ** 0.5
        angle = round(self.get_angle((coord_x, coord_y), (goal_post_x_coordinate, goal_post_y_coordinate)), 2)

        return distance, angle, (goal_post_x_coordinate, goal_post_y_coordinate)

    @staticmethod
    def get_angle(shot_coord, goal_coord):
        """
        :param shot_coord: (s_x,c_y)
        :param goal_coord: (g_x,g_y)
        :return:  Angle in degrees subtended by shot position on horizontal goal line, We set angle as positive if s_y > 0
        """
        s_x, s_y = shot_coord
        g_x, g_y = goal_coord
        vector1 = np.array([g_x - s_x, g_y-s_y])
        vector2 = np.array([g_x, g_y])
        sign = [1 if s_y>=0 else -1]
        angle_in_degrees = np.arccos(vector1.dot(vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))) * 57.2958
        return sign[0]*angle_in_degrees

    @staticmethod
    def get_coords(event_data):
        # for coordinates section
        coord_x = None
        coord_y = None
        if 'coordinates' in event_data:
            coord_x = event_data['coordinates'].get('x')
            coord_y = event_data['coordinates'].get('y')
        return coord_x, coord_y

    def get_prev_event_info(self, last_event_data: Dict, curr_time, curr_coords, goal_coords) -> Dict:
        '''
        :param last_event_data:  Dict
        :param curr_time: current event time in seconds
        :param curr_coords: tuple of current event x,y positions
        :param goal_coords: tuple of goal x, y coordinates
        :return: Dict with keys : ()
        '''

        rebound = False
        change_in_angle = 0
        event_type = last_event_data['result']['event']

        # get time
        period = last_event_data['about']['period']
        period_time = last_event_data['about']['periodTime']
        last_time = self.get_game_seconds(period, period_time)
        time_from_last_event = curr_time - last_time

        # get distance metrics
        coord_x, coord_y = self.get_coords(last_event_data)
        curr_x, curr_y = curr_coords
        if not None in [curr_x, curr_y, coord_x, coord_y]:
            distance = ((curr_x - coord_x) ** 2 + (curr_y - coord_y) ** 2) ** 0.5
            distance = round(distance, 2)
            if time_from_last_event == 0:
                speed = 0
            else:
                speed = round(distance/time_from_last_event, 2)
        else:
            distance, speed = None, None

        if event_type == "Shot":
            rebound = True

        if rebound and distance is not None:
            last_shot_angle = self.get_angle((coord_x, coord_y), goal_coords)
            curr_shot_angle = self.get_angle(curr_coords, goal_coords)
            change_in_angle = abs(curr_shot_angle - last_shot_angle)

        info = {"Last event type": event_type, "Last X": coord_x, "Last Y": coord_y, "Time from last event": time_from_last_event,
                "Rebound": rebound, "Distance from last event": distance, "Speed": speed,
                "Change in shot angle": change_in_angle}

        return info

    def process_json(self, data, game_id):
        header_name = ['eventId', 'eventIdx', 'Game ID', 'Event', 'Home Team Name', 'Away Team Name', 'Event Team Name',
                       'Date & Time', 'Period', 'Period Time', 'Period Time Remaining', 'Period Type', 'Home Rink Side',
                       'Shooter Name', 'Goalie Name', 'Scorer Name', 'Shot Type', 'X-Coordinate', 'Y-Coordinate',
                       'Was Net Empty', 'Goalie Strength', 'Game Seconds', 'Shot Distance', 'Shot Angle', "Last event type",
                       "Last X", "Last Y", "Time from last event", "Rebound", "Distance from last event", "Speed",
                       "Change in shot angle"]

        home_side = None
        num_periods = len(data['liveData']['linescore']['periods'])

        if num_periods > 0:
            home_side = data['liveData']['linescore']['periods'][0]['home'].get('rinkSide')

        retain_event = ["Shot", "Goal"]
        home_team = data['gameData']['teams']['home'].get('name')
        away_team = data['gameData']['teams']['away'].get('name')

        all_plays = data['liveData']["plays"]["allPlays"]
        event_data = []  # tidy_data

        for i in range(len(all_plays)):
            event = all_plays[i]['result']['event']
            if event in retain_event:

                # for players section
                scorer_name, shooter_name, goalie_name = None, None, None
                for player in all_plays[i]['players']:
                    if player['playerType'] == 'Shooter':
                        shooter_name = player['player']['fullName']
                    elif player['playerType'] == 'Goalie':
                        goalie_name = player['player']['fullName']
                    elif player['playerType'] == 'Scorer':
                        # When scorer field is present Shooter field is empty in json, so a Scorer is also the shooter
                        scorer_name = player['player']['fullName']
                        shooter_name = player['player']['fullName']

                # shot type
                shot_type = None
                if 'secondaryType' in all_plays[i]['result']:
                    shot_type = all_plays[i]['result']['secondaryType']

                # for about section
                date_time = all_plays[i]['about']['dateTime']
                period = all_plays[i]['about']['period']
                period_time = all_plays[i]['about']['periodTime']
                period_time_remaining = all_plays[i]['about']['periodTimeRemaining']
                period_type = all_plays[i]['about']['periodType']
                event_Idx = all_plays[i]['about']['eventIdx']
                event_Id = all_plays[i]['about']['eventId']

                game_seconds = self.get_game_seconds(int(period), period_time)

                # for coordinates section
                coord_x, coord_y = self.get_coords(all_plays[i])

                # for goal situation
                empty_net = False
                goalie_strength = None
                if event == 'Goal':
                    if 'emptyNet' in all_plays[i]['result']:
                        empty_net = all_plays[i]['result']['emptyNet']
                    goalie_strength = all_plays[i]['result']['strength']['name']

                # team information
                event_team_name = all_plays[i]['team']['name']

                # goal distance and shot angle computation
                goal_distance, goal_angle, goal_coords = self.get_shot_geometry(event_team_name, home_team, home_side, period, coord_x, coord_y)

                data_sample = [event_Id, event_Idx, game_id, event, home_team, away_team, event_team_name, date_time,
                               period, period_time, period_time_remaining, period_type, home_side, shooter_name,
                               goalie_name, scorer_name, shot_type, coord_x, coord_y,
                               empty_net, goalie_strength, game_seconds, goal_distance, goal_angle]


                # add features from last event
                curr_coords = (coord_x, coord_y)
                prev_event_features = self.get_prev_event_info(all_plays[i-1], game_seconds, curr_coords, goal_coords)
                feature_values = list(prev_event_features.values())
                data_sample.extend(list(feature_values))

                assert len(header_name) == len(data_sample)
                event_data.append(data_sample)

        df = pd.DataFrame(event_data, columns=header_name)
        time_since_powerplay, friendly_skaters, non_friendly_skaters = self.penalty.process_events(data)
        df["Time since Powerplay"] = time_since_powerplay
        df["Friendly skaters"] = friendly_skaters
        df["Non Friendly Skaters"] = non_friendly_skaters
        return df