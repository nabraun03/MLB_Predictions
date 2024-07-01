import pandas as pd
import numpy as np
from statutil import (
    convert_innings_pitched,
    reconstruct_lost_pitching_stats,
    reconstruct_lost_team_stats,
    reconstruct_lost_fielding_stats,
    reconstruct_lost_batting_stats,
)

import warnings
from pandas.errors import PerformanceWarning

warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
warnings.filterwarnings("ignore", category=PerformanceWarning, module="pandas")


class Preprocessor:

    def __init__(self, seasons, span, shift):

        self.seasons = seasons
        self.span = span
        self.shift = shift
        self.games = self.load_games()
        self.team_data = self.load_team_data()
        self.load_player_data()
        self.generate_all_rosters()
        # Combine player data for each year
        # Calculate running averages
        # Generate rosters
        self.save_data()

    def load_games(self):
        seasons = []
        for season in self.seasons:
            seasons.append(pd.read_csv(f"{season}_games.csv"))
        return pd.concat(seasons)

    def load_team_data(self):
        modified_groups = []
        for season in self.seasons:
            team_df = pd.read_csv(f"{season}_team_stats.csv")
            # Calculate statistics for each season
            ## Game count, time between games, running averages, winning percentages, streaks
            grouped = team_df.groupby("teamCode")
            for name, group in grouped:
                group["game_count"] = (
                    group["game_id"].expanding().count().shift(self.shift).fillna(0)
                )
                group["date"] = pd.to_datetime(group["date"])
                group["time_between_games"] = group["date"].diff().dt.days
                group["playoff"] = (group["game_count"] > 162).astype(int)

                group["pitching_inningspitched"] = convert_innings_pitched(
                    group["pitching_inningspitched"]
                )

                print("Generating team data")
                group = self.generate_team_running_averages(group)
                group = self.generate_winning_percentages(group)
                group = self.generate_streak(group)

                modified_groups.append(group)

        # Concatenate team data
        return pd.concat(modified_groups)

    def generate_winning_percentages(self, group):
        # Calculate overall winning percentage
        for span_factor in [1, 2, 10]:
            col_name = f"winning_percentage_last_{self.span/span_factor}"
            group[col_name] = (
                group["win"]
                .rolling(window=int(self.span / span_factor), min_periods=1)
                .mean()
                .shift(self.shift)
            )

            # Calculate winning percentage for away and away games
            home_games = group[group["home"] == True]
            home_games[f"home_{col_name}"] = (
                home_games["win"]
                .rolling(window=int(self.span / span_factor), min_periods=0)
                .mean()
            )

            away_games = group[group["home"] == False]
            away_games[f"away_{col_name}"] = (
                away_games["win"]
                .rolling(window=int(self.span / span_factor), min_periods=0)
                .mean()
            )

            # Merge back the calculated home and away percentages to the main dataframe
            group = group.merge(
                home_games[["game_id", f"home_{col_name}"]], on="game_id", how="left"
            )
            group = group.merge(
                away_games[["game_id", f"away_{col_name}"]], on="game_id", how="left"
            )

            # Forward fill the NaN values in home and away winning percentages
            group[f"home_{col_name}"] = (
                group[f"home_{col_name}"].ffill().shift(self.shift)
            )
            group[f"away_{col_name}"] = (
                group[f"away_{col_name}"].ffill().shift(self.shift)
            )

            # Fill remaining NaN values with 0 (for the start of the series)
            group[[f"home_{col_name}", f"away_{col_name}"]] = group[
                [f"home_{col_name}", f"away_{col_name}"]
            ].fillna(0)

            return group

    def generate_team_running_averages(self, group):
        for span_factor in [1, 2, 10]:
            averaging_columns = [
                col
                for col in group.columns
                if col
                not in [
                    "teamCode",
                    "team_id",
                    "name",
                    "home",
                    "game_id",
                    "date",
                    "win",
                    "game_count",
                    "time_between_games",
                    "playoff",
                    "batting_avg",
                    "batting_obp",
                    "batting_slg",
                    "batting_ops",
                    "batting_stolenbasepercentage",
                    "batting_atbatsperhomerun",
                    "fielding_stolenbasepercentage",
                    "pitching_obp",
                    "pitching_stolenbasepercentage",
                    "pitching_era",
                    "pitching_whip",
                    "pitching_groundoutstoairouts",
                    "pitching_strikepercentage",
                ]
            ]
            for col in averaging_columns:

                running_avg_col_name = f"running_avg_{col}_last_{self.span/span_factor}"
                group[running_avg_col_name] = (
                    group[col]
                    .ewm(span=self.span / span_factor, min_periods=1)
                    .mean()
                    .shift(self.shift)
                )
            print(self.span / span_factor)
            group = reconstruct_lost_team_stats(
                group, self.span / span_factor, self.shift
            )
        group = group.drop(columns=averaging_columns)

        group = group.drop(
            columns=[
                "batting_avg",
                "batting_obp",
                "batting_slg",
                "batting_ops",
                "batting_stolenbasepercentage",
                "batting_atbatsperhomerun",
                "fielding_stolenbasepercentage",
                "pitching_obp",
                "pitching_stolenbasepercentage",
                "pitching_era",
                "pitching_whip",
                "pitching_groundoutstoairouts",
                "pitching_strikepercentage",
            ]
        )
        return group

    def calculate_streak(self, group, home_or_away):
        # Initialize streak column

        group[f"home_streak"] = np.nan
        current_streak = 0

        # Select only the relevant games
        relevant_games = group[group["home"] == True]

        # Calculate the streaks
        for game in relevant_games.itertuples():
            if current_streak < 1:
                if game.win:
                    current_streak = 1
                else:
                    current_streak -= 1
            else:
                if game.win:
                    current_streak += 1
                else:
                    current_streak = -1

            # Use .at for a more efficient assignment
            group.at[game.Index, f"home_streak"] = current_streak

        # Shift the streaks to avoid lookahead bias
        group[f"home_streak"] = (
            group[f"home_streak"].bfill().shift(self.shift).fillna(current_streak)
        )

        group[f"away_streak"] = np.nan
        current_streak = 0

        # Select only the relevant games
        relevant_games = group[group["home"] == False]

        # Calculate the streaks
        for game in relevant_games.itertuples():
            if current_streak < 1:
                if game.win:
                    current_streak = 1
                else:
                    current_streak -= 1
            else:
                if game.win:
                    current_streak += 1
                else:
                    current_streak = -1

            # Use .at for a more efficient assignment
            group.at[game.Index, f"away_streak"] = current_streak

        # Shift the streaks to avoid lookahead bias
        group[f"away_streak"] = (
            group[f"away_streak"].bfill().shift(self.shift).fillna(current_streak)
        )

        return group

    def generate_streak(self, group):
        group["streak"] = 0
        current_streak = 0
        for i, row in group.iterrows():

            if current_streak < 1:
                if row["win"]:
                    current_streak = 1
                else:
                    current_streak -= 1
            else:
                if row["win"]:
                    current_streak += 1
                else:
                    current_streak = -1

            group.at[i, "streak"] = current_streak
        group["streak"] = group["streak"].shift(self.shift).fillna(0)
        group = self.calculate_streak(group, True)
        group = self.calculate_streak(group, False)
        return group

    def load_player_data(self):

        # Merge all years of data
        pitching_data = []
        fielding_data = []
        batting_data = []
        for season in self.seasons:
            pitching_data.append(pd.read_csv(f"{season}_pitching_stats.csv"))
            fielding_data.append(pd.read_csv(f"{season}_fielding_stats.csv"))
            batting_data.append(pd.read_csv(f"{season}_batting_stats.csv"))
        merged_pitching_stats = pd.concat(pitching_data).sort_values(by=["date"])
        merged_fielding_stats = pd.concat(fielding_data).sort_values(by=["date"])
        merged_batting_stats = pd.concat(batting_data).sort_values(by=["date"])

        merged_pitching_stats["inningspitched"] = convert_innings_pitched(
            merged_pitching_stats["inningspitched"]
        )
        print("Generating batting data")
        self.batting_data = self.generate_batting_averages(merged_batting_stats)
        self.batting_data = self.batting_data.drop_duplicates(["player_id", "game_id"])
        print("Generating pitching data")
        self.pitching_data = self.generate_pitching_averages(merged_pitching_stats)
        self.pitching_data = self.pitching_data.drop_duplicates(
            ["player_id", "game_id"]
        )
        print("Generating fielding data")
        self.fielding_data = self.generate_fielding_averages(merged_fielding_stats)
        self.fielding_data = self.fielding_data.drop_duplicates(
            ["player_id", "game_id"]
        )

    def generate_pitching_averages(self, data):
        modified_groups = []
        grouped = data.groupby(["player_id"])
        count = 0
        for name, group in grouped:
            group = group.sort_values(by=["date"])
            if count % 10 == 0:
                print(count / len(grouped))
            count += 1
            group = self.running_pitching_averages(group)
            modified_groups.append(group)
        return pd.concat(modified_groups)

    def generate_fielding_averages(self, data):
        modified_groups = []
        grouped = data.groupby(["player_id"])
        count = 0
        for name, group in grouped:
            group = group.sort_values(by=["date"])
            if count % 10 == 0:
                print(count / len(grouped))
            count += 1
            group = self.running_fielding_averages(group)
            modified_groups.append(group)
        return pd.concat(modified_groups)

    def generate_batting_averages(self, data):
        modified_groups = []
        grouped = data.groupby(["player_id"])
        count = 0
        for name, group in grouped:
            group = group.sort_values(by=["date"])
            if count % 10 == 0:
                print(count / len(grouped))
            count += 1
            group = self.running_batting_averages(group)
            modified_groups.append(group)
        return pd.concat(modified_groups)

    def running_pitching_averages(self, group):
        averaging_columns = [
            col
            for col in group.columns
            if col
            not in [
                "game_id",
                "player_id",
                "team_id",
                "name",
                "date",
                "gamesstarted",
                "position",
                "summary",
                "note",
                "stolenbasepercentage",
                "strikepercentage",
                "runsscoredper9",
                "homerunsper9",
                "atbats",
                "position",
                "battingorder",
            ]
        ]

        new_columns = {}
        for span_factor in [1, 2, 10]:
            at_bats = (
                group["atbats"]
                .rolling(window=int(self.span / span_factor), min_periods=1)
                .sum()
                .shift(self.shift)
            )
            for col in averaging_columns:

                running_avg_col_name = f"running_avg_{col}_{int(self.span/span_factor)}"
                # Perform the calculation and store the result in the container
                per_at_bat = (
                    group[col]
                    .rolling(window=int(self.span / span_factor), min_periods=1)
                    .sum()
                    .shift(self.shift)
                ) / at_bats
                new_columns[running_avg_col_name] = per_at_bat
            group = reconstruct_lost_pitching_stats(
                group, int(self.span / span_factor), self.shift
            )

        # Create a new DataFrame from the container
        new_columns_df = pd.DataFrame(new_columns, index=group.index)

        # Concatenate the new DataFrame with the original group DataFrame
        group = pd.concat([group, new_columns_df], axis=1)

        # Drop the original averaging columns
        group = group.drop(columns=averaging_columns)
        group = group.drop(
            columns=[
                "stolenbasepercentage",
                "strikepercentage",
                "runsscoredper9",
                "homerunsper9",
                "summary",
                "note",
            ]
        )

        return group

    def running_fielding_averages(self, group):
        averaging_columns = [
            col
            for col in group.columns
            if col
            not in [
                "game_id",
                "player_id",
                "team_id",
                "name",
                "date",
                "position",
                "stolenbasepercentage",
                "battingorder",
            ]
        ]

        new_columns = {}
        for span_factor in [1, 2, 10]:
            for col in averaging_columns:

                running_avg_col_name = f"running_avg_{col}_{int(self.span/span_factor)}"
                # Perform the calculation and store the result in the container
                new_columns[running_avg_col_name] = (
                    group[col]
                    .ewm(span=int(self.span / span_factor), min_periods=1)
                    .mean()
                    .shift(self.shift)
                )
            group = reconstruct_lost_fielding_stats(
                group, int(self.span / span_factor), self.shift
            )

        # Create a new DataFrame from the container
        new_columns_df = pd.DataFrame(new_columns, index=group.index)

        # Concatenate the new DataFrame with the original group DataFrame
        group = pd.concat([group, new_columns_df], axis=1)

        # Drop the original averaging columns
        group = group.drop(columns=averaging_columns)
        group = group.drop(columns=["stolenbasepercentage"])
        return group

    def running_batting_averages(self, group):
        averaging_columns = [
            col
            for col in group.columns
            if col
            not in [
                "game_id",
                "player_id",
                "team_id",
                "summary",
                "note",
                "name",
                "date",
                "position",
                "stolenbasepercentage",
                "atbatsperhomerun",
                "atbats",
                "battingorder",
            ]
        ]

        new_columns = {}
        for span_factor in [1, 2, 10]:
            at_bats = (
                group["atbats"]
                .rolling(window=int(self.span / span_factor), min_periods=1)
                .sum()
                .shift(self.shift)
            )
            for col in averaging_columns:
                running_avg_col_name = f"running_avg_{col}_{int(self.span/span_factor)}"
                # Perform the calculation and store the result in the container
                per_at_bat = (
                    group[col]
                    .rolling(window=int(self.span / span_factor), min_periods=1)
                    .sum()
                    .shift(self.shift)
                ) / (at_bats)
                new_columns[running_avg_col_name] = per_at_bat
            group = reconstruct_lost_batting_stats(
                group, int(self.span / span_factor), self.shift
            )

        # Create a new DataFrame from the container
        new_columns_df = pd.DataFrame(new_columns, index=group.index)

        # Concatenate the new DataFrame with the original group DataFrame
        group = pd.concat([group, new_columns_df], axis=1)

        # Drop the original averaging columns
        group = group.drop(columns=averaging_columns)
        group = group.drop(
            columns=["stolenbasepercentage", "summary", "note", "atbatsperhomerun"]
        )
        return group

    def generate_all_rosters(self):

        profiles = []
        count = 0
        for game in self.games.itertuples():
            if count % 10 == 0:
                print(count / len(self.games))
            count += 1
            game_id = game.game_id
            date = game.date
            home_team = game.home_id
            away_team = game.away_id
            home_roster = self.generate_roster(home_team, game_id, date)
            away_roster = self.generate_roster(away_team, game_id, date)
            profiles.append(home_roster)
            profiles.append(away_roster)
        self.rosters = pd.DataFrame(profiles).sort_values(by=["date"])

    def generate_roster(self, team, game_id, date):
        pitchers = self.pitching_data[
            (self.pitching_data["game_id"] == game_id)
            & (self.pitching_data["team_id"] == team)
            & (self.pitching_data["gamesstarted"] == 1)
        ]

        batters = self.batting_data[
            (self.batting_data["game_id"] == game_id)
            & (self.batting_data["team_id"] == team)
            & (self.batting_data["battingorder"] != None)
            & (self.batting_data["battingorder"] % 100 == 0)
        ]
        fielders = self.fielding_data[
            (self.fielding_data["game_id"] == game_id)
            & (self.fielding_data["team_id"] == team)
        ]

        profile = {"game_id": game_id, "team_id": team, "date": date}

        if len(pitchers) != 1:
            print(pitchers)
            assert len(pitchers) == 1
        if len(batters) != 9:
            print(batters)
            all_batters = self.batting_data[
                (self.batting_data["game_id"] == game_id)
                & (self.batting_data["team_id"] == team)
                & (self.batting_data["battingorder"] != None)
            ].sort_values(by=["battingorder"])

            # Separate starters and pinch hitters
            starters = all_batters[all_batters["battingorder"] % 100 == 0].copy()
            pinch_hitters = all_batters[all_batters["battingorder"] % 100 == 1].copy()

            # Create a dictionary to keep track of batting order positions
            batting_order = {i: None for i in range(100, 1000, 100)}

            # Fill the batting order with starters first
            for _, batter in starters.iterrows():
                batting_order[batter["battingorder"]] = batter

            # Fill in pinch hitters where there are no starters
            for _, batter in pinch_hitters.iterrows():
                order = batter["battingorder"] - 1
                if batting_order[order] is None:
                    batting_order[order] = batter

                    # Identify missing spots and fill with the batter with the most at-bats
            missing_spots = [
                order for order, batter in batting_order.items() if batter is None
            ]
            all_batters_sorted = batters.sort_values(by="atbats", ascending=False)

            batters_included = batting_order.values()

            for order in missing_spots:
                for _, batter in all_batters_sorted.iterrows():
                    if batter["player_id"] not in [batters_included]:
                        batting_order[order] = batter
                        break

            # Collect the final list of all_batters
            batters = pd.DataFrame(
                [batter for batter in batting_order.values() if batter is not None]
            )
            if len(batters) != 9:
                print(all_batters["battingorder"])
                assert len(batters) == 9
        if len(fielders) != 9:
            print(fielders)
            assert len(fielders) == 9

        # Add pitcher stats to profile
        for index, row in pitchers.iterrows():
            for stat in row.index:
                if stat not in [
                    "game_id",
                    "team_id",
                    "gamesstarted",
                    "date",
                    "player_id",
                    "name",
                ]:
                    profile_key = f"SP_{stat}"
                    profile[profile_key] = row[stat]

        # Add batters stats to profile
        nonstat_columns = [
            "game_id",
            "team_id",
            "battingorder",
            "date",
            "player_id",
            "name",
            "position",
        ]
        count = 1
        for index, row in batters.iterrows():
            for stat in row.index:
                if stat not in nonstat_columns:
                    profile_key = f"batter_{count}_{stat}"
                    profile[profile_key] = row[stat]
            count += 1

            # Add fielders stats to profile
        for index, row in fielders.iterrows():
            for stat in row.index:
                if stat not in nonstat_columns:
                    profile_key = f"fielder_{row['position']}_{stat}"
                    profile[profile_key] = row[stat]
        return profile

    def save_data(self):
        self.team_data.to_csv("team_data.csv")
        self.pitching_data.to_csv("pitching_data.csv")
        self.fielding_data.to_csv("fielding_data.csv")
        self.batting_data.to_csv("batting_data.csv")
        self.rosters.to_csv("rosters.csv")
        self.complete_profiles = pd.merge(
            self.team_data, self.rosters, on=["game_id", "team_id"], how="inner"
        )
        self.complete_profiles.to_csv("complete_profiles.csv")


if __name__ == "__main__":
    Preprocessor([2022, 2023, 2024], 50, 1)
