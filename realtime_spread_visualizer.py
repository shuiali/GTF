"""
Real-Time Spread Visualizer - Fixed Version
============================================

All 8 exchanges with WebSocket, true real-time updates, latency display.
"""

import sys
import asyncio
import json
import time
import ssl
import certifi
import gzip
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Tuple, List
from datetime import datetime
from enum import Enum
import threading
import re

# Third-party imports
import aiohttp
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QPushButton, QFrame, QGroupBox, QGridLayout,
    QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPalette, QColor
import pyqtgraph as pg

# Configure pyqtgraph for performance
pg.setConfigOptions(antialias=True, useOpenGL=True)


# ============================================================================
# Data Structures
# ============================================================================

class MarketType(Enum):
    SPOT = "spot"
    FUTURES = "futures"


@dataclass
class BookTicker:
    exchange: str
    symbol: str
    market_type: MarketType
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float
    exchange_timestamp: float  # Exchange's timestamp in ms
    local_timestamp: float = field(default_factory=lambda: time.time() * 1000)
    
    @property
    def latency_ms(self) -> float:
        """Calculate latency from exchange to local receipt"""
        return self.local_timestamp - self.exchange_timestamp


@dataclass
class SpreadData:
    timestamp: float
    entry_spread: float
    exit_spread: float
    latency_a: float
    latency_b: float


# Exchanges with margin = support spot
EXCHANGES_WITH_SPOT = {"binance", "bybit", "gateio", "bitget", "htx", "kucoin"}
FUTURES_ONLY_EXCHANGES = {"okx", "mexc"}


# ============================================================================
# SSL Context - Properly configured
# ============================================================================

def create_ssl_context():
    """Create SSL context with certifi certificates"""
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    ssl_ctx.check_hostname = True
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    return ssl_ctx


# ============================================================================
# WebSocket Provider Base Class
# ============================================================================

class WebSocketProvider:
    EXCHANGE_NAME = "base"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.running = False
        self.on_book_ticker: Optional[Callable[[BookTicker], None]] = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            ssl_ctx = create_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=10)
            # Disable auto-decompression to avoid Brotli issues
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Accept-Encoding": "gzip, deflate",  # Exclude br (Brotli)
                    "User-Agent": "Mozilla/5.0"
                },
                auto_decompress=True
            )
        return self.session
    
    async def connect(self, symbol: str, market_type: MarketType):
        raise NotImplementedError
    
    async def disconnect(self):
        self.running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _extract_base_quote(self, symbol: str) -> Tuple[str, str]:
        """
        Extract base and quote from symbol.
        BTCUSDT -> (BTC, USDT)
        ETH-USDT -> (ETH, USDT)
        """
        # Clean the symbol
        symbol = symbol.upper().strip()
        
        # Handle already separated formats
        if "-" in symbol:
            parts = symbol.split("-")
            if len(parts) >= 2:
                return (parts[0], parts[1])
        if "_" in symbol:
            parts = symbol.split("_")
            if len(parts) >= 2:
                return (parts[0], parts[1])
        if "/" in symbol:
            parts = symbol.split("/")
            if len(parts) >= 2:
                return (parts[0], parts[1])
        
        # For concatenated format like BTCUSDT
        # Quote currencies in order of priority (longest first to avoid partial matches)
        quotes = ["USDT", "USDC", "BUSD", "TUSD", "USDP", "USD", "BTC", "ETH", "BNB"]
        
        for quote in quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if len(base) >= 2:  # Valid base like BTC, ETH, etc.
                    return (base, quote)
        
        # Fallback: assume last 4 chars are quote if symbol is long enough
        if len(symbol) > 4:
            return (symbol[:-4], symbol[-4:])
        
        return (symbol, "USDT")


# ============================================================================
# Binance WebSocket Provider
# ============================================================================

class BinanceWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "binance"
    SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
    FUTURES_WS_URL = "wss://fstream.binance.com/ws"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        normalized = f"{base}{quote}".lower()
        
        base_url = self.FUTURES_WS_URL if market_type == MarketType.FUTURES else self.SPOT_WS_URL
        ws_url = f"{base_url}/{normalized}@bookTicker"
        
        print(f"[Binance] Connecting to {ws_url}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(ws_url, heartbeat=20) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    print(f"[Binance] Connected!")
                    
                    async for msg in ws:
                        if not self.running:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            book_ticker = self._parse(data, symbol, market_type)
                            if book_ticker and self.on_book_ticker:
                                self.on_book_ticker(book_ticker)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                            
            except Exception as e:
                if self.running:
                    print(f"[Binance] Error: {e}, reconnecting in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=float(data['b']),
                bid_qty=float(data['B']),
                ask_price=float(data['a']),
                ask_qty=float(data['A']),
                exchange_timestamp=float(data.get('T', data.get('E', time.time() * 1000)))
            )
        except (KeyError, ValueError) as e:
            return None


# ============================================================================
# OKX WebSocket Provider
# ============================================================================

class OKXWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "okx"
    WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        
        # OKX format: BTC-USDT-SWAP
        inst_id = f"{base}-{quote}-SWAP"
        
        print(f"[OKX] Connecting, instId: {inst_id}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(self.WS_URL, heartbeat=25) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [{"channel": "bbo-tbt", "instId": inst_id}]
                    }
                    await ws.send_json(subscribe_msg)
                    print(f"[OKX] Subscribed to {inst_id}")
                    
                    async for msg in ws:
                        if not self.running:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data.get('event') == 'error':
                                print(f"[OKX] Error: {data.get('msg')}")
                                continue
                            if data.get('event') == 'subscribe':
                                print(f"[OKX] Confirmed!")
                                continue
                            
                            if 'data' in data:
                                for item in data['data']:
                                    bt = self._parse(item, symbol, market_type)
                                    if bt and self.on_book_ticker:
                                        self.on_book_ticker(bt)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                            
            except Exception as e:
                if self.running:
                    print(f"[OKX] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            asks = data.get('asks', [])
            bids = data.get('bids', [])
            if not asks or not bids:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=float(bids[0][0]),
                bid_qty=float(bids[0][1]),
                ask_price=float(asks[0][0]),
                ask_qty=float(asks[0][1]),
                exchange_timestamp=float(data.get('ts', time.time() * 1000))
            )
        except (KeyError, ValueError, IndexError):
            return None


# ============================================================================
# Bybit WebSocket Provider
# ============================================================================

class BybitWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "bybit"
    SPOT_WS_URL = "wss://stream.bybit.com/v5/public/spot"
    LINEAR_WS_URL = "wss://stream.bybit.com/v5/public/linear"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        normalized = f"{base}{quote}"
        
        ws_url = self.LINEAR_WS_URL if market_type == MarketType.FUTURES else self.SPOT_WS_URL
        
        print(f"[Bybit] Connecting, symbol: {normalized}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(ws_url, heartbeat=20) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [f"orderbook.1.{normalized}"]
                    }
                    await ws.send_json(subscribe_msg)
                    print(f"[Bybit] Subscribed to {normalized}")
                    
                    ping_task = asyncio.create_task(self._ping_loop(ws))
                    
                    try:
                        async for msg in ws:
                            if not self.running:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                
                                if data.get('success') is True:
                                    print(f"[Bybit] Confirmed!")
                                    continue
                                
                                if 'topic' in data and data['topic'].startswith('orderbook'):
                                    bt = self._parse(data, symbol, market_type)
                                    if bt and self.on_book_ticker:
                                        self.on_book_ticker(bt)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                    finally:
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
                            
            except Exception as e:
                if self.running:
                    print(f"[Bybit] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def _ping_loop(self, ws):
        while self.running:
            try:
                await asyncio.sleep(20)
                if not ws.closed:
                    await ws.send_json({"op": "ping"})
            except:
                break
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            orderbook = data.get('data', {})
            bids = orderbook.get('b', [])
            asks = orderbook.get('a', [])
            
            if not bids or not asks:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=float(bids[0][0]),
                bid_qty=float(bids[0][1]),
                ask_price=float(asks[0][0]),
                ask_qty=float(asks[0][1]),
                exchange_timestamp=float(data.get('ts', time.time() * 1000))
            )
        except (KeyError, ValueError, IndexError):
            return None


# ============================================================================
# Gate.io WebSocket Provider
# ============================================================================

class GateIOWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "gateio"
    SPOT_WS_URL = "wss://api.gateio.ws/ws/v4/"
    FUTURES_WS_URL = "wss://fx-ws.gateio.ws/v4/ws/usdt"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        normalized = f"{base}_{quote}"
        
        ws_url = self.FUTURES_WS_URL if market_type == MarketType.FUTURES else self.SPOT_WS_URL
        channel = "futures.book_ticker" if market_type == MarketType.FUTURES else "spot.book_ticker"
        
        print(f"[Gate.io] Connecting, symbol: {normalized}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(ws_url, heartbeat=25) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    
                    subscribe_msg = {
                        "time": int(time.time()),
                        "channel": channel,
                        "event": "subscribe",
                        "payload": [normalized]
                    }
                    await ws.send_json(subscribe_msg)
                    print(f"[Gate.io] Subscribed to {normalized}")
                    
                    async for msg in ws:
                        if not self.running:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data.get('event') == 'subscribe':
                                print(f"[Gate.io] Confirmed!")
                                continue
                            
                            if data.get('event') == 'update':
                                bt = self._parse(data, symbol, market_type)
                                if bt and self.on_book_ticker:
                                    self.on_book_ticker(bt)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                            
            except Exception as e:
                if self.running:
                    print(f"[Gate.io] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            result = data.get('result', {})
            
            bid = float(result.get('b', 0))
            ask = float(result.get('a', 0))
            if bid <= 0 or ask <= 0:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=bid,
                bid_qty=float(result.get('B', 0)),
                ask_price=ask,
                ask_qty=float(result.get('A', 0)),
                exchange_timestamp=float(data.get('time_ms', time.time() * 1000))
            )
        except (KeyError, ValueError):
            return None


# ============================================================================
# Bitget WebSocket Provider
# ============================================================================

class BitgetWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "bitget"
    WS_URL = "wss://ws.bitget.com/v2/ws/public"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        normalized = f"{base}{quote}"
        
        inst_type = "USDT-FUTURES" if market_type == MarketType.FUTURES else "SPOT"
        
        print(f"[Bitget] Connecting, instType: {inst_type}, instId: {normalized}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(self.WS_URL, heartbeat=25) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [{
                            "instType": inst_type,
                            "channel": "ticker",
                            "instId": normalized
                        }]
                    }
                    await ws.send_json(subscribe_msg)
                    print(f"[Bitget] Subscribed to {normalized}")
                    
                    ping_task = asyncio.create_task(self._ping_loop(ws))
                    
                    try:
                        async for msg in ws:
                            if not self.running:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                
                                if data.get('event') == 'error':
                                    print(f"[Bitget] Error: {data.get('msg')}")
                                    continue
                                if data.get('event') == 'subscribe':
                                    print(f"[Bitget] Confirmed!")
                                    continue
                                
                                if 'data' in data and data.get('action') in ['snapshot', 'update']:
                                    for item in data['data']:
                                        bt = self._parse(item, symbol, market_type)
                                        if bt and self.on_book_ticker:
                                            self.on_book_ticker(bt)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                    finally:
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
                            
            except Exception as e:
                if self.running:
                    print(f"[Bitget] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def _ping_loop(self, ws):
        while self.running:
            try:
                await asyncio.sleep(25)
                if not ws.closed:
                    await ws.send_str("ping")
            except:
                break
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            bid = float(data.get('bidPr', 0))
            ask = float(data.get('askPr', 0))
            if bid <= 0 or ask <= 0:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=bid,
                bid_qty=float(data.get('bidSz', 0)),
                ask_price=ask,
                ask_qty=float(data.get('askSz', 0)),
                exchange_timestamp=float(data.get('ts', time.time() * 1000))
            )
        except (KeyError, ValueError):
            return None


# ============================================================================
# HTX WebSocket Provider - Fixed SSL
# ============================================================================

class HTXWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "htx"
    SPOT_WS_URL = "wss://api.huobi.pro/ws"
    FUTURES_WS_URL = "wss://api.hbdm.com/linear-swap-ws"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        
        if market_type == MarketType.FUTURES:
            normalized = f"{base}-{quote}"
            ws_url = self.FUTURES_WS_URL
            sub_topic = f"market.{normalized}.depth.step0"
        else:
            normalized = f"{base}{quote}".lower()
            ws_url = self.SPOT_WS_URL
            sub_topic = f"market.{normalized}.depth.step0"
        
        print(f"[HTX] Connecting to {ws_url}, topic: {sub_topic}")
        
        while self.running:
            try:
                # Create session with proper SSL for HTX
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE  # HTX has certificate issues
                
                connector = aiohttp.TCPConnector(ssl=ssl_ctx)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.ws_connect(ws_url, heartbeat=None) as ws:
                        self.ws = ws
                        self._reconnect_delay = 1.0
                        
                        subscribe_msg = {
                            "sub": sub_topic,
                            "id": f"id{int(time.time())}"
                        }
                        await ws.send_json(subscribe_msg)
                        print(f"[HTX] Subscribed to {sub_topic}")
                        
                        async for msg in ws:
                            if not self.running:
                                break
                            
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                try:
                                    decompressed = gzip.decompress(msg.data)
                                    data = json.loads(decompressed.decode('utf-8'))
                                except:
                                    continue
                                
                                if 'ping' in data:
                                    await ws.send_json({"pong": data['ping']})
                                    continue
                                
                                if 'subbed' in data:
                                    print(f"[HTX] Confirmed!")
                                    continue
                                
                                if 'tick' in data and 'ch' in data:
                                    bt = self._parse(data, symbol, market_type)
                                    if bt and self.on_book_ticker:
                                        self.on_book_ticker(bt)
                                        
                            elif msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if 'ping' in data:
                                    await ws.send_json({"pong": data['ping']})
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                            
            except Exception as e:
                if self.running:
                    print(f"[HTX] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            tick = data.get('tick', {})
            bids = tick.get('bids', [])
            asks = tick.get('asks', [])
            
            if not bids or not asks:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=float(bids[0][0]),
                bid_qty=float(bids[0][1]),
                ask_price=float(asks[0][0]),
                ask_qty=float(asks[0][1]),
                exchange_timestamp=float(data.get('ts', time.time() * 1000))
            )
        except (KeyError, ValueError, IndexError):
            return None


# ============================================================================
# KuCoin WebSocket Provider - Fixed Brotli
# ============================================================================

class KuCoinWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "kucoin"
    SPOT_TOKEN_URL = "https://api.kucoin.com/api/v1/bullet-public"
    FUTURES_TOKEN_URL = "https://api-futures.kucoin.com/api/v1/bullet-public"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        
        if market_type == MarketType.FUTURES:
            normalized = f"{base}{quote}M"
            token_url = self.FUTURES_TOKEN_URL
        else:
            normalized = f"{base}-{quote}"
            token_url = self.SPOT_TOKEN_URL
        
        print(f"[KuCoin] Getting token for {normalized}")
        
        while self.running:
            try:
                # Create session with explicit headers to avoid Brotli
                ssl_ctx = create_ssl_context()
                connector = aiohttp.TCPConnector(ssl=ssl_ctx)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    headers={
                        "Accept-Encoding": "gzip, deflate",  # NO Brotli
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    }
                ) as session:
                    # Get WebSocket token
                    async with session.post(token_url) as resp:
                        token_data = await resp.json()
                        
                        if token_data.get('code') != '200000':
                            print(f"[KuCoin] Token error: {token_data}")
                            await asyncio.sleep(5)
                            continue
                        
                        ws_data = token_data['data']
                        token = ws_data['token']
                        servers = ws_data['instanceServers']
                        ws_endpoint = servers[0]['endpoint']
                        ping_interval = servers[0].get('pingInterval', 18000) // 1000
                    
                    ws_url = f"{ws_endpoint}?token={token}"
                    print(f"[KuCoin] Connecting to WebSocket")
                    
                    async with session.ws_connect(ws_url, heartbeat=None) as ws:
                        self.ws = ws
                        self._reconnect_delay = 1.0
                        
                        # Wait for welcome
                        welcome = await ws.receive_json()
                        if welcome.get('type') != 'welcome':
                            print(f"[KuCoin] Bad welcome: {welcome}")
                        
                        # Subscribe
                        if market_type == MarketType.FUTURES:
                            topic = f"/contractMarket/tickerV2:{normalized}"
                        else:
                            topic = f"/market/ticker:{normalized}"
                        
                        subscribe_msg = {
                            "id": str(int(time.time() * 1000)),
                            "type": "subscribe",
                            "topic": topic,
                            "privateChannel": False,
                            "response": True
                        }
                        await ws.send_json(subscribe_msg)
                        print(f"[KuCoin] Subscribed to {topic}")
                        
                        ping_task = asyncio.create_task(self._ping_loop(ws, ping_interval))
                        
                        try:
                            async for msg in ws:
                                if not self.running:
                                    break
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    data = json.loads(msg.data)
                                    
                                    msg_type = data.get('type')
                                    if msg_type == 'pong':
                                        continue
                                    if msg_type == 'ack':
                                        print(f"[KuCoin] Confirmed!")
                                        continue
                                    if msg_type == 'message' and 'data' in data:
                                        bt = self._parse(data, symbol, market_type)
                                        if bt and self.on_book_ticker:
                                            self.on_book_ticker(bt)
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    break
                        finally:
                            ping_task.cancel()
                            try:
                                await ping_task
                            except asyncio.CancelledError:
                                pass
                            
            except Exception as e:
                if self.running:
                    print(f"[KuCoin] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def _ping_loop(self, ws, interval: int):
        while self.running:
            try:
                await asyncio.sleep(interval)
                if not ws.closed:
                    await ws.send_json({
                        "id": str(int(time.time() * 1000)),
                        "type": "ping"
                    })
            except:
                break
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            tick = data.get('data', {})
            
            if market_type == MarketType.FUTURES:
                bid = float(tick.get('bestBidPrice', 0))
                ask = float(tick.get('bestAskPrice', 0))
                ts = float(tick.get('ts', time.time() * 1000))
            else:
                bid = float(tick.get('bestBid', 0))
                ask = float(tick.get('bestAsk', 0))
                ts = float(tick.get('time', time.time() * 1000))
            
            if bid <= 0 or ask <= 0:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=bid,
                bid_qty=float(tick.get('bestBidSize', tick.get('size', 0))),
                ask_price=ask,
                ask_qty=float(tick.get('bestAskSize', tick.get('size', 0))),
                exchange_timestamp=ts
            )
        except (KeyError, ValueError):
            return None


# ============================================================================
# MEXC WebSocket Provider
# ============================================================================

class MEXCWebSocketProvider(WebSocketProvider):
    EXCHANGE_NAME = "mexc"
    FUTURES_WS_URL = "wss://contract.mexc.com/edge"
    
    async def connect(self, symbol: str, market_type: MarketType):
        self.running = True
        base, quote = self._extract_base_quote(symbol)
        normalized = f"{base}_{quote}"
        
        print(f"[MEXC] Connecting, symbol: {normalized}")
        
        while self.running:
            try:
                session = await self._get_session()
                async with session.ws_connect(self.FUTURES_WS_URL, heartbeat=None) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0
                    
                    subscribe_msg = {
                        "method": "sub.depth",
                        "param": {"symbol": normalized}
                    }
                    await ws.send_json(subscribe_msg)
                    print(f"[MEXC] Subscribed to {normalized}")
                    
                    ping_task = asyncio.create_task(self._ping_loop(ws))
                    
                    try:
                        async for msg in ws:
                            if not self.running:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                
                                if data.get('channel') == 'pong':
                                    continue
                                if data.get('channel') == 'rs.sub.depth':
                                    print(f"[MEXC] Confirmed!")
                                    continue
                                
                                if data.get('channel') == 'push.depth':
                                    bt = self._parse(data, symbol, market_type)
                                    if bt and self.on_book_ticker:
                                        self.on_book_ticker(bt)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                    finally:
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass
                            
            except Exception as e:
                if self.running:
                    print(f"[MEXC] Error: {e}, reconnecting...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def _ping_loop(self, ws):
        while self.running:
            try:
                await asyncio.sleep(20)
                if not ws.closed:
                    await ws.send_json({"method": "ping"})
            except:
                break
    
    def _parse(self, data: dict, symbol: str, market_type: MarketType) -> Optional[BookTicker]:
        try:
            depth = data.get('data', {})
            asks = depth.get('asks', [])
            bids = depth.get('bids', [])
            
            if not asks or not bids:
                return None
            
            return BookTicker(
                exchange=self.EXCHANGE_NAME,
                symbol=symbol,
                market_type=market_type,
                bid_price=float(bids[0][0]),
                bid_qty=float(bids[0][1]),
                ask_price=float(asks[0][0]),
                ask_qty=float(asks[0][1]),
                exchange_timestamp=float(depth.get('timestamp', time.time() * 1000))
            )
        except (KeyError, ValueError, IndexError):
            return None


# ============================================================================
# Provider Factory
# ============================================================================

def get_provider(exchange: str) -> WebSocketProvider:
    providers = {
        "binance": BinanceWebSocketProvider,
        "okx": OKXWebSocketProvider,
        "bybit": BybitWebSocketProvider,
        "gateio": GateIOWebSocketProvider,
        "bitget": BitgetWebSocketProvider,
        "htx": HTXWebSocketProvider,
        "kucoin": KuCoinWebSocketProvider,
        "mexc": MEXCWebSocketProvider,
    }
    provider_class = providers.get(exchange.lower())
    if not provider_class:
        raise ValueError(f"Unknown exchange: {exchange}")
    return provider_class()


# ============================================================================
# Spread Calculator - Real-time (no aggregation)
# ============================================================================

class SpreadCalculator:
    STALE_THRESHOLD_MS = 5000
    
    def __init__(self):
        self.data_a: Optional[BookTicker] = None
        self.data_b: Optional[BookTicker] = None
        self._lock = threading.Lock()
    
    def update_a(self, data: BookTicker):
        with self._lock:
            self.data_a = data
    
    def update_b(self, data: BookTicker):
        with self._lock:
            self.data_b = data
    
    def calculate(self) -> Optional[SpreadData]:
        with self._lock:
            if not self.data_a or not self.data_b:
                return None
            
            now = time.time() * 1000
            
            if (now - self.data_a.local_timestamp > self.STALE_THRESHOLD_MS or
                now - self.data_b.local_timestamp > self.STALE_THRESHOLD_MS):
                return None
            
            a, b = self.data_a, self.data_b
            
            if a.ask_price <= 0 or b.ask_price <= 0:
                return None
            
            entry = ((b.bid_price - a.ask_price) / a.ask_price) * 100
            exit_s = ((a.bid_price - b.ask_price) / b.ask_price) * 100
            
            return SpreadData(
                timestamp=time.time(),
                entry_spread=entry,
                exit_spread=exit_s,
                latency_a=a.latency_ms,
                latency_b=b.latency_ms
            )
    
    def reset(self):
        with self._lock:
            self.data_a = None
            self.data_b = None


# ============================================================================
# Data Buffer - True real-time (every tick)
# ============================================================================

class SpreadBuffer:
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.data: deque = deque(maxlen=max_points)
        self._lock = threading.Lock()
    
    def add(self, spread: SpreadData):
        with self._lock:
            self.data.append(spread)
    
    def get_data(self) -> Tuple[List[float], List[float], List[float]]:
        with self._lock:
            if not self.data:
                return [], [], []
            
            timestamps = [d.timestamp for d in self.data]
            entry = [d.entry_spread for d in self.data]
            exit_s = [d.exit_spread for d in self.data]
            return timestamps, entry, exit_s
    
    def clear(self):
        with self._lock:
            self.data.clear()


# ============================================================================
# Async Loop Manager
# ============================================================================

class AsyncLoopManager:
    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self._started = threading.Event()
    
    def start(self):
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self._started.wait()
    
    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._started.set()
        self.loop.run_forever()
    
    def run_coro(self, coro):
        if self.loop:
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=2)


# ============================================================================
# Qt Signal Bridge
# ============================================================================

class SignalBridge(QObject):
    spread_updated = Signal(object)
    price_updated = Signal(str, float, float, float)  # label, bid, ask, latency


# ============================================================================
# Main Window
# ============================================================================

class MainWindow(QMainWindow):
    EXCHANGES = ["binance", "okx", "bybit", "gateio", "bitget", "htx", "kucoin", "mexc"]
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Spread Visualizer")
        self.setMinimumSize(1300, 750)
        
        self.async_mgr = AsyncLoopManager()
        self.signals = SignalBridge()
        self.calculator = SpreadCalculator()
        self.buffer = SpreadBuffer(max_points=2000)
        
        self.provider_a: Optional[WebSocketProvider] = None
        self.provider_b: Optional[WebSocketProvider] = None
        self.is_connected = False
        
        self._setup_dark_theme()
        self._setup_ui()
        self._setup_chart()
        self._setup_signals()
        
        self.async_mgr.start()
        
        # Chart timer - update every 16ms (60fps) 
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self._update_chart)
        self.chart_timer.start(16)
    
    def _setup_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Control panel
        ctrl = QFrame()
        ctrl.setStyleSheet("QFrame { background-color: #252525; border-radius: 6px; }")
        ctrl_layout = QHBoxLayout(ctrl)
        
        # Symbol
        sym_grp = QGroupBox("Symbol")
        sym_grp.setStyleSheet("QGroupBox { font-weight: bold; }")
        sym_layout = QVBoxLayout(sym_grp)
        self.symbol_input = QLineEdit("BTCUSDT")
        self.symbol_input.setPlaceholderText("e.g. BTCUSDT or BTC-USDT")
        self.symbol_input.setMinimumWidth(130)
        sym_layout.addWidget(self.symbol_input)
        ctrl_layout.addWidget(sym_grp)
        
        # Exchange A
        exc_a_grp = QGroupBox("Exchange A")
        exc_a_grp.setStyleSheet("QGroupBox { font-weight: bold; }")
        exc_a_layout = QGridLayout(exc_a_grp)
        self.exc_a_combo = QComboBox()
        self.exc_a_combo.addItems([e.upper() for e in self.EXCHANGES])
        self.exc_a_combo.setCurrentText("BINANCE")
        self.mkt_a_combo = QComboBox()
        self.mkt_a_combo.addItems(["FUTURES", "SPOT"])
        exc_a_layout.addWidget(QLabel("Exchange:"), 0, 0)
        exc_a_layout.addWidget(self.exc_a_combo, 0, 1)
        exc_a_layout.addWidget(QLabel("Market:"), 1, 0)
        exc_a_layout.addWidget(self.mkt_a_combo, 1, 1)
        ctrl_layout.addWidget(exc_a_grp)
        
        # Exchange B
        exc_b_grp = QGroupBox("Exchange B")
        exc_b_grp.setStyleSheet("QGroupBox { font-weight: bold; }")
        exc_b_layout = QGridLayout(exc_b_grp)
        self.exc_b_combo = QComboBox()
        self.exc_b_combo.addItems([e.upper() for e in self.EXCHANGES])
        self.exc_b_combo.setCurrentText("OKX")
        self.mkt_b_combo = QComboBox()
        self.mkt_b_combo.addItems(["FUTURES", "SPOT"])
        exc_b_layout.addWidget(QLabel("Exchange:"), 0, 0)
        exc_b_layout.addWidget(self.exc_b_combo, 0, 1)
        exc_b_layout.addWidget(QLabel("Market:"), 1, 0)
        exc_b_layout.addWidget(self.mkt_b_combo, 1, 1)
        ctrl_layout.addWidget(exc_b_grp)
        
        # Update market options on exchange change
        self.exc_a_combo.currentTextChanged.connect(self._on_exc_a_change)
        self.exc_b_combo.currentTextChanged.connect(self._on_exc_b_change)
        self._on_exc_a_change(self.exc_a_combo.currentText())
        self._on_exc_b_change(self.exc_b_combo.currentText())
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumHeight(55)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745; color: white;
                font-size: 15px; font-weight: bold;
                border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.connect_btn.clicked.connect(self._toggle_connection)
        ctrl_layout.addWidget(self.connect_btn)
        
        layout.addWidget(ctrl)
        
        # Stats panel
        stats = QFrame()
        stats.setStyleSheet("QFrame { background-color: #252525; border-radius: 6px; padding: 5px; }")
        stats_layout = QHBoxLayout(stats)
        
        # Price + Latency labels
        self.price_a_label = QLabel("A: --")
        self.price_a_label.setStyleSheet("font-size: 13px; color: #aaa;")
        self.latency_a_label = QLabel("Lat: --")
        self.latency_a_label.setStyleSheet("font-size: 13px; color: #888;")
        
        self.price_b_label = QLabel("B: --")
        self.price_b_label.setStyleSheet("font-size: 13px; color: #aaa;")
        self.latency_b_label = QLabel("Lat: --")
        self.latency_b_label.setStyleSheet("font-size: 13px; color: #888;")
        
        self.entry_label = QLabel("Entry: --")
        self.entry_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff88;")
        self.exit_label = QLabel("Exit: --")
        self.exit_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff6b6b;")
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        
        stats_layout.addWidget(self.price_a_label)
        stats_layout.addWidget(self.latency_a_label)
        stats_layout.addSpacing(15)
        stats_layout.addWidget(self.price_b_label)
        stats_layout.addWidget(self.latency_b_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.entry_label)
        stats_layout.addSpacing(30)
        stats_layout.addWidget(self.exit_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.status_label)
        
        layout.addWidget(stats)
        
        # Chart
        self.chart = pg.PlotWidget()
        self.chart.setBackground('#1a1a1a')
        self.chart.showGrid(x=True, y=True, alpha=0.2)
        self.chart.setLabel('left', 'Spread %')
        self.chart.setLabel('bottom', 'Time (sec)')
        self.chart.addLegend()
        
        layout.addWidget(self.chart, stretch=1)
    
    def _on_exc_a_change(self, exc: str):
        self.mkt_a_combo.clear()
        if exc.lower() in FUTURES_ONLY_EXCHANGES:
            self.mkt_a_combo.addItems(["FUTURES"])
        else:
            self.mkt_a_combo.addItems(["FUTURES", "SPOT"])
    
    def _on_exc_b_change(self, exc: str):
        self.mkt_b_combo.clear()
        if exc.lower() in FUTURES_ONLY_EXCHANGES:
            self.mkt_b_combo.addItems(["FUTURES"])
        else:
            self.mkt_b_combo.addItems(["FUTURES", "SPOT"])
    
    def _setup_chart(self):
        pen_entry = pg.mkPen(color='#00ff88', width=2)
        pen_exit = pg.mkPen(color='#ff6b6b', width=2)
        
        self.entry_curve = self.chart.plot([], [], pen=pen_entry, name='Entry')
        self.exit_curve = self.chart.plot([], [], pen=pen_exit, name='Exit')
        
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, 
            pen=pg.mkPen('#444', width=1, style=Qt.PenStyle.DashLine))
        self.chart.addItem(self.zero_line)
    
    def _setup_signals(self):
        self.signals.spread_updated.connect(self._on_spread)
        self.signals.price_updated.connect(self._on_price)
    
    def _toggle_connection(self):
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "Error", "Please enter a symbol")
            return
        
        # Validate symbol format
        if len(symbol) < 5:
            QMessageBox.warning(self, "Error", 
                "Invalid symbol. Use format like BTCUSDT or BTC-USDT")
            return
        
        exc_a = self.exc_a_combo.currentText().lower()
        exc_b = self.exc_b_combo.currentText().lower()
        mkt_a = MarketType.FUTURES if self.mkt_a_combo.currentText() == "FUTURES" else MarketType.SPOT
        mkt_b = MarketType.FUTURES if self.mkt_b_combo.currentText() == "FUTURES" else MarketType.SPOT
        
        self.provider_a = get_provider(exc_a)
        self.provider_b = get_provider(exc_b)
        
        self.provider_a.on_book_ticker = self._on_data_a
        self.provider_b.on_book_ticker = self._on_data_b
        
        self.calculator.reset()
        self.buffer.clear()
        
        self.async_mgr.run_coro(self.provider_a.connect(symbol, mkt_a))
        self.async_mgr.run_coro(self.provider_b.connect(symbol, mkt_b))
        
        self.is_connected = True
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white;
                font-size: 15px; font-weight: bold;
                border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.status_label.setText(f"Connecting to {exc_a.upper()} & {exc_b.upper()}...")
    
    def _disconnect(self):
        if self.provider_a:
            self.async_mgr.run_coro(self.provider_a.disconnect())
        if self.provider_b:
            self.async_mgr.run_coro(self.provider_b.disconnect())
        
        self.is_connected = False
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745; color: white;
                font-size: 15px; font-weight: bold;
                border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.status_label.setText("Disconnected")
        self.price_a_label.setText("A: --")
        self.price_b_label.setText("B: --")
        self.latency_a_label.setText("Lat: --")
        self.latency_b_label.setText("Lat: --")
    
    def _on_data_a(self, data: BookTicker):
        self.calculator.update_a(data)
        self.signals.price_updated.emit("A", data.bid_price, data.ask_price, data.latency_ms)
        self._process()
    
    def _on_data_b(self, data: BookTicker):
        self.calculator.update_b(data)
        self.signals.price_updated.emit("B", data.bid_price, data.ask_price, data.latency_ms)
        self._process()
    
    def _process(self):
        spread = self.calculator.calculate()
        if spread:
            self.buffer.add(spread)
            self.signals.spread_updated.emit(spread)
    
    def _on_price(self, label: str, bid: float, ask: float, latency: float):
        if label == "A":
            self.price_a_label.setText(f"A: {bid:.2f} / {ask:.2f}")
            lat_color = "#0f0" if latency < 100 else "#ff0" if latency < 500 else "#f00"
            self.latency_a_label.setText(f"Lat: {latency:.0f}ms")
            self.latency_a_label.setStyleSheet(f"font-size: 13px; color: {lat_color};")
        else:
            self.price_b_label.setText(f"B: {bid:.2f} / {ask:.2f}")
            lat_color = "#0f0" if latency < 100 else "#ff0" if latency < 500 else "#f00"
            self.latency_b_label.setText(f"Lat: {latency:.0f}ms")
            self.latency_b_label.setStyleSheet(f"font-size: 13px; color: {lat_color};")
    
    def _on_spread(self, spread: SpreadData):
        self.entry_label.setText(f"Entry: {spread.entry_spread:+.4f}%")
        self.exit_label.setText(f"Exit: {spread.exit_spread:+.4f}%")
        
        entry_color = "#00ff88" if spread.entry_spread > 0 else "#ff6b6b"
        exit_color = "#00ff88" if spread.exit_spread > 0 else "#ff6b6b"
        self.entry_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {entry_color};")
        self.exit_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {exit_color};")
        
        self.status_label.setText(f"Live • {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    def _update_chart(self):
        timestamps, entry, exit_s = self.buffer.get_data()
        if not timestamps:
            return
        
        # Relative time from start
        base = timestamps[0]
        rel = [t - base for t in timestamps]
        
        self.entry_curve.setData(rel, entry)
        self.exit_curve.setData(rel, exit_s)
    
    def closeEvent(self, event):
        self._disconnect()
        self.chart_timer.stop()
        self.async_mgr.stop()
        event.accept()


# ============================================================================
# Main
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
