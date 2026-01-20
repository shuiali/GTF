"""
Klines Mixin - Provides kline/candlestick fetching functionality with 7-day historical data support.
This module contains helper functions for calculating timestamps and intervals.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict

# Standard interval mappings for each exchange
INTERVAL_MAPPINGS = {
    'binance': {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
        '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
    },
    'bitget_futures': {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
        '1d': '1D', '3d': '3D', '1w': '1W', '1M': '1M'
    },
    'bitget_spot': {
        '1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '12h': '12h',
        '1d': '1day', '3d': '3day', '1w': '1week', '1M': '1M'
    },
    'bybit': {
        '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
        '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
        '1d': 'D', '1w': 'W', '1M': 'M'
    },
    'gateio': {
        '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '4h': '4h', '8h': '8h',
        '1d': '1d', '7d': '7d', '30d': '30d'
    },
    'htx_futures': {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '60min', '4h': '4hour',
        '1d': '1day', '1w': '1week', '1M': '1mon'
    },
    'htx_spot': {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '60min', '4h': '4hour',
        '1d': '1day', '1w': '1week', '1M': '1mon', '1y': '1year'
    },
    'kucoin_futures': {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240, '8h': 480, '12h': 720,
        '1d': 1440, '1w': 10080
    },
    'kucoin_spot': {
        '1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1hour', '2h': '2hour', '4h': '4hour', '6h': '6hour', '8h': '8hour', '12h': '12hour',
        '1d': '1day', '1w': '1week'
    },
    'mexc_futures': {
        '1m': 'Min1', '5m': 'Min5', '15m': 'Min15', '30m': 'Min30',
        '1h': 'Min60', '4h': 'Hour4', '8h': 'Hour8',
        '1d': 'Day1', '1w': 'Week1', '1M': 'Month1'
    },
    'mexc_spot': {
        '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '60m', '4h': '4h', '1d': '1d', '1w': '1W', '1M': '1M'
    },
    'okx': {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
        '1d': '1D', '2d': '2D', '3d': '3D', '1w': '1W', '1M': '1M', '3M': '3M'
    }
}

# Interval to minutes mapping
INTERVAL_MINUTES = {
    '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
    '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
    '1d': 1440, '3d': 4320, '7d': 10080, '1w': 10080, '30d': 43200, '1M': 43200
}


def get_seven_day_timestamps(interval: str = '1h') -> Tuple[int, int]:
    """
    Calculate start and end timestamps for 7 days of data.
    Uses timezone-aware UTC datetime for accurate timestamp calculation.
    
    Args:
        interval: The kline interval
        
    Returns:
        Tuple of (start_timestamp_ms, end_timestamp_ms)
    """
    # Use timezone-aware UTC time for accuracy
    now = datetime.now(timezone.utc)
    end_time = now
    start_time = now - timedelta(days=7)
    
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    return start_ms, end_ms


def get_seven_day_timestamps_seconds(interval: str = '1h') -> Tuple[int, int]:
    """
    Calculate start and end timestamps in SECONDS for 7 days of data.
    Used by Gate.io, HTX, MEXC which use seconds.
    Uses timezone-aware UTC datetime for accurate timestamp calculation.
    
    Args:
        interval: The kline interval
        
    Returns:
        Tuple of (start_timestamp_sec, end_timestamp_sec)
    """
    # Use timezone-aware UTC time for accuracy
    now = datetime.now(timezone.utc)
    end_time = now
    start_time = now - timedelta(days=7)
    
    start_sec = int(start_time.timestamp())
    end_sec = int(end_time.timestamp())
    
    return start_sec, end_sec


# Keep old functions for backwards compatibility
def get_one_month_timestamps(interval: str = '1h') -> Tuple[int, int]:
    """Alias for get_seven_day_timestamps for backwards compatibility"""
    return get_seven_day_timestamps(interval)


def get_one_month_timestamps_seconds(interval: str = '1h') -> Tuple[int, int]:
    """Alias for get_seven_day_timestamps_seconds for backwards compatibility"""
    return get_seven_day_timestamps_seconds(interval)


def calculate_klines_needed(interval: str = '1h', days: int = 7) -> int:
    """
    Calculate how many klines are needed for the given interval and time period.
    
    Args:
        interval: The kline interval
        days: Number of days of data
        
    Returns:
        Number of klines needed
    """
    minutes_in_period = days * 24 * 60
    interval_minutes = INTERVAL_MINUTES.get(interval, 60)
    return minutes_in_period // interval_minutes


def get_exchange_interval(exchange: str, interval: str) -> str:
    """
    Convert a standard interval to exchange-specific format.
    
    Args:
        exchange: Exchange name (e.g., 'binance', 'bitget_futures')
        interval: Standard interval (e.g., '1h', '4h', '1d')
        
    Returns:
        Exchange-specific interval string
    """
    mappings = INTERVAL_MAPPINGS.get(exchange, {})
    return mappings.get(interval, interval)
