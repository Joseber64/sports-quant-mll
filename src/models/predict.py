import pandas as pd
import joblib

from kelly import kelly

model = joblib.load(
    "data/models/lightgbm.pkl"
)

df = pd.read_csv(
    "data/processed/features.csv"
)

features = [
    "odds",
    "implied_probability",
    "market_edge",
    "line_value"
]

X = df[features]

df["win_probability"] = (
    model.predict_proba(X)[:,1]
)

df["expected_value"] = (
    (df["win_probability"] * df["odds"]) - 1
)

df["kelly"] = df.apply(
    lambda row: kelly(
        row["win_probability"],
        row["odds"]
    ),
    axis=1
)

final_bets = df[
    (df["expected_value"] > 0.05)
    &
    (df["kelly"] > 0.02)
]

final_bets.to_csv(
    "data/processed/final_bets.csv",
    index=False
)

print(final_bets.head())
