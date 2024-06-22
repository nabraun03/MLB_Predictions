def print_object_fields(obj):
    # Filter out built-in attributes/methods
    attributes = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]
    
    for attr in attributes:
        print(attr)

def add_identifying_fields_to_dict(dict, player, date, fullname, position, game_id):
    dict['player_id'] = int(player[2:])
    dict['date'] = date
    dict['name'] = fullname
    dict['position'] = position
    dict['game_id'] = game_id

def merge_team_stats(team_dict, date, game_id):
    teamstats = team_dict.teamstats
    stattypes = ['batting', 'fielding', 'pitching']
    merged_stats = {'name' : team_dict.team.name, 'teamCode' : team_dict.team.teamcode, 'date' : date, 'game_id' : game_id}
    for type in stattypes:
        stats = teamstats[type]
        for k, v in stats.items():
            merged_stats[f'{type}_{k}'] = v
    return merged_stats

def add_stats_to_list(stattype, list, player, date, dict, game_id):
    if dict.stats[stattype] != {}:
        pitching_stats = dict.stats[stattype]
        add_identifying_fields_to_dict(pitching_stats, player, date, dict.person.fullname, dict.position.abbreviation, game_id)
        list.append(pitching_stats)


def add_player_stats(team, date, pitcher_stats, batter_stats, fielder_stats, game_id):
    for player, dict in team.players.items():
        add_stats_to_list('pitching', pitcher_stats, player, date, dict, game_id)
        add_stats_to_list('batting', batter_stats, player, date, dict, game_id)
        add_stats_to_list('fielding', fielder_stats, player, date, dict, game_id)
