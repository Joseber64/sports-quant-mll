"""
Calculate ELO ratings for teams based on historical match results.
Vectorized implementation for performance.
"""
import pandas as pd
import numpy as np
import sqlite3
import logging
import config
from utils import calculate_elo_expected

logger = logging.getLogger(__name__)

def calculate_elo_ratings_vectorized(matches_df: pd.DataFrame, k_factor: int = config.ELO_K_FACTOR) -> pd.DataFrame:
    """
    Calculate ELO ratings for all teams using vectorized operations.
    
    Args:
        matches_df: DataFrame with historical match results
        k_factor: ELO K-factor for rating adjustments
        
    Returns:
        DataFrame with ELO ratings history
    """
    # Initialize ratings dictionary
    ratings = {}
    elo_history = []
    
    # Sort matches by date
    matches_df = matches_df.sort_values("date").reset_index(drop=True)
    
    def get_rating(team: str) -> float:
        """Get current rating for team, initialize if new."""
        if team not in ratings:
            ratings[team] = config.ELO_INITIAL_RATING
        return ratings[team]
    
    # Process matches
    for idx, match in matches_df.iterrows():
        home_team = match["home_team"]
        away_team = match["away_team"]
        result = match["result"]
        
        # Get current ratings
        home_rating = get_rating(home_team)
        away_rating = get_rating(away_team)
        
        # Calculate expected scores
        home_expected = calculate_elo_expected(home_rating, away_rating)
        away_expected = 1 - home_expected
        
        # Calculate actual scores (handle draws properly)
        home_actual = result
        away_actual = 1 - result
        
        # Update ratings
        home_new = home_rating + k_factor * (home_actual - home_expected)
        away_new = away_rating + k_factor * (away_actual - away_expected)
        
        # Store updates
        ratings[home_team] = home_new
        ratings[away_team] = away_new
        
        # Record history
        elo_history.append({
            "match_index": idx,
            "date": match["date"],
            "home_team": home_team,
            "away_team": away_team,
            "home_elo_before": home_rating,
            "away_elo_before": away_rating,
            "home_elo_after": home_new,
            "away_elo_after": away_new,
            "home_expected": home_expected,
            "home_actual": home_actual,
            "result": result
        })
    
    return pd.DataFrame(elo_history)

def get_latest_elo_ratings() -> pd.DataFrame:
    """
    Get the latest ELO rating for each team.
    
    Returns:
        DataFrame with team names and current ratings
    """
    try:
        conn = sqlite3.connect(config.DATABASE_FILE)
        
        # Get latest ratings for each team
        query = """
        SELECT 
            team,
            elo_rating,
            last_updated
        FROM (
            SELECT home_team as team, home_elo_after as elo_rating, date as last_updated
            FROM elo_ratings
            UNION ALL
            SELECT away_team as team, away_elo_after as elo_rating, date as last_updated
            FROM elo_ratings
        ) 
        GROUP BY team
        HAVING MAX(last_updated)
        ORDER BY elo_rating DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to retrieve latest ELO ratings: {str(e)}")
        return pd.DataFrame()

def main():
    """Main execution function."""
    try:
        logger.info("Starting ELO rating calculation...")
        
        # Connect to database
        conn = sqlite3.connect(config.DATABASE_FILE)
        
        # Load historical results
        matches_df = pd.read_sql(
            "SELECT * FROM historical_results ORDER BY date",
            conn
        )
        
        if matches_df.empty:
            logger.error("No historical results found in database")
            conn.close()
            return
        
        logger.info(f"Loaded {len(matches_df)} matches from database")
        
        # Calculate ELO ratings
        elo_df = calculate_elo_ratings_vectorized(matches_df)
        
        if elo_df.empty:
            logger.error("ELO calculation failed")
            conn.close()
            return
        
        # Create table with proper schema
        conn.execute("DROP TABLE IF EXISTS elo_ratings")
        conn.execute("""
            CREATE TABLE elo_ratings (
                match_index INTEGER,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_elo_before REAL,
                away_elo_before REAL,
                home_elo_after REAL,
                away_elo_after REAL,
                home_expected REAL,
                home_actual REAL,
                result REAL
            )
        """)
        
        # Create indexes
        conn.execute("CREATE INDEX idx_elo_home ON elo_ratings(home_team)")
        conn.execute("CREATE INDEX idx_elo_away ON elo_ratings(away_team)")
        conn.execute("CREATE INDEX idx_elo_date ON elo_ratings(date)")
        
        # Store ELO history
        elo_df.to_sql(
            "elo_ratings",
            conn,
            if_exists="append",
            index=False
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"ELO ratings calculated for {len(elo_df)} matches")
        logger.info(f"Preview:\n{elo_df.head()}")
        
        # Show top teams
        latest_ratings = get_latest_elo_ratings()
        if not latest_ratings.empty:
            logger.info(f"\nTop 10 teams by ELO:\n{latest_ratings.head(10)}")
        
    except Exception as e:
        logger.error(f"ELO calculation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
