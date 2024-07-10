import pandas as pd
from preprocessing import Preprocessor
import subprocess
import requests
from bs4 import BeautifulSoup
import re
import json


def load_rosters():
    with open("rosters.json", "r") as file:
        rosters = json.load(file)
        return rosters


def get_player_stats(p, player_id, pitching, batting, fielding):
    if pitching:
        pitching_df = p.pitching_data[p.pitching_data["player_id"] == player_id]
        recent_stats = pitching_df.sort_values(by="date", ascending=False).head(1)
        return recent_stats
    if batting:
        batting_df = p.batting_data[p.batting_data["player_id"] == player_id]
        recent_stats = batting_df.sort_values(by="date", ascending=False).head(1)
        return recent_stats
    if fielding:
        fielding_df = p.fielding_data[p.fielding_data["player_id"] == player_id]
        recent_stats = fielding_df.sort_values(by="date", ascending=False).head(1)
        return recent_stats


def add_stats_to_dict(prefix, stats, dict, home_or_away):
    for i, r in stats.iterrows():
        for col in stats.columns:
            if col not in [
                "player_id",
                "date",
                "name",
                "position",
                "game_id",
                "team_id",
                "battingorder",
            ]:

                dict[f"{prefix}_{col}_{home_or_away}"] = r[col]


def generate_full_rosters(rosters, p):
    games = []
    for game in rosters:
        if "home_1" not in game:
            continue
        game_dict = {}
        away_pitcher_stats = get_player_stats(
            p, game["away_pitcher_id"], True, False, False
        )
        home_pitcher_stats = get_player_stats(
            p, game["home_pitcher_id"], True, False, False
        )
        add_stats_to_dict("SP", away_pitcher_stats, game_dict, "away")
        add_stats_to_dict("SP", home_pitcher_stats, game_dict, "home")
        for i in range(1, 10):

            home_player_id = game[f"home_{i}"]["id"]
            away_player_id = game[f"away_{i}"]["id"]
            home_position = game[f"home_{i}"]["position"]
            away_position = game[f"away_{i}"]["position"]
            home_batter_stats = get_player_stats(p, home_player_id, False, True, False)
            away_batter_stats = get_player_stats(p, away_player_id, False, True, False)
            home_fielder_stats = get_player_stats(p, home_player_id, False, False, True)
            away_fielder_stats = get_player_stats(p, away_player_id, False, False, True)
            add_stats_to_dict(f"batter_{i}", home_batter_stats, game_dict, "home")
            add_stats_to_dict(f"batter_{i}", away_batter_stats, game_dict, "away")
            add_stats_to_dict(
                f"fielder_{home_position}", home_fielder_stats, game_dict, "home"
            )
            add_stats_to_dict(
                f"fielder_{away_position}", away_fielder_stats, game_dict, "away"
            )

        games.append(game_dict)
    game_profiles = pd.DataFrame(games)
    game_profiles.to_csv("game_profiles.csv")
    return game_profiles


if __name__ == "__main__":
    subprocess.run(["python", "rosters.py"])
    rosters = load_rosters()
    p = Preprocessor([2024], 50, 0, False)
    print(generate_full_rosters(rosters, p))
