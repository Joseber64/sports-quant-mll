"""
Utility functions for data validation, error handling, and common operations.
"""
import pandas as pd
import logging
import time
import requests
from typing import Optional, Callable, Any, Dict, List
from pathlib import Path
import numpy as np
from functools import wraps

logger = logging.getLogger(__name__)

def validate_dataframe(
    df: pd.DataFrame,
    required_columns: list,
    min_rows: int = 1
) -> bool:
    """
    Validate DataFrame structure and content.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None")
    
    if len(df) < min_rows:
        raise ValueError(f"DataFrame has {len(df)} rows, minimum {min_rows} required")
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    logger.info(f"DataFrame validated: {len(df)} rows, {len(df.columns)} columns")
    return True

def retry_on_failure(
    max_retries: int = 3,
    delay: int = 2,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        
        return wrapper
    
    return decorator

@retry_on_failure(max_retries=3, exceptions=(requests.RequestException,))
def safe_api_request(
    url: str,
    params: dict = None,
    timeout: int = 30,
    headers: dict = None
) -> Optional[dict]:
    """
    Make API request with error handling and retries.
    
    Args:
        url: API endpoint URL
        params: Request parameters
        timeout: Request timeout in seconds
        headers: Request headers (optional)
        
    Returns:
        dict: Response JSON or None if failed
    """
    try:
        response = requests.get(url, params=params, timeout=timeout, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {url} - {str(e)}")
        raise

def fetch_api_football_data(
    endpoint: str,
    params: dict = None,
    headers: dict = None,
    rate_limit_delay: float = 0.1
) -> Optional[dict]:
    """
    Fetch data from API-Football with rate limiting.
    
    Args:
        endpoint: API endpoint (e.g., '/fixtures', '/standings')
        params: Query parameters
        headers: Request headers including API key
        rate_limit_delay: Delay between requests in seconds
        
    Returns:
        dict: Response data or None if failed
    """
    import config
    
    url = f"{config.API_FOOTBALL_BASE_URL}{endpoint}"
    
    # Add rate limiting
    time.sleep(rate_limit_delay)
    
    return safe_api_request(url, params=params, headers=headers)

def extract_api_football_matches(
    response_data: dict,
    include_stats: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract and flatten match data from API-Football response.
    
    Args:
        response_data: Raw API response
        include_stats: Whether to include detailed statistics
        
    Returns:
        List of flattened match dictionaries
    """
    matches = []
    
    try:
        if not response_data or "response" not in response_data:
            logger.warning("No response data in API-Football response")
            return matches
        
        for fixture in response_data.get("response", []):
            try:
                match_data = {
                    "fixture_id": fixture.get("fixture", {}).get("id"),
                    "date": fixture.get("fixture", {}).get("date"),
                    "status": fixture.get("fixture", {}).get("status", {}).get("short"),
                    "home_team": fixture.get("teams", {}).get("home", {}).get("name"),
                    "away_team": fixture.get("teams", {}).get("away", {}).get("name"),
                    "home_team_id": fixture.get("teams", {}).get("home", {}).get("id"),
                    "away_team_id": fixture.get("teams", {}).get("away", {}).get("id"),
                    "home_goals": fixture.get("goals", {}).get("home"),
                    "away_goals": fixture.get("goals", {}).get("away"),
                    "league": fixture.get("league", {}).get("name"),
                    "league_id": fixture.get("league", {}).get("id"),
                    "season": fixture.get("league", {}).get("season"),
                }
                
                if include_stats and "statistics" in fixture:
                    stats = fixture.get("statistics", [])
                    if len(stats) >= 2:
                        home_stats, away_stats = stats[0], stats[1]
                        
                        match_data.update({
                            "home_shots": home_stats.get("statistics", [{}])[0].get("value", 0),
                            "away_shots": away_stats.get("statistics", [{}])[0].get("value", 0),
                            "home_shots_on_target": home_stats.get("statistics", [{}])[1].get("value", 0),
                            "away_shots_on_target": away_stats.get("statistics", [{}])[1].get("value", 0),
                            "home_possession": home_stats.get("statistics", [{}])[8].get("value", 0),
                            "away_possession": away_stats.get("statistics", [{}])[8].get("value", 0),
                            "home_passes": home_stats.get("statistics", [{}])[2].get("value", 0),
                            "away_passes": away_stats.get("statistics", [{}])[2].get("value", 0),
                        })
                
                matches.append(match_data)
                
            except Exception as e:
                logger.warning(f"Error extracting match data: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(matches)} matches from API-Football")
        return matches
        
    except Exception as e:
        logger.error(f"Error processing API-Football response: {str(e)}")
        return matches

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails
        
    Returns:
        float: Result of division or default
    """
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator

def load_csv_safe(
    file_path: Path,
    required_columns: list = None,
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Safely load CSV file with validation.
    
    Args:
        file_path: Path to CSV file
        required_columns: List of required columns
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        pd.DataFrame or None: Loaded DataFrame or None if failed
    """
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        df = pd.read_csv(file_path, **kwargs)
        
        if required_columns:
            validate_dataframe(df, required_columns)
        
        logger.info(f"Loaded {file_path.name}: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {str(e)}")
        return None

def save_csv_safe(
    df: pd.DataFrame,
    file_path: Path,
    **kwargs
) -> bool:
    """
    Safely save DataFrame to CSV.
    
    Args:
        df: DataFrame to save
        file_path: Destination file path
        **kwargs: Additional arguments for DataFrame.to_csv
        
    Returns:
        bool: True if successful
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=False, **kwargs)
        logger.info(f"Saved {file_path.name}: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Failed to save {file_path}: {str(e)}")
        return False

def clip_probability(probability: float, min_val: float = 0.001, max_val: float = 0.999) -> float:
    """
    Clip probability to valid range to avoid edge cases.
    
    Args:
        probability: Input probability
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        float: Clipped probability
    """
    return np.clip(probability, min_val, max_val)

def calculate_elo_expected(rating_a: float, rating_b: float) -> float:
    """
    Calculate expected score for ELO rating.
    
    Args:
        rating_a: Rating of team A
        rating_b: Rating of team B
        
    Returns:
        float: Expected score for team A
    """
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
