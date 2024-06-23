import pandas as pd


def reconstruct_lost_team_stats(group, span, shift):

    rolling_columns = [
        "batting_hits",
        "batting_atbats",
        "batting_baseonballs",
        "batting_homeruns",
        "batting_hitbypitch",
        "batting_sacflies",
        "batting_totalbases",
        "batting_stolenbases",
        "batting_caughtstealing",
        "fielding_caughtstealing",
        "fielding_stolenbases",
        "pitching_baseonballs",
        "pitching_hitbypitch",
        "pitching_atbats",
        "pitching_sacflies",
        "pitching_caughtstealing",
        "pitching_stolenbases",
        "pitching_hits",
        "pitching_strikes",
        "pitching_pitchesthrown",
        "pitching_earnedruns",
        "pitching_inningspitched",
        "pitching_groundouts",
        "pitching_airouts",
    ]

    rolling = (
        group[rolling_columns].rolling(window=span, min_periods=1).sum().shift(shift)
    )

    group["rolling_batting_avg"] = rolling["batting_hits"] / rolling["batting_atbats"]
    group["rolling_batting_obp"] = (
        rolling["batting_hits"]
        + rolling["batting_baseonballs"]
        + rolling["batting_hitbypitch"]
    ) / (
        rolling["batting_atbats"]
        + rolling["batting_baseonballs"]
        + rolling["batting_hitbypitch"]
        + rolling["batting_sacflies"]
    )

    group["rolling_batting_slg"] = (
        rolling["batting_totalbases"] / rolling["batting_atbats"]
    )
    group["rolling_batting_ops"] = (
        group["rolling_batting_obp"] + group["rolling_batting_slg"]
    )

    group["rolling_batting_stolenbasepercentage"] = rolling["batting_stolenbases"] / (
        rolling["batting_stolenbases"] + rolling["batting_caughtstealing"]
    )
    group["rolling_batting_atbatsperhomerun"] = (
        rolling["batting_atbats"] / rolling["batting_homeruns"]
    )

    group["rolling_fielding_stolenbasepercentage"] = rolling[
        "fielding_caughtstealing"
    ] / (rolling["fielding_caughtstealing"] + rolling["fielding_stolenbases"])

    group["rolling_pitching_obp"] = (
        rolling["pitching_hits"]
        + rolling["pitching_baseonballs"]
        + rolling["pitching_hitbypitch"]
    ) / (
        rolling["pitching_atbats"]
        + rolling["pitching_baseonballs"]
        + rolling["pitching_hitbypitch"]
        + rolling["pitching_sacflies"]
    )
    group["rolling_pitching_stolenbasepercentage"] = rolling[
        "pitching_caughtstealing"
    ] / (rolling["pitching_caughtstealing"] + rolling["pitching_stolenbases"])
    group["rolling_pitching_era"] = (rolling["pitching_earnedruns"] * 9) / rolling[
        "pitching_inningspitched"
    ]
    group["rolling_pitching_whip"] = (
        rolling["pitching_hits"] + rolling["pitching_baseonballs"]
    ) / rolling["pitching_inningspitched"]
    group["rolling_pitching_groundoutstoairouts"] = (
        rolling["pitching_groundouts"] / rolling["pitching_airouts"]
    )
    group["rolling_pitching_strikepercentage"] = (
        rolling["pitching_strikes"] / rolling["pitching_pitchesthrown"]
    )
    return group
