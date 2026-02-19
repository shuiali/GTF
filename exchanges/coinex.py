import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class CoinExExchange(BaseExchange):
    """CoinEx Exchange API Implementation for Futures Arbitrage
    
    API docs: https://api.coinex.com/v2
    Note: CoinEx does not provide a bulk best-bid/ask endpoint for futures,
    so we use the last price from the ticker as both bid and ask.
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('coinex')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api.coinex.com/v2"
        self.rate_limit_ms = 50

    def _normalize_symbol(self, market: str) -> str:
        """Normalize CoinEx symbol (e.g., 'BTCUSDT') to standard format.
        CoinEx futures markets already use format like BTCUSDT."""
        return market.upper()

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates using the futures ticker endpoint.
        
        CoinEx /futures/ticker returns mark_price for all markets.
        Funding rate is not directly in the ticker, so we return 0 for funding rates.
        This exchange is primarily used for price spread detection.
        """
        # CoinEx does not have a bulk funding rate endpoint, return empty
        # This exchange is used for price spreads, not funding arbitrage
        logger.info("CoinEx: Funding rates not available via bulk endpoint (spread-only exchange)")
        return {}

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures prices using /futures/ticker"""
        endpoint = "/futures/ticker"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('code') == 0:
            data = response.get('data', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        market = item.get('market', '')
                        if not market:
                            continue
                        symbol = self._normalize_symbol(market)
                        price = float(item.get('last', 0))
                        if price > 0:
                            result[symbol] = price
                    except Exception as e:
                        logger.debug(f"CoinEx: Error processing price item {item}: {str(e)}")
                        continue
        else:
            logger.warning(f"CoinEx: Unexpected prices response: {str(response)[:200]}")

        logger.info(f"CoinEx: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT using /futures/ticker"""
        endpoint = "/futures/ticker"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('code') == 0:
            data = response.get('data', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        market = item.get('market', '')
                        if not market:
                            continue
                        symbol = self._normalize_symbol(market)
                        # 'value' is the 24h filled value (turnover in USDT)
                        volume = float(item.get('value', 0))
                        if volume > 0:
                            result[symbol] = volume
                    except Exception as e:
                        logger.debug(f"CoinEx: Error processing volume item: {str(e)}")
                        continue
        else:
            logger.warning(f"CoinEx: Unexpected volumes response: {str(response)[:200]}")

        logger.info(f"CoinEx: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices for all futures.
        
        CoinEx does not have a bulk bid/ask endpoint for futures,
        so we use the last price as both bid and ask (approximation).
        """
        endpoint = "/futures/ticker"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        result = {}
        if isinstance(response, dict) and response.get('code') == 0:
            data = response.get('data', [])
            if isinstance(data, list):
                for item in data:
                    try:
                        market = item.get('market', '')
                        if not market:
                            continue
                        symbol = self._normalize_symbol(market)
                        last_price = float(item.get('last', 0))
                        if last_price > 0:
                            # Use last price as both bid and ask
                            result[symbol] = {'bid': last_price, 'ask': last_price}
                    except Exception as e:
                        logger.debug(f"CoinEx: Error processing order book item: {str(e)}")
                        continue
        else:
            logger.warning(f"CoinEx: Unexpected order book response: {str(response)[:200]}")

        logger.info(f"CoinEx: Successfully fetched {len(result)} order books (last price as bid/ask)")
        return result

    async def get_next_funding_time(self) -> datetime:
        """CoinEx uses 8-hour funding intervals"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
