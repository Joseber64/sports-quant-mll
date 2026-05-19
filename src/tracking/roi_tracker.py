"""
Track ROI by comparing predictions with actual results.
Calculates realized returns from historical bets.
"""
import pandas as pd
import sqlite3
import logging
from datetime import datetime, timedelta
import config
from utils import load_csv_safe

logger = logging.getLogger(__name__)

def load_placed_bets() -> pd.DataFrame:
    """
    Load bets that were placed based on predictions.
    
    Returns:
        DataFrame with placed bets
    """
    df = load_csv_safe(
        config.FINAL_BETS_FILE,
        required_columns=["home_team", "away_team", "team", "odds", "kelly_stake"]
    )
    
    if df is None or df.empty:
        logger.warning("No placed bets found")
        return pd.DataFrame()
    
    return df

def load_actual_results(lookback_days: int = 7) -> pd.DataFrame:
    """
    Load actual match results from database.
    
    Args:
        lookback_days: Number of days to look back
        
    Returns:
        DataFrame with results
    """
    try:
        conn = sqlite3.connect(config.DATABASE_FILE)
        
        # Calculate date threshold
        threshold_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()
        
        query = f"""
        SELECT * FROM historical_results
        WHERE date >= '{threshold_date}'
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            logger.warning("No recent results found")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(df)} results from last {lookback_days} days")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load results: {str(e)}")
        return pd.DataFrame()

def match_bets_to_results(bets_df: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match placed bets with actual results.
    
    Args:
        bets_df: DataFrame with placed bets
        results_df: DataFrame with actual results
        
    Returns:
        DataFrame with matched bets and outcomes
    """
    matched = []
    
    for _, bet in bets_df.iterrows():
        # Find matching result
        match_result = results_df[
            (results_df["home_team"] == bet["home_team"]) &
            (results_df["away_team"] == bet["away_team"])
        ]
        
        if match_result.empty:
            logger.debug(f"No result found for {bet['home_team']} vs {bet['away_team']}")
            continue
        
        result = match_result.iloc[0]
        
        # Determine if bet won
        bet_won = False
        if bet["team"] == bet["home_team"]:
            bet_won = result["result"] == 1  # Home win
        elif bet["team"] == bet["away_team"]:
            bet_won = result["result"] == 0  # Away win
        else:
            bet_won = result["result"] == 0.5  # Draw
        
        matched.append({
            "home_team": bet["home_team"],
            "away_team": bet["away_team"],
            "team_bet": bet["team"],
            "odds": bet["odds"],
            "kelly_stake": bet["kelly_stake"],
            "bet_won": bet_won,
            "actual_result": result["result"],
            "date": result["date"]
        })
    
    matched_df = pd.DataFrame(matched)
    logger.info(f"Matched {len(matched_df)} bets to results")
    
    return matched_df

def calculate_roi(matched_bets: pd.DataFrame, initial_bankroll: float = 100.0) -> dict:
    """
    Calculate ROI from matched bets.
    
    Args:
        matched_bets: DataFrame with matched bets and outcomes
        initial_bankroll: Starting bankroll amount
        
    Returns:
        Dictionary with ROI metrics
    """
    if matched_bets.empty:
        logger.warning("No matched bets to calculate ROI")
        return {}
    
    # Calculate profit/loss for each bet
    matched_bets["stake_amount"] = matched_bets["kelly_stake"] * initial_bankroll
    
    matched_bets["profit_loss"] = matched_bets.apply(
        lambda row: (row["odds"] - 1) * row["stake_amount"] if row["bet_won"] 
        else -row["stake_amount"],
        axis=1
    )
    
    # Calculate metrics
    total_staked = matched_bets["stake_amount"].sum()
    total_profit = matched_bets["profit_loss"].sum()
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    
    win_rate = matched_bets["bet_won"].mean() * 100
    avg_odds = matched_bets["odds"].mean()
    
    metrics = {
        "total_bets": len(matched_bets),
        "bets_won": int(matched_bets["bet_won"].sum()),
        "bets_lost": int((~matched_bets["bet_won"]).sum()),
        "win_rate": win_rate,
        "total_staked": total_staked,
        "total_profit": total_profit,
        "roi": roi,
        "average_odds": avg_odds,
        "final_bankroll": initial_bankroll + total_profit
    }
    
    return metrics

def print_roi_report(metrics: dict):
    """
    Print formatted ROI report.
    
    Args:
        metrics: Dictionary with ROI metrics
    """
    if not metrics:
        logger.warning("No metrics to report")
        return
    
    report = f"""
{'='*50}
ROI TRACKING REPORT
{'='*50}

📊 BETTING STATISTICS
Total Bets Placed: {metrics['total_bets']}
Bets Won: {metrics['bets_won']}
Bets Lost: {metrics['bets_lost']}
Win Rate: {metrics['win_rate']:.2f}%
Average Odds: {metrics['average_odds']:.2f}

💰 FINANCIAL PERFORMANCE
Total Staked: ${metrics['total_staked']:.2f}
Total Profit/Loss: ${metrics['total_profit']:.2f}
ROI: {metrics['roi']:.2f}%
Final Bankroll: ${metrics['final_bankroll']:.2f}

{'='*50}
"""
    
    print(report)
    logger.info("ROI report generated")

def main():
    """Main execution function."""
    try:
        logger.info("Starting ROI tracking...")
        
        # Load placed bets
        bets_df = load_placed_bets()
        
        if bets_df.empty:
            logger.error("No bets to track")
            return
        
        # Load actual results
        results_df = load_actual_results(lookback_days=7)
        
        if results_df.empty:
            logger.error("No results available")
            return
        
        # Match bets to results
        matched = match_bets_to_results(bets_df, results_df)
        
        if matched.empty:
            logger.warning("No matches found between bets and results")
            return
        
        # Calculate ROI
        metrics = calculate_roi(matched, initial_bankroll=100.0)
        
        # Print report
        print_roi_report(metrics)
        
        # Save matched bets with outcomes
        matched.to_csv(
            config.PROCESSED_DATA_DIR / "matched_bets.csv",
            index=False
        )
        logger.info("Matched bets saved")
        
    except Exception as e:
        logger.error(f"ROI tracking failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
