import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

df = pd.read_csv(
    "data/processed/market_features.csv"
)

df["target"] = (
    df["reverse_line_movement"]
)

features = [
    "odds",
    "market_avg",
    "market_std",
    "sharp_disagreement"
]

X = df[features]

y = df["target"]

lgbm = LGBMClassifier()

xgb = XGBClassifier()

rf = RandomForestClassifier()

lgbm.fit(X, y)
xgb.fit(X, y)
rf.fit(X, y)

joblib.dump(
    lgbm,
    "data/models/lgbm.pkl"
)

joblib.dump(
    xgb,
    "data/models/xgb.pkl"
)

joblib.dump(
    rf,
    "data/models/rf.pkl"
)

print("ENSEMBLE TRAINED")
