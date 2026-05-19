"""
Utility functions for data validation, error handling, and common operations.
"""
import pandas as pd
import logging
import time
import requests
from typing import Optional, Callable, Any
from pathlib import Path
import numpy as np

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
    func: Callable,
    max_retries: int = 3,
    delay: int = 2,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions on failure with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Wrapped function with retry logic
    """
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

def safe_api_request(
    url: str,
    params: dict = None,
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[dict]:
    """
    Make API request with error handling and retries.
    
    Args:
        url: API endpoint URL
        params: Request parameters
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        dict: Response JSON or None if failed
    """
    @retry_on_failure(max_retries=max_retries, exceptions=(requests.RequestException,))
    def _request():
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    try:
        return _request()
    except requests.RequestException as e:
        logger.error(f"API request failed: {url} - {str(e)}")
        return None

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
