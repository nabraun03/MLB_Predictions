def print_object_fields(obj):
    # Filter out built-in attributes/methods
    attributes = [
        attr
        for attr in dir(obj)
        if not callable(getattr(obj, attr)) and not attr.startswith("__")
    ]

    for attr in attributes:
        print(attr)


def add_identifying_fields_to_dict(
    dict, player, date, fullname, position, game_id, team_id, battingorder
):
    dict["player_id"] = int(player[2:])
    dict["date"] = date
    dict["name"] = fullname
    dict["position"] = position
    dict["game_id"] = game_id
    dict["team_id"] = team_id
    dict["battingorder"] = battingorder


def merge_team_stats(team_dict, date, game_id, win, home):
    teamstats = team_dict.teamstats
    stattypes = ["batting", "fielding", "pitching"]
    merged_stats = {
        "name": team_dict.team.name,
        "teamCode": team_dict.team.teamcode,
        "team_id": team_dict.team.id,
        "date": date,
        "game_id": game_id,
        "win": win,
        "home": home,
    }
    # print(team_dict.info)
    for type in stattypes:
        stats = teamstats[type]
        for k, v in stats.items():
            merged_stats[f"{type}_{k}"] = v
    return merged_stats


def add_stats_to_list(stattype, list, player, date, dict, game_id, team_id):
    battingorder = dict.battingorder
    if dict.stats[stattype] != {}:
        stats = dict.stats[stattype]
        add_identifying_fields_to_dict(
            stats,
            player,
            date,
            dict.person.fullname,
            dict.position.abbreviation,
            game_id,
            team_id,
            battingorder,
        )
        list.append(stats)


def add_player_stats(team, date, pitcher_stats, batter_stats, fielder_stats, game_id):
    team_id = team.team.id
    for player, dict in team.players.items():
        add_stats_to_list(
            "pitching", pitcher_stats, player, date, dict, game_id, team_id
        )
        add_stats_to_list("batting", batter_stats, player, date, dict, game_id, team_id)
        add_stats_to_list(
            "fielding", fielder_stats, player, date, dict, game_id, team_id
        )
