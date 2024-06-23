import pandas as pd
import numpy as np
from statutil import reconstruct_lost_team_stats


class Preprocessor:

    def __init__(self, seasons, span, shift):

        self.seasons = seasons
        self.span = span
        self.shift = shift
        self.team_data = self.load_team_data()
        # Combine player data for each year
        # Calculate running averages
        # Generate rosters

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

                group = self.generate_team_running_averages(group)

                group = self.generate_winning_percentages(group)
                group = self.generate_streak(group)

                modified_groups.append(group)

        # Concatenate team data
        return pd.concat(modified_groups)

    def generate_winning_percentages(self, group):
        # Calculate overall winning percentage
        col_name = f"winning_percentage_last_{self.span}"
        group[col_name] = (
            group["win"]
            .rolling(window=self.span, min_periods=1)
            .mean()
            .shift(self.shift)
        )

        # Calculate winning percentage for away and away games
        home_games = group[group["home"] == True]
        home_games[f"home_{col_name}"] = (
            home_games["win"].rolling(window=self.span, min_periods=0).mean()
        )

        away_games = group[group["home"] == False]
        away_games[f"away_{col_name}"] = (
            away_games["win"].rolling(window=self.span, min_periods=0).mean()
        )

        # Merge back the calculated home and away percentages to the main dataframe
        group = group.merge(
            home_games[["game_id", f"home_{col_name}"]], on="game_id", how="left"
        )
        group = group.merge(
            away_games[["game_id", f"away_{col_name}"]], on="game_id", how="left"
        )

        # Forward fill the NaN values in home and away winning percentages
        group[f"home_{col_name}"] = group[f"home_{col_name}"].ffill().shift(self.shift)
        group[f"away_{col_name}"] = group[f"away_{col_name}"].ffill().shift(self.shift)

        # Fill remaining NaN values with 0 (for the start of the series)
        group[[f"home_{col_name}", f"away_{col_name}"]] = group[
            [f"home_{col_name}", f"away_{col_name}"]
        ].fillna(0)

        return group

    def generate_team_running_averages(self, group):
        averaging_columns = [
            col
            for col in group.columns
            if col
            not in [
                "teamCode",
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
            running_avg_col_name = f"running_avg_{col}_last_{self.span}"
            group[running_avg_col_name] = (
                group[col].ewm(span=self.span, min_periods=1).mean().shift(self.shift)
            )
        group = reconstruct_lost_team_stats(group, self.span, self.shift)
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

        # Generate running averages
        pass

    def generate_rosters(self):

        # Find starters from fielding data

        # Assort best 5 pitchers from bullpen

        # Create vector for each team and game
        pass


if __name__ == "__main__":
    Preprocessor([2022, 2023, 2024], 50, 1)
