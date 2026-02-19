import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class BloFinExchange(BaseExchange):
    """BloFin Exchange API Implementation for Futures Arbitrage
    
    API endpoint: https://blofin.com/uapi/v3/market/ticker
    BloFin provides bid_price/ask_price in its ticker endpoint.
    Symbol format: BTC-USDC -> BTCUSDC, BTC-USDT -> BTCUSDT
    
    Note: BloFin has both USDT and USDC pairs. We normalize both.
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('blofin')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://blofin.com"
        self.rate_limit_ms = 100

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize BloFin symbol (e.g., 'BTC-USDC' or 'BTC-USDT') to standard format (BTCUSDT).
        Convert USDC pairs to USDT equivalent for cross-exchange matching."""
        normalized = symbol.replace('-', '').upper()
        # Convert USDC pairs to USDT for matching with other exchanges
        if normalized.endswith('USDC'):
            normalized = normalized[:-4] + 'USDT'
        return normalized

    async def _fetch_ticker(self) -> list:
        """Fetch all futures tickers from BloFin"""
        endpoint = "/uapi/v3/market/ticker"
        url = f"{self.base_url}{endpoint}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://blofin.com/futures/en/BTC-USDT',
        }

        response = await self._make_request("GET", url, headers=headers)

        if isinstance(response, dict):
            if response.get('code') == 200 or response.get('msg') == 'success':
                data = response.get('data', [])
                if isinstance(data, list):
                    return data
            # Try alternate structure
            data = response.get('data', [])
            if isinstance(data, list):
                return data

        logger.warning(f"BloFin: Unexpected ticker response: {str(response)[:200]}")
        return []

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates from BloFin.
        BloFin ticker does not include funding rate in the ticker endpoint.
        This exchange is primarily used for price spread detection."""
        logger.info("BloFin: Funding rates not available via ticker endpoint (spread-only exchange)")
        return {}

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures last prices from BloFin"""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                # 'last' is the last traded price, 'close' is also available
                price = float(item.get('last', 0) or item.get('close', 0) or 0)
                if price > 0:
                    result[symbol] = price
            except Exception as e:
                logger.debug(f"BloFin: Error processing price item: {str(e)}")
                continue

        logger.info(f"BloFin: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT from BloFin.
        'amount' field is the 24h turnover in quote currency."""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                # 'amount' is 24h turnover in quote currency
                volume = float(item.get('amount', 0) or 0)
                if volume > 0:
                    result[symbol] = volume
            except Exception as e:
                logger.debug(f"BloFin: Error processing volume item: {str(e)}")
                continue

        logger.info(f"BloFin: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices from BloFin ticker.
        BloFin provides ask_price and bid_price in the ticker response."""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                bid_price = float(item.get('bid_price', 0) or 0)
                ask_price = float(item.get('ask_price', 0) or 0)

                if bid_price > 0 and ask_price > 0:
                    result[symbol] = {'bid': bid_price, 'ask': ask_price}
            except Exception as e:
                logger.debug(f"BloFin: Error processing order book item: {str(e)}")
                continue

        logger.info(f"BloFin: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        """BloFin uses 8-hour funding intervals"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
