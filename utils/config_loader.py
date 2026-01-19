import json
import os
from typing import Dict, Any

class ConfigLoader:
    """Configuration loader that reads from config.json"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from config.json"""
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to find config.json in the project root
        config_path = os.path.join(os.path.dirname(current_dir), 'config.json')
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                # Remove any comments from JSON (they start with //)
                lines = content.split('\n')
                clean_lines = [line for line in lines if not line.strip().startswith('//')]
                clean_content = '\n'.join(clean_lines)
                self._config = json.loads(clean_content)
        except FileNotFoundError:
            raise Exception(f"Config file not found at: {config_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to load config.json: {str(e)}")
    
    def get_exchange_keys(self, exchange: str) -> Dict[str, str]:
        """Get API keys for specific exchange"""
        exchange_config = self._config.get(exchange.lower(), {})
        return {
            'api_key': exchange_config.get('apiKey', ''),
            'secret': exchange_config.get('secret', ''),
            'password': exchange_config.get('password', '')  # For exchanges that need it
        }
    
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token"""
        return self._config.get('telegram_bot_token', '')
    
    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID"""
        return self._config.get('telegram_chat_id', '')
    
    @property
    def proxy_url(self) -> str:
        """Get proxy URL if configured"""
        return self._config.get('proxy_url', '')
    
    @property
    def arbitrage_mode(self) -> str:
        """Get current arbitrage mode (futures-futures, spot-futures, futures-margin)"""
        return self._config.get('arbitrage_mode', 'futures-futures')
    
    def set_arbitrage_mode(self, mode: str) -> bool:
        """Set arbitrage mode and save to config"""
        valid_modes = ['futures-futures', 'spot-futures', 'futures-margin']
        if mode not in valid_modes:
            return False
        
        self._config['arbitrage_mode'] = mode
        
        # Save to file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), 'config.json')
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception:
            return False