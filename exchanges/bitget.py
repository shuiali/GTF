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
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Bitget V2 API uses plain symbol (e.g., 'BTCUSDT') with productType parameter
        # Remove _UMCBL suffix if present
        if symbol.endswith('_UMCBL'):
            symbol = symbol[:-6]
        
        # Convert interval to Bitget futures format (1m, 5m, 1H, 4H, 1D, etc.)
        granularity = get_exchange_interval('bitget_futures', interval)
        
        endpoint = "/api/v2/mix/market/candles"
        
        all_klines = []
        max_limit = 1000
        
        # Calculate interval in milliseconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_ms = interval_minutes * 60 * 1000
        
        # Bitget returns most recent data first when endTime is specified
        # We need to paginate backwards from end_time
        current_end = end_time
        
        while current_end > start_time:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'granularity': granularity,
                'endTime': str(current_end),
                'limit': str(max_limit)
            }
            
            response = await self._make_bitget_request(endpoint, params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                break
            
            batch_klines = []
            for kline in response['data']:
                try:
                    kline_time = int(kline[0]) / 1000  # Convert to seconds
                    kline_time_ms = int(kline[0])
                    # Only include if within our time range
                    if kline_time_ms >= start_time:
                        batch_klines.append({
                            'time': kline_time,
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5]) if len(kline) > 5 else 0
                        })
                except Exception as e:
                    logger.debug(f"Bitget: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines.extend(batch_klines)
            
            # Move backwards - find earliest timestamp in this batch
            earliest_time = min(int(k[0]) for k in response['data'])
            if earliest_time <= start_time:
                break
            current_end = earliest_time - 1
        
        # Remove duplicates and sort
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"Bitget Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 7 days of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in milliseconds (optional, defaults to 7 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Convert interval to Bitget spot format (1min, 5min, 1h, 1day, etc.)
        granularity = get_exchange_interval('bitget_spot', interval)
        
        endpoint = "/api/v2/spot/market/history-candles"
        
        all_klines = []
        max_limit = 200
        
        # Calculate interval in milliseconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_ms = interval_minutes * 60 * 1000
        
        # Paginate backwards from end_time
        current_end = end_time
        max_iterations = 200  # Safety limit to prevent infinite loops
        iteration = 0
        
        while current_end > start_time and iteration < max_iterations:
            iteration += 1
            
            params = {
                'symbol': symbol,
                'granularity': granularity,
                'endTime': str(current_end),
                'limit': str(max_limit)
            }
            
            response = await self._make_bitget_request(endpoint, params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                logger.debug(f"Bitget Spot: No more data at iteration {iteration}")
                break
            
            batch_klines = []
            for kline in response['data']:
                try:
                    kline_time = int(kline[0]) / 1000  # Convert to seconds
                    kline_time_ms = int(kline[0])
                    if kline_time_ms >= start_time:
                        batch_klines.append({
                            'time': kline_time,
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5]) if len(kline) > 5 else 0
                        })
                except Exception as e:
                    logger.debug(f"Bitget: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines.extend(batch_klines)
            logger.debug(f"Bitget Spot: Iteration {iteration}, got {len(batch_klines)} klines, total: {len(all_klines)}")
            
            # Move backwards - find earliest timestamp in this batch
            earliest_time = min(int(k[0]) for k in response['data'])
            if earliest_time <= start_time:
                logger.debug(f"Bitget Spot: Reached start_time at iteration {iteration}")
                break
            
            # Move to just before the earliest time we got
            current_end = earliest_time - 1
            
            # Add small delay to respect rate limits
            await asyncio.sleep(0.05)
        
        # Remove duplicates and sort
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"Bitget Spot: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines