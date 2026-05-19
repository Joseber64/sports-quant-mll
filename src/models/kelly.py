"""
Kelly Criterion calculator for optimal bet sizing.
Includes safety checks and fractional Kelly implementation.
"""
import numpy as np
import logging
import config
from utils import clip_probability

logger = logging.getLogger(__name__)

def kelly_criterion(
    win_probability: float,
    odds: float,
    fraction: float = 1.0,
    min_stake: float = config.MIN_KELLY_STAKE
) -> float:
    """
    Calculate optimal bet size using Kelly Criterion with safety checks.
    
    Args:
        win_probability: Probability of winning (0 to 1)
        odds: Decimal odds
        fraction: Kelly fraction (0 to 1, typically 0.25 for quarter-Kelly)
        min_stake: Minimum stake to return
        
    Returns:
        float: Recommended stake as fraction of bankroll (0 to max_fraction)
    """
    # Input validation
    if not (0 <= win_probability <= 1):
        logger.warning(f"Invalid probability: {win_probability}, clipping to valid range")
        win_probability = clip_probability(win_probability)
    
    if odds <= 1.0:
        logger.warning(f"Invalid odds: {odds}, returning 0 stake")
        return 0.0
    
    if not (0 < fraction <= 1):
        logger.warning(f"Invalid fraction: {fraction}, using 1.0")
        fraction = 1.0
    
    # Avoid edge cases
    if win_probability <= 0.001:
        return 0.0
    
    if win_probability >= 0.999:
        logger.warning("Probability too high (overconfidence), capping at 0.95")
        win_probability = 0.95
    
    # Kelly formula: f = (bp - q) / b
    # where b = odds - 1, p = win probability, q = 1 - p
    b = odds - 1
    q = 1 - win_probability
    
    kelly_stake = ((b * win_probability) - q) / b
    
    # Apply fractional Kelly
    kelly_stake *= fraction
    
    # Ensure non-negative
    kelly_stake = max(0, kelly_stake)
    
    # Apply maximum Kelly fraction from config
    kelly_stake = min(kelly_stake, config.MAX_KELLY_FRACTION)
    
    # Return 0 if below minimum threshold
    if kelly_stake < min_stake:
        return 0.0
    
    return kelly_stake

def fractional_kelly(
    win_probability: float,
    odds: float,
    fraction: float = 0.25
) -> float:
    """
    Calculate fractional Kelly (typically quarter-Kelly for safety).
    
    Args:
        win_probability: Probability of winning
        odds: Decimal odds
        fraction: Fraction of full Kelly (default 0.25 = quarter-Kelly)
        
    Returns:
        float: Recommended stake
    """
    return kelly_criterion(win_probability, odds, fraction=fraction)

def validate_kelly_output(stake: float) -> bool:
    """
    Validate Kelly output is within acceptable range.
    
    Args:
        stake: Calculated Kelly stake
        
    Returns:
        bool: True if valid
    """
    if not (0 <= stake <= config.MAX_KELLY_FRACTION):
        logger.error(f"Kelly stake {stake} outside valid range")
        return False
    return True

# Convenience functions
def quarter_kelly(win_probability: float, odds: float) -> float:
    """Quarter-Kelly (25% of full Kelly) - conservative."""
    return fractional_kelly(win_probability, odds, fraction=0.25)

def half_kelly(win_probability: float, odds: float) -> float:
    """Half-Kelly (50% of full Kelly) - moderate."""
    return fractional_kelly(win_probability, odds, fraction=0.5)

def full_kelly(win_probability: float, odds: float) -> float:
    """Full Kelly - aggressive (not recommended for most)."""
    return kelly_criterion(win_probability, odds, fraction=1.0)
