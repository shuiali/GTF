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
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 7 days of data
        
        Args:
            symbol: Trading symbol in Gate.io format (e.g., 'BTC_USDT' or 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 7d, 30d)
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
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}_USDT"
        
        # Convert interval to Gate.io format
        gateio_interval = get_exchange_interval('gateio', interval)
        
        endpoint = "/api/v4/futures/usdt/candlesticks"
        
        all_klines = []
        current_end = end_time
        max_limit = 2000
        
        # Calculate interval in seconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_seconds = interval_minutes * 60
        
        # Work backwards to get all data
        while current_end > start_time:
            # Calculate how far back to request (max 2000 candles)
            chunk_start = max(start_time, current_end - (max_limit * interval_seconds))
            
            params = {
                'contract': symbol,
                'interval': gateio_interval,
                'from': chunk_start,
                'to': current_end
            }
            
            response = await self._make_gateio_request(endpoint, params=params)
            
            if not isinstance(response, list) or len(response) == 0:
                break
            
            batch_klines = []
            for kline in response:
                try:
                    # Gate.io returns: {t, v, c, h, l, o, sum}
                    batch_klines.append({
                        'time': float(kline['t']),  # Already in seconds
                        'open': float(kline['o']),
                        'high': float(kline['h']),
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v'])
                    })
                except Exception as e:
                    logger.debug(f"Gate.io: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Prepend to maintain order (oldest first)
            all_klines = batch_klines + all_klines
            
            # If we got less than max, we have all the data
            if len(response) < max_limit:
                break
            
            # Move backwards - set end to before the earliest kline we received
            earliest_time = min(float(k['t']) for k in response)
            current_end = int(earliest_time) - 1
        
        # Sort by time ascending and remove duplicates
        all_klines.sort(key=lambda x: x['time'])
        seen = set()
        unique_klines = []
        for k in all_klines:
            if k['time'] not in seen:
                seen.add(k['time'])
                unique_klines.append(k)
        
        logger.info(f"Gate.io Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 7 days of data
        
        Note: Gate.io spot API has special rule - 'limit' conflicts with 'from/to'.
        We must use 'limit' and paginate by using 'to' as the end marker.
        
        Args:
            symbol: Trading symbol in Gate.io format (e.g., 'BTC_USDT' or 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 7d, 30d)
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
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}_USDT"
        
        # Convert interval to Gate.io format
        gateio_interval = get_exchange_interval('gateio', interval)
        
        endpoint = "/api/v4/spot/candlesticks"
        
        all_klines = []
        current_end = end_time
        max_limit = 1000  # Gate.io spot max is 1000
        
        # Work backwards using 'to' and 'limit' (NOT 'from')
        while current_end > start_time:
            # Gate.io spot: "limit conflicts with from and to"
            # So we use 'to' and 'limit' only
            params = {
                'currency_pair': symbol,
                'interval': gateio_interval,
                'to': current_end,
                'limit': max_limit
            }
            
            response = await self._make_gateio_request(endpoint, params=params)
            
            if not isinstance(response, list) or len(response) == 0:
                break
            
            batch_klines = []
            for kline in response:
                try:
                    kline_time = float(kline[0])
                    # Only include klines within our time range
                    if kline_time >= start_time:
                        batch_klines.append({
                            'time': kline_time,  # Already in seconds
                            'open': float(kline[5]),
                            'high': float(kline[3]),
                            'low': float(kline[4]),
                            'close': float(kline[2]),
                            'volume': float(kline[1])
                        })
                except Exception as e:
                    logger.debug(f"Gate.io: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines.extend(batch_klines)
            
            if len(response) < max_limit:
                break
            
            # Move backwards - use the earliest timestamp from response minus 1 second
            earliest_time = min(float(k[0]) for k in response)
            if earliest_time <= start_time:
                break
            current_end = int(earliest_time) - 1
        
        # Sort and remove duplicates
        all_klines.sort(key=lambda x: x['time'])
        seen = set()
        unique_klines = []
        for k in all_klines:
            if k['time'] not in seen:
                seen.add(k['time'])
                unique_klines.append(k)
        
        logger.info(f"Gate.io Spot: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
