import json
import os
from typing import Dict, List, Tuple
import numpy as np
from bisect import bisect

class Penalty:
    def __init__(self):

        # time for which team is shorthanded, for major and match penalties actual times are double of this value
        # Since Misconduct penalties don't cause shorthanded play, we ignore that penalty in this calculation
        self.penalty_times = {"Minor": 120, "Double Minor": 240, "Major": 300, "Match": 300}
        self.period_len = 1200

    def get_game_seconds(self, all_plays):
        event_time = []
        for i in range(len(all_plays)):
            period_num = all_plays[i]['about']['period']
            period_time = all_plays[i]['about']['periodTime']
            minutes, sec = [int(x) for x in period_time.split(":")]
            time_in_seconds = (period_num - 1) * self.period_len + minutes * 60 + sec
            event_time.append(time_in_seconds)
        return event_time

    def get_teamwise_penalty_events(self, data, home, away):
        # return penalty events for home, away team
        home_events, away_events = [], []
        play_data = data['liveData']["plays"]["allPlays"]
        penalty_events = [i for i, x in enumerate(play_data) if x["result"]["event"] == "Penalty"]

        for event in penalty_events:
            p_type = play_data[event]["result"].get("penaltySeverity")
            if p_type in list(self.penalty_times.keys()):
                p_time = self.penalty_times[p_type]
                if play_data[event]["team"]["name"] == home:
                    home_events.append((event, p_type, p_time))
                elif play_data[event]["team"]["name"] == away:
                    away_events.append((event, p_type, p_time))
            else:
                pass
                # just to log
                # if p_type != "Misconduct":
                #     print("Found new penalty type", p_type)
        return home_events, away_events

    def get_teamwise_goal_events(self, data, home, away):
        home_events, away_events = [], []
        play_data = data['liveData']["plays"]["allPlays"]
        goal_events = [i for i, x in enumerate(play_data) if x["result"]["event"] == "Goal"]
        for event in goal_events:
            if play_data[event]["team"]["name"] == home:
                home_events.append(event)
            elif play_data[event]["team"]["name"] == away:
                away_events.append(event)
        return home_events, away_events

    def get_active_penalties(self, penalty_events, opposite_goal_events, event_time):
        active = np.zeros(len(event_time))
        for start_idx, p_type, p_time in penalty_events:
            end_time = event_time[start_idx] + p_time
            # find event idx at which penalty would have normally expired
            end_idx = bisect(event_time, end_time) - 1

            goals_between_penalty = [goal_idx for goal_idx in opposite_goal_events if
                                     start_idx + 1 < goal_idx < end_idx]
            copy_active = active.copy()

            if p_type == "Minor" and len(goals_between_penalty) > 0:
                # if opposite team scores goal in between, set end index as goal event
                end_idx = goals_between_penalty[0]
                opposite_goal_events.remove(end_idx)

            elif p_type == "Double Minor" and len(goals_between_penalty) > 0:
                # if goals between, update end index
                for i in goals_between_penalty[:2]:
                    goal_time = event_time[i]
                    end_time = max(goal_time, end_time - 60)
                    opposite_goal_events.remove(i)
                end_idx = bisect(event_time, end_time) - 1

            copy_active[start_idx+1: end_idx+1] += -1

            # check if this causes more than 2 shorthands, if it does, readjust penalty such that there is max 2 shorthands
            if min(copy_active) < -2:
                # find where -2 ends,
                double_penalty_ends_at = np.max(np.where(copy_active == -2))
                start_idx = double_penalty_ends_at
                end_time = event_time[start_idx] + p_time
                end_idx = bisect(event_time, end_time) - 1

            active[start_idx+1: end_idx+1] += -1

        return active

    def get_time_since_powerplay(self, play_data, is_powerplay, event_times):
        time_since_powerplay = []
        powerplay_start = 0
        for i, item in enumerate(is_powerplay):
            if item == 0:
                # if next event is powerplay event, reset start timer
                next_index = min(i+1, len(is_powerplay)-1)
                if is_powerplay[next_index] == 1:
                    powerplay_start = event_times[i]
                time_since_powerplay.append(0)
            elif item == 1:
                time = event_times[i] - powerplay_start
                time_since_powerplay.append(time)

        filtered_times = []
        for i in range(len(play_data)):
            if play_data[i]["result"]["event"] in ["Shot", "Goal"]:
                filtered_times.append(time_since_powerplay[i])
            else:
                continue

        return filtered_times

    def get_friendly_non_friendly_skaters(self, play_data, home_skaters, away_skaters, home_name, away_name):
        friendly_skaters, non_friendly_skaters = [], []
        for i in range(len(play_data)):
            if play_data[i]["result"]["event"] not in ["Shot", "Goal"]:
                continue

            event_team = play_data[i]["team"]["name"]
            if event_team == home_name:
                friendly_skaters.append(home_skaters[i])
                non_friendly_skaters.append(away_skaters[i])
            else:
                friendly_skaters.append(away_skaters[i])
                non_friendly_skaters.append(home_skaters[i])
        return friendly_skaters, non_friendly_skaters

    def process_events(self, data: Dict):
        # return time since power play started(seconds)
        # return number of skaters players for both teams

        home, away = [data["gameData"]["teams"][i]["name"] for i in ["home", "away"]]

        play_data = data['liveData']["plays"]["allPlays"]
        home_penalty, away_penalty = self.get_teamwise_penalty_events(data, home, away)
        home_goal, away_goal = self.get_teamwise_goal_events(data, home, away)
        event_times = self.get_game_seconds(play_data)

        home_active_penalty = self.get_active_penalties(home_penalty, away_goal.copy(), event_times)
        away_active_penalty = self.get_active_penalties(away_penalty, home_goal.copy(), event_times)

        home_active_penalty[home_active_penalty < -2] = -2
        away_active_penalty[away_active_penalty < -2] = -2
        # assert np.min(home_active_penalty) >= -2
        # assert np.min(away_active_penalty) >= -2

        home_skaters, away_skaters = 5*np.ones(len(event_times)), 5*np.ones(len(event_times))
        home_skaters += home_active_penalty
        away_skaters += away_active_penalty

        powerplay = np.abs(home_skaters - away_skaters)
        powerplay[powerplay > 0] = 1
        time_since_powerplay = self.get_time_since_powerplay(play_data, powerplay, event_times)
        friendly_skaters, non_friendly_skaters = self.get_friendly_non_friendly_skaters(play_data, home_skaters,
                                                                                        away_skaters, home, away)

        return time_since_powerplay, friendly_skaters, non_friendly_skaters



