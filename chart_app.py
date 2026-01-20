"""
Chart Application - Python Windows Desktop App using TradingView Lightweight Charts
This app allows viewing charts from all supported exchanges for both futures and spot markets.
"""

import asyncio
import sys
import os
import json
import webview
from datetime import datetime
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

# Standard intervals (will be converted to exchange-specific format)
INTERVALS = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']


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
    
    def fetch_chart_data(self, exchange: str, symbol: str, interval: str, market: str) -> str:
        """
        Fetch chart data for the specified parameters
        
        Args:
            exchange: Exchange name (binance, bitget, etc.)
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1h, 4h, 1d, etc.)
            market: 'futures' or 'spot'
            
        Returns:
            JSON string with chart data
        """
        try:
            # Run async function in event loop
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
        """Async method to fetch chart data"""
        if exchange not in EXCHANGES:
            return {'error': f'Unknown exchange: {exchange}', 'data': []}
        
        try:
            # Create exchange instance if not exists
            if exchange not in self.exchange_instances:
                self.exchange_instances[exchange] = EXCHANGES[exchange]()
            
            ex = self.exchange_instances[exchange]
            
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
            return {'error': str(e), 'data': []}
    
    def cleanup(self):
        """Cleanup exchange instances"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for ex in self.exchange_instances.values():
            try:
                loop.run_until_complete(ex.close())
            except:
                pass
        loop.close()


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
        .market-toggle {
            display: flex;
            gap: 5px;
        }
        .market-btn {
            padding: 8px 16px;
            border: 1px solid #333;
            background: #0f3460;
            cursor: pointer;
        }
        .market-btn.active {
            background: #4a9eff;
            border-color: #4a9eff;
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
            background: rgba(22, 33, 62, 0.9);
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 100;
        }
        .price-row {
            display: flex;
            gap: 15px;
            margin-bottom: 5px;
        }
        .price-label {
            color: #888;
            width: 50px;
        }
        .price-value {
            font-weight: bold;
        }
        .price-up { color: #26a69a; }
        .price-down { color: #ef5350; }
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <div class="control-group">
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
            <div class="control-group">
                <label>Market</label>
                <div class="market-toggle">
                    <button class="market-btn active" data-market="futures">Futures</button>
                    <button class="market-btn" data-market="spot">Spot</button>
                </div>
            </div>
            <div class="control-group">
                <label>&nbsp;</label>
                <button id="loadBtn" onclick="loadChart()">Load Chart</button>
            </div>
        </div>
        
        <div id="chartContainer">
            <div id="priceInfo" style="display: none;">
                <div class="price-row">
                    <span class="price-label">Open:</span>
                    <span class="price-value" id="infoOpen">-</span>
                </div>
                <div class="price-row">
                    <span class="price-label">High:</span>
                    <span class="price-value price-up" id="infoHigh">-</span>
                </div>
                <div class="price-row">
                    <span class="price-label">Low:</span>
                    <span class="price-value price-down" id="infoLow">-</span>
                </div>
                <div class="price-row">
                    <span class="price-label">Close:</span>
                    <span class="price-value" id="infoClose">-</span>
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
        </div>
    </div>

    <script>
        let chart = null;
        let candlestickSeries = null;
        let selectedMarket = 'futures';

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
                },
            });

            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderDownColor: '#ef5350',
                borderUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                wickUpColor: '#26a69a',
            });

            // Crosshair move handler for price info
            chart.subscribeCrosshairMove((param) => {
                const priceInfo = document.getElementById('priceInfo');
                if (param.time) {
                    const data = param.seriesData.get(candlestickSeries);
                    if (data) {
                        priceInfo.style.display = 'block';
                        document.getElementById('infoOpen').textContent = data.open.toFixed(2);
                        document.getElementById('infoHigh').textContent = data.high.toFixed(2);
                        document.getElementById('infoLow').textContent = data.low.toFixed(2);
                        document.getElementById('infoClose').textContent = data.close.toFixed(2);
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

        // Market toggle
        document.querySelectorAll('.market-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.market-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMarket = btn.dataset.market;
            });
        });

        // Load chart data
        async function loadChart() {
            const exchange = document.getElementById('exchange').value;
            const symbol = document.getElementById('symbol').value.toUpperCase();
            const interval = document.getElementById('interval').value;
            const market = selectedMarket;

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
                // Call Python API
                const resultStr = await pywebview.api.fetch_chart_data(exchange, symbol, interval, market);
                const result = JSON.parse(resultStr);

                if (result.error) {
                    throw new Error(result.error);
                }

                if (!result.data || result.data.length === 0) {
                    throw new Error('No data returned from exchange');
                }

                // Update chart
                candlestickSeries.setData(result.data);
                chart.timeScale().fitContent();

                // Update status
                statusEl.textContent = `Loaded: ${exchange.toUpperCase()} ${symbol} ${market.toUpperCase()}`;
                document.getElementById('dataPoints').textContent = result.count;

                // Calculate time range
                if (result.data.length > 0) {
                    const firstDate = new Date(result.data[0].time * 1000).toLocaleDateString();
                    const lastDate = new Date(result.data[result.data.length - 1].time * 1000).toLocaleDateString();
                    document.getElementById('timeRange').textContent = `${firstDate} - ${lastDate}`;
                }

            } catch (error) {
                statusEl.innerHTML = `<span class="error">Error: ${error.message}</span>`;
                console.error('Error loading chart:', error);
            } finally {
                loadBtn.disabled = false;
                loading.style.display = 'none';
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
    
    # Create window
    window = webview.create_window(
        'Crypto Chart Viewer - TradingView Lightweight Charts',
        html=HTML_TEMPLATE,
        js_api=api,
        width=1400,
        height=900,
        min_size=(1000, 700),
        resizable=True
    )
    
    # Start the application
    webview.start(debug=False)
    
    # Cleanup on exit
    api.cleanup()


if __name__ == '__main__':
    main()
