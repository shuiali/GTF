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
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 7 days of data
        
        Note: HTX futures API has limited time range for from/to queries.
        We use 'size' parameter and paginate backwards using timestamps.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            start_time: Start timestamp in SECONDS (optional, defaults to 7 days ago)
            end_time: End timestamp in SECONDS (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps_seconds, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps_seconds()
        
        # Ensure symbol has dash format for futures
        if '-' not in symbol:
            # Convert BTCUSDT to BTC-USDT
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}-USDT"
        
        # Convert interval to HTX format
        htx_interval = get_exchange_interval('htx_futures', interval)
        
        endpoint = "/linear-swap-ex/market/history/kline"
        
        all_klines = []
        max_size = 2000
        
        # Calculate interval in seconds
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_seconds = interval_minutes * 60
        
        # Start by getting most recent data, then paginate backwards
        current_to = end_time
        
        while current_to > start_time:
            # HTX: use 'to' and 'size' to get data ending at current_to
            # Unfortunately HTX doesn't support 'to' alone, so we use a short from/to range
            # Use a range of ~1 day which is within HTX's limits
            range_seconds = min(1440 * interval_seconds, current_to - start_time)  # Max ~1 day of candles
            current_from = max(start_time, current_to - range_seconds)
            
            params = {
                'contract_code': symbol,
                'period': htx_interval,
                'from': current_from,
                'to': current_to
            }
            
            response = await self._make_htx_request(endpoint, params=params)
            
            if not isinstance(response, dict) or response.get('status') != 'ok' or 'data' not in response:
                # If from/to fails, try using size parameter alone
                params = {
                    'contract_code': symbol,
                    'period': htx_interval,
                    'size': max_size
                }
                response = await self._make_htx_request(endpoint, params=params)
                if not isinstance(response, dict) or response.get('status') != 'ok' or 'data' not in response:
                    break
            
            data = response['data']
            if len(data) == 0:
                break
            
            for kline in data:
                try:
                    kline_time = float(kline['id'])
                    if start_time <= kline_time <= end_time:
                        all_klines.append({
                            'time': kline_time,  # Already in seconds
                            'open': float(kline['open']),
                            'high': float(kline['high']),
                            'low': float(kline['low']),
                            'close': float(kline['close']),
                            'volume': float(kline['amount'])
                        })
                except Exception as e:
                    logger.debug(f"HTX: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Move backwards
            earliest_time = min(float(k['id']) for k in data)
            if earliest_time <= start_time:
                break
            current_to = int(earliest_time) - 1
        
        # Sort by time ascending and remove duplicates
        all_klines.sort(key=lambda x: x['time'])
        seen = set()
        unique_klines = []
        for k in all_klines:
            if k['time'] not in seen:
                seen.add(k['time'])
                unique_klines.append(k)
        
        logger.info(f"HTX Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
        
        # Sort by time ascending and remove duplicates
        all_klines.sort(key=lambda x: x['time'])
        seen = set()
        unique_klines = []
        for k in all_klines:
            if k['time'] not in seen:
                seen.add(k['time'])
                unique_klines.append(k)
        
        logger.info(f"HTX Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 7 days of data
        
        Note: HTX spot API only supports 'size' parameter (max 2000), not time range.
        For 1m data over 7 days (10080 candles), we need multiple requests.
        
        Args:
            symbol: Trading symbol (e.g., 'btcusdt')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            start_time: Start timestamp in SECONDS (optional, defaults to 7 days ago)
            end_time: End timestamp in SECONDS (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps_seconds, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps_seconds()
        
        # Convert interval to HTX spot format
        htx_interval = get_exchange_interval('htx_spot', interval)
        
        url = "https://api.huobi.pro/market/history/kline"
        # HTX spot uses 'size' parameter (max 2000) - returns most recent candles
        params = {
            'symbol': symbol.lower(),
            'period': htx_interval,
            'size': 2000
        }
        
        await self._init_session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        all_klines = []
        try:
            async with self.session.request("GET", url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    import json
                    response = json.loads(text)
                    
                    if isinstance(response, dict) and response.get('status') == 'ok' and 'data' in response:
                        for kline in response['data']:
                            try:
                                kline_time = float(kline['id'])
                                # Filter by time range
                                if start_time <= kline_time <= end_time:
                                    all_klines.append({
                                        'time': kline_time,  # Already in seconds
                                        'open': float(kline['open']),
                                        'high': float(kline['high']),
                                        'low': float(kline['low']),
                                        'close': float(kline['close']),
                                        'volume': float(kline['amount'])
                                    })
                            except Exception as e:
                                logger.debug(f"HTX: Error processing kline {kline}: {str(e)}")
                                continue
                else:
                    logger.warning(f"HTX: HTTP {resp.status} for spot klines")
        except Exception as e:
            logger.debug(f"HTX: Error fetching spot klines: {str(e)}")
        
        # Sort by time ascending
        all_klines.sort(key=lambda x: x['time'])
        logger.info(f"HTX Spot: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines
