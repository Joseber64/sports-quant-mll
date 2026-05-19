"""
Calculate team-level features from odds and market data.
Includes implied probabilities, market edges, and sharp indicators.
"""
import pandas as pd
import numpy as np
import logging
import config
from utils import load_csv_safe, save_csv_safe, validate_dataframe, safe_divide

logger = logging.getLogger(__name__)

def calculate_team_features(odds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate team-level betting features.
    
    Args:
        odds_df: DataFrame with odds data
        
    Returns:
        DataFrame with team features
    """
    required_columns = ["home_team", "away_team", "team", "odds"]
    validate_dataframe(odds_df, required_columns)
    
    logger.info(f"Calculating team features for {len(odds_df)} records...")
    
    # Calculate implied probability (handle division safely)
    odds_df["implied_probability"] = odds_df["odds"].apply(
        lambda x: safe_divide(1, x, default=0)
    )
    
    # Calculate market average implied probability
    market_avg_prob = odds_df.groupby(
        ["home_team", "away_team", "team"]
    )["implied_probability"].transform("mean")
    
    # Market edge (how much better/worse than market average)
    odds_df["market_edge"] = odds_df["implied_probability"] - market_avg_prob
    
    # Line value (expected return)
    odds_df["line_value"] = odds_df["odds"] * odds_df["implied_probability"]
    
    # Sharp indicator (significant positive edge)
    odds_df["sharp_indicator"] = np.where(
        odds_df["market_edge"] > 0.02,  # 2% edge threshold
        1,
        0
    )
    
    # Overround (bookmaker margin)
    match_group = odds_df.groupby(["home_team", "away_team"])
    odds_df["overround"] = match_group["implied_probability"].transform("sum")
    
    # True probability (removing overround)
    odds_df["true_probability"] = odds_df.apply(
        lambda row: safe_divide(
            row["implied_probability"],
            row["overround"],
            default=row["implied_probability"]
        ),
        axis=1
    )
    
    # Value indicator (true probability higher than implied)
    odds_df["value_indicator"] = (
        odds_df["true_probability"] > odds_df["implied_probability"]
    ).astype(int)
    
    logger.info("Team features calculated successfully")
    logger.info(f"Sharp bets detected: {odds_df['sharp_indicator'].sum()}")
    logger.info(f"Value bets detected: {odds_df['value_indicator'].sum()}")
    
    return odds_df

def main():
    """Main execution function."""
    try:
        logger.info("Starting team features calculation...")
        
        # Load odds data
        df = load_csv_safe(
            config.ODDS_FILE,
            required_columns=["home_team", "away_team", "team", "odds"]
        )
        
        if df is None or df.empty:
            logger.error("No odds data available")
            return
        
        # Calculate features
        df_with_features = calculate_team_features(df)
        
        # Save results
        success = save_csv_safe(df_with_features, config.FEATURES_FILE)
        
        if success:
            logger.info("Team features saved successfully")
            logger.info(f"Preview:\n{df_with_features.head()}")
            logger.info(f"\nFeature statistics:\n{df_with_features.describe()}")
        
    except Exception as e:
        logger.error(f"Team features calculation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
