import pandas as pd
import numpy as np

odds = pd.read_csv("data/raw/odds.csv")

odds["implied_probability"] = 1 / odds["odds"]

market_avg = odds.groupby(
    ["home_team", "away_team"]
)["implied_probability"].transform("mean")

odds["market_edge"] = (
    odds["implied_probability"] - market_avg
)

odds["line_value"] = (
    odds["odds"] * odds["implied_probability"]
)

odds["sharp_indicator"] = np.where(
    odds["market_edge"] > 0.02,
    1,
    0
)

odds.to_csv(
    "data/processed/features.csv",
    index=False
)

print(odds.head())
