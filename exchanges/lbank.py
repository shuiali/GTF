import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class LBankExchange(BaseExchange):
    """LBank Exchange - Futures price data only (no funding rates).
    
    Uses the internal ticker endpoint to fetch last prices for futures contracts.
    LBank does not provide best bid/ask in its ticker, so 'cu' (last price)
    is used as both bid and ask (approximation).
    
    Response key: 'dataWrapper' contains the ticker groups.
    Ticker fields: 's' = symbol, 'cu' = last price, 'a' = 24h turnover, 'v' = 24h volume.
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('lbank')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://uuapi.rerrkvifj.com"
        self.rate_limit_ms = 100

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize LBank symbol (e.g., 'BTCUSDT') to standard format"""
        return symbol.upper()

    async def _fetch_futures_tickers(self) -> list:
        """Fetch all futures tickers via POST to LBank's internal API.
        
        Returns list of ticker dicts:
            {'s': 'BTCUSDT', 'cu': '69339.6', 'a': '403500431...', 'v': '5814.927', ...}
        """
        url = f"{self.base_url}/cfd/instrment/v1/ticker/24hr/intact"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.lbank.com/',
            'Content-Type': 'application/json',
            'Origin': 'https://www.lbank.com',
            'ex-client-source': 'WEB',
            'ex-client-type': 'WEB',
            'ex-language': 'en-US',
            'source': '4',
        }

        post_data = {"product": ["FUTURES"], "area": "usdt"}

        response = await self._make_request("POST", url, headers=headers, data=post_data)

        tickers = []
        if not isinstance(response, dict):
            logger.warning(f"LBank: Expected dict, got {type(response)}")
            return tickers

        # Response uses 'dataWrapper' (not 'data')
        # Structure: {"code": 200, "dataWrapper": [{"product": "FUTURES", "tickers": [...]}]}
        wrapper = response.get('dataWrapper') or response.get('data') or []
        if not isinstance(wrapper, list):
            logger.warning(f"LBank: No dataWrapper/data list in response: {str(response)[:200]}")
            return tickers

        for group in wrapper:
            if not isinstance(group, dict):
                continue
            if group.get('product') == 'FUTURES':
                group_tickers = group.get('tickers', [])
                if isinstance(group_tickers, list):
                    tickers.extend(group_tickers)

        logger.info(f"LBank: Fetched {len(tickers)} futures tickers")
        return tickers

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Not implemented - LBank is used for price spreads only."""
        return {}

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch last prices for all LBank futures contracts."""
        tickers = await self._fetch_futures_tickers()

        result = {}
        for item in tickers:
            try:
                symbol_raw = item.get('s', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                # 'cu' = current/last price, 'c' = close price (fallback)
                price = float(item.get('cu', 0) or item.get('c', 0) or 0)
                if price > 0:
                    result[symbol] = price
            except Exception as e:
                logger.debug(f"LBank: Error processing price: {str(e)}")
                continue

        logger.info(f"LBank: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes (turnover in USDT)."""
        tickers = await self._fetch_futures_tickers()

        result = {}
        for item in tickers:
            try:
                symbol_raw = item.get('s', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                # 'a' = 24h turnover in quote currency (USDT)
                volume = float(item.get('a', 0) or 0)
                if volume > 0:
                    result[symbol] = volume
            except Exception as e:
                logger.debug(f"LBank: Error processing volume: {str(e)}")
                continue

        logger.info(f"LBank: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch 'order book' for all LBank futures.
        
        LBank does not provide bid/ask prices, so the last price ('cu')
        is used as both bid and ask. This is an approximation.
        """
        tickers = await self._fetch_futures_tickers()

        result = {}
        for item in tickers:
            try:
                symbol_raw = item.get('s', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                last_price = float(item.get('cu', 0) or item.get('c', 0) or 0)
                if last_price > 0:
                    result[symbol] = {'bid': last_price, 'ask': last_price}
            except Exception as e:
                logger.debug(f"LBank: Error processing order book: {str(e)}")
                continue

        logger.info(f"LBank: Successfully fetched {len(result)} order books (last price as bid/ask)")
        return result

    async def get_next_funding_time(self) -> datetime:
        """Calculate next funding time (8-hour cycles)."""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
