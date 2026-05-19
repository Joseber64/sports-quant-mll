"""
Collect live scores and match data from ESPN API.
"""
import pandas as pd
import logging
from typing import List, Dict
import config
from utils import safe_api_request, save_csv_safe

logger = logging.getLogger(__name__)

LEAGUES = {
    "epl": "eng.1",
    "laliga": "esp.1",
    "seriea": "ita.1",
    "bundesliga": "ger.1"
}

def fetch_league_data(league_name: str, league_code: str) -> List[Dict]:
    """
    Fetch match data for a specific league.
    
    Args:
        league_name: Display name of league
        league_code: ESPN league code
        
    Returns:
        List of match records
    """
    url = f"{config.ESPN_API_BASE_URL}/{league_code}/scoreboard"
    
    logger.info(f"Fetching data for {league_name}...")
    data = safe_api_request(url, timeout=config.REQUEST_TIMEOUT)
    
    if not data or "events" not in data:
        logger.warning(f"No events found for {league_name}")
        return []
    
    rows = []
    for event in data["events"]:
        try:
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            
            comp = competitions[0]
            competitors = comp.get("competitors", [])
            
            if len(competitors) < 2:
                continue
            
            home = competitors[0]
            away = competitors[1]
            
            status = comp.get("status", {}).get("type", {}).get("description", "Unknown")
            
            rows.append({
                "league": league_name,
                "home_team": home.get("team", {}).get("displayName"),
                "away_team": away.get("team", {}).get("displayName"),
                "home_score": int(home.get("score", 0)),
                "away_score": int(away.get("score", 0)),
                "status": status,
                "date": event.get("date"),
                "event_id": event.get("id")
            })
        
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            continue
    
    logger.info(f"Collected {len(rows)} matches for {league_name}")
    return rows

def collect_all_matches() -> pd.DataFrame:
    """
    Collect match data from all configured leagues.
    
    Returns:
        DataFrame with all match data
    """
    all_rows = []
    
    for league_name, league_code in LEAGUES.items():
        league_rows = fetch_league_data(league_name, league_code)
        all_rows.extend(league_rows)
    
    if not all_rows:
        logger.error("No match data collected")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_rows)
    df = df.dropna(subset=["home_team", "away_team"])
    
    logger.info(f"Total matches collected: {len(df)}")
    return df

def main():
    """Main execution function."""
    try:
        logger.info("Starting ESPN data collection...")
        
        df = collect_all_matches()
        
        if df.empty:
            logger.error("No match data to save")
            return
        
        save_csv_safe(df, config.ESPN_FILE)
        
        logger.info("ESPN data collection completed successfully")
        logger.info(f"Preview:\n{df.head()}")
        
    except Exception as e:
        logger.error(f"ESPN collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
