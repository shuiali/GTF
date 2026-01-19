import sys
import traceback

try:
    from telegram_bot import TelegramBot
    print("✓ TelegramBot imported successfully")
    
    bot = TelegramBot()
    print("✓ TelegramBot initialized successfully")
    
    print("Starting bot...")
    bot.run()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
