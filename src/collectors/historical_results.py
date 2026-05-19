"""
Collect and store historical match results in SQLite database.
Handles duplicates and calculates proper match results including draws.
"""
import pandas as pd
import sqlite3
import logging
from typing import List, Dict
import config
from utils import safe_api_request

logger = logging.getLogger(__name__)

LEAGUES = {
    "eng.1": "EPL",
    "esp.1": "LALIGA",
    "ita.1": "SERIEA",
    "ger.1": "BUNDESLIGA"
}

def calculate_match_result(home_score: int, away_score: int) -> int:
    """
    Calculate match result from home team perspective.
    
    Args:
        home_score: Home team score
        away_score: Away team score
        
    Returns:
        int: 1 for home win, 0.5 for draw, 0 for away win
    """
    if home_score > away_score:
        return 1
    elif home_score == away_score:
        return 0.5  # Draw
    else:
        return 0

def fetch_historical_results() -> List[Dict]:
    """
    Fetch historical match results from all leagues.
    
    Returns:
        List of match result records
    """
    all_rows = []
    
    for code, league in LEAGUES.items():
        url = f"{config.ESPN_API_BASE_URL}/{code}/scoreboard"
        
        logger.info(f"Fetching results for {league}...")
        data = safe_api_request(url, timeout=config.REQUEST_TIMEOUT)
        
        if not data or "events" not in data:
            logger.warning(f"No events found for {league}")
            continue
        
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
                
                status = comp.get("status", {}).get("type", {}).get("completed", False)
                
                # Only include completed matches
                if not status:
                    continue
                
                home_score = int(home.get("score", 0))
                away_score = int(away.get("score", 0))
                
                result = calculate_match_result(home_score, away_score)
                
                all_rows.append({
                    "league": league,
                    "home_team": home.get("team", {}).get("displayName"),
                    "away_team": away.get("team", {}).get("displayName"),
                    "home_score": home_score,
                    "away_score": away_score,
                    "result": result,
                    "date": event.get("date"),
                    "event_id": event.get("id")
                })
            
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                continue
        
        logger.info(f"Collected {len([r for r in all_rows if r['league'] == league])} results for {league}")
    
    return all_rows

def store_results_in_database(results: List[Dict]) -> bool:
    """
    Store match results in SQLite database, avoiding duplicates.
    
    Args:
        results: List of match result dictionaries
        
    Returns:
        bool: True if successful
    """
    try:
        df = pd.DataFrame(results)
        
        if df.empty:
            logger.warning("No results to store")
            return False
        
        conn = sqlite3.connect(config.DATABASE_FILE)
        
        # Create table with unique constraint if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_results (
                league TEXT,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                result REAL,
                date TEXT,
                event_id TEXT UNIQUE,
                PRIMARY KEY (event_id)
            )
        """)
        
        # Create index for faster queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams 
            ON historical_results(home_team, away_team)
        """)
        
        # Get existing event IDs to avoid duplicates
        existing_ids = pd.read_sql(
            "SELECT event_id FROM historical_results",
            conn
        )["event_id"].tolist()
        
        # Filter out duplicates
        df_new = df[~df["event_id"].isin(existing_ids)]
        
        if df_new.empty:
            logger.info("No new results to add (all duplicates)")
            conn.close()
            return True
        
        # Insert new results
        df_new.to_sql(
            "historical_results",
            conn,
            if_exists="append",
            index=False
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {len(df_new)} new results in database")
        return True
        
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")
        return False

def main():
    """Main execution function."""
    try:
        logger.info("Starting historical results collection...")
        
        results = fetch_historical_results()
        
        if not results:
            logger.error("No results collected")
            return
        
        success = store_results_in_database(results)
        
        if success:
            logger.info("Historical results stored successfully")
            logger.info(f"Sample: {pd.DataFrame(results).head()}")
        
    except Exception as e:
        logger.error(f"Historical results collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
