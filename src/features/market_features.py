"""
Calculate market features from odds data with optimized vectorization.
Includes sharp disagreement detection and reverse line movement indicators.
"""
import pandas as pd
import numpy as np
import logging
import config
from utils import load_csv_safe, save_csv_safe, validate_dataframe

logger = logging.getLogger(__name__)

def calculate_market_features(odds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate market-level features with optimized vectorization.
    
    Args:
        odds_df: DataFrame with odds data
        
    Returns:
        DataFrame with added market features
    """
    required_columns = ["home_team", "away_team", "team", "odds"]
    validate_dataframe(odds_df, required_columns)
    
    logger.info(f"Calculating market features for {len(odds_df)} records...")
    
    # Group by match
    match_group = odds_df.groupby(["home_team", "away_team", "team"])
    
    # Calculate market statistics (single pass)
    market_stats = match_group["odds"].agg(["mean", "std", "min", "max", "count"])
    market_stats.columns = ["market_avg", "market_std", "market_min", "market_max", "bookmaker_count"]
    
    # Merge back to original dataframe
    odds_df = odds_df.merge(
        market_stats,
        left_on=["home_team", "away_team", "team"],
        right_index=True,
        how="left"
    )
    
    # Fill NaN std with 0 (single bookmaker case)
    odds_df["market_std"] = odds_df["market_std"].fillna(0)
    
    # Calculate sharp disagreement (vectorized)
    odds_df["sharp_disagreement"] = np.abs(odds_df["odds"] - odds_df["market_avg"])
    
    # Reverse line movement indicator
    odds_df["reverse_line_movement"] = (
        odds_df["sharp_disagreement"] > 0.15
    ).astype(int)
    
    # Market efficiency score (lower is better)
    odds_df["market_efficiency"] = odds_df["market_std"] / odds_df["market_avg"]
    odds_df["market_efficiency"] = odds_df["market_efficiency"].fillna(0)
    
    # Bookmaker consensus (how many agree within 5% of mean)
    consensus_threshold = odds_df["market_avg"] * 0.05
    odds_df["bookmaker_consensus"] = (
        odds_df["sharp_disagreement"] <= consensus_threshold
    ).astype(int)
    
    # Identify potential value bets (odds above average)
    odds_df["potential_value"] = (
        odds_df["odds"] > odds_df["market_avg"]
    ).astype(int)
    
    logger.info(f"Market features calculated successfully")
    logger.info(f"Sharp disagreements detected: {odds_df['reverse_line_movement'].sum()}")
    
    return odds_df

def main():
    """Main execution function."""
    try:
        logger.info("Starting market features calculation...")
        
        # Load odds data
        df = load_csv_safe(
            config.ODDS_FILE,
            required_columns=["home_team", "away_team", "team", "odds"]
        )
        
        if df is None or df.empty:
            logger.error("No odds data available")
            return
        
        # Calculate features
        df_with_features = calculate_market_features(df)
        
        # Save results
        success = save_csv_safe(df_with_features, config.MARKET_FEATURES_FILE)
        
        if success:
            logger.info("Market features saved successfully")
            logger.info(f"Preview:\n{df_with_features.head()}")
            logger.info(f"\nFeature statistics:\n{df_with_features.describe()}")
        
    except Exception as e:
        logger.error(f"Market features calculation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
