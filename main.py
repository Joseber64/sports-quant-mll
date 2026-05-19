"""
Main orchestration pipeline for the sports betting quantitative system.
Runs all components in correct order with error handling.
"""
import logging
import sys
from datetime import datetime

import config
import odds_collector
import espn_collector
import historical_results
import elo_rating
import market_features
import team_features
import train_ensemble
import predict_ev
import telegram
import roi_tracker

# Configure main logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.BASE_DIR / "system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_data_collection():
    """Run data collection phase."""
    logger.info("="*50)
    logger.info("PHASE 1: DATA COLLECTION")
    logger.info("="*50)
    
    try:
        logger.info("Collecting odds data...")
        odds_collector.main()
        
        logger.info("Collecting ESPN data...")
        espn_collector.main()
        
        logger.info("Collecting historical results...")
        historical_results.main()
        
        logger.info("Data collection completed successfully")
        return True
    except Exception as e:
        logger.error(f"Data collection failed: {str(e)}")
        return False

def run_feature_engineering():
    """Run feature engineering phase."""
    logger.info("="*50)
    logger.info("PHASE 2: FEATURE ENGINEERING")
    logger.info("="*50)
    
    try:
        logger.info("Calculating ELO ratings...")
        elo_rating.main()
        
        logger.info("Calculating market features...")
        market_features.main()
        
        logger.info("Calculating team features...")
        team_features.main()
        
        logger.info("Feature engineering completed successfully")
        return True
    except Exception as e:
        logger.error(f"Feature engineering failed: {str(e)}")
        return False

def run_model_training():
    """Run model training phase."""
    logger.info("="*50)
    logger.info("PHASE 3: MODEL TRAINING")
    logger.info("="*50)
    
    try:
        logger.info("Training ensemble models...")
        train_ensemble.main()
        
        logger.info("Model training completed successfully")
        return True
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        return False

def run_prediction_and_alerts():
    """Run prediction and alert phase."""
    logger.info("="*50)
    logger.info("PHASE 4: PREDICTION & ALERTS")
    logger.info("="*50)
    
    try:
        logger.info("Predicting expected value...")
        predict_ev.main()
        
        logger.info("Sending Telegram alerts...")
        telegram.main()
        
        logger.info("Prediction and alerts completed successfully")
        return True
    except Exception as e:
        logger.error(f"Prediction/alerts failed: {str(e)}")
        return False

def run_roi_tracking():
    """Run ROI tracking phase."""
    logger.info("="*50)
    logger.info("PHASE 5: ROI TRACKING")
    logger.info("="*50)
    
    try:
        logger.info("Tracking ROI...")
        roi_tracker.main()
        
        logger.info("ROI tracking completed successfully")
        return True
    except Exception as e:
        logger.error(f"ROI tracking failed: {str(e)}")
        return False

def main(phases: list = None):
    """
    Run the complete pipeline or specific phases.
    
    Args:
        phases: List of phase numbers to run (1-5), or None for all
    """
    start_time = datetime.now()
    
    logger.info("="*60)
    logger.info("SPORTS BETTING QUANTITATIVE SYSTEM")
    logger.info(f"Started at: {start_time}")
    logger.info("="*60)
    
    phases_to_run = phases or [1, 2, 3, 4, 5]
    results = {}
    
    if 1 in phases_to_run:
        results["data_collection"] = run_data_collection()
    
    if 2 in phases_to_run:
        results["feature_engineering"] = run_feature_engineering()
    
    if 3 in phases_to_run:
        results["model_training"] = run_model_training()
    
    if 4 in phases_to_run:
        results["prediction_alerts"] = run_prediction_and_alerts()
    
    if 5 in phases_to_run:
        results["roi_tracking"] = run_roi_tracking()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("="*60)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("="*60)
    
    for phase, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{phase.upper()}: {status}")
    
    logger.info(f"\nTotal Duration: {duration}")
    logger.info(f"Finished at: {end_time}")
    logger.info("="*60)
    
    # Return overall success
    return all(results.values())

if __name__ == "__main__":
    # Run full pipeline
    success = main()
    sys.exit(0 if success else 1)
