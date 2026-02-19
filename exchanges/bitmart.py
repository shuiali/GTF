import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class BitMartExchange(BaseExchange):
    """BitMart Exchange API Implementation for Futures Arbitrage
    
    API docs: https://api-cloud-v2.bitmart.com
    Note: BitMart does not provide a bulk best-bid/ask endpoint for futures,
    so we use the last price from contract details as both bid and ask.
    BitMart DOES provide funding_rate and expected_funding_rate in contract details.
    """

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('bitmart')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://api-cloud-v2.bitmart.com"
        self.rate_limit_ms = 100

    def _normalize_symbol(self, bm_symbol: str) -> str:
        """Normalize BitMart symbol (e.g., 'BTCUSDT') to standard format.
        BitMart futures symbols are already in format like BTCUSDT."""
        return bm_symbol.upper()

    async def _fetch_contract_details(self) -> list:
        """Fetch all contract details from BitMart (single API call).
        Returns the list of symbol objects from the response."""
        endpoint = "/contract/public/details"
        url = f"{self.base_url}{endpoint}"

        response = await self._make_request("GET", url)

        if isinstance(response, dict) and response.get('code') == 1000:
            data = response.get('data', {})
            symbols = data.get('symbols', [])
            if isinstance(symbols, list):
                return symbols
            else:
                logger.warning(f"BitMart: 'symbols' is not a list: {type(symbols)}")
        else:
            logger.warning(f"BitMart: Unexpected response: {str(response)[:200]}")

        return []

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates from BitMart contract details.
        
        BitMart provides funding_rate and expected_funding_rate in the
        /contract/public/details endpoint.
        """
        symbols_data = await self._fetch_contract_details()

        result = {}
        for item in symbols_data:
            try:
                symbol = item.get('symbol', '')
                if not symbol:
                    continue

                # Only include active (Trading) contracts
                status = item.get('status', '')
                if status != 'Trading':
                    continue

                # Only perpetual contracts (product_type=1)
                product_type = item.get('product_type')
                if product_type != 1:
                    continue

                normalized = self._normalize_symbol(symbol)
                funding_rate = float(item.get('funding_rate', 0))
                predicted_rate = float(item.get('expected_funding_rate', 0))

                # Calculate next funding time from funding_interval_hours
                funding_interval = item.get('funding_interval_hours', 8)
                now = self._get_current_time()
                next_hour = ((now.hour // funding_interval) + 1) * funding_interval
                next_funding_time = now.replace(
                    hour=next_hour % 24, minute=0, second=0, microsecond=0
                )

                result[normalized] = FundingInfo(
                    symbol=normalized,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding_time,
                    predicted_rate=predicted_rate
                )
            except Exception as e:
                logger.debug(f"BitMart: Error processing funding rate {item.get('symbol', '?')}: {str(e)}")
                continue

        logger.info(f"BitMart: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures prices from BitMart contract details."""
        symbols_data = await self._fetch_contract_details()

        result = {}
        for item in symbols_data:
            try:
                symbol = item.get('symbol', '')
                if not symbol:
                    continue
                status = item.get('status', '')
                if status != 'Trading':
                    continue
                product_type = item.get('product_type')
                if product_type != 1:
                    continue

                normalized = self._normalize_symbol(symbol)
                price = float(item.get('last_price', 0))
                if price > 0:
                    result[normalized] = price
            except Exception as e:
                logger.debug(f"BitMart: Error processing price item: {str(e)}")
                continue

        logger.info(f"BitMart: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes from BitMart contract details.
        Uses turnover_24h which is the 24h turnover value."""
        symbols_data = await self._fetch_contract_details()

        result = {}
        for item in symbols_data:
            try:
                symbol = item.get('symbol', '')
                if not symbol:
                    continue
                status = item.get('status', '')
                if status != 'Trading':
                    continue
                product_type = item.get('product_type')
                if product_type != 1:
                    continue

                normalized = self._normalize_symbol(symbol)
                # turnover_24h is the 24h value in quote currency (USDT)
                volume = float(item.get('turnover_24h', 0))
                if volume > 0:
                    result[normalized] = volume
            except Exception as e:
                logger.debug(f"BitMart: Error processing volume item: {str(e)}")
                continue

        logger.info(f"BitMart: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices for all futures.
        
        BitMart does not provide a bulk bid/ask endpoint for futures,
        so we use the last_price as both bid and ask (approximation).
        """
        symbols_data = await self._fetch_contract_details()

        result = {}
        for item in symbols_data:
            try:
                symbol = item.get('symbol', '')
                if not symbol:
                    continue
                status = item.get('status', '')
                if status != 'Trading':
                    continue
                product_type = item.get('product_type')
                if product_type != 1:
                    continue

                normalized = self._normalize_symbol(symbol)
                last_price = float(item.get('last_price', 0))
                if last_price > 0:
                    # Use last price as both bid and ask
                    result[normalized] = {'bid': last_price, 'ask': last_price}
            except Exception as e:
                logger.debug(f"BitMart: Error processing order book item: {str(e)}")
                continue

        logger.info(f"BitMart: Successfully fetched {len(result)} order books (last price as bid/ask)")
        return result

    async def get_next_funding_time(self) -> datetime:
        """BitMart uses 8-hour funding intervals"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        return now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
