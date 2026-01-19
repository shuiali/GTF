import time
import hmac
import hashlib
import logging
import asyncio
import aiohttp
from typing import Dict
from datetime import datetime, timedelta
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class GateioExchange(BaseExchange):
    """Gate.io Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('gateio')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api.gateio.ws"
        self.rate_limit_ms = 50  # Fast rate limit
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize Gate.io symbol to standard format"""
        return symbol.replace('_', '')
    
    async def _make_gateio_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Custom request method for Gate.io with NO TIMEOUT"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        await self._init_session()
        
        try:
            # NO TIMEOUT - let it take as long as it needs
            async with self.session.request("GET", url, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result if result is not None else {}
                else:
                    text = await response.text()
                    logger.warning(f"Gate.io: HTTP {response.status} for {url}: {text[:100]}")
                    return {}
        except Exception as e:
            logger.debug(f"Gate.io: Request error for {url}: {str(e)}")
            return {}
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates using tickers endpoint"""
        endpoint = "/api/v4/futures/usdt/tickers"
        response = await self._make_gateio_request(endpoint)
        
        result = {}
        
        if isinstance(response, list) and len(response) > 0:
            logger.info(f"Gate.io: Processing {len(response)} tickers for funding rates")
            for item in response:
                try:
                    gate_symbol = item.get('contract', '')
                    if not gate_symbol or '_USDT' not in gate_symbol:
                        continue
                        
                    symbol = self._normalize_symbol(gate_symbol)
                    
                    funding_rate_str = item.get('funding_rate')
                    if not funding_rate_str:
                        continue
                        
                    funding_rate = float(funding_rate_str)
                    
                    # Estimate next funding time (Gate.io uses 8-hour cycles)
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
                        next_funding_time += timedelta(days=1)
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                except Exception as e:
                    logger.debug(f"Gate.io: Error processing funding rate item: {str(e)}")
                    continue
        
        logger.info(f"Gate.io: Successfully fetched {len(result)} funding rates")
        return result
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch prices using tickers endpoint"""
        endpoint = "/api/v4/futures/usdt/tickers"
        response = await self._make_gateio_request(endpoint)
        
        result = {}
        if isinstance(response, list) and len(response) > 0:
            logger.info(f"Gate.io: Processing {len(response)} tickers for prices")
            for item in response:
                try:
                    gate_symbol = item.get('contract', '')
                    if not gate_symbol or '_USDT' not in gate_symbol:
                        continue
                        
                    symbol = self._normalize_symbol(gate_symbol)
                    
                    price_str = item.get('mark_price')
                    if not price_str or float(price_str) <= 0:
                        price_str = item.get('last')

                    if price_str and float(price_str) > 0:
                        result[symbol] = float(price_str)

                except Exception as e:
                    logger.debug(f"Gate.io: Error processing price item: {str(e)}")
                    continue
        
        logger.info(f"Gate.io: Successfully fetched {len(result)} prices")
        return result
    
    async def get_next_funding_time(self) -> datetime:
        """Get next funding time - 8-hour cycle"""
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
            next_funding_time += timedelta(days=1)
            
        return next_funding_time
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens from Gate.io"""
        # Using /spot/currency_pairs to get tradable pairs with margin info
        endpoint = "/api/v4/spot/currency_pairs"
        response = await self._make_gateio_request(endpoint)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    trade_status = item.get('trade_status', '')
                    base = item.get('base', '')
                    
                    # Check if the pair is tradable (margin pairs are usually tradable)
                    if trade_status == 'tradable' and base:
                        if base not in result:
                            result[base] = MarginTokenInfo(
                                symbol=base,
                                is_borrowable=True,
                                max_leverage=None
                            )
                except Exception as e:
                    logger.debug(f"Gate.io: Error processing margin item: {str(e)}")
                    continue
        
        logger.info(f"Gate.io: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from Gate.io"""
        endpoint = "/api/v4/spot/tickers"
        response = await self._make_gateio_request(endpoint)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    currency_pair = item.get('currency_pair', '')
                    last_price = item.get('last', '')
                    
                    if currency_pair and last_price:
                        # Convert Gate.io format (BTC_USDT) to standard (BTCUSDT)
                        symbol = currency_pair.replace('_', '')
                        price = float(last_price)
                        if price > 0:
                            result[symbol] = price
                except Exception as e:
                    logger.debug(f"Gate.io: Error processing spot price item: {str(e)}")
                    continue
        
        logger.info(f"Gate.io: Successfully fetched {len(result)} spot prices")
        return result
