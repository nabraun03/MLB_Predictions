import requests
from bs4 import BeautifulSoup
import re
import json


def get_raw_matchups():

    url = "https://www.mlb.com/starting-lineups"
    response = requests.get(url)
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    matchups_raw = soup.find_all("div", class_="starting-lineups__matchup")

    return matchups_raw


def clean_raw_matchups(matchups_raw):

    matchups_text = []
    for matchup in matchups_raw:
        text = matchup.get_text()
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        matchups_text.append(cleaned_text)
    return matchups_text


def add_team_fields_to_dict(m_dict, team, home):
    if home:
        home_or_away = "home"
    else:
        home_or_away = "away"
    m_dict[f"{home_or_away}_team"] = team.get_text().strip()
    m_dict[f"{home_or_away}_id"] = int(
        team.select("a.starting-lineups__team-name--link")[0].get("data-id")
    )


def add_pitcher_fields_to_dict(m_dict, pitchers):
    away_pitcher = pitchers[0]
    home_pitcher = pitchers[1]
    m_dict["away_pitcher"] = away_pitcher.get_text().strip()
    m_dict["home_pitcher"] = home_pitcher.get_text().strip()
    m_dict["away_pitcher_id"] = int(
        away_pitcher.select("a.starting-lineups__pitcher--link")[0]
        .get("href")
        .split("-")[-1]
    )
    m_dict["home_pitcher_id"] = int(
        home_pitcher.select("a.starting-lineups__pitcher--link")[0]
        .get("href")
        .split("-")[2]
    )


def add_lineup_to_dict(m_dict, lineup, home):
    if home:
        home_or_away = "home"
    else:
        home_or_away = "away"

    order = 1
    players = lineup.select("li.starting-lineups__player")
    for player in players:
        player_dict = {}
        player_dict["name"] = player.get_text().strip()
        player_dict["id"] = int(
            player.select("a.starting-lineups__player--link")[0]
            .get("href")
            .split("-")[-1]
        )
        player_dict["position"] = (
            player.select("span.starting-lineups__player--position")[0]
            .get_text()
            .strip()
            .split(" ")[1]
        )
        m_dict[f"{home_or_away}_{order}"] = player_dict
        order += 1


def generate_matchup_dicts(matchups):

    dicts = []

    for matchup in matchups:
        matchup_dict = {}
        # print(matchup)

        home_team = matchup.select("span.starting-lineups__team-name--home")
        away_team = matchup.select("span.starting-lineups__team-name--away")
        add_team_fields_to_dict(matchup_dict, home_team[0], True)
        add_team_fields_to_dict(matchup_dict, away_team[0], False)

        pitchers = matchup.select("div.starting-lineups__pitcher-name")
        add_pitcher_fields_to_dict(matchup_dict, pitchers)

        home_lineup = matchup.select(
            "ol.starting-lineups__team.starting-lineups__team--home"
        )
        away_lineup = matchup.select(
            "ol.starting-lineups__team.starting-lineups__team--away"
        )
        add_lineup_to_dict(matchup_dict, home_lineup[0], True)
        add_lineup_to_dict(matchup_dict, away_lineup[0], False)

        dicts.append(matchup_dict)
    return dicts


if __name__ == "__main__":
    raw_matchups = get_raw_matchups()
    matchups = generate_matchup_dicts(raw_matchups)
    with open("rosters.json", "w") as file:
        json.dump(matchups, file, indent=4)

    # matchups = clean_raw_matchups(raw_matchups)
