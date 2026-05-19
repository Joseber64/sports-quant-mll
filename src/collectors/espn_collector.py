"""
ESPN data collector for historical and live match data extraction.
FREE API - No API key required.
Used for training and real-time prediction.
"""
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

import config
import utils

logger = logging.getLogger(__name__)

def fetch_league_scoreboard(league_id: str) -> List[Dict]:
    """
    Fetch current scoreboard/fixtures for a specific league.
    
    Args:
        league_id: ESPN league ID (e.g., 'eng.1' for Premier League)
        
    Returns:
        List of fixture dictionaries
    """
    logger.info(f"Fetching scoreboard for league {league_id}")
    
    fixtures = []
    
    try:
        endpoint = f"/{league_id}/scoreboard"
        response = utils.fetch_espn_data(
            endpoint,
            rate_limit_delay=config.ESPN_RATE_LIMIT
        )
        
        if response and "events" in response:
            fixtures = response.get("events", [])
            logger.info(f"Fetched {len(fixtures)} fixtures from scoreboard")
        else:
            logger.warning(f"No scoreboard data for league {league_id}")
            
    except Exception as e:
        logger.error(f"Error fetching scoreboard for league {league_id}: {str(e)}")
    
    return fixtures

def fetch_league_standings(league_id: str) -> Optional[Dict]:
    """
    Fetch league standings/table.
    
    Args:
        league_id: ESPN league ID
        
    Returns:
        Standings dictionary or None
    """
    logger.info(f"Fetching standings for league {league_id}")
    
    try:
        endpoint = f"/{league_id}/standings"
        response = utils.fetch_espn_data(
            endpoint,
            rate_limit_delay=config.ESPN_RATE_LIMIT
        )
        
        if response:
            logger.info(f"Fetched standings for {league_id}")
            return response
        
    except Exception as e:
        logger.warning(f"Error fetching standings for league {league_id}: {str(e)}")
    
    return None

def fetch_team_schedule(league_id: str, team_id: str) -> List[Dict]:
    """
    Fetch team schedule for a specific league.
    
    Args:
        league_id: ESPN league ID
        team_id: Team ID
        
    Returns:
        List of schedule events
    """
    logger.info(f"Fetching schedule for team {team_id} in league {league_id}")
    
    events = []
    
    try:
        endpoint = f"/{league_id}/teams/{team_id}/schedule"
        response = utils.fetch_espn_data(
            endpoint,
            rate_limit_delay=config.ESPN_RATE_LIMIT
        )
        
        if response and "events" in response:
            events = response.get("events", [])
            logger.info(f"Fetched {len(events)} schedule events for team {team_id}")
        
    except Exception as e:
        logger.warning(f"Error fetching schedule for team {team_id}: {str(e)}")
    
    return events

def process_fixtures_to_dataframe(fixtures: List[Dict]) -> pd.DataFrame:
    """
    Convert ESPN fixtures to DataFrame format with feature engineering.
    
    Args:
        fixtures: List of fixture dictionaries
        
    Returns:
        Processed DataFrame
    """
    try:
        matches = utils.extract_espn_matches(
            {"events": fixtures},
            include_stats=True
        )
        
        if not matches:
            logger.warning("No matches extracted from fixtures")
            return pd.DataFrame()
        
        df = pd.DataFrame(matches)
        
        # Data cleaning and type conversion
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["home_goals", "away_goals"])
        
        # Feature engineering
        df["home_goals"] = df["home_goals"].astype(int)
        df["away_goals"] = df["away_goals"].astype(int)
        
        df["result"] = df.apply(
            lambda row: "home_win" if row["home_goals"] > row["away_goals"] 
                       else ("draw" if row["home_goals"] == row["away_goals"] else "away_win"),
            axis=1
        )
        
        df["total_goals"] = df["home_goals"] + df["away_goals"]
        df["goal_diff"] = df["home_goals"] - df["away_goals"]
        
        logger.info(f"Processed {len(df)} matches to DataFrame")
        return df
        
    except Exception as e:
        logger.error(f"Error processing fixtures: {str(e)}")
        return pd.DataFrame()

def collect_live_data() -> bool:
    """
    Collect current live/upcoming fixture data from ESPN.
    
    Returns:
        bool: True if successful
    """
    logger.info("Starting ESPN live data collection")
    
    all_fixtures = []
    
    try:
        for league_name, league_id in config.ESPN_LEAGUES.items():
            logger.info(f"Collecting live data for {league_name}")
            
            try:
                fixtures = fetch_league_scoreboard(league_id)
                
                if fixtures:
                    df_matches = process_fixtures_to_dataframe(fixtures)
                    if not df_matches.empty:
                        all_fixtures.append(df_matches)
                        logger.info(f"Collected {len(df_matches)} live matches for {league_name}")
                
                time.sleep(0.2)  # Rate limiting between leagues
                
            except Exception as e:
                logger.error(f"Error collecting live data for {league_name}: {str(e)}")
                continue
        
        if all_fixtures:
            df_combined = pd.concat(all_fixtures, ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["event_id"])
            
            utils.save_csv_safe(df_combined, config.ESPN_LIVE_FILE)
            logger.info(f"Saved {len(df_combined)} total live matches")
            return True
        else:
            logger.error("No live matches collected")
            return False
            
    except Exception as e:
        logger.error(f"Live data collection failed: {str(e)}")
        return False

def collect_historical_data() -> bool:
    """
    Collect historical fixture data from ESPN.
    Note: ESPN doesn't provide historical API, so this fetches recent archived data.
    
    Returns:
        bool: True if successful
    """
    logger.info("Starting ESPN historical data collection")
    logger.warning("Note: ESPN provides recent data. For older historical data, consider combining with other sources.")
    
    all_fixtures = []
    
    try:
        for league_name, league_id in config.ESPN_LEAGUES.items():
            logger.info(f"Collecting data for {league_name}")
            
            try:
                fixtures = fetch_league_scoreboard(league_id)
                
                if fixtures:
                    df_matches = process_fixtures_to_dataframe(fixtures)
                    if not df_matches.empty:
                        all_fixtures.append(df_matches)
                        logger.info(f"Collected {len(df_matches)} matches for {league_name}")
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error collecting data for {league_name}: {str(e)}")
                continue
        
        if all_fixtures:
            df_combined = pd.concat(all_fixtures, ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["event_id"])
            
            utils.save_csv_safe(df_combined, config.ESPN_HISTORICAL_FILE)
            logger.info(f"Saved {len(df_combined)} total matches")
            return True
        else:
            logger.error("No matches collected")
            return False
            
    except Exception as e:
        logger.error(f"Historical data collection failed: {str(e)}")
        return False

def main():
    """Main entry point for ESPN data collection."""
    logger.info("="*50)
    logger.info("ESPN DATA COLLECTION (FREE API)")
    logger.info("="*50)
    
    success_live = collect_live_data()
    time.sleep(1)
    success_historical = collect_historical_data()
    
    if success_live and success_historical:
        logger.info("✅ ESPN data collection completed successfully")
        return True
    else:
        logger.error("❌ ESPN data collection had errors")
        return False

if __name__ == "__main__":
    main()
