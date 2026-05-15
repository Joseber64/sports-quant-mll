import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier

df = pd.read_csv("data/processed/features.csv")

df["target"] = (
    df["sharp_indicator"]
)

features = [
    "odds",
    "implied_probability",
    "market_edge",
    "line_value"
]

X = df[features]

y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = LGBMClassifier(
    n_estimators=300,
    learning_rate=0.03,
    max_depth=6
)

model.fit(X_train, y_train)

joblib.dump(
    model,
    "data/models/lightgbm.pkl"
)

print("MODEL TRAINED")
