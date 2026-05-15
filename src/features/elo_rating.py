import pandas as pd
import sqlite3

K = 30

conn = sqlite3.connect("database/sports.db")

matches = pd.read_sql(
    "SELECT * FROM historical_results",
    conn
)

ratings = {}

def get_rating(team):

    if team not in ratings:
        ratings[team] = 1500

    return ratings[team]

rows = []

for _, match in matches.iterrows():

    home = match["home_team"]
    away = match["away_team"]

    home_rating = get_rating(home)
    away_rating = get_rating(away)

    expected_home = 1 / (
        1 + 10 ** ((away_rating - home_rating) / 400)
    )

    result = match["result"]

    new_home = (
        home_rating
        + K * (result - expected_home)
    )

    new_away = (
        away_rating
        + K * ((1 - result) - (1 - expected_home))
    )

    ratings[home] = new_home
    ratings[away] = new_away

    rows.append({
        "home_team": home,
        "away_team": away,
        "home_elo": new_home,
        "away_elo": new_away
    })

elo_df = pd.DataFrame(rows)

elo_df.to_sql(
    "elo_ratings",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(elo_df.head())
