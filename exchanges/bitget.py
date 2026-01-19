import time
import hmac
import hashlib
import logging
import base64
import asyncio
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class BitgetExchange(BaseExchange):
    """BitGet Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('bitget')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api.bitget.com"
        self.passphrase = keys.get('password', '')
        self.rate_limit_ms = 150
    
    async def _make_bitget_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Custom request method for Bitget with proper headers to avoid brotli encoding"""
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
                        logger.error(f"Bitget: JSON decode error for {url}: {str(e)}")
                        return {}
                else:
                    text = await response.text()
                    logger.warning(f"Bitget: HTTP {response.status} for {url}: {text[:200]}")
                    return {}
        except Exception as e:
            logger.debug(f"Bitget: Request error for {url}: {str(e)}")
            return {}
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates using the current funding rate endpoint"""
        endpoint = "/api/v2/mix/market/current-fund-rate"
        params = {"productType": "USDT-FUTURES"}
        response = await self._make_bitget_request(endpoint, params=params)
        
        result = {}
        if 'data' in response and isinstance(response['data'], list):
            for item in response['data']:
                try:
                    symbol = item['symbol']
                    
                    # Get funding rate
                    funding_rate = float(item.get('fundingRate', 0))
                    
                    # Get next funding time
                    next_update_str = item.get('nextUpdate')
                    if next_update_str:
                        next_funding_time = self._timestamp_to_datetime(int(next_update_str))
                    else:
                        # Fallback to 8-hour calculation
                        now = self._get_current_time()
                        next_hour = ((now.hour // 8) + 1) * 8
                        next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                        if next_hour == 24:
                            next_funding_time = next_funding_time.replace(day=next_funding_time.day + 1)
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                    
                except Exception as e:
                    logger.debug(f"BitGet: Error processing funding rate {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"BitGet: Unexpected funding rates response format: {response}")
        
        logger.info(f"BitGet: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices in ONE API call using V2 API"""
        endpoint = "/api/v2/mix/market/tickers"
        params = {"productType": "USDT-FUTURES"}
        response = await self._make_bitget_request(endpoint, params=params)
        
        result = {}
        if 'data' in response:
            for item in response['data']:
                try:
                    bg_symbol = item['symbol']
                    symbol = bg_symbol.replace("_UMCBL", "")
                    
                    # Try multiple price fields
                    price = None
                    price_fields = ['last', 'close', 'markPrice', 'lastPr']
                    for field in price_fields:
                        if field in item and item[field] is not None:
                            try:
                                price = float(item[field])
                                if price > 0:
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    if price and price > 0:
                        result[symbol] = price
                        
                except Exception as e:
                    logger.debug(f"BitGet: Error processing price {item}: {str(e)}")
                    continue
        
        logger.info(f"BitGet: Successfully fetched {len(result)} prices")
        return result

    async def get_next_funding_time(self) -> datetime:
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
        if next_hour == 24:
            next_funding_time = next_funding_time.replace(day=next_funding_time.day + 1)
        return next_funding_time
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens from Bitget"""
        endpoint = "/api/v2/margin/currencies"
        response = await self._make_bitget_request(endpoint)
        
        result = {}
        if 'data' in response and isinstance(response['data'], list):
            for item in response['data']:
                try:
                    base_coin = item.get('baseCoin', '')
                    is_borrowable = item.get('isCrossBorrowable', False) or item.get('isBorrowable', False)
                    status = item.get('status', '')
                    
                    if base_coin and is_borrowable and status == '1':
                        max_leverage = float(item.get('maxCrossedLeverage', 0)) if item.get('maxCrossedLeverage') else None
                        result[base_coin] = MarginTokenInfo(
                            symbol=base_coin,
                            is_borrowable=True,
                            max_leverage=max_leverage
                        )
                except Exception as e:
                    logger.debug(f"Bitget: Error processing margin item: {str(e)}")
                    continue
        
        logger.info(f"Bitget: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from Bitget"""
        endpoint = "/api/v2/spot/market/tickers"
        response = await self._make_bitget_request(endpoint)
        
        result = {}
        if 'data' in response and isinstance(response['data'], list):
            for item in response['data']:
                try:
                    symbol = item.get('symbol', '')
                    last_price = item.get('lastPr', '') or item.get('close', '')
                    
                    if symbol and last_price:
                        price = float(last_price)
                        if price > 0:
                            result[symbol] = price
                except Exception as e:
                    logger.debug(f"Bitget: Error processing spot price item: {str(e)}")
                    continue
        
        logger.info(f"Bitget: Successfully fetched {len(result)} spot prices")
        return result