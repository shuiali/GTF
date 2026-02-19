import time
import logging
from typing import Dict
from datetime import datetime
from .base import BaseExchange, FundingInfo
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class BingXExchange(BaseExchange):
    """BingX Exchange API Implementation for Futures Arbitrage"""

    def __init__(self):
        config = ConfigLoader()
        keys = config.get_exchange_keys('bingx')
        super().__init__(api_key=keys['api_key'], api_secret=keys['secret'])
        self.base_url = "https://open-api.bingx.com"
        self.rate_limit_ms = 20  # 500 requests per 10 seconds = 20ms per request

    def _normalize_symbol(self, bx_symbol: str) -> str:
        """Normalize BingX symbol (BTC-USDT) to standard format (BTCUSDT)"""
        return bx_symbol.replace('-', '')

    def _to_bingx_symbol(self, symbol: str) -> str:
        """Convert standard symbol (BTCUSDT) to BingX format (BTC-USDT)"""
        if '-' in symbol:
            return symbol
        if symbol.endswith('USDT'):
            return f"{symbol[:-4]}-USDT"
        return symbol

    async def _make_bingx_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a public market data request to BingX (no signature needed)"""
        url = f"{self.base_url}{endpoint}"

        # BingX requires timestamp even for public endpoints
        if params is None:
            params = {}
        params['timestamp'] = str(int(time.time() * 1000))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }

        await self._init_session()

        try:
            async with self.session.request("GET", url, params=params, headers=headers) as response:
                if response.status == 200:
                    try:
                        result = await response.json()
                        return result if result is not None else {}
                    except Exception as e:
                        logger.error(f"BingX: JSON decode error for {url}: {str(e)}")
                        return {}
                else:
                    text = await response.text()
                    logger.warning(f"BingX: HTTP {response.status} for {url}: {text[:200]}")
                    return {}
        except Exception as e:
            logger.debug(f"BingX: Request error for {url}: {str(e)}")
            return {}

    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        """Fetch ALL funding rates using premiumIndex endpoint (no symbol = all)"""
        endpoint = "/openApi/swap/v2/quote/premiumIndex"
        response = await self._make_bingx_request(endpoint)

        result = {}
        if response.get('code') == 0 and 'data' in response:
            data = response['data']
            # Can be a single dict or a list
            items = data if isinstance(data, list) else [data]

            for item in items:
                try:
                    bx_symbol = item.get('symbol', '')
                    if not bx_symbol:
                        continue

                    symbol = self._normalize_symbol(bx_symbol)
                    funding_rate = float(item.get('lastFundingRate', 0))

                    # nextFundingTime is milliseconds timestamp
                    next_funding_ms = item.get('nextFundingTime')
                    if next_funding_ms:
                        next_funding_time = self._timestamp_to_datetime(int(next_funding_ms))
                    else:
                        # Fallback: 8-hour cycle
                        now = self._get_current_time()
                        next_hour = ((now.hour // 8) + 1) * 8
                        next_funding_time = now.replace(
                            hour=next_hour % 24, minute=0, second=0, microsecond=0
                        )

                    result[symbol] = FundingInfo(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        next_funding_time=next_funding_time
                    )
                except Exception as e:
                    logger.debug(f"BingX: Error processing funding rate {item}: {str(e)}")
                    continue
        else:
            logger.warning(f"BingX: Unexpected funding rates response: {str(response)[:200]}")

        logger.info(f"BingX: Successfully fetched {len(result)} funding rates")
        return result

    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch ALL futures prices using ticker endpoint (no symbol = all)"""
        endpoint = "/openApi/swap/v2/quote/ticker"
        response = await self._make_bingx_request(endpoint)

        result = {}
        if response.get('code') == 0 and 'data' in response:
            data = response['data']
            items = data if isinstance(data, list) else [data]

            for item in items:
                try:
                    bx_symbol = item.get('symbol', '')
                    if not bx_symbol:
                        continue

                    symbol = self._normalize_symbol(bx_symbol)
                    price = float(item.get('lastPrice', 0))
                    if price > 0:
                        result[symbol] = price
                except Exception as e:
                    logger.debug(f"BingX: Error processing price {item}: {str(e)}")
                    continue

        logger.info(f"BingX: Successfully fetched {len(result)} prices")
        return result

    async def fetch_volumes(self) -> Dict[str, float]:
        """Fetch 24h trading volumes in USDT using ticker endpoint"""
        endpoint = "/openApi/swap/v2/quote/ticker"
        response = await self._make_bingx_request(endpoint)

        result = {}
        if response.get('code') == 0 and 'data' in response:
            data = response['data']
            items = data if isinstance(data, list) else [data]

            for item in items:
                try:
                    bx_symbol = item.get('symbol', '')
                    if not bx_symbol:
                        continue

                    symbol = self._normalize_symbol(bx_symbol)
                    # quoteVolume is 24h turnover in USDT
                    volume = float(item.get('quoteVolume', 0))
                    if volume > 0:
                        result[symbol] = volume
                except Exception as e:
                    logger.debug(f"BingX: Error processing volume: {str(e)}")
                    continue

        logger.info(f"BingX: Successfully fetched {len(result)} volumes")
        return result

    async def fetch_order_book(self) -> Dict[str, Dict[str, float]]:
        """Fetch best bid/ask prices for all futures using ticker endpoint.
        
        Uses GET /openApi/swap/v2/quote/ticker without symbol param to get ALL tickers.
        Response includes bidPrice and askPrice for each symbol.
        """
        endpoint = "/openApi/swap/v2/quote/ticker"
        response = await self._make_bingx_request(endpoint)

        result = {}
        if response.get('code') == 0 and 'data' in response:
            data = response['data']
            items = data if isinstance(data, list) else [data]

            for item in items:
                try:
                    bx_symbol = item.get('symbol', '')
                    if not bx_symbol:
                        continue

                    symbol = self._normalize_symbol(bx_symbol)

                    bid_price = float(item.get('bidPrice', 0))
                    ask_price = float(item.get('askPrice', 0))

                    if bid_price > 0 and ask_price > 0:
                        result[symbol] = {'bid': bid_price, 'ask': ask_price}
                except Exception as e:
                    logger.debug(f"BingX: Error processing order book item: {str(e)}")
                    continue
        else:
            logger.warning(f"BingX: No data in ticker response: {str(response)[:200]}")

        logger.info(f"BingX: Successfully fetched {len(result)} order books")
        return result

    async def get_next_funding_time(self) -> datetime:
        """Calculate next BingX funding time (8-hour cycle: 00:00, 08:00, 16:00 UTC)"""
        now = self._get_current_time()
        next_hour = ((now.hour // 8) + 1) * 8
        next_funding_time = now.replace(
            hour=next_hour % 24, minute=0, second=0, microsecond=0
        )
        if next_hour >= 24:
            from datetime import timedelta
            next_funding_time += timedelta(days=1)
            next_funding_time = next_funding_time.replace(hour=0)
        return next_funding_time
