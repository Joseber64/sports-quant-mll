import requests
import pandas as pd
from datetime import datetime
from config import ODDS_API_KEY

SPORTS = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_uefa_champs_league"
]

BASE_URL = "https://api.the-odds-api.com/v4/sports"

all_rows = []

for sport in SPORTS:

    url = f"{BASE_URL}/{sport}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        continue

    games = response.json()

    for game in games:

        home = game["home_team"]
        away = game["away_team"]

        for bookmaker in game["bookmakers"]:

            book = bookmaker["title"]

            for market in bookmaker["markets"]:

                for outcome in market["outcomes"]:

                    all_rows.append({
                        "sport": sport,
                        "home_team": home,
                        "away_team": away,
                        "team": outcome["name"],
                        "odds": outcome["price"],
                        "bookmaker": book,
                        "commence_time": game["commence_time"],
                        "pulled_at": datetime.utcnow()
                    })

df = pd.DataFrame(all_rows)

df.to_csv("data/raw/odds.csv", index=False)

print(df.head())
