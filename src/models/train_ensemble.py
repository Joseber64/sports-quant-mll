import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

# Cargar datos de características de mercado
df = pd.read_csv(
    "data/processed/market_features.csv"
)

# Definir la variable objetivo (Reverse Line Movement)
df["target"] = (
    df["reverse_line_movement"]
)

# Selección de características (features)
features = [
    "odds",
    "market_avg",
    "market_std",
    "sharp_disagreement"
]

X = df[features]
y = df["target"]

# Inicializar modelos (LightGBM configurado sin advertencias spammers)
lgbm = LGBMClassifier(verbose=-1)

xgb = XGBClassifier()

rf = RandomForestClassifier()

# Entrenar los modelos
lgbm.fit(X, y)
xgb.fit(X, y)
rf.fit(X, y)

# Guardar los archivos de los modelos entrenados
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
