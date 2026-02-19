import time
import hmac
import hashlib
import logging
from typing import Dict
from datetime import datetime
import urllib.parse
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class BinanceExchange(BaseExchange):
    """Binance Exchange API Implementation for Funding Rates"""
    
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('binance')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://fapi.binance.com"
        self.spot_url = "https://api.binance.com"
        self.rate_limit_ms = 200  # More conservative
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates in ONE API call"""
        endpoint = "/fapi/v1/premiumIndex"
        url = f"{self.base_url}{endpoint}"
        
        response = await self._make_request("GET", url)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    symbol = item['symbol']
                    funding_rate = float(item['lastFundingRate'])
                    next_funding_time = self._timestamp_to_datetime(int(item['nextFundingTime']))
                    predicted_rate = float(item.get('predictedFundingRate', 0.0))
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time,
                        predicted_rate=predicted_rate
                    )
                except Exception as e:
                    logger.debug(f"Binance: Error processing item {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"Binance: Expected list, got {type(response)}: {response}")
        
        logger.info(f"Binance: Successfully fetched {len(result)} funding rates")
        return result
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices in ONE API call using /fapi/v2/ticker/price"""
        endpoint = "/fapi/v2/ticker/price"
        url = f"{self.base_url}{endpoint}"
        
        response = await self._make_request("GET", url)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    symbol = item.get('symbol', '')
                    price = float(item.get('price', 0))
                    if symbol and price > 0:
                        result[symbol] = price
                except Exception as e:
                    logger.debug(f"Binance: Error processing price item {item}: {str(e)}")
                    continue
        elif isinstance(response, dict) and 'symbol' in response:
            # Single symbol response
            try:
                result[response['symbol']] = float(response['price'])
            except Exception as e:
                logger.debug(f"Binance: Error processing single price: {str(e)}")
        
        logger.info(f"Binance: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT using /fapi/v1/ticker/24hr"""
        endpoint = "/fapi/v1/ticker/24hr"
        url = f"{self.base_url}{endpoint}"
        
        response = await self._make_request("GET", url)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    symbol = item.get('symbol', '')
                    # quoteVolume is the 24h volume in USDT
                    volume = float(item.get('quoteVolume', 0))
                    if symbol and volume > 0:
                        result[symbol] = volume
                except Exception as e:
                    logger.debug(f"Binance: Error processing volume item: {str(e)}")
                    continue
        
        logger.info(f"Binance: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices using /fapi/v1/ticker/bookTicker"""
        endpoint = "/fapi/v1/ticker/bookTicker"
        url = f"{self.base_url}{endpoint}"
        
        response = await self._make_request("GET", url)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    symbol = item.get('symbol', '')
                    bid_price = float(item.get('bidPrice', 0))
                    ask_price = float(item.get('askPrice', 0))
                    if symbol and bid_price > 0 and ask_price > 0:
                        result[symbol] = {'bid': bid_price, 'ask': ask_price}
                except Exception as e:
                    logger.debug(f"Binance: Error processing order book item: {str(e)}")
                    continue
        
        logger.info(f"Binance: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch all margin trading pairs from Binance using /sapi/v1/margin/allPairs with authentication"""
        endpoint = "/sapi/v1/margin/allPairs"
        
        # Create authenticated request
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{self.spot_url}{endpoint}?{query_string}&signature={signature}"
        
        # Add authentication headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        response = await self._make_request("GET", url, headers=headers)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    # Check if margin trading is enabled
                    is_margin_trade = item.get('isMarginTrade', False)
                    if is_margin_trade:
                        base = item.get('base', '')
                        if base and base not in result:
                            result[base] = MarginTokenInfo(
                                symbol=base,
                                is_borrowable=True,
                                max_leverage=None
                            )
                except Exception as e:
                    logger.debug(f"Binance: Error processing margin pair item: {str(e)}")
                    continue
        else:
            logger.warning(f"Binance: Unexpected margin response type: {type(response)}, response: {response}")
        
        logger.info(f"Binance: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from Binance"""
        endpoint = "/api/v3/ticker/price"
        url = f"{self.spot_url}{endpoint}"
        
        response = await self._make_request("GET", url)
        
        result = {}
        if isinstance(response, list):
            for item in response:
                try:
                    symbol = item.get('symbol', '')
                    price = float(item.get('price', 0))
                    if symbol and price > 0:
                        result[symbol] = price
                except Exception as e:
                    logger.debug(f"Binance: Error processing spot price item {item}: {str(e)}")
                    continue
        
        logger.info(f"Binance: Successfully fetched {len(result)} spot prices")
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
        from .klines_mixin import get_one_month_timestamps
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        endpoint = "/fapi/v1/klines"
        url = f"{self.base_url}{endpoint}"
        
        all_klines = []
        current_start = start_time
        max_limit = 1500
        
        while current_start < end_time:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_time,
                'limit': max_limit
            }
            
            response = await self._make_request("GET", url, params=params)
            
            if not isinstance(response, list) or len(response) == 0:
                break
            
            for kline in response:
                try:
                    all_klines.append({
                        'time': int(kline[0]) / 1000,  # Convert to seconds
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"Binance: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Move to next batch
            if len(response) < max_limit:
                break
            last_time = int(response[-1][0])
            current_start = last_time + 1
        
        logger.info(f"Binance Futures: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        endpoint = "/api/v3/klines"
        url = f"{self.spot_url}{endpoint}"
        
        all_klines = []
        current_start = start_time
        max_limit = 1000
        
        while current_start < end_time:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_time,
                'limit': max_limit
            }
            
            response = await self._make_request("GET", url, params=params)
            
            if not isinstance(response, list) or len(response) == 0:
                break
            
            for kline in response:
                try:
                    all_klines.append({
                        'time': int(kline[0]) / 1000,  # Convert to seconds
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"Binance: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Move to next batch
            if len(response) < max_limit:
                break
            last_time = int(response[-1][0])
            current_start = last_time + 1
        
        logger.info(f"Binance Spot: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines