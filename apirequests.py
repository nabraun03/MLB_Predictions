import statsapi
import pandas as pd
import json

# Display all columns
pd.set_option("display.max_columns", None)

# Display all rows
pd.set_option("display.max_rows", None)

# Optionally, set the width to avoid truncating cell content
pd.set_option("display.max_colwidth", None)


def get_all_teams():
    return pd.DataFrame(statsapi.lookup_team(""))[["id", "name", "teamCode"]]


def get_team_id(team):
    teams = get_all_teams()
    teamid = teams[teams["teamCode"] == team]["id"].values[0]
    return teamid


def get_player_id(player):
    response = statsapi.lookup_player(player)
    if len(response) > 1:
        raise Exception
    else:
        return response[0]["id"]


def get_season_schedule(team, year):
    teamid = get_team_id(team)
    df = pd.DataFrame(
        statsapi.schedule(
            start_date=f"{year}-01-01", end_date=f"{year}-12-31", team=teamid
        )
    )
    df = df[df["game_type"] == "R"]
    return df[
        ["game_id", "away_name", "home_name", "away_score", "home_score", "status"]
    ]


def get_boxscore(game_id):
    return statsapi.boxscore_data(game_id)


def get_season_boxscores(team, year):
    box_scores = []
    games = get_season_schedule(team, year)
    games = games[games["status"] == "Final"]
    for game in games.itertuples():
        box_scores.append(get_boxscore(game.game_id))
    return pd.DataFrame(box_scores)


def get_roster(team, date):
    roster = statsapi.roster(teamId=team, rosterType="depthChart", date=date)
    players = []
    for player in roster.strip().split("\n"):
        fields = player.strip().split()
        print(fields)
        players.append({"position": fields[1], "name": fields[2] + " " + fields[3]})
    return pd.DataFrame(players)


def get_players_df(team, date):
    roster = get_roster(team, date)
    players = []
    for row in roster.itertuples():
        players.append(statsapi.lookup_player(row.name)[0])
    return pd.DataFrame(players)[["id", "fullName"]]
