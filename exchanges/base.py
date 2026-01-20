import aiohttp
import asyncio
import time
import logging
import pytz
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FundingInfo:
    symbol: str
    funding_rate: float
    next_funding_time: datetime
    predicted_rate: Optional[float] = None

@dataclass
class MarginTokenInfo:
    """Information about a margin-tradable token"""
    symbol: str  # Base token symbol (e.g., 'BTC')
    is_borrowable: bool
    max_leverage: Optional[float] = None

class BaseExchange(ABC):
    """Base class for all exchange implementations"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", request_timeout: float = 30.0):
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: float = 0.0
        self.rate_limit_ms: int = 50  # Fast rate limit
        self.utc = pytz.UTC
    
    def _get_current_time(self) -> datetime:
        return datetime.now(self.utc)
    
    def _timestamp_to_datetime(self, timestamp: int, is_milliseconds: bool = True) -> datetime:
        """Convert timestamp to UTC datetime"""
        try:
            if is_milliseconds:
                timestamp_sec = timestamp / 1000.0
            else:
                timestamp_sec = float(timestamp)
            
            # Create UTC datetime
            dt = datetime.fromtimestamp(timestamp_sec, self.utc)
            return dt
        except (ValueError, OSError, OverflowError) as e:
            # If timestamp is invalid, calculate next funding time
            logger.warning(f"Invalid timestamp {timestamp}: {e}")
            now = self._get_current_time()
            current_hour = now.hour
            if current_hour < 8:
                next_hour = 8
            elif current_hour < 16:
                next_hour = 16
            else:
                next_hour = 24
            
            next_time = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
            if next_hour == 24:
                next_time = next_time.replace(day=next_time.day + 1)
            return next_time
    
    async def _init_session(self):
        if self.session is None or self.session.closed:
            # NO TIMEOUT - let requests take as long as they need
            timeout = aiohttp.ClientTimeout(total=None)
            connector = aiohttp.TCPConnector(
                ssl=True,
                limit=200, 
                limit_per_host=50,
                keepalive_timeout=300
            )
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Accept-Encoding': 'gzip, deflate'  # Avoid brotli (br) which causes decode errors
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector,
                headers=headers
            )
    
    async def _close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, url: str, params: Dict = None, headers: Dict = None, data: Dict = None) -> Dict:
        await self._init_session()
        
        # Minimal rate limiting
        current_time = time.time() * 1000
        if current_time - self.last_request_time < self.rate_limit_ms:
            await asyncio.sleep((self.rate_limit_ms - (current_time - self.last_request_time)) / 1000)
        
        try:
            logger.debug(f"Making request to: {url}")
            
            async with self.session.request(method, url, params=params, headers=headers, json=data) as response:
                self.last_request_time = time.time() * 1000
                
                if response.status == 200:
                    try:
                        result = await response.json()
                        return result if result is not None else {}
                    except Exception as e:
                        logger.error(f"JSON decode error for {url}: {str(e)}")
                        return {}
                else:
                    text = await response.text()
                    logger.warning(f"HTTP {response.status} for {url}: {text[:200]}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return {}
    
    @abstractmethod
    async def fetch_funding_rates(self) -> Dict[str, FundingInfo]:
        pass
    
    @abstractmethod
    async def get_next_funding_time(self) -> datetime:
        pass
    
    @abstractmethod
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch futures prices"""
        pass
    
    async def fetch_margin_tokens(self) -> Dict[str, MarginTokenInfo]:
        """Fetch margin-tradable tokens. Override in exchanges that support margin.
        Returns dict of base symbols (e.g., 'BTC') to MarginTokenInfo"""
        return {}
    
    async def fetch_spot_prices(self) -> Dict[str, float]:
        """Fetch spot prices for tokens. Override in exchanges that support spot.
        Returns dict of symbols (e.g., 'BTCUSDT') to price"""
        return {}
    
    async def close(self):
        """Close the exchange session properly"""
        await self._close_session()