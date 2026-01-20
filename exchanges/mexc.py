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
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 7 days of data
        
        Note: MEXC Futures API returns max 2000 klines per request
        
        Args:
            symbol: Trading symbol (e.g., 'BTC_USDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 1w, 1M)
            start_time: Start timestamp in SECONDS (optional, defaults to 7 days ago)
            end_time: End timestamp in SECONDS (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps_seconds, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps_seconds()
        
        # Ensure symbol has underscore format
        if '_' not in symbol:
            # Convert BTCUSDT to BTC_USDT
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}_USDT"
        
        # Convert interval to MEXC format (Min1, Min60, Hour4, Day1, etc.)
        mexc_interval = get_exchange_interval('mexc_futures', interval)
        
        endpoint = f"/api/v1/contract/kline/{symbol}"
        
        all_klines = []
        max_limit = 2000  # MEXC returns max 2000 per request
        
        # Calculate interval in seconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_seconds = interval_minutes * 60
        
        # Work forwards from start_time to end_time
        current_start = start_time
        
        while current_start < end_time:
            # Calculate chunk end (max 2000 candles)
            chunk_end = min(end_time, current_start + (max_limit * interval_seconds))
            
            params = {
                'interval': mexc_interval,
                'start': current_start,
                'end': chunk_end
            }
            
            response = await self._make_mexc_request(endpoint, params=params)
            
            batch_klines = []
            # MEXC returns data in a special format with separate arrays
            if isinstance(response, dict):
                if response.get('success') and 'data' in response:
                    data = response['data']
                    if all(key in data for key in ['time', 'open', 'high', 'low', 'close', 'vol']):
                        times = data['time']
                        opens = data['open']
                        highs = data['high']
                        lows = data['low']
                        closes = data['close']
                        volumes = data['vol']
                        
                        # Combine arrays into kline objects
                        for i in range(len(times)):
                            try:
                                batch_klines.append({
                                    'time': float(times[i]),  # Already in seconds
                                    'open': float(opens[i]),
                                    'high': float(highs[i]),
                                    'low': float(lows[i]),
                                    'close': float(closes[i]),
                                    'volume': float(volumes[i])
                                })
                            except Exception as e:
                                logger.debug(f"MEXC: Error processing kline at index {i}: {str(e)}")
                                continue
            
            all_klines.extend(batch_klines)
            
            if len(batch_klines) == 0 or len(batch_klines) < max_limit:
                break
            
            # Move forward
            last_time = max(k['time'] for k in batch_klines)
            current_start = int(last_time) + interval_seconds
        
        # Remove duplicates and sort
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"MEXC Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 7 days of data
        
        Note: MEXC spot API returns max 500 klines per request
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            start_time: Start timestamp in milliseconds (optional, defaults to 7 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # MEXC spot uses standard symbol format without underscore
        if '_' in symbol:
            symbol = symbol.replace('_', '')
        
        # Convert interval to MEXC spot format
        mexc_interval = get_exchange_interval('mexc_spot', interval)
        
        spot_url = "https://api.mexc.com"
        endpoint = "/api/v3/klines"
        
        all_klines = []
        max_limit = 500  # MEXC spot actually returns max 500 per request
        
        # Calculate interval in milliseconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_ms = interval_minutes * 60 * 1000
        
        await self._init_session()
        
        # Work forwards from start_time to end_time
        current_start = start_time
        
        while current_start < end_time:
            url = f"{spot_url}{endpoint}"
            params = {
                'symbol': symbol,
                'interval': mexc_interval,
                'startTime': current_start,
                'endTime': end_time,
                'limit': max_limit
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
            
            try:
                async with self.session.request("GET", url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list) and len(data) > 0:
                            for kline in data:
                                try:
                                    # MEXC spot returns: [open_time, open, high, low, close, volume, close_time, ...]
                                    all_klines.append({
                                        'time': int(kline[0]) / 1000,  # Convert to seconds
                                        'open': float(kline[1]),
                                        'high': float(kline[2]),
                                        'low': float(kline[3]),
                                        'close': float(kline[4]),
                                        'volume': float(kline[5])
                                    })
                                except Exception as e:
                                    logger.debug(f"MEXC: Error processing spot kline {kline}: {str(e)}")
                                    continue
                            
                            # Move forward based on last timestamp
                            last_time = int(data[-1][0])
                            if last_time >= end_time:
                                break
                            current_start = last_time + interval_ms
                        else:
                            break
                    else:
                        logger.warning(f"MEXC: HTTP {response.status} for spot klines")
                        break
            except Exception as e:
                logger.debug(f"MEXC: Error fetching spot klines: {str(e)}")
                break
        
        # Remove duplicates and sort
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"MEXC Spot: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
