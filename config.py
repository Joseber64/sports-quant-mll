"""
Configuration module for sports betting quantitative system.
Validates environment variables and provides default values.
"""
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Configuration with validation
def get_env_variable(var_name: str, default: str = None, required: bool = True) -> str:
    """
    Safely retrieve environment variable with validation.
    
    Args:
        var_name: Name of environment variable
        default: Default value if not found
        required: Whether variable is required
        
    Returns:
        str: Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(var_name, default)
    
    if required and not value:
        error_msg = f"Environment variable '{var_name}' is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if value:
        logger.info(f"Loaded {var_name} successfully")
    else:
        logger.warning(f"Using default value for {var_name}")
    
    return value

# API Keys
ODDS_API_KEY = get_env_variable("ODDS_API_KEY", required=True)
TELEGRAM_TOKEN = get_env_variable("TELEGRAM_TOKEN", required=True)
TELEGRAM_CHAT_ID = get_env_variable("TELEGRAM_CHAT_ID", required=True)

# API Configuration
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4/sports"
ESPN_API_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
TELEGRAM_API_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds

# Model configuration
RANDOM_SEED = 42
TEST_SIZE = 0.2
VALIDATION_SIZE = 0.1

# ELO Configuration
ELO_K_FACTOR = 30
ELO_INITIAL_RATING = 1500

# Kelly Criterion Configuration
MAX_KELLY_FRACTION = 0.25  # Maximum 25% of bankroll
MIN_KELLY_STAKE = 0.01  # Minimum 1% stake

# Betting Thresholds
MIN_EXPECTED_VALUE = 0.05  # 5% minimum EV
MIN_WIN_PROBABILITY = 0.35  # 35% minimum win probability
MAX_WIN_PROBABILITY = 0.95  # 95% maximum (avoid overconfidence)

# File paths
ODDS_FILE = RAW_DATA_DIR / "odds.csv"
ESPN_FILE = RAW_DATA_DIR / "espn.csv"
FEATURES_FILE = PROCESSED_DATA_DIR / "features.csv"
MARKET_FEATURES_FILE = PROCESSED_DATA_DIR / "market_features.csv"
FINAL_BETS_FILE = PROCESSED_DATA_DIR / "final_bets.csv"
DATABASE_FILE = DATABASE_DIR / "sports.db"

# Model files
LGBM_MODEL_FILE = MODELS_DIR / "lgbm.pkl"
XGB_MODEL_FILE = MODELS_DIR / "xgb.pkl"
RF_MODEL_FILE = MODELS_DIR / "rf.pkl"
METRICS_FILE = MODELS_DIR / "metrics.json"

logger.info("Configuration loaded successfully")
