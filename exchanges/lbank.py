import time
import hmac
import hashlib
import logging
import base64
import json
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class LBankExchange(BaseExchange):
    """LBank Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('lbank')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://lbkperp.lbank.com"
        self.rate_limit_ms = 100
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize LBank symbol to standard format"""
        # LBank uses format like BTCUSDT, which is already standard
        return symbol.upper()
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates using market data endpoint"""
        endpoint = "/cfd/openApi/v1/pub/marketData"
        params = {"productGroup": "SwapU"}  # SwapU is for USDT perpetual contracts
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        
        # Check if response has the expected structure
        if isinstance(response, dict):
            # Response might be wrapped in success/data structure
            if 'data' in response and isinstance(response['data'], list):
                market_data = response['data']
            elif isinstance(response.get('result'), str) and response.get('result') == 'true':
                # The response itself contains the market data (as seen in your log)
                # Extract all keys that look like market data (not meta fields)
                market_data = []
                for key, value in response.items():
                    if key not in ['result', 'error_code', 'msg', 'success'] and isinstance(value, list):
                        market_data = value
                        break
                # If no list found in response, try to extract from response directly
                if not market_data:
                    # Look for any list in the response
                    for value in response.values():
                        if isinstance(value, list):
                            market_data = value
                            break
            else:
                logger.warning(f"LBank: Unexpected response structure: {response}")
                return result
        elif isinstance(response, list):
            market_data = response
        else:
            logger.warning(f"LBank: Expected dict or list, got {type(response)}: {response}")
            return result
        
        if market_data:
            logger.info(f"LBank: Processing {len(market_data)} market data items")
            for item in market_data:
                try:
                    if not isinstance(item, dict):
                        continue
                        
                    symbol = item.get('symbol', '')
                    if not symbol:
                        continue
                    
                    # Normalize symbol
                    normalized_symbol = self._normalize_symbol(symbol)
                    
                    # Get funding rate - try multiple field names
                    funding_rate = 0.0
                    funding_rate_fields = ['fundingRate', 'positionFeeRate', 'prePositionFeeRate']
                    
                    for field in funding_rate_fields:
                        if field in item and item[field] is not None:
                            try:
                                funding_rate = float(item[field])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # Get next funding time from nextFeeTime (timestamp in milliseconds)
                    next_funding_time = None
                    if 'nextFeeTime' in item and item['nextFeeTime']:
                        try:
                            timestamp_ms = int(item['nextFeeTime'])
                            next_funding_time = self._timestamp_to_datetime(timestamp_ms, is_milliseconds=True)
                        except (ValueError, TypeError, OverflowError):
                            pass
                    
                    # If no valid timestamp, calculate next funding time
                    if not next_funding_time:
                        now = self._get_current_time()
                        current_hour = now.hour
                        if current_hour < 8:
                            next_funding_hour = 8
                        elif current_hour < 16:
                            next_funding_hour = 16
                        else:
                            next_funding_hour = 24
                        
                        next_funding_time = now.replace(hour=next_funding_hour % 24, minute=0, second=0, microsecond=0)
                        if next_funding_hour == 24:
                            next_funding_time = next_funding_time.replace(day=next_funding_time.day + 1)
                    
                    result[normalized_symbol] = FundingInfo(
                        symbol=normalized_symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                    
                    logger.debug(f"LBank: {normalized_symbol} - funding_rate: {funding_rate}, next_time: {next_funding_time}")
                    
                except Exception as e:
                    logger.debug(f"LBank: Error processing funding rate item {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"LBank: No market data found in response")
        
        logger.info(f"LBank: Successfully fetched {len(result)} funding rates")
        return result
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch prices using market data endpoint"""
        endpoint = "/cfd/openApi/v1/pub/marketData"
        params = {"productGroup": "SwapU"}  # SwapU is for USDT perpetual contracts
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        
        # Check if response has the expected structure (same logic as funding_rates)
        if isinstance(response, dict):
            # Response might be wrapped in success/data structure
            if 'data' in response and isinstance(response['data'], list):
                market_data = response['data']
            elif isinstance(response.get('result'), str) and response.get('result') == 'true':
                # Extract market data from response
                market_data = []
                for key, value in response.items():
                    if key not in ['result', 'error_code', 'msg', 'success'] and isinstance(value, list):
                        market_data = value
                        break
                # If no list found, try to extract from response directly
                if not market_data:
                    for value in response.values():
                        if isinstance(value, list):
                            market_data = value
                            break
            else:
                logger.warning(f"LBank: Unexpected response structure for prices: {response}")
                return result
        elif isinstance(response, list):
            market_data = response
        else:
            logger.warning(f"LBank: Expected dict or list for prices, got {type(response)}: {response}")
            return result
        
        if market_data:
            logger.info(f"LBank: Processing {len(market_data)} market data items for prices")
            for item in market_data:
                try:
                    if not isinstance(item, dict):
                        continue
                        
                    symbol = item.get('symbol', '')
                    if not symbol:
                        continue
                    
                    # Normalize symbol
                    normalized_symbol = self._normalize_symbol(symbol)
                    
                    # Get price - try multiple price fields
                    price = None
                    price_fields = ['markedPrice', 'lastPrice', 'underlyingPrice']
                    
                    for field in price_fields:
                        if field in item and item[field] is not None:
                            try:
                                price_val = float(item[field])
                                if price_val > 0:
                                    price = price_val
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    if price and price > 0:
                        result[normalized_symbol] = price
                        logger.debug(f"LBank: {normalized_symbol} - price: {price}")
                        
                except Exception as e:
                    logger.debug(f"LBank: Error processing price item {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"LBank: No market data found for prices")
        
        logger.info(f"LBank: Successfully fetched {len(result)} prices")
        return result
    
    async def get_next_funding_time(self) -> datetime:
        """Calculate next funding time - assuming 8-hour cycles"""
        now = self._get_current_time()
        current_hour = now.hour
        if current_hour < 8:
            next_funding_hour = 8
        elif current_hour < 16:
            next_funding_hour = 16
        else:
            next_funding_hour = 24
        
        next_funding_time = now.replace(hour=next_funding_hour % 24, minute=0, second=0, microsecond=0)
        if next_funding_hour == 24:
            next_funding_time = next_funding_time.replace(day=next_funding_time.day + 1)
        return next_funding_time