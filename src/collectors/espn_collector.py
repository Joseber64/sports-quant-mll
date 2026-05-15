import requests
import pandas as pd

LEAGUES = {
    "epl": "eng.1",
    "laliga": "esp.1",
    "seriea": "ita.1",
    "bundesliga": "ger.1"
}

rows = []

for league_name, league_code in LEAGUES.items():

    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"

    response = requests.get(url)

    data = response.json()

    if "events" not in data:
        continue

    for event in data["events"]:

        comp = event["competitions"][0]

        home = comp["competitors"][0]
        away = comp["competitors"][1]

        rows.append({
            "league": league_name,
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": home.get("score", 0),
            "away_score": away.get("score", 0),
            "status": comp["status"]["type"]["description"],
            "date": event["date"]
        })

df = pd.DataFrame(rows)

df.to_csv("data/raw/espn.csv", index=False)

print(df.head())
