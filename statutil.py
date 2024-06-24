import pandas as pd


def convert_innings_pitched(column):
    def convert_inning(inning_float):
        # Split the integer and fractional part
        whole_innings = int(inning_float)
        outs = (inning_float - whole_innings) * 10
        true_inning = whole_innings + (outs / 3)
        return true_inning

    return column.apply(convert_inning)


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
        group[rolling_columns]
        .rolling(window=int(span), min_periods=1)
        .sum()
        .shift(shift)
    )

    group[f"rolling_batting_avg_{span}"] = (
        rolling["batting_hits"] / rolling["batting_atbats"]
    )
    group[f"rolling_batting_obp_{span}"] = (
        rolling["batting_hits"]
        + rolling["batting_baseonballs"]
        + rolling["batting_hitbypitch"]
    ) / (
        rolling["batting_atbats"]
        + rolling["batting_baseonballs"]
        + rolling["batting_hitbypitch"]
        + rolling["batting_sacflies"]
    )

    group[f"rolling_batting_slg_{span}"] = (
        rolling["batting_totalbases"] / rolling["batting_atbats"]
    )
    group[f"rolling_batting_ops_{span}"] = (
        group[f"rolling_batting_obp_{span}"] + group[f"rolling_batting_slg_{span}"]
    )

    group[f"rolling_batting_stolenbasepercentage_{span}"] = rolling[
        "batting_stolenbases"
    ] / (rolling["batting_stolenbases"] + rolling["batting_caughtstealing"])
    group[f"rolling_batting_atbatsperhomerun_{span}"] = (
        rolling["batting_atbats"] / rolling["batting_homeruns"]
    )

    group[f"rolling_fielding_stolenbasepercentage_{span}"] = rolling[
        "fielding_caughtstealing"
    ] / (rolling["fielding_caughtstealing"] + rolling["fielding_stolenbases"])

    group[f"rolling_pitching_obp_{span}"] = (
        rolling["pitching_hits"]
        + rolling["pitching_baseonballs"]
        + rolling["pitching_hitbypitch"]
    ) / (
        rolling["pitching_atbats"]
        + rolling["pitching_baseonballs"]
        + rolling["pitching_hitbypitch"]
        + rolling["pitching_sacflies"]
    )
    group[f"rolling_pitching_stolenbasepercentage_{span}"] = rolling[
        "pitching_caughtstealing"
    ] / (rolling["pitching_caughtstealing"] + rolling["pitching_stolenbases"])
    group[f"rolling_pitching_era_{span}"] = (
        rolling["pitching_earnedruns"] * 9
    ) / rolling["pitching_inningspitched"]
    group[f"rolling_pitching_whip_{span}"] = (
        rolling["pitching_hits"] + rolling["pitching_baseonballs"]
    ) / rolling["pitching_inningspitched"]
    group[f"rolling_pitching_groundoutstoairouts_{span}"] = (
        rolling["pitching_groundouts"] / rolling["pitching_airouts"]
    )
    group[f"rolling_pitching_strikepercentage_{span}"] = (
        rolling["pitching_strikes"] / rolling["pitching_pitchesthrown"]
    )
    return group


def reconstruct_lost_pitching_stats(group, span, shift):
    rolling_columns = [
        "baseonballs",
        "hitbypitch",
        "atbats",
        "sacflies",
        "caughtstealing",
        "stolenbases",
        "hits",
        "strikes",
        "pitchesthrown",
        "earnedruns",
        "inningspitched",
        "groundouts",
        "airouts",
        "homeruns",
    ]

    rolling = (
        group[rolling_columns]
        .rolling(window=int(span), min_periods=1)
        .sum()
        .shift(shift)
    )

    group[f"rolling_stolenbasepercentage_{span}"] = rolling["caughtstealing"] / (
        rolling["stolenbases"] + rolling["caughtstealing"]
    )
    group[f"rolling_strikepercentage_{span}"] = (
        rolling["strikes"] / rolling["pitchesthrown"]
    )
    group[f"rolling_runsscoredper9_{span}"] = (
        rolling["earnedruns"] / rolling["inningspitched"] * 9.0
    )
    group[f"rolling_homerunsper9_{span}"] = (
        rolling["homeruns"] / rolling["inningspitched"] * 9.0
    )
    return group


def reconstruct_lost_fielding_stats(group, span, shift):
    rolling_columns = ["caughtstealing", "stolenbases"]
    rolling = (
        group[rolling_columns]
        .rolling(window=int(span), min_periods=1)
        .sum()
        .shift(shift)
    )
    group[f"rolling_stolenbases_{span}"] = rolling["caughtstealing"] / (
        rolling["stolenbases"] + rolling["caughtstealing"]
    )

    return group


def reconstruct_lost_batting_stats(group, span, shift):
    rolling_columns = [
        "hits",
        "atbats",
        "baseonballs",
        "homeruns",
        "hitbypitch",
        "sacflies",
        "totalbases",
        "stolenbases",
        "caughtstealing",
    ]

    rolling = (
        group[rolling_columns].rolling(window=span, min_periods=1).sum().shift(shift)
    )

    group[f"rolling_avg_{span}"] = rolling["hits"] / rolling["atbats"]
    group[f"rolling_obp_{span}"] = (
        rolling["hits"] + rolling["baseonballs"] + rolling["hitbypitch"]
    ) / (
        rolling["atbats"]
        + rolling["baseonballs"]
        + rolling["hitbypitch"]
        + rolling["sacflies"]
    )

    group[f"rolling_slg_{span}"] = rolling["totalbases"] / rolling["atbats"]
    group[f"rolling_ops_{span}"] = (
        group[f"rolling_obp_{span}"] + group[f"rolling_slg_{span}"]
    )

    group[f"rolling_stolenbasepercentage_{span}"] = rolling["stolenbases"] / (
        rolling["stolenbases"] + rolling["caughtstealing"]
    )
    group[f"rolling_atbatsperhomerun_{span}"] = rolling["atbats"] / rolling["homeruns"]

    return group
