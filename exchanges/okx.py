import asyncio
import time
import hmac
import base64
import hashlib
import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class OKXExchange(BaseExchange):
    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('okx')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://www.okx.com"
        self.passphrase = keys['password']
        self.rate_limit_ms = 30  # Faster rate limit
    
    def _normalize_symbol(self, inst_id: str) -> str:
        """Normalize OKX instrument ID to standard format"""
        return inst_id.replace('-SWAP', '').replace('-', '')
    
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates using batch processing with NO delays"""
        # First get all SWAP instruments
        endpoint = "/api/v5/public/instruments"
        params = {"instType": "SWAP"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        if 'data' not in response:
            logger.warning("OKX: No instruments data found")
            return {}
        
        # Get all USDT perpetual contracts
        usdt_instruments = []
        for item in response['data']:
            if item['instId'].endswith('-USDT-SWAP'):
                usdt_instruments.append(item['instId'])
        
        logger.info(f"OKX: Found {len(usdt_instruments)} USDT perpetual contracts")
        
        result = {}
        
        # Process instruments in smaller batches but faster
        batch_size = 10  # Smaller batches
        for i in range(0, len(usdt_instruments), batch_size):
            batch = usdt_instruments[i:i+batch_size]
            
            # Create tasks for this batch
            tasks = []
            for inst_id in batch:
                task = asyncio.create_task(self._fetch_single_funding_rate(inst_id))
                tasks.append(task)
            
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, funding_info in enumerate(batch_results):
                    if isinstance(funding_info, Exception):
                        logger.debug(f"OKX: Error fetching {batch[j]}: {str(funding_info)}")
                        continue
                    elif funding_info:
                        result[funding_info.symbol] = funding_info
                
                # Minimal wait between batches
                if i + batch_size < len(usdt_instruments):
                    await asyncio.sleep(0.1)  # Just 0.1 second
                    
            except Exception as e:
                logger.warning(f"OKX: Batch error for instruments {i}-{i+batch_size}: {str(e)}")
                continue
        
        logger.info(f"OKX: Successfully fetched {len(result)} funding rates")
        return result
    
    async def _fetch_single_funding_rate(self, inst_id: str) -> FundingInfo:
        """Fetch funding rate for a single instrument"""
        try:
            endpoint = "/api/v5/public/funding-rate"
            params = {"instId": inst_id}
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'data' in response and response['data']:
                funding_item = response['data'][0]
                symbol = self._normalize_symbol(inst_id)
                funding_rate = float(funding_item['fundingRate'])
                next_funding_time = self._timestamp_to_datetime(int(funding_item['fundingTime']))
                
                return FundingInfo(
                    symbol=symbol,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding_time
                )
            
            # Minimal rate limiting
            await asyncio.sleep(0.03)  # Just 30ms
            
        except Exception as e:
            logger.debug(f"OKX: Error processing {inst_id}: {str(e)}")
            raise e
        
        return None

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL prices in ONE API call"""
        endpoint = "/api/v5/public/mark-price"
        params = {"instType": "SWAP"}
        response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
        
        result = {}
        if 'data' in response:
            for item in response['data']:
                try:
                    inst_id = item['instId']
                    if inst_id.endswith('-USDT-SWAP'):
                        symbol = self._normalize_symbol(inst_id)
                        result[symbol] = float(item['markPx'])
                except Exception as e:
                    logger.debug(f"OKX: Error processing price {item}: {str(e)}")
                    continue
        
        logger.info(f"OKX: Successfully fetched {len(result)} prices")
        return result

    async def get_next_funding_time(self) -> datetime:
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
    
    async def get_klines_futures(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for futures - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT-SWAP' or 'BTCUSDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Normalize symbol to OKX format
        if not symbol.endswith('-SWAP'):
            # Convert BTCUSDT to BTC-USDT-SWAP
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}-USDT-SWAP"
        
        # Convert interval to OKX format (1m, 1H, 1D, etc.)
        okx_interval = get_exchange_interval('okx', interval)
        
        # Use history-candles endpoint for historical data
        endpoint = "/api/v5/market/history-candles"
        
        all_klines = []
        current_end = end_time
        max_limit = 300  # OKX max limit is 300
        
        while current_end > start_time:
            params = {
                'instId': symbol,
                'bar': okx_interval,
                'after': str(current_end),  # Pagination: get data before this timestamp
                'limit': str(max_limit)
            }
            
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                break
            
            batch_klines = []
            for kline in response['data']:
                try:
                    kline_time = int(kline[0])
                    if kline_time >= start_time:
                        batch_klines.append({
                            'time': kline_time / 1000,  # Convert to seconds
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                except Exception as e:
                    logger.debug(f"OKX: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines = batch_klines + all_klines  # Prepend since we're going backwards
            
            if len(response['data']) < max_limit:
                break
            # Get the earliest timestamp from this batch
            earliest_time = int(response['data'][-1][0])
            current_end = earliest_time
        
        # Sort by time ascending
        all_klines.sort(key=lambda x: x['time'])
        logger.info(f"OKX Futures: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines
    
    async def get_klines_spot(self, symbol: str, interval: str = '1h', start_time: int = None, end_time: int = None) -> list:
        """Fetch kline/candlestick data for spot - 1 MONTH of data
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT' or 'BTCUSDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M)
            start_time: Start timestamp in milliseconds (optional, defaults to 30 days ago)
            end_time: End timestamp in milliseconds (optional, defaults to now)
        
        Returns:
            List of klines: [{time, open, high, low, close, volume}, ...]
        """
        from .klines_mixin import get_one_month_timestamps, get_exchange_interval
        
        if start_time is None or end_time is None:
            start_time, end_time = get_one_month_timestamps()
        
        # Normalize symbol to OKX spot format (without -SWAP)
        if symbol.endswith('-SWAP'):
            symbol = symbol.replace('-SWAP', '')
        elif not '-' in symbol:
            # Convert BTCUSDT to BTC-USDT
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                symbol = f"{base}-USDT"
        
        # Convert interval to OKX format
        okx_interval = get_exchange_interval('okx', interval)
        
        # Use history-candles endpoint for historical data
        endpoint = "/api/v5/market/history-candles"
        
        all_klines = []
        current_end = end_time
        max_limit = 300
        
        while current_end > start_time:
            params = {
                'instId': symbol,
                'bar': okx_interval,
                'after': str(current_end),
                'limit': str(max_limit)
            }
            
            response = await self._make_request("GET", f"{self.base_url}{endpoint}", params=params)
            
            if 'data' not in response or not isinstance(response['data'], list) or len(response['data']) == 0:
                break
            
            batch_klines = []
            for kline in response['data']:
                try:
                    kline_time = int(kline[0])
                    if kline_time >= start_time:
                        batch_klines.append({
                            'time': kline_time / 1000,  # Convert to seconds
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                except Exception as e:
                    logger.debug(f"OKX: Error processing kline {kline}: {str(e)}")
                    continue
            
            all_klines = batch_klines + all_klines
            
            if len(response['data']) < max_limit:
                break
            earliest_time = int(response['data'][-1][0])
            current_end = earliest_time
        
        all_klines.sort(key=lambda x: x['time'])
        logger.info(f"OKX Spot: Fetched {len(all_klines)} klines for {symbol}")
        return all_klines