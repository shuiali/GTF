import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class XTExchange(BaseExchange):
    """XT Exchange API Implementation for Futures Arbitrage
    
    API docs: https://fapi.xt.com
    XT provides bid/ask prices via the agg-tickers endpoint (ap=ask price, bp=bid price).
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('xt')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://fapi.xt.com"
        self.rate_limit_ms = 100

    def _normalize_symbol(self, xt_symbol: str) -> str:
        """Normalize XT symbol (e.g., 'btc_usdt') to standard format (BTCUSDT)"""
        return xt_symbol.replace('_', '').upper()

    async def _fetch_active_symbols(self) -> set:
        """Fetch active tradable futures symbols from /future/market/v1/public/q/tickers."""
        endpoint = "/future/market/v1/public/q/tickers"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        active_symbols = set()
        if isinstance(response, dict) and response.get('returnCode') == 0:
            data = response.get('result', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        xt_symbol = item.get('s', '')
                        if not xt_symbol:
                            continue
                        active_symbols.add(self._normalize_symbol(xt_symbol))
                    except Exception as e:
                        logger.debug(f"XT: Error processing active symbol {item}: {str(e)}")
                        continue
        else:
            logger.warning(f"XT: Unexpected active symbols response: {str(response)[:200]}")

        return active_symbols

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """XT does not provide a bulk funding rate endpoint.
        This exchange is primarily used for price spread detection."""
        logger.info("XT: Funding rates not available via bulk endpoint (spread-only exchange)")
        return {}

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures prices using /future/market/v1/public/q/agg-tickers"""
        active_symbols = await self._fetch_active_symbols()
        endpoint = "/future/market/v1/public/q/agg-tickers"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('returnCode') == 0:
            data = response.get('result', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        xt_symbol = item.get('s', '')
                        if not xt_symbol:
                            continue
                        symbol = self._normalize_symbol(xt_symbol)
                        if active_symbols and symbol not in active_symbols:
                            continue
                        # 'c' = latest/close price
                        price = float(item.get('c', 0))
                        if price > 0:
                            result[symbol] = price
                    except Exception as e:
                        logger.debug(f"XT: Error processing price item {item}: {str(e)}")
                        continue
        else:
            logger.warning(f"XT: Unexpected prices response: {str(response)[:200]}")

        logger.info(f"XT: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes using /future/market/v1/public/q/agg-tickers"""
        active_symbols = await self._fetch_active_symbols()
        endpoint = "/future/market/v1/public/q/agg-tickers"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('returnCode') == 0:
            data = response.get('result', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        xt_symbol = item.get('s', '')
                        if not xt_symbol:
                            continue
                        symbol = self._normalize_symbol(xt_symbol)
                        if active_symbols and symbol not in active_symbols:
                            continue
                        # 'v' = 24h turnover (value in USDT)
                        volume = float(item.get('v', 0))
                        if volume > 0:
                            result[symbol] = volume
                    except Exception as e:
                        logger.debug(f"XT: Error processing volume item: {str(e)}")
                        continue
        else:
            logger.warning(f"XT: Unexpected volumes response: {str(response)[:200]}")

        logger.info(f"XT: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices for all futures using agg-tickers.
        
        XT agg-tickers provides:
        - 'ap' = ask price
        - 'bp' = bid price
        """
        active_symbols = await self._fetch_active_symbols()
        endpoint = "/future/market/v1/public/q/agg-tickers"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('returnCode') == 0:
            data = response.get('result', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        xt_symbol = item.get('s', '')
                        if not xt_symbol:
                            continue
                        symbol = self._normalize_symbol(xt_symbol)
                        if active_symbols and symbol not in active_symbols:
                            continue

                        bid_price = float(item.get('bp', 0))
                        ask_price = float(item.get('ap', 0))

                        if bid_price > 0 and ask_price > 0:
                            result[symbol] = {'bid': bid_price, 'ask': ask_price}
                    except Exception as e:
                        logger.debug(f"XT: Error processing order book item: {str(e)}")
                        continue
        else:
            logger.warning(f"XT: Unexpected order book response: {str(response)[:200]}")

        logger.info(f"XT: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        """XT uses 8-hour funding intervals"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
