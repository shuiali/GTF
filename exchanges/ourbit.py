import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class OurBitExchange(BaseExchange):
    """OurBit Exchange API Implementation for Futures Arbitrage
    
    API endpoint: https://futures.ourbit.com/api/v1/contract/ticker
    OurBit provides bid1/ask1 (best bid/ask) in its ticker endpoint.
    Symbol format: BTC_USDT -> BTCUSDT
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('ourbit')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://futures.ourbit.com"
        self.rate_limit_ms = 100

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize OurBit symbol (e.g., 'BTC_USDT') to standard format (BTCUSDT)"""
        return symbol.replace('_', '').upper()

    async def _fetch_ticker(self) -> list:
        """Fetch all futures tickers from OurBit"""
        endpoint = "/api/v1/contract/ticker"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        if isinstance(response, dict) and response.get('success') is True:
            data = response.get('data', [])
            if isinstance(data, list):
                return data
        elif isinstance(response, dict) and response.get('code') == 0:
            data = response.get('data', [])
            if isinstance(data, list):
                return data

        logger.warning(f"OurBit: Unexpected ticker response: {str(response)[:200]}")
        return []

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch funding rates from OurBit ticker endpoint.
        The ticker includes fundingRate for each contract."""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                funding_rate = float(item.get('fundingRate', 0) or 0)

                # OurBit provides timestamp in ms
                ts = item.get('timestamp')
                if ts:
                    next_funding_time = self._timestamp_to_datetime(int(ts), is_milliseconds=True)
                else:
                    next_funding_time = self._get_current_time()

                result[symbol] = FundingInfo(
                    symbol=symbol,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding_time
                )
            except Exception as e:
                logger.debug(f"OurBit: Error processing funding rate item: {str(e)}")
                continue

        logger.info(f"OurBit: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures last prices from OurBit"""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)
                price = float(item.get('lastPrice', 0) or 0)
                if price > 0:
                    result[symbol] = price
            except Exception as e:
                logger.debug(f"OurBit: Error processing price item: {str(e)}")
                continue

        logger.info(f"OurBit: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT from OurBit.
        amount24 is the 24h turnover in USDT."""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)
                # amount24 = 24h turnover in quote currency (USDT)
                volume = float(item.get('amount24', 0) or item.get('volume24', 0) or 0)
                if volume > 0:
                    result[symbol] = volume
            except Exception as e:
                logger.debug(f"OurBit: Error processing volume item: {str(e)}")
                continue

        logger.info(f"OurBit: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices from OurBit ticker.
        OurBit provides bid1 (best bid) and ask1 (best ask) in the ticker."""
        data = await self._fetch_ticker()

        result = {}
        for item in data:
            try:
                symbol_raw = item.get('symbol', '')
                if not symbol_raw:
                    continue
                symbol = self._normalize_symbol(symbol_raw)

                bid_price = float(item.get('bid1', 0) or 0)
                ask_price = float(item.get('ask1', 0) or 0)

                if bid_price > 0 and ask_price > 0:
                    result[symbol] = {'bid': bid_price, 'ask': ask_price}
            except Exception as e:
                logger.debug(f"OurBit: Error processing order book item: {str(e)}")
                continue

        logger.info(f"OurBit: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        """OurBit uses 8-hour funding intervals"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
