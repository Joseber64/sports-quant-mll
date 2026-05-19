# Sports Betting Quantitative ML System

A complete quantitative sports betting system using machine learning to identify +EV (Expected Value) betting opportunities.

## 🎯 Features

- **Multi-source data collection** (Odds API, ESPN)
- **ELO rating system** for team strength
- **Market analysis** (sharp disagreement detection, reverse line movement)
- **ML ensemble** (LightGBM, XGBoost, Random Forest)
- **Kelly Criterion** bet sizing
- **Telegram alerts** for profitable opportunities
- **ROI tracking** with actual results

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/Joseber64/sports-quant-mll.git
cd sports-quant-mll

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys
