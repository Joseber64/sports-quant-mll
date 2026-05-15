import pandas as pd
import joblib
import numpy as np

from kelly import kelly

df = pd.read_csv(
    "data/processed/market_features.csv"
)

features = [
    "odds",
    "market_avg",
    "market_std",
    "sharp_disagreement"
]

X = df[features]

lgbm = joblib.load(
    "data/models/lgbm.pkl"
)

xgb = joblib.load(
    "data/models/xgb.pkl"
)

rf = joblib.load(
    "data/models/rf.pkl"
)

p1 = lgbm.predict_proba(X)[:,1]
p2 = xgb.predict_proba(X)[:,1]
p3 = rf.predict_proba(X)[:,1]

df["win_probability"] = (
    p1 + p2 + p3
) / 3

df["expected_value"] = (
    (df["win_probability"] * df["odds"]) - 1
)

df["kelly"] = df.apply(
    lambda row:
    kelly(
        row["win_probability"],
        row["odds"]
    ),
    axis=1
)

final_bets = df[
    (df["expected_value"] > 0.05)
    &
    (df["kelly"] > 0.01)
]

final_bets.to_csv(
    "data/processed/final_bets.csv",
    index=False
)

print(final_bets.head())
