import pandas as pd

df = pd.read_csv(
    "data/processed/final_bets.csv"
)

stake = 1

df["profit"] = (
    (df["odds"] - 1) * stake
)

roi = (
    df["profit"].sum()
    /
    (len(df) * stake)
) * 100

print(f"ROI: {roi:.2f}%")
