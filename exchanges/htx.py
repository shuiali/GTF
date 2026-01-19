import asyncio
import time
import hmac
import hashlib
import logging
from typing import Dict
from datetime import datetime, timedelta
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class HTXExchange(BaseExchange):
    """HTX Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('huobi')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api.hbdm.com"
        self.rate_limit_ms = 100
    
    def _normalize_symbol(self, contract_code: str) -> str:
        """Normalize HTX contract code to standard format"""
        return contract_code.replace('-', '')
    
    async def _make_htx_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Custom request method for HTX with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        # HTX specific headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        await self._init_session()
        
        try:
            async with self.session.request("GET", url, params=params, headers=headers) as response:
                if response.status == 200:
                    # HTX returns text/plain but it's actually JSON
                    text = await response.text()
                    try:
                        import json
                        result = json.loads(text)
                        return result
                    except json.JSONDecodeError:
                        logger.warning(f"HTX: Invalid JSON response from {url}")
                        return {}
                else:
                    text = await response.text()
                    logger.warning(f"HTX: HTTP {response.status} for {url}: {text[:200]}")
                    return {}
        except Exception as e:
            logger.debug(f"HTX: Request error for {url}: {str(e)}")
            return {}
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates using batch endpoint"""
        endpoint = "/linear-swap-api/v1/swap_batch_funding_rate"
        response = await self._make_htx_request(endpoint)
        
        result = {}
        
        if isinstance(response, dict) and response.get('status') == 'ok' and 'data' in response:
            for item in response['data']:
                try:
                    contract_code = item['contract_code']
                    symbol = self._normalize_symbol(contract_code)
                    funding_rate = float(item['funding_rate'])
                    
                    # Use funding_time if available, otherwise estimate next funding
                    if 'funding_time' in item and item['funding_time']:
                        next_funding_time = self._timestamp_to_datetime(int(item['funding_time']))
                    else:
                        now = self._get_current_time()
                        next_hour = ((now.hour // 8) + 1) * 8
                        next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                        if next_hour >= 24:
                            next_funding_time = next_funding_time + timedelta(days=1)
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                except Exception as e:
                    logger.debug(f"HTX: Error processing {item}: {str(e)}")
                    continue
        
        logger.info(f"HTX: Successfully fetched {len(result)} funding rates")
        return result
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch prices using index price endpoint"""
        endpoint = "/linear-swap-api/v1/swap_index"
        response = await self._make_htx_request(endpoint)
        
        result = {}
        
        if isinstance(response, dict) and response.get('status') == 'ok' and 'data' in response:
            for item in response['data']:
                try:
                    contract_code = item['contract_code']
                    symbol = self._normalize_symbol(contract_code)
                    price = float(item['index_price'])
                    result[symbol] = price
                except Exception as e:
                    logger.debug(f"HTX: Error processing price for {item}: {str(e)}")
                    continue
        
        logger.info(f"HTX: Successfully fetched {len(result)} prices")
        return result
    
    async def get_next_funding_time(self) -> datetime:
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens from HTX using public symbols endpoint"""
        # Use public /v1/common/symbols endpoint - checks for leverage-permitted symbols
        url = "https://api.huobi.pro/v1/common/symbols"
        
        await self._init_session()
        result = {}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        try:
            async with self.session.request("GET", url, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    import json
                    response = json.loads(text)
                    
                    if isinstance(response, dict) and response.get('status') == 'ok' and 'data' in response:
                        for item in response['data']:
                            try:
                                # Check if leverage is permitted (meaning margin trading)
                                leverage_ratio = item.get('leverage-ratio', 0)
                                state = item.get('state', '')
                                base_currency = item.get('base-currency', '').upper()
                                quote_currency = item.get('quote-currency', '').upper()
                                
                                # Only include if leverage is allowed and trading against USDT
                                if leverage_ratio and leverage_ratio > 0 and state == 'online' and quote_currency == 'USDT':
                                    if base_currency and base_currency not in result:
                                        result[base_currency] = MarginTokenInfo(
                                            symbol=base_currency,
                                            is_borrowable=True,
                                            max_leverage=float(leverage_ratio)
                                        )
                            except Exception as e:
                                logger.debug(f"HTX: Error processing symbol item: {str(e)}")
                                continue
                else:
                    logger.warning(f"HTX: HTTP {resp.status} for margin tokens")
        except Exception as e:
            logger.debug(f"HTX: Error fetching margin tokens: {str(e)}")
        
        logger.info(f"HTX: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from HTX"""
        url = "https://api.huobi.pro/market/tickers"
        
        await self._init_session()
        result = {}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        try:
            async with self.session.request("GET", url, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    import json
                    response = json.loads(text)
                    
                    if isinstance(response, dict) and response.get('status') == 'ok' and 'data' in response:
                        for item in response['data']:
                            try:
                                symbol = item.get('symbol', '').upper()
                                close_price = item.get('close', 0)
                                
                                if symbol and close_price and close_price > 0:
                                    result[symbol] = float(close_price)
                            except Exception as e:
                                logger.debug(f"HTX: Error processing spot price item: {str(e)}")
                                continue
                else:
                    logger.warning(f"HTX: HTTP {resp.status} for spot prices")
        except Exception as e:
            logger.debug(f"HTX: Error fetching spot prices: {str(e)}")
        
        logger.info(f"HTX: Successfully fetched {len(result)} spot prices")
        return result
