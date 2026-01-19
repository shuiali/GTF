import time
import hmac
import hashlib
import logging
from typing import Dict
from datetime import datetime
import urllib.parse
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class MEXCExchange(BaseExchange):
    """MEXC Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('mexc')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://contract.mexc.com"
        self.rate_limit_ms = 200
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize MEXC symbol to standard format"""
        return symbol.replace('_', '')
    
    async def _make_mexc_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Custom request method for MEXC with proper headers to avoid brotli encoding"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'  # Explicitly avoid brotli
        }
        
        await self._init_session()
        
        try:
            async with self.session.request("GET", url, params=params, headers=headers) as response:
                if response.status == 200:
                    try:
                        result = await response.json()
                        return result if result is not None else {}
                    except Exception as e:
                        logger.error(f"MEXC: JSON decode error for {url}: {str(e)}")
                        return {}
                else:
                    text = await response.text()
                    logger.warning(f"MEXC: HTTP {response.status} for {url}: {text[:200]}")
                    return {}
        except Exception as e:
            logger.debug(f"MEXC: Request error for {url}: {str(e)}")
            return {}
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates in ONE API call"""
        endpoint = "/api/v1/contract/funding_rate"
        
        response = await self._make_mexc_request(endpoint)
        
        result = {}
        
        # Handle different response formats
        data = None
        if isinstance(response, dict):
            # Check for 'data' key directly
            if 'data' in response:
                data = response['data']
            # Check for success/code pattern
            elif response.get('success') is True or response.get('code') == 0:
                data = response.get('data', [])
            # Log the actual response for debugging
            else:
                logger.warning(f"MEXC: Unexpected response format: {str(response)[:500]}")
        elif isinstance(response, list):
            data = response
        
        if data:
            
            for item in data:
                try:
                    mexc_symbol = item.get('symbol', '')
                    if not mexc_symbol:
                        continue
                    symbol = self._normalize_symbol(mexc_symbol)
                    
                    # Try different field names for funding rate
                    funding_rate = item.get('fundingRate') or item.get('funding_rate') or item.get('lastFundingRate') or 0
                    funding_rate = float(funding_rate)
                    
                    # Handle different timestamp field names
                    timestamp_value = item.get('fundingTime') or item.get('nextFundingTime') or item.get('nextSettleTime') or item.get('timestamp')
                    
                    if timestamp_value:
                        try:
                            next_funding_time = self._timestamp_to_datetime(int(timestamp_value))
                        except (ValueError, TypeError):
                            now = self._get_current_time()
                            next_hour = ((now.hour // 8) + 1) * 8
                            next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                    else:
                        now = self._get_current_time()
                        next_hour = ((now.hour // 8) + 1) * 8
                        next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                except Exception as e:
                    logger.debug(f"MEXC: Error processing {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"MEXC: Expected dict with 'data', got {type(response)}: {response}")
        
        logger.info(f"MEXC: Successfully fetched {len(result)} funding rates")
        return result
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices in ONE API call"""
        endpoint = "/api/v1/contract/ticker"
        
        response = await self._make_mexc_request(endpoint)
        
        result = {}
        
        # Handle different response formats
        data = None
        if isinstance(response, dict):
            if 'data' in response:
                data = response['data']
            elif response.get('success') is True or response.get('code') == 0:
                data = response.get('data', [])
        elif isinstance(response, list):
            data = response
        
        if data:
            for item in data:
                try:
                    mexc_symbol = item.get('symbol', '')
                    if not mexc_symbol:
                        continue
                    symbol = self._normalize_symbol(mexc_symbol)
                    price = item.get('last') or item.get('lastPrice') or item.get('price') or item.get('close') or item.get('fairPrice')
                    if price:
                        result[symbol] = float(price)
                except Exception as e:
                    logger.debug(f"MEXC: Error processing price {item}: {str(e)}")
                    continue
        
        logger.info(f"MEXC: Successfully fetched {len(result)} prices")
        return result
    
    async def get_next_funding_time(self) -> datetime:
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
