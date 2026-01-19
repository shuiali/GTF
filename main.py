import logging
import sys
import os
from telegram_bot import TelegramBot
from utils.config_loader import ConfigLoader

def main():
    # Set up logging with filtered noise from telegram libraries
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress verbose logging from telegram-related libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Test config loading
        config = ConfigLoader()
        if not config.telegram_bot_token:
            logger.error("Telegram bot token not found in config.json")
            sys.exit(1)
            
        # Initialize and run bot
        bot = TelegramBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True) # Add exc_info=True here
        sys.exit(1)

if __name__ == '__main__':
    main()