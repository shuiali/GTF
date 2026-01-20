import time
import hmac
import hashlib
import base64
import logging
from typing import Dict
from datetime import datetime, timedelta
from .base import BaseExchange, FundingInfo, MarginTokenInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class KucoinExchange(BaseExchange):
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('kucoin')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api-futures.kucoin.com"
        self.passphrase = keys['password']
        self.rate_limit_ms = 10
    
    def _normalize_symbol(self, kc_symbol: str) -> str:
        """Normalize KuCoin symbol to standard format"""
        if kc_symbol == "XBTUSDTM":
            return "BTCUSDT"
        elif kc_symbol.endswith("USDTM"):
            return kc_symbol[:-1]  # Remove 'M'
        else:
            return kc_symbol
    
    def _calculate_next_kucoin_funding_time(self) -> datetime:
        """Calculate next KuCoin funding time - they use different schedule"""
        now = self._get_current_time()
        
        # KuCoin funding times: 04:00, 12:00, 20:00 UTC (8-hour cycle starting at 04:00)
        funding_hours = [4, 12, 20]
        
        current_hour = now.hour
        current_minute = now.minute
        
        # Find next funding hour
        next_funding_hour = None
        for hour in funding_hours:
            if current_hour < hour or (current_hour == hour and current_minute < 0):
                next_funding_hour = hour
                break
        
        # If no funding hour found today, use first hour tomorrow
        if next_funding_hour is None:
            next_funding_hour = funding_hours[0]
            next_funding_time = now.replace(hour=next_funding_hour, minute=0, second=0, microsecond=0)
            next_funding_time += timedelta(days=1)
        else:
            next_funding_time = now.replace(hour=next_funding_hour, minute=0, second=0, microsecond=0)
        
        return next_funding_time

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates in ONE API call"""
        endpoint = "/api/v1/contracts/active"
        response = await self._make_request("GET", f"{self.base_url}{endpoint}")
        
        result = {}
        logger.debug(f"KuCoin funding response: {type(response)}, has data: {'data' in response if isinstance(response, dict) else False}")
        
        if 'data' in response:
            logger.debug(f"KuCoin data length: {len(response['data'])}")
            for item in response['data']:
                try:
                    kc_symbol = item['symbol']
                    symbol = self._normalize_symbol(kc_symbol)
                    
                    funding_rate = float(item.get('fundingFeeRate', 0))
                    # nextFundingRateTime is the number of MILLISECONDS until the next funding
                    funding_time_ms = item.get('nextFundingRateTime')
                    
                    if funding_time_ms:
                        try:
                            # Convert milliseconds-until-funding to actual datetime
                            ms_until_funding = int(funding_time_ms)
                            now = self._get_current_time()
                            
                            # Add milliseconds to current time
                            from datetime import timedelta
                            next_funding_time = now + timedelta(milliseconds=ms_until_funding)
                            logger.debug(f"KuCoin {symbol}: {ms_until_funding}ms until funding, next_time={next_funding_time}")
                                
                        except (ValueError, TypeError, OverflowError) as e:
                            logger.debug(f"KuCoin {symbol}: Error parsing time until funding {funding_time_ms}: {e}")
                            next_funding_time = self._calculate_next_kucoin_funding_time()
                    else:
                        next_funding_time = self._calculate_next_kucoin_funding_time()
                    
                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                    
                    logger.debug(f"KuCoin {symbol}: rate={funding_rate:.6f}, next_time={next_funding_time}")
                    
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"KuCoin: No data field in response: {response}")
        
        logger.info(f"KuCoin: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices in ONE API call"""
        endpoint = "/api/v1/contracts/active"
        response = await self._make_request("GET", f"{self.base_url}{endpoint}")
        
        result = {}
        if 'data' in response:
            for item in response['data']:
                try:
                    kc_symbol = item['symbol']
                    symbol = self._normalize_symbol(kc_symbol)
                    
                    mark_price = item.get('markPrice')
                    if mark_price:
                        result[symbol] = float(mark_price)
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing price {item}: {str(e)}")
                    continue
        
        logger.info(f"KuCoin: Successfully fetched {len(result)} prices")
        return result

    async def get_next_funding_time(self) -> datetime:
        return self._calculate_next_kucoin_funding_time()
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens from KuCoin"""
        # Using /api/v3/margin/symbols for cross margin
        spot_url = "https://api.kucoin.com"
        endpoint = "/api/v3/margin/symbols"
        
        response = await self._make_request("GET", f"{spot_url}{endpoint}")
        
        result = {}
        if 'data' in response and 'items' in response['data']:
            for item in response['data']['items']:
                try:
                    base_currency = item.get('baseCurrency', '')
                    enable_trading = item.get('enableTrading', False)
                    
                    if base_currency and enable_trading:
                        result[base_currency] = MarginTokenInfo(
                            symbol=base_currency,
                            is_borrowable=True,
                            max_leverage=None
                        )
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing margin item: {str(e)}")
                    continue
        
        # Fallback: try isolated margin symbols
        if not result:
            endpoint = "/api/v1/isolated/symbols"
            response = await self._make_request("GET", f"{spot_url}{endpoint}")
            
            if 'data' in response:
                for item in response['data']:
                    try:
                        base_currency = item.get('baseCurrency', '')
                        trade_enable = item.get('tradeEnable', False)
                        
                        if base_currency and trade_enable:
                            max_leverage = float(item.get('maxLeverage', 0)) if item.get('maxLeverage') else None
                            result[base_currency] = MarginTokenInfo(
                                symbol=base_currency,
                                is_borrowable=True,
                                max_leverage=max_leverage
                            )
                    except Exception as e:
                        logger.debug(f"KuCoin: Error processing isolated margin item: {str(e)}")
                        continue
        
        logger.info(f"KuCoin: Successfully fetched {len(result)} margin tokens")
        return result
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch all spot prices from KuCoin"""
        spot_url = "https://api.kucoin.com"
        endpoint = "/api/v1/market/allTickers"
        
        response = await self._make_request("GET", f"{spot_url}{endpoint}")
        
        result = {}
        if 'data' in response and 'ticker' in response['data']:
            for item in response['data']['ticker']:
                try:
                    symbol = item.get('symbol', '')
                    last_price = item.get('last', '')
                    
                    if symbol and last_price:
                        # Convert KuCoin format (BTC-USDT) to standard (BTCUSDT)
                        normalized_symbol = symbol.replace('-', '')
                        price = float(last_price)
                        if price > 0:
                            result[normalized_symbol] = price
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing spot price item: {str(e)}")
                    continue
        
        logger.info(f"KuCoin: Successfully fetched {len(result)} spot prices")
        return result
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 7 days of data
        
        Note: KuCoin Futures API returns max 200 klines per request (despite docs saying 500)
        
        Args:
            symbol: Trading symbol in KuCoin format (e.g., 'XBTUSDTM' or 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 1w)
            start_time: Start timestamp in milliseconds (optional, defaults to 7 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Normalize symbol to KuCoin format
        if symbol == 'BTCUSDT':
            symbol = 'XBTUSDTM'
        elif not symbol.endswith('M'):
            symbol = f"{symbol}M"
        
        # Convert interval to KuCoin futures format (minutes as integer)
        kucoin_granularity = get_exchange_interval('kucoin_futures', interval)
        
        endpoint = "/api/v1/kline/query"
        
        all_klines = []
        max_limit = 200  # KuCoin actually returns max 200 per request
        
        # Calculate interval in milliseconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_ms = interval_minutes * 60 * 1000
        
        # Work forwards from start_time to end_time
        current_start = start_time
        
        while current_start < end_time:
            # Calculate chunk end (max 200 candles)
            chunk_end = min(end_time, current_start + (max_limit * interval_ms))
            
            params = {
                'symbol': symbol,
                'granularity': kucoin_granularity,
                'from': current_start,
                'to': chunk_end
            }
            
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                break
            
            for kline in response['data']:
                try:
                    # KuCoin futures returns: [timestamp, open, high, low, close, volume, turnover]
                    all_klines.append({
                        'time': float(kline[0]) / 1000,  # Convert to seconds
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing kline {kline}: {str(e)}")
                    continue
            
            # Move forward based on last timestamp received
            last_time = max(int(k[0]) for k in response['data'])
            if last_time >= end_time:
                break
            current_start = last_time + interval_ms
        
        # Remove duplicates by timestamp
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"KuCoin Futures: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 7 days of data
        
        Note: KuCoin spot returns data in DESCENDING order (newest first)
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w)
            start_time: Start timestamp in SECONDS (optional, defaults to 7 days ago)
            end_time: End timestamp in SECONDS (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps_seconds, get_exchange_interval, INTERVAL_MINUTES
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps_seconds()
        
        # Ensure symbol has dash format
        if '-' not in symbol:
            # Convert BTCUSDT to BTC-USDT
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}-USDT"
        
        # Convert interval to KuCoin spot format (1min, 1hour, 1day, etc.)
        kucoin_interval = get_exchange_interval('kucoin_spot', interval)
        
        spot_url = "https://api.kucoin.com"
        endpoint = "/api/v1/market/candles"
        
        all_klines = []
        max_limit = 1500
        
        # Calculate interval in seconds for pagination
        interval_minutes = INTERVAL_MINUTES.get(interval, 60)
        interval_seconds = interval_minutes * 60
        
        # KuCoin spot returns data in descending order (newest first)
        # So we need to paginate backwards from end_time
        current_end = end_time
        
        while current_end > start_time:
            params = {
                'symbol': symbol,
                'type': kucoin_interval,
                'startAt': start_time,
                'endAt': current_end
            }
            
            response = await self._make_request("GET", f"{spot_url}{endpoint}", params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                break
            
            for kline in response['data']:
                try:
                    # KuCoin spot returns: [timestamp, open, close, high, low, volume, turnover]
                    all_klines.append({
                        'time': float(kline[0]),  # Already in seconds
                        'open': float(kline[1]),
                        'high': float(kline[3]),
                        'low': float(kline[4]),
                        'close': float(kline[2]),
                        'volume': float(kline[5])
                    })
                except Exception as e:
                    logger.debug(f"KuCoin: Error processing kline {kline}: {str(e)}")
                    continue
            
            if len(response['data']) < max_limit:
                break
            
            # KuCoin returns in descending order, so the last item is the oldest
            earliest_time = int(response['data'][-1][0])
            current_end = earliest_time - 1
        
        # Remove duplicates and sort by time ascending
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline['time'] not in seen:
                seen.add(kline['time'])
                unique_klines.append(kline)
        
        unique_klines.sort(key=lambda x: x['time'])
        logger.info(f"KuCoin Spot: Fetched {len(unique_klines)} klines for {symbol}")
        return unique_klines
