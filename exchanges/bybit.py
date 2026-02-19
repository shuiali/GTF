import time
import hmac
import hashlib
import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class BybitExchange(BaseExchange):
    """Bybit Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('bybit')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api.bybit.com"
        self.rate_limit_ms = 150
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates using tickers endpoint - includes fundingRate and nextFundingTime"""
        endpoint = "/v5/market/tickers"
        params = {"category": "linear"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    symbol = item['symbol']
                    
                    # Skip if not USDT perpetual
                    if not symbol.endswith('USDT'):
                        continue
                    
                    # Get funding rate - the tickers endpoint includes this!
                    funding_rate_str = item.get('fundingRate', '0')
                    try:
                        funding_rate = float(funding_rate_str) if funding_rate_str else 0.0
                    except (ValueError, TypeError):
                        logger.debug(f"Bybit: Invalid funding rate for {symbol}: {funding_rate_str}")
                        continue
                    
                    # Get next funding time - also included in tickers!
                    next_funding_str = item.get('nextFundingTime', '0')
                    try:
                        if next_funding_str and next_funding_str != '0':
                            next_funding_time = self._timestamp_to_datetime(int(next_funding_str))
                        else:
                            # Fallback to 8-hour calculation
                            now = self._get_current_time()
                            next_hour = ((now.hour // 8) + 1) * 8
                            next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                    except (ValueError, TypeError):
                        # Fallback to 8-hour calculation
                        now = self._get_current_time()
                        next_hour = ((now.hour // 8) + 1) * 8
                        next_funding_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                    
                except Exception as e:
                    logger.debug(f"Bybit: Error processing funding rate item {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"Bybit: Unexpected funding rates response format: {response}")
        
        logger.info(f"Bybit: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices using tickers endpoint - same as funding rates but extract prices"""
        endpoint = "/v5/market/tickers"
        params = {"category": "linear"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    symbol = item['symbol']
                    
                    # Skip if not USDT perpetual
                    if not symbol.endswith('USDT'):
                        continue
                    
                    # Get mark price - prefer markPrice, fallback to lastPrice
                    mark_price_str = item.get('markPrice') or item.get('lastPrice', '0')
                    try:
                        mark_price = float(mark_price_str) if mark_price_str else 0.0
                        if mark_price > 0:  # Only add valid prices
                            result[symbol] = mark_price
                    except (ValueError, TypeError):
                        logger.debug(f"Bybit: Invalid price for {symbol}: {mark_price_str}")
                        continue
                        
                except Exception as e:
                    logger.debug(f"Bybit: Error processing price item {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"Bybit: Unexpected price response format: {response}")
        
        logger.info(f"Bybit: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT"""
        endpoint = "/v5/market/tickers"
        params = {"category": "linear"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    symbol = item['symbol']
                    if not symbol.endswith('USDT'):
                        continue
                    # turnover24h is the 24h volume in quote currency (USDT)
                    volume = float(item.get('turnover24h', 0))
                    if volume > 0:
                        result[symbol] = volume
                except Exception as e:
                    logger.debug(f"Bybit: Error processing volume: {str(e)}")
                    continue
        
        logger.info(f"Bybit: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices using /v5/market/tickers"""
        endpoint = "/v5/market/tickers"
        params = {"category": "linear"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    symbol = item['symbol']
                    if not symbol.endswith('USDT'):
                        continue
                    
                    bid_price = float(item.get('bid1Price', 0))
                    ask_price = float(item.get('ask1Price', 0))
                    if bid_price > 0 and ask_price > 0:
                        result[symbol] = {'bid': bid_price, 'ask': ask_price}
                except Exception as e:
                    logger.debug(f"Bybit: Error processing order book item: {str(e)}")
                    continue
        
        logger.info(f"Bybit: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        """Calculate next funding time - Bybit uses 8-hour cycles"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens from Bybit using spot instruments endpoint"""
        # Use /v5/market/instruments-info with spot category and check marginTrading field
        result = {}
        
        # Primary: get spot instruments and check marginTrading field
        endpoint = "/v5/market/instruments-info"
        params = {"category": "spot"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    base_coin = item.get('baseCoin', '')
                    margin_trading = item.get('marginTrading', '')
                    
                    # marginTrading can be 'both', 'utaOnly', 'normalSpotOnly', or 'none'
                    if base_coin and margin_trading in ['both', 'utaOnly', 'normalSpotOnly']:
                        if base_coin not in result:
                            result[base_coin] = MarginTokenInfo(
                                symbol=base_coin,
                                is_borrowable=True,
                                max_leverage=None
                            )
                except Exception as e:
                    logger.debug(f"Bybit: Error processing instrument item: {str(e)}")
                    continue
        
        logger.info(f"Bybit: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from Bybit"""
        endpoint = "/v5/market/tickers"
        params = {"category": "spot"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'result' in response and 'list' in response['result']:
            for item in response['result']['list']:
                try:
                    symbol = item.get('symbol', '')
                    price = float(item.get('lastPrice', 0))
                    if symbol and price > 0:
                        result[symbol] = price
                except Exception as e:
                    logger.debug(f"Bybit: Error processing spot price item {item}: {str(e)}")
                    continue
        
        logger.info(f"Bybit: Successfully fetched {len(result)} spot prices")
        return result
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Convert interval to Bybit format (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
        bybit_interval = get_exchange_interval('bybit', interval)
        
        endpoint = "/v5/market/kline"
        
        all_klines = []
        current_end = end_time
        max_limit = 1000
        
        while current_end > start_time:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': bybit_interval,
                'start': start_time,
                'end': current_end,
                'limit': max_limit
            }
            
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'result' not in response or 'list' not in response['result'] or len(response['result']['list']) == 0:
                break
            
            batch_klines = []
            for kline in response['result']['list']:
                try:
                    # Bybit returns: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
                    batch_klines.append({
                        'time': int(kline[0]) / 1000,  # Convert to seconds
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"Bybit: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Bybit returns in descending order, so prepend
            all_klines = batch_klines + all_klines
            
            if len(response['result']['list']) < max_limit:
                break
            # Get the earliest timestamp from this batch
            earliest_time = int(response['result']['list'][-1][0])
            current_end = earliest_time - 1
        
        # Sort by time ascending
        all_klines.sort(key=lambda x: x['time'])
        logger.info(f"Bybit Futures: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Convert interval to Bybit format
        bybit_interval = get_exchange_interval('bybit', interval)
        
        endpoint = "/v5/market/kline"
        
        all_klines = []
        current_end = end_time
        max_limit = 1000
        
        while current_end > start_time:
            params = {
                'category': 'spot',
                'symbol': symbol,
                'interval': bybit_interval,
                'start': start_time,
                'end': current_end,
                'limit': max_limit
            }
            
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'result' not in response or 'list' not in response['result'] or len(response['result']['list']) == 0:
                break
            
            batch_klines = []
            for kline in response['result']['list']:
                try:
                    batch_klines.append({
                        'time': int(kline[0]) / 1000,  # Convert to seconds
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"Bybit: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines = batch_klines + all_klines
            
            if len(response['result']['list']) < max_limit:
                break
            earliest_time = int(response['result']['list'][-1][0])
            current_end = earliest_time - 1
        
        all_klines.sort(key=lambda x: x['time'])
        logger.info(f"Bybit Spot: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines