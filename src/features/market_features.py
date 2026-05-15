import pandas as pd

df = pd.read_csv(
    "data/raw/odds.csv"
)

market_avg = df.groupby(
    ["home_team", "away_team"]
)["odds"].transform("mean")

market_std = df.groupby(
    ["home_team", "away_team"]
)["odds"].transform("std")

df["market_avg"] = market_avg

df["market_std"] = market_std

df["sharp_disagreement"] = (
    abs(df["odds"] - market_avg)
)

df["reverse_line_movement"] = (
    df["sharp_disagreement"] > 0.15
).astype(int)

df.to_csv(
    "data/processed/market_features.csv",
    index=False
)

print(df.head())
