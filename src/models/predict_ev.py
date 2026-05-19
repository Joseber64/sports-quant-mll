"""
Predict expected value (EV) using ensemble models and apply Kelly sizing.
"""
import pandas as pd
import numpy as np
import joblib
import logging
import config
from utils import load_csv_safe, save_csv_safe, validate_dataframe, clip_probability
from kelly import quarter_kelly

logger = logging.getLogger(__name__)

def load_models() -> dict:
    """
    Load trained models from disk.
    
    Returns:
        Dictionary of loaded models
    """
    try:
        models = {
            "lgbm": joblib.load(config.LGBM_MODEL_FILE),
            "xgb": joblib.load(config.XGB_MODEL_FILE),
            "rf": joblib.load(config.RF_MODEL_FILE)
        }
        logger.info("Models loaded successfully")
        return models
    except Exception as e:
        logger.error(f"Failed to load models: {str(e)}")
        raise

def predict_win_probabilities(df: pd.DataFrame, models: dict) -> pd.DataFrame:
    """
    Generate ensemble predictions for win probabilities.
    
    Args:
        df: DataFrame with features
        models: Dictionary of trained models
        
    Returns:
        DataFrame with predictions
    """
    features = ["odds", "market_avg", "market_std", "sharp_disagreement"]
    validate_dataframe(df, features)
    
    X = df[features]
    
    logger.info("Generating predictions...")
    
    # Get predictions from all models
    predictions = []
    for name, model in models.items():
        try:
            proba = model.predict_proba(X)[:, 1]
            predictions.append(proba)
            logger.info(f"{name} predictions generated")
        except Exception as e:
            logger.error(f"Failed to predict with {name}: {str(e)}")
            raise
    
    # Ensemble average
    df["win_probability"] = np.mean(predictions, axis=0)
    
    # Clip probabilities to valid range
    df["win_probability"] = df["win_probability"].apply(
        lambda p: clip_probability(p, min_val=0.001, max_val=0.999)
    )
    
    logger.info(f"Predictions complete. Mean probability: {df['win_probability'].mean():.3f}")
    
    return df

def calculate_expected_value(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate expected value for each bet.
    
    Args:
        df: DataFrame with odds and win probabilities
        
    Returns:
        DataFrame with EV calculations
    """
    # EV = (probability × odds) - 1
    df["expected_value"] = (df["win_probability"] * df["odds"]) - 1
    
    logger.info(f"EV calculated. Positive EV bets: {(df['expected_value'] > 0).sum()}")
    
    return df

def apply_kelly_sizing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Kelly Criterion sizing to bets (vectorized).
    
    Args:
        df: DataFrame with probabilities and odds
        
    Returns:
        DataFrame with Kelly stakes
    """
    # Vectorized Kelly calculation using quarter-Kelly for safety
    df["kelly_stake"] = df.apply(
        lambda row: quarter_kelly(row["win_probability"], row["odds"]),
        axis=1
    )
    
    logger.info(f"Kelly sizing applied. Mean stake: {df['kelly_stake'].mean():.3f}")
    
    return df

def filter_profitable_bets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter bets based on EV and Kelly thresholds.
    
    Args:
        df: DataFrame with all bets
        
    Returns:
        DataFrame with filtered bets
    """
    logger.info("Applying bet filters...")
    
    initial_count = len(df)
    
    # Apply filters
    filtered = df[
        (df["expected_value"] > config.MIN_EXPECTED_VALUE) &
        (df["kelly_stake"] > config.MIN_KELLY_STAKE) &
        (df["win_probability"] >= config.MIN_WIN_PROBABILITY) &
        (df["win_probability"] <= config.MAX_WIN_PROBABILITY)
    ].copy()
    
    logger.info(f"Filtered {initial_count} bets to {len(filtered)} profitable opportunities")
    
    if len(filtered) > 0:
        logger.info(f"Average EV: {filtered['expected_value'].mean():.2%}")
        logger.info(f"Average Kelly: {filtered['kelly_stake'].mean():.2%}")
    
    return filtered

def main():
    """Main execution function."""
    try:
        logger.info("Starting EV prediction...")
        
        # Load market features
        df = load_csv_safe(
            config.MARKET_FEATURES_FILE,
            required_columns=["odds", "market_avg", "market_std", "sharp_disagreement"]
        )
        
        if df is None or df.empty:
            logger.error("No market features available")
            return
        
        # Load models
        models = load_models()
        
        # Generate predictions
        df = predict_win_probabilities(df, models)
        
        # Calculate EV
        df = calculate_expected_value(df)
        
        # Apply Kelly sizing
        df = apply_kelly_sizing(df)
        
        # Filter profitable bets
        final_bets = filter_profitable_bets(df)
        
        # Sort by EV descending
        final_bets = final_bets.sort_values("expected_value", ascending=False)
        
        # Save results
        success = save_csv_safe(final_bets, config.FINAL_BETS_FILE)
        
        if success:
            logger.info("EV prediction completed successfully")
            if not final_bets.empty:
                logger.info(f"\nTop 5 bets:\n{final_bets.head()}")
            else:
                logger.warning("No profitable bets found")
        
    except Exception as e:
        logger.error(f"EV prediction failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
