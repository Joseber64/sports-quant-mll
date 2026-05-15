import requests
import pandas as pd
import sqlite3

LEAGUES = {
    "eng.1": "EPL",
    "esp.1": "LALIGA",
    "ita.1": "SERIEA",
    "ger.1": "BUNDESLIGA"
}

all_rows = []

for code, league in LEAGUES.items():

    url = (
        f"https://site.api.espn.com/apis/site/v2/"
        f"sports/soccer/{code}/scoreboard"
    )

    response = requests.get(url)

    data = response.json()

    if "events" not in data:
        continue

    for event in data["events"]:

        comp = event["competitions"][0]

        home = comp["competitors"][0]
        away = comp["competitors"][1]

        home_score = int(home.get("score", 0))
        away_score = int(away.get("score", 0))

        result = 0

        if home_score > away_score:
            result = 1

        all_rows.append({
            "league": league,
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": home_score,
            "away_score": away_score,
            "result": result,
            "date": event["date"]
        })

df = pd.DataFrame(all_rows)

conn = sqlite3.connect("database/sports.db")

df.to_sql(
    "historical_results",
    conn,
    if_exists="append",
    index=False
)

conn.close()

print(df.head())
