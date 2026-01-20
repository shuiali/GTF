"""
Chart Application - Python Windows Desktop App using TradingView Lightweight Charts
This app allows viewing charts from all supported exchanges for both futures and spot markets.
Supports single exchange price charts and cross-exchange spread charts.
"""

import asyncio
import sys
import os
import json
import webview
from datetime import datetime, timezone
from typing import Optional, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchanges.binance import BinanceExchange
from exchanges.bitget import BitgetExchange
from exchanges.bybit import BybitExchange
from exchanges.gateio import GateioExchange
from exchanges.htx import HTXExchange
from exchanges.kucoin import KucoinExchange
from exchanges.mexc import MEXCExchange
from exchanges.okx import OKXExchange


# Available exchanges
EXCHANGES = {
    'binance': BinanceExchange,
    'bitget': BitgetExchange,
    'bybit': BybitExchange,
    'gateio': GateioExchange,
    'htx': HTXExchange,
    'kucoin': KucoinExchange,
    'mexc': MEXCExchange,
    'okx': OKXExchange
}

# Standard intervals
INTERVALS = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']

# Interval to seconds mapping
INTERVAL_SECONDS = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '30m': 1800,
    '1h': 3600,
    '4h': 14400,
    '1d': 86400
}


class ChartAPI:
    """API class exposed to JavaScript"""
    
    def __init__(self):
        self.exchange_instances: Dict[str, object] = {}
        self.current_data: List[dict] = []
    
    def get_exchanges(self) -> List[str]:
        """Get list of available exchanges"""
        return list(EXCHANGES.keys())
    
    def get_intervals(self) -> List[str]:
        """Get list of available intervals"""
        return INTERVALS
    
    def fetch_spread_data(self, exchange1: str, exchange2: str, symbol: str, interval: str, market1: str, market2: str) -> str:
        """
        Fetch spread data between two exchanges with independent market types.
        
        The spread is calculated as: (Ex1_price - Ex2_price) / Ex2_price * 100
        
        Candles are continuous: each candle's OPEN equals the previous candle's CLOSE.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_fetch_spread_data(exchange1, exchange2, symbol, interval, market1, market2)
            )
            loop.close()
            return json.dumps(result)
        except Exception as e:
            return json.dumps({'error': str(e), 'data': []})
    
    async def _async_fetch_spread_data(self, exchange1: str, exchange2: str, symbol: str, interval: str, market1: str, market2: str) -> dict:
        """Async method to fetch and calculate spread data between two exchanges"""
        if exchange1 not in EXCHANGES:
            return {'error': f'Unknown exchange: {exchange1}', 'data': []}
        if exchange2 not in EXCHANGES:
            return {'error': f'Unknown exchange: {exchange2}', 'data': []}
        
        try:
            # Create fresh exchange instances
            ex1 = EXCHANGES[exchange1]()
            ex2 = EXCHANGES[exchange2]()
            
            # Fetch klines from both exchanges concurrently
            if market1 == 'futures':
                fetch1 = ex1.get_klines_futures(symbol, interval)
            else:
                fetch1 = ex1.get_klines_spot(symbol, interval)
            
            if market2 == 'futures':
                fetch2 = ex2.get_klines_futures(symbol, interval)
            else:
                fetch2 = ex2.get_klines_spot(symbol, interval)
            
            klines1, klines2 = await asyncio.gather(fetch1, fetch2)
            
            # Close sessions
            await ex1.close()
            await ex2.close()
            
            if not klines1:
                return {'error': f'No data from {exchange1}', 'data': []}
            if not klines2:
                return {'error': f'No data from {exchange2}', 'data': []}
            
            # Get interval in seconds
            period_sec = INTERVAL_SECONDS.get(interval, 60)
            
            # Normalize timestamps: round to nearest period boundary
            # This handles minor drift between exchanges (e.g., 12:00:00.1 vs 12:00:00.0)
            def normalize_timestamp(t):
                return int(round(float(t) / period_sec) * period_sec)
            
            # Build lookup maps with normalized timestamps
            data1_map = {}
            for k in klines1:
                normalized_t = normalize_timestamp(k['time'])
                data1_map[normalized_t] = k
            
            data2_map = {}
            for k in klines2:
                normalized_t = normalize_timestamp(k['time'])
                data2_map[normalized_t] = k
            
            if not data1_map or not data2_map:
                return {'error': 'No data after normalization', 'data': []}
            
            # Find overlapping time range
            common_times = sorted(set(data1_map.keys()) & set(data2_map.keys()))
            
            if not common_times:
                return {'error': 'No overlapping timestamps between exchanges', 'data': []}
            
            # Calculate spread for each common timestamp
            # CRITICAL: Candles are CONTINUOUS - Open = Previous Close
            spread_line_data = []
            spread_candle_data = []
            prev_spread_close = None
            
            for timestamp in common_times:
                k1 = data1_map[timestamp]
                k2 = data2_map[timestamp]
                
                # Skip if any price is zero (invalid data)
                if k2['open'] == 0 or k2['high'] == 0 or k2['low'] == 0 or k2['close'] == 0:
                    continue
                if k1['open'] == 0 or k1['high'] == 0 or k1['low'] == 0 or k1['close'] == 0:
                    continue
                
                # Calculate spread percentage for each OHLC component
                spread_close = ((k1['close'] - k2['close']) / k2['close']) * 100
                
                # CONTINUOUS CANDLES: Open = Previous candle's Close
                if prev_spread_close is not None:
                    spread_open = prev_spread_close
                else:
                    # First candle: calculate actual open spread
                    spread_open = ((k1['open'] - k2['open']) / k2['open']) * 100
                
                # Calculate raw high/low spreads
                raw_spread_high = ((k1['high'] - k2['high']) / k2['high']) * 100
                raw_spread_low = ((k1['low'] - k2['low']) / k2['low']) * 100
                
                # High must be >= max(open, close), Low must be <= min(open, close)
                spread_high = max(spread_open, spread_close, raw_spread_high, raw_spread_low)
                spread_low = min(spread_open, spread_close, raw_spread_high, raw_spread_low)
                
                # Update previous close for next candle continuity
                prev_spread_close = spread_close
                
                # Line data (for baseline chart)
                spread_line_data.append({
                    'time': int(timestamp),
                    'value': round(spread_close, 6),
                    'ex1_close': k1['close'],
                    'ex2_close': k2['close']
                })
                
                # Candlestick data
                spread_candle_data.append({
                    'time': int(timestamp),
                    'open': round(spread_open, 6),
                    'high': round(spread_high, 6),
                    'low': round(spread_low, 6),
                    'close': round(spread_close, 6),
                    'ex1_prices': {
                        'open': k1['open'], 'high': k1['high'],
                        'low': k1['low'], 'close': k1['close']
                    },
                    'ex2_prices': {
                        'open': k2['open'], 'high': k2['high'],
                        'low': k2['low'], 'close': k2['close']
                    }
                })
            
            if not spread_line_data:
                return {'error': 'No valid spread data calculated', 'data': []}
            
            # Calculate statistics
            close_values = [d['value'] for d in spread_line_data]
            avg_spread = sum(close_values) / len(close_values)
            max_spread = max(close_values)
            min_spread = min(close_values)
            
            return {
                'error': None,
                'lineData': spread_line_data,
                'candleData': spread_candle_data,
                'symbol': symbol,
                'exchange1': exchange1,
                'exchange2': exchange2,
                'market1': market1,
                'market2': market2,
                'interval': interval,
                'count': len(spread_line_data),
                'stats': {
                    'avg': round(avg_spread, 4),
                    'max': round(max_spread, 4),
                    'min': round(min_spread, 4)
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'data': []}
    
    def fetch_chart_data(self, exchange: str, symbol: str, interval: str, market: str) -> str:
        """
        Fetch chart data for a single exchange.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_fetch_data(exchange, symbol, interval, market)
            )
            loop.close()
            return json.dumps(result)
        except Exception as e:
            return json.dumps({'error': str(e), 'data': []})
    
    async def _async_fetch_data(self, exchange: str, symbol: str, interval: str, market: str) -> dict:
        """Async method to fetch chart data from a single exchange"""
        if exchange not in EXCHANGES:
            return {'error': f'Unknown exchange: {exchange}', 'data': []}
        
        try:
            # Create fresh exchange instance
            ex = EXCHANGES[exchange]()
            
            # Fetch klines based on market type
            if market == 'futures':
                klines = await ex.get_klines_futures(symbol, interval)
            else:
                klines = await ex.get_klines_spot(symbol, interval)
            
            # Close the session
            await ex.close()
            
            if not klines:
                return {'error': 'No data returned', 'data': []}
            
            # Convert to TradingView format
            chart_data = []
            for k in klines:
                chart_data.append({
                    'time': int(k['time']),
                    'open': k['open'],
                    'high': k['high'],
                    'low': k['low'],
                    'close': k['close']
                })
            
            # Sort by time
            chart_data.sort(key=lambda x: x['time'])
            
            self.current_data = chart_data
            
            return {
                'error': None,
                'data': chart_data,
                'symbol': symbol,
                'exchange': exchange,
                'market': market,
                'interval': interval,
                'count': len(chart_data)
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'data': []}
    
    def cleanup(self):
        """Cleanup exchange instances"""
        pass


# HTML template with TradingView Lightweight Charts
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Crypto Chart Viewer</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1a1a2e;
            color: #eee;
            overflow: hidden;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 10px;
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 10px;
            background: #16213e;
            border-radius: 8px;
            margin-bottom: 10px;
            align-items: center;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .control-group label {
            font-size: 12px;
            color: #888;
        }
        select, input, button {
            padding: 8px 12px;
            border: 1px solid #333;
            border-radius: 4px;
            background: #0f3460;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        select:hover, input:hover {
            border-color: #4a9eff;
        }
        button {
            background: #4a9eff;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        button:hover {
            background: #357abd;
        }
        button:disabled {
            background: #555;
            cursor: not-allowed;
        }
        .market-toggle, .mode-toggle {
            display: flex;
            gap: 5px;
        }
        .market-btn, .mode-btn, .chart-type-btn {
            padding: 8px 16px;
            border: 1px solid #333;
            background: #0f3460;
            cursor: pointer;
            color: #d1d4dc;
            border-radius: 4px;
        }
        .market-btn.active, .mode-btn.active, .chart-type-btn.active {
            background: #4a9eff;
            border-color: #4a9eff;
        }
        .mode-btn.spread-mode.active {
            background: #9c27b0;
            border-color: #9c27b0;
        }
        .chart-type-btn.active[data-charttype="candlestick"] {
            background: #ff9800;
            border-color: #ff9800;
        }
        #chartContainer {
            flex: 1;
            background: #16213e;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            padding: 8px 10px;
            background: #16213e;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .status-item {
            display: flex;
            gap: 8px;
        }
        .status-label {
            color: #888;
        }
        .status-value {
            color: #4a9eff;
        }
        .status-value.spread-stats {
            color: #9c27b0;
        }
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 18px;
            color: #4a9eff;
        }
        .error {
            color: #ff6b6b;
        }
        #priceInfo {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(22, 33, 62, 0.95);
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 100;
            border: 1px solid #333;
        }
        .price-row {
            display: flex;
            gap: 15px;
            margin-bottom: 5px;
        }
        .price-label {
            color: #888;
            width: 80px;
        }
        .price-value {
            font-weight: bold;
        }
        .price-up { color: #26a69a; }
        .price-down { color: #ef5350; }
        .spread-positive { color: #26a69a; }
        .spread-negative { color: #ef5350; }
        .hidden { display: none !important; }
        .exchange-pair {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .exchange-pair span {
            color: #9c27b0;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <div class="control-group">
                <label>Mode</label>
                <div class="mode-toggle">
                    <button class="mode-btn active" data-mode="price">Price Chart</button>
                    <button class="mode-btn spread-mode" data-mode="spread">Spread Chart</button>
                </div>
            </div>
            
            <div class="control-group hidden" id="spreadChartTypeGroup">
                <label>Spread Type</label>
                <div class="mode-toggle">
                    <button class="chart-type-btn active" data-charttype="baseline">Baseline</button>
                    <button class="chart-type-btn" data-charttype="candlestick">Candlestick</button>
                </div>
            </div>
            
            <div class="control-group" id="singleExchangeGroup">
                <label>Exchange</label>
                <select id="exchange">
                    <option value="binance">Binance</option>
                    <option value="bitget">Bitget</option>
                    <option value="bybit">Bybit</option>
                    <option value="gateio">Gate.io</option>
                    <option value="htx">HTX</option>
                    <option value="kucoin">KuCoin</option>
                    <option value="mexc">MEXC</option>
                    <option value="okx">OKX</option>
                </select>
            </div>
            
            <div class="control-group hidden" id="spreadExchangeGroup">
                <label>Exchanges (Ex1 - Ex2)</label>
                <div class="exchange-pair">
                    <select id="exchange1">
                        <option value="binance">Binance</option>
                        <option value="bitget">Bitget</option>
                        <option value="bybit">Bybit</option>
                        <option value="gateio">Gate.io</option>
                        <option value="htx">HTX</option>
                        <option value="kucoin">KuCoin</option>
                        <option value="mexc">MEXC</option>
                        <option value="okx">OKX</option>
                    </select>
                    <span>vs</span>
                    <select id="exchange2">
                        <option value="binance">Binance</option>
                        <option value="bitget">Bitget</option>
                        <option value="bybit" selected>Bybit</option>
                        <option value="gateio">Gate.io</option>
                        <option value="htx">HTX</option>
                        <option value="kucoin">KuCoin</option>
                        <option value="mexc">MEXC</option>
                        <option value="okx">OKX</option>
                    </select>
                </div>
            </div>
            
            <div class="control-group">
                <label>Symbol</label>
                <input type="text" id="symbol" value="BTCUSDT" placeholder="e.g., BTCUSDT">
            </div>
            <div class="control-group">
                <label>Interval</label>
                <select id="interval">
                    <option value="1m">1 Minute</option>
                    <option value="5m">5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="30m">30 Minutes</option>
                    <option value="1h" selected>1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1d">1 Day</option>
                </select>
            </div>
            <div class="control-group" id="singleMarketGroup">
                <label>Market</label>
                <div class="market-toggle">
                    <button class="market-btn active" data-market="futures">Futures</button>
                    <button class="market-btn" data-market="spot">Spot</button>
                </div>
            </div>
            
            <div class="control-group hidden" id="spreadMarketGroup">
                <label>Markets (Ex1 / Ex2)</label>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div class="market-toggle">
                        <button class="market-btn active" data-market="futures" data-exchange="1">Futures</button>
                        <button class="market-btn" data-market="spot" data-exchange="1">Spot</button>
                    </div>
                    <span style="color: #9c27b0; font-weight: bold;">/</span>
                    <div class="market-toggle">
                        <button class="market-btn active" data-market="futures" data-exchange="2">Futures</button>
                        <button class="market-btn" data-market="spot" data-exchange="2">Spot</button>
                    </div>
                </div>
            </div>
            <div class="control-group">
                <label>&nbsp;</label>
                <button id="loadBtn" onclick="loadChart()">Load Chart</button>
            </div>
        </div>
        
        <div id="chartContainer">
            <div id="priceInfo" style="display: none;">
                <div class="price-row" id="priceInfoTime">
                    <span class="price-label">Time:</span>
                    <span class="price-value" id="infoTime">-</span>
                </div>
                <div class="price-row" id="priceInfoOpen">
                    <span class="price-label">Open:</span>
                    <span class="price-value" id="infoOpen">-</span>
                </div>
                <div class="price-row" id="priceInfoHigh">
                    <span class="price-label">High:</span>
                    <span class="price-value price-up" id="infoHigh">-</span>
                </div>
                <div class="price-row" id="priceInfoLow">
                    <span class="price-label">Low:</span>
                    <span class="price-value price-down" id="infoLow">-</span>
                </div>
                <div class="price-row" id="priceInfoClose">
                    <span class="price-label">Close:</span>
                    <span class="price-value" id="infoClose">-</span>
                </div>
                <div class="price-row hidden" id="spreadInfoRow">
                    <span class="price-label">Spread:</span>
                    <span class="price-value" id="infoSpread">-</span>
                </div>
                <div class="price-row hidden" id="spreadEx1Row">
                    <span class="price-label" id="ex1Label">Ex1:</span>
                    <span class="price-value" id="infoEx1">-</span>
                </div>
                <div class="price-row hidden" id="spreadEx2Row">
                    <span class="price-label" id="ex2Label">Ex2:</span>
                    <span class="price-value" id="infoEx2">-</span>
                </div>
            </div>
            <div class="loading" id="loading" style="display: none;">Loading chart data...</div>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <span class="status-label">Status:</span>
                <span class="status-value" id="status">Ready</span>
            </div>
            <div class="status-item">
                <span class="status-label">Data Points:</span>
                <span class="status-value" id="dataPoints">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">Time Range:</span>
                <span class="status-value" id="timeRange">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">Latest:</span>
                <span class="status-value" id="latestTime">-</span>
            </div>
            <div class="status-item hidden" id="spreadStatsContainer">
                <span class="status-label">Spread (Avg/Min/Max):</span>
                <span class="status-value spread-stats" id="spreadStats">-</span>
            </div>
        </div>
    </div>

    <script>
        let chart = null;
        let candlestickSeries = null;
        let spreadBaselineSeries = null;
        let spreadCandlestickSeries = null;
        let selectedMarket = 'futures';
        let selectedMarket1 = 'futures';
        let selectedMarket2 = 'futures';
        let selectedMode = 'price';
        let selectedSpreadChartType = 'baseline';
        let currentSpreadLineData = [];
        let currentSpreadCandleData = [];

        // Format timestamp for display (local time)
        function formatTime(timestamp) {
            const date = new Date(timestamp * 1000);
            return date.toLocaleString();
        }
        
        // Format timestamp for short display
        function formatTimeShort(timestamp) {
            const date = new Date(timestamp * 1000);
            return date.toLocaleTimeString();
        }

        // Initialize chart
        function initChart() {
            const container = document.getElementById('chartContainer');
            
            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight - 20,
                layout: {
                    background: { type: 'solid', color: '#16213e' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#1e3a5f' },
                    horzLines: { color: '#1e3a5f' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#1e3a5f',
                },
                timeScale: {
                    borderColor: '#1e3a5f',
                    timeVisible: true,
                    secondsVisible: false,
                    barSpacing: 6,
                    minBarSpacing: 1,
                },
                localization: {
                    timeFormatter: (timestamp) => {
                        const date = new Date(timestamp * 1000);
                        return date.toLocaleString();
                    },
                },
            });

            // Regular candlestick series for price chart
            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderDownColor: '#ef5350',
                borderUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                wickUpColor: '#26a69a',
            });
            
            // Baseline series for spread chart (line with fill)
            spreadBaselineSeries = chart.addBaselineSeries({
                baseValue: { type: 'price', price: 0 },
                topLineColor: '#26a69a',
                topFillColor1: 'rgba(38, 166, 154, 0.4)',
                topFillColor2: 'rgba(38, 166, 154, 0.1)',
                bottomLineColor: '#ef5350',
                bottomFillColor1: 'rgba(239, 83, 80, 0.1)',
                bottomFillColor2: 'rgba(239, 83, 80, 0.4)',
                lineWidth: 2,
                visible: false,
                priceLineVisible: true,
                lastValueVisible: true,
                priceFormat: {
                    type: 'custom',
                    formatter: (price) => price.toFixed(4) + '%',
                    minMove: 0.0001,
                },
            });
            
            // Candlestick series for spread OHLC
            spreadCandlestickSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderDownColor: '#ef5350',
                borderUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                wickUpColor: '#26a69a',
                visible: false,
                priceFormat: {
                    type: 'custom',
                    formatter: (price) => price.toFixed(4) + '%',
                    minMove: 0.0001,
                },
            });

            // Crosshair move handler
            chart.subscribeCrosshairMove((param) => {
                const priceInfo = document.getElementById('priceInfo');
                
                if (param.time) {
                    priceInfo.style.display = 'block';
                    document.getElementById('infoTime').textContent = formatTime(param.time);
                    
                    if (selectedMode === 'price') {
                        const data = param.seriesData.get(candlestickSeries);
                        if (data) {
                            document.getElementById('infoOpen').textContent = data.open.toFixed(2);
                            document.getElementById('infoHigh').textContent = data.high.toFixed(2);
                            document.getElementById('infoLow').textContent = data.low.toFixed(2);
                            document.getElementById('infoClose').textContent = data.close.toFixed(2);
                        }
                    } else {
                        // Spread mode
                        if (selectedSpreadChartType === 'baseline') {
                            const data = param.seriesData.get(spreadBaselineSeries);
                            if (data) {
                                const spreadVal = data.value;
                                const spreadEl = document.getElementById('infoSpread');
                                spreadEl.textContent = spreadVal.toFixed(4) + '%';
                                spreadEl.className = 'price-value ' + (spreadVal >= 0 ? 'spread-positive' : 'spread-negative');
                                
                                // Find matching data for exchange prices
                                const matchingPoint = currentSpreadLineData.find(d => d.time === param.time);
                                if (matchingPoint) {
                                    document.getElementById('infoEx1').textContent = matchingPoint.ex1_close.toFixed(4);
                                    document.getElementById('infoEx2').textContent = matchingPoint.ex2_close.toFixed(4);
                                }
                            }
                        } else {
                            // Candlestick spread
                            const data = param.seriesData.get(spreadCandlestickSeries);
                            if (data) {
                                const spreadVal = data.close;
                                const spreadEl = document.getElementById('infoSpread');
                                spreadEl.textContent = `O:${data.open.toFixed(3)}% H:${data.high.toFixed(3)}% L:${data.low.toFixed(3)}% C:${data.close.toFixed(3)}%`;
                                spreadEl.className = 'price-value ' + (spreadVal >= 0 ? 'spread-positive' : 'spread-negative');
                                
                                const matchingPoint = currentSpreadCandleData.find(d => d.time === param.time);
                                if (matchingPoint && matchingPoint.ex1_prices && matchingPoint.ex2_prices) {
                                    document.getElementById('infoEx1').textContent = matchingPoint.ex1_prices.close.toFixed(4);
                                    document.getElementById('infoEx2').textContent = matchingPoint.ex2_prices.close.toFixed(4);
                                }
                            }
                        }
                    }
                } else {
                    priceInfo.style.display = 'none';
                }
            });

            // Resize handler
            window.addEventListener('resize', () => {
                chart.applyOptions({
                    width: container.clientWidth,
                    height: container.clientHeight - 20,
                });
            });
        }

        // Mode toggle handlers
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMode = btn.dataset.mode;
                updateUIForMode();
            });
        });
        
        function updateUIForMode() {
            const singleExGroup = document.getElementById('singleExchangeGroup');
            const spreadExGroup = document.getElementById('spreadExchangeGroup');
            const singleMarketGroup = document.getElementById('singleMarketGroup');
            const spreadMarketGroup = document.getElementById('spreadMarketGroup');
            const spreadStatsContainer = document.getElementById('spreadStatsContainer');
            const spreadChartTypeGroup = document.getElementById('spreadChartTypeGroup');
            
            const priceRows = ['priceInfoOpen', 'priceInfoHigh', 'priceInfoLow', 'priceInfoClose'];
            const spreadRows = ['spreadInfoRow', 'spreadEx1Row', 'spreadEx2Row'];
            
            if (selectedMode === 'spread') {
                singleExGroup.classList.add('hidden');
                spreadExGroup.classList.remove('hidden');
                singleMarketGroup.classList.add('hidden');
                spreadMarketGroup.classList.remove('hidden');
                spreadStatsContainer.classList.remove('hidden');
                spreadChartTypeGroup.classList.remove('hidden');
                priceRows.forEach(id => document.getElementById(id).classList.add('hidden'));
                spreadRows.forEach(id => document.getElementById(id).classList.remove('hidden'));
            } else {
                singleExGroup.classList.remove('hidden');
                spreadExGroup.classList.add('hidden');
                singleMarketGroup.classList.remove('hidden');
                spreadMarketGroup.classList.add('hidden');
                spreadStatsContainer.classList.add('hidden');
                spreadChartTypeGroup.classList.add('hidden');
                priceRows.forEach(id => document.getElementById(id).classList.remove('hidden'));
                spreadRows.forEach(id => document.getElementById(id).classList.add('hidden'));
            }
        }

        // Market toggle - single mode
        document.querySelectorAll('#singleMarketGroup .market-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#singleMarketGroup .market-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMarket = btn.dataset.market;
            });
        });
        
        // Market toggle - spread mode exchange 1
        document.querySelectorAll('#spreadMarketGroup .market-btn[data-exchange="1"]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#spreadMarketGroup .market-btn[data-exchange="1"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMarket1 = btn.dataset.market;
            });
        });
        
        // Market toggle - spread mode exchange 2
        document.querySelectorAll('#spreadMarketGroup .market-btn[data-exchange="2"]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#spreadMarketGroup .market-btn[data-exchange="2"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMarket2 = btn.dataset.market;
            });
        });
        
        // Spread chart type toggle
        document.querySelectorAll('#spreadChartTypeGroup .chart-type-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#spreadChartTypeGroup .chart-type-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedSpreadChartType = btn.dataset.charttype;
                if (currentSpreadLineData.length > 0 || currentSpreadCandleData.length > 0) {
                    updateSpreadChartVisibility();
                }
            });
        });
        
        function updateSpreadChartVisibility() {
            if (selectedSpreadChartType === 'baseline') {
                spreadBaselineSeries.applyOptions({ visible: true });
                spreadCandlestickSeries.applyOptions({ visible: false });
            } else {
                spreadBaselineSeries.applyOptions({ visible: false });
                spreadCandlestickSeries.applyOptions({ visible: true });
            }
        }

        // Main load chart function
        async function loadChart() {
            const symbol = document.getElementById('symbol').value.toUpperCase();
            const interval = document.getElementById('interval').value;

            if (!symbol) {
                alert('Please enter a symbol');
                return;
            }

            const loadBtn = document.getElementById('loadBtn');
            const loading = document.getElementById('loading');
            const statusEl = document.getElementById('status');

            loadBtn.disabled = true;
            loading.style.display = 'block';
            statusEl.textContent = 'Loading...';

            try {
                if (selectedMode === 'price') {
                    await loadPriceChart(symbol, interval, statusEl);
                } else {
                    await loadSpreadChart(symbol, interval, statusEl);
                }
            } catch (error) {
                statusEl.innerHTML = `<span class="error">Error: ${error.message}</span>`;
                console.error('Error loading chart:', error);
            } finally {
                loadBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        async function loadPriceChart(symbol, interval, statusEl) {
            const exchange = document.getElementById('exchange').value;
            
            // Show regular candlestick, hide spread series
            candlestickSeries.applyOptions({ visible: true });
            spreadBaselineSeries.applyOptions({ visible: false });
            spreadCandlestickSeries.applyOptions({ visible: false });
            
            const resultStr = await pywebview.api.fetch_chart_data(exchange, symbol, interval, selectedMarket);
            const result = JSON.parse(resultStr);

            if (result.error) {
                throw new Error(result.error);
            }

            if (!result.data || result.data.length === 0) {
                throw new Error('No data returned from exchange');
            }

            // Update chart
            candlestickSeries.setData(result.data);
            spreadBaselineSeries.setData([]);
            spreadCandlestickSeries.setData([]);
            chart.timeScale().fitContent();

            // Update status
            statusEl.textContent = `Loaded: ${exchange.toUpperCase()} ${symbol} ${selectedMarket.toUpperCase()}`;
            document.getElementById('dataPoints').textContent = result.count;

            // Time range
            if (result.data.length > 0) {
                const firstDate = new Date(result.data[0].time * 1000).toLocaleString();
                const lastDate = new Date(result.data[result.data.length - 1].time * 1000).toLocaleString();
                document.getElementById('timeRange').textContent = `${new Date(result.data[0].time * 1000).toLocaleDateString()} - ${new Date(result.data[result.data.length - 1].time * 1000).toLocaleDateString()}`;
                document.getElementById('latestTime').textContent = lastDate;
            }
        }
        
        async function loadSpreadChart(symbol, interval, statusEl) {
            const exchange1 = document.getElementById('exchange1').value;
            const exchange2 = document.getElementById('exchange2').value;
            
            if (exchange1 === exchange2) {
                throw new Error('Please select two different exchanges');
            }
            
            // Update labels
            document.getElementById('ex1Label').textContent = 
                exchange1.charAt(0).toUpperCase() + exchange1.slice(1) + ` (${selectedMarket1}):`;
            document.getElementById('ex2Label').textContent = 
                exchange2.charAt(0).toUpperCase() + exchange2.slice(1) + ` (${selectedMarket2}):`;
            
            // Hide regular candlestick
            candlestickSeries.applyOptions({ visible: false });
            
            const resultStr = await pywebview.api.fetch_spread_data(
                exchange1, exchange2, symbol, interval, selectedMarket1, selectedMarket2
            );
            const result = JSON.parse(resultStr);

            if (result.error) {
                throw new Error(result.error);
            }

            if (!result.lineData || result.lineData.length === 0) {
                throw new Error('No matching data between exchanges');
            }

            // Store data for crosshair
            currentSpreadLineData = result.lineData;
            currentSpreadCandleData = result.candleData || [];
            
            // Prepare clean data for TradingView
            const cleanLineData = currentSpreadLineData
                .map(d => ({ time: d.time, value: d.value }))
                .sort((a, b) => a.time - b.time);
            
            const cleanCandleData = currentSpreadCandleData
                .map(d => ({
                    time: d.time,
                    open: d.open,
                    high: d.high,
                    low: d.low,
                    close: d.close
                }))
                .sort((a, b) => a.time - b.time);
            
            // Set data
            candlestickSeries.setData([]);
            spreadBaselineSeries.setData(cleanLineData);
            spreadCandlestickSeries.setData(cleanCandleData);
            
            updateSpreadChartVisibility();
            chart.timeScale().fitContent();

            // Update status
            statusEl.textContent = `Spread: ${exchange1.toUpperCase()} (${selectedMarket1}) vs ${exchange2.toUpperCase()} (${selectedMarket2}) - ${symbol}`;
            document.getElementById('dataPoints').textContent = result.count;
            
            if (result.stats) {
                document.getElementById('spreadStats').textContent = 
                    `${result.stats.avg}% / ${result.stats.min}% / ${result.stats.max}%`;
            }

            // Time range
            if (result.lineData.length > 0) {
                const firstDate = new Date(result.lineData[0].time * 1000).toLocaleString();
                const lastDate = new Date(result.lineData[result.lineData.length - 1].time * 1000).toLocaleString();
                document.getElementById('timeRange').textContent = `${new Date(result.lineData[0].time * 1000).toLocaleDateString()} - ${new Date(result.lineData[result.lineData.length - 1].time * 1000).toLocaleDateString()}`;
                document.getElementById('latestTime').textContent = lastDate;
            }
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', () => {
            initChart();
        });
    </script>
</body>
</html>
"""


def main():
    """Main entry point"""
    api = ChartAPI()
    
    window = webview.create_window(
        'Crypto Chart Viewer - TradingView Lightweight Charts',
        html=HTML_TEMPLATE,
        js_api=api,
        width=1400,
        height=900,
        min_size=(1000, 700),
        resizable=True
    )
    
    webview.start(debug=True)
    api.cleanup()


if __name__ == '__main__':
    main()
