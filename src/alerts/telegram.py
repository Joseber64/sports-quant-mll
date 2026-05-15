import pandas as pd
import requests

from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID
)

df = pd.read_csv(
    "data/processed/final_bets.csv"
)

for _, row in df.iterrows():

    message = f"""
🔥 QUANT EV+ ALERT

⚽ {row['team']}

🏆 {row['home_team']} vs {row['away_team']}

💰 Odds: {round(row['odds'],2)}

📈 Win Probability:
{round(row['win_probability'] * 100,2)}%

💵 Expected Value:
{round(row['expected_value'] * 100,2)}%

🧠 Kelly Stake:
{round(row['kelly'] * 100,2)}%
"""

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
    )

print("TELEGRAM ALERTS SENT")
