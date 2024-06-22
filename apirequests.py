import statsapi
import pandas as pd
import json
from datetime import date, timedelta
import mlbstatsapi
from util import merge_team_stats, add_identifying_fields_to_dict, add_player_stats
mlb = mlbstatsapi.Mlb()

# Display all columns
pd.set_option("display.max_columns", None)

# Display all rows
pd.set_option("display.max_rows", None)

# Optionally, set the width to avoid truncating cell content
pd.set_option("display.max_colwidth", None)

class DataFetcher:

    def __init__(self, season, use_existing=True):
        self.season = season
        self.existing_team_stats = pd.DataFrame()
        self.existing_pitching_stats = pd.DataFrame()
        self.existing_fielding_stats = pd.DataFrame()
        self.existing_batting_stats = pd.DataFrame()
        self.fetch_and_save_data()

    def find_existing_data(self):
        try:
            self.existing_team_stats = pd.read_csv(f'{self.season}_team_stats.csv')
            self.existing_fielding_stats = pd.read_csv(f'{self.season}_fielding_stats.csv')
            self.existing_batting_stats = pd.read_csv(f'{self.season}_batting_stats.csv')
            self.existing_pitching_stats = pd.read_csv(f'{self.season}_pitching_stats.csv')
        except:
            print("Existing data not found")

    def data_exists(self, game_id):
        return not self.existing_team_stats.empty and game_id in self.existing_team_stats['game_id'].unique()

    def get_season_games(self):
        if self.season == 2024:
            yesterday = date.today() - timedelta(days=1)
            yesterday.strftime('%y-%m-%d')
            schedule = mlb.get_schedule(start_date=f'{self.season}-01-01', end_date=yesterday, gameTypes=['R', 'P'])
        else:
            schedule = mlb.get_schedule(start_date=f'{self.season}-01-01', end_date=f'{self.season}-12-31', gameTypes=['R', 'P'])
        games = []
        for day in schedule.dates:
            for game in day.games:
                games.append((game.gamepk, day.date))
        return games
    
    def concatenate_existing_data(self, team_stats, pitcher_stats, batter_stats, fielder_stats):
        if not self.existing_team_stats.empty and len(team_stats) != 0:
            team_df = pd.concat([self.existing_team_stats, pd.concat(team_stats, ignore_index=True)], ignore_index=True)
        elif len(team_stats) == 0:
            team_df = self.existing_team_stats
        else:
            team_df = pd.DataFrame(team_stats)

        if not self.existing_pitching_stats.empty and len(pitcher_stats) != 0:
            pitcher_df = pd.concat([self.existing_pitching_stats, pd.concat(pitcher_stats, ignore_index=True)], ignore_index=True)
        elif len(pitcher_stats) == 0:
            pitcher_df = self.existing_pitching_stats
        else:
            pitcher_df = pd.DataFrame(pitcher_stats)

        if not self.existing_batting_stats.empty and len(batter_stats) != 0:
            batter_df = pd.concat([self.existing_batting_stats, pd.concat(batter_stats, ignore_index=True)], ignore_index=True)
        elif len(batter_stats) == 0:
            batter_df = self.existing_batting_stats
        else:
            batter_df = pd.DataFrame(batter_stats)
        
        if not self.existing_fielding_stats.empty and len(fielder_stats) != 0:
            fielder_df = pd.concat([self.existing_fielding_stats, pd.concat(fielder_stats, ignore_index=True)], ignore_index=True)
        elif len(fielder_stats) == 0:
            fielder_df = self.existing_fielding_stats
        else:
            fielder_df = pd.DataFrame(fielder_stats)
        
        return team_df, pitcher_df, batter_df, fielder_df
        

        

    def fetch_stats(self):

        team_stats = []
        pitcher_stats = []
        batter_stats = []
        fielder_stats = []

        game_ids = self.get_season_games()
        count = 0
        for game, date in game_ids:
            if count % 10 == 0:
                print(f'{count} / {len(game_ids)}')
            
            count += 1

            if not self.data_exists(game):
            
                box_score = mlb.get_game_box_score(game)

                home_team = box_score.teams.home
                away_team = box_score.teams.away

                team_stats.append(merge_team_stats(home_team, date, game))
                team_stats.append(merge_team_stats(away_team, date, game))

                add_player_stats(home_team, date, pitcher_stats, batter_stats, fielder_stats, game)
                add_player_stats(away_team, date, pitcher_stats, batter_stats, fielder_stats, game)
            else:
                print("skipped")


        team_df, pitching_df, batter_df, fielding_df = self.concatenate_existing_data(team_stats, pitcher_stats, batter_stats, fielder_stats)
        
        team_df = team_df.sort_values(by = ['date'])

        pitching_df = pitching_df.sort_values(by = ['name', 'date'])

        batter_df = batter_df[batter_df['atbats'] > 0].sort_values(by = ['name', 'date'])

        fielding_df = fielding_df[fielding_df['gamesstarted'] == 1.0].sort_values(by = ['name', 'date'])

        return team_df, pitching_df, batter_df, fielding_df
    
    def fetch_and_save_data(self):
        self.find_existing_data()
        tdf, pdf, bdf, fdf = self.fetch_stats()
        tdf.to_csv(f'{self.season}_team_stats.csv', index=False)
        print("saved team data")
        pdf.to_csv(f'{self.season}_pitching_stats.csv', index=False)
        print("saved pitching data")
        bdf.to_csv(f'{self.season}_batting_stats.csv', index=False)
        print("saved batting data")
        fdf.to_csv(f'{self.season}_fielding_stats.csv', index=False)
        print("saved fielding data")

seasons = [2022, 2023, 2024]
for season in seasons:
    DataFetcher(season)