"""
Collect odds data from The Odds API for multiple sports.
Handles rate limiting, errors, and data validation.
"""
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Add parent directory to path to find config and utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from utils import safe_api_request, save_csv_safe

logger = logging.getLogger(__name__)

SPORTS = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_uefa_champs_league"
]

def fetch_odds_for_sport(sport: str) -> List[Dict]:
    """
    Fetch odds data for a specific sport.
    
    Args:
        sport: Sport identifier
        
    Returns:
        List of odds records
    """
    url = f"{config.ODDS_API_BASE_URL}/{sport}/odds"
    
    params = {
        "apiKey": config.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    
    logger.info(f"Fetching odds for {sport}...")
    data = safe_api_request(url, params=params, timeout=config.REQUEST_TIMEOUT)
    
    if not data:
        logger.warning(f"No data received for {sport}")
        return []
    
    rows = []
    for game in data:
        try:
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            commence_time = game.get("commence_time")
            
            if not all([home_team, away_team, commence_time]):
                logger.warning(f"Missing required fields in game data: {game}")
                continue
            
            for bookmaker in game.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title")
                
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "h2h":
                        continue
                    
                    for outcome in market.get("outcomes", []):
                        rows.append({
                            "sport": sport,
                            "home_team": home_team,
                            "away_team": away_team,
                            "team": outcome.get("name"),
                            "odds": float(outcome.get("price", 0)),
                            "bookmaker": bookmaker_name,
                            "commence_time": commence_time,
                            "pulled_at": datetime.utcnow().isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Error processing game: {str(e)}")
            continue
    
    logger.info(f"Collected {len(rows)} odds records for {sport}")
    return rows

def collect_all_odds() -> pd.DataFrame:
    """
    Collect odds from all configured sports.
    
    Returns:
        DataFrame with all odds data
    """
    all_rows = []
    
    for sport in SPORTS:
        sport_rows = fetch_odds_for_sport(sport)
        all_rows.extend(sport_rows)
    
    if not all_rows:
        logger.error("No odds data collected from any sport")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    
    # Data validation
    df = df[df["odds"] > 1.0]  # Remove invalid odds
    df = df.dropna(subset=["home_team", "away_team", "team", "odds"])
    
    logger.info(f"Total odds records collected: {len(df)}")
    return df

def append_to_historical(new_df: pd.DataFrame) -> bool:
    """
    Append new odds to historical data, avoiding duplicates.
    
    Args:
        new_df: DataFrame with new odds
        
    Returns:
        bool: True if successful
    """
    try:
        if config.ODDS_FILE.exists():
            historical_df = pd.read_csv(config.ODDS_FILE)
            
            # Remove duplicates based on key columns
            combined = pd.concat([historical_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["home_team", "away_team", "team", "bookmaker", "commence_time"],
                keep="last"
            )
            
            logger.info(f"Appended {len(new_df)} new records to {len(historical_df)} existing")
            return save_csv_safe(combined, config.ODDS_FILE)
        else:
            return save_csv_safe(new_df, config.ODDS_FILE)
    
    except Exception as e:
        logger.error(f"Failed to append historical data: {str(e)}")
        return False

def main():
    """Main execution function."""
    try:
        logger.info("Starting odds collection...")
        
        df = collect_all_odds()
        
        if df.empty:
            logger.error("No odds data to save")
            return
        
        # Save current snapshot
        save_csv_safe(df, config.ODDS_FILE)
        
        logger.info("Odds collection completed successfully")
        logger.info(f"Preview:\n{df.head()}")
        
    except Exception as e:
        logger.error(f"Odds collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
