"""
Send betting alerts via Telegram with async processing and error handling.
"""
import pandas as pd
import logging
import requests
from typing import List, Dict
import time
import config
from utils import load_csv_safe, retry_on_failure

logger = logging.getLogger(__name__)

def format_bet_message(bet: pd.Series) -> str:
    """
    Format bet data into readable Telegram message.
    
    Args:
        bet: Series with bet information
        
    Returns:
        str: Formatted message
    """
    message = f"""
🔥 **QUANT EV+ ALERT**

⚽ **Team**: {bet['team']}

🏆 **Match**: {bet['home_team']} vs {bet['away_team']}

💰 **Odds**: {bet['odds']:.2f}

📈 **Win Probability**: {bet['win_probability'] * 100:.2f}%

💵 **Expected Value**: {bet['expected_value'] * 100:.2f}%

🧠 **Kelly Stake**: {bet['kelly_stake'] * 100:.2f}%

📊 **Bookmaker**: {bet.get('bookmaker', 'N/A')}

⏰ **Commence Time**: {bet.get('commence_time', 'N/A')}
"""
    return message

@retry_on_failure(max_retries=3, exceptions=(requests.RequestException,))
def send_telegram_message(message: str) -> bool:
    """
    Send message to Telegram with retry logic.
    
    Args:
        message: Message text
        
    Returns:
        bool: True if successful
    """
    url = f"{config.TELEGRAM_API_BASE_URL}/sendMessage"
    
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=config.REQUEST_TIMEOUT)
    response.raise_for_status()
    
    return True

def send_batch_alerts(bets_df: pd.DataFrame, batch_delay: float = 1.0) -> Dict[str, int]:
    """
    Send alerts for all bets with rate limiting.
    
    Args:
        bets_df: DataFrame with bets to alert
        batch_delay: Delay between messages (seconds)
        
    Returns:
        Dictionary with success/failure counts
    """
    results = {"success": 0, "failed": 0}
    
    for idx, bet in bets_df.iterrows():
        try:
            message = format_bet_message(bet)
            success = send_telegram_message(message)
            
            if success:
                results["success"] += 1
                logger.info(f"Alert sent for {bet['team']} ({idx + 1}/{len(bets_df)})")
            else:
                results["failed"] += 1
                logger.warning(f"Failed to send alert for {bet['team']}")
            
            # Rate limiting
            if idx < len(bets_df) - 1:
                time.sleep(batch_delay)
        
        except Exception as e:
            results["failed"] += 1
            logger.error(f"Error sending alert for {bet['team']}: {str(e)}")
    
    return results

def send_summary_message(total_bets: int, results: Dict[str, int]) -> bool:
    """
    Send summary message with overall statistics.
    
    Args:
        total_bets: Total number of bets
        results: Success/failure counts
        
    Returns:
        bool: True if successful
    """
    summary = f"""
📊 **BETTING SUMMARY**

✅ Total Opportunities: {total_bets}
✉️ Alerts Sent: {results['success']}
❌ Failed: {results['failed']}

🤖 Powered by Quant Sports ML
"""
    
    try:
        return send_telegram_message(summary)
    except Exception as e:
        logger.error(f"Failed to send summary: {str(e)}")
        return False

def main():
    """Main execution function."""
    try:
        logger.info("Starting Telegram alert system...")
        
        # Load final bets
        df = load_csv_safe(
            config.FINAL_BETS_FILE,
            required_columns=["team", "home_team", "away_team", "odds", 
                            "win_probability", "expected_value", "kelly_stake"]
        )
        
        if df is None or df.empty:
            logger.warning("No bets to alert")
            
            # Send notification that no bets found
            send_telegram_message("📭 No profitable betting opportunities found today.")
            return
        
        logger.info(f"Sending alerts for {len(df)} bets...")
        
        # Send individual alerts
        results = send_batch_alerts(df, batch_delay=1.0)
        
        # Send summary
        send_summary_message(len(df), results)
        
        logger.info(f"Telegram alerts completed: {results['success']} sent, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Telegram alert system failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
