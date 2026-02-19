"""
Continuous monitoring script for futures bid/ask spread arbitrage between MEXC and Gate.io
Sends Telegram alerts when spreads are found
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, UTC


# Load configuration
def load_config():
    """Load bot configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return {
            'telegram_token': config.get('telegram_bot_token'),
            'chat_id': config.get('telegram_chat_id'),
            'min_spread': config.get('min_spread', 2.4),
            'max_spread': config.get('max_spread', 50.0),
            'blocked_tokens': config.get('blocked_tokens', ["ALLUSDT", "FLOWUSDT", "1USDT"])
        }
    except Exception as e:
        print(f"⚠️ Warning: Could not load config: {e}")
        return {
            'telegram_token': None,
            'chat_id': None,
            'min_spread': 2.4,
            'max_spread': 50.0,
            'blocked_tokens': ["ALLUSDT", "FLOWUSDT", "1USDT"]
        }


CONFIG = load_config()
TELEGRAM_TOKEN = CONFIG['telegram_token']
CHAT_ID = CONFIG['chat_id']


async def send_telegram_alert(symbol: str, spread_pct: float, buy_exchange: str, buy_price: float, sell_exchange: str, sell_price: float):
    """Send Telegram alert for spread opportunity using main project format"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print(f"⚠️ Telegram not configured, skipping alert for {symbol}")
        return
    
    try:
        # Position sizing (matching main project)
        TOTAL_POSITION_USD = 50.0
        NUM_PARTS = 4
        
        # Calculate coin amounts - EQUAL on both exchanges
        if buy_price > 0 and sell_price > 0:
            coins_on_buy_exchange = TOTAL_POSITION_USD / buy_price
            coins_on_sell_exchange = TOTAL_POSITION_USD / sell_price
            max_equal_coins = min(coins_on_buy_exchange, coins_on_sell_exchange)
            part_coins = max_equal_coins / NUM_PARTS
            usd_needed_buy = max_equal_coins * buy_price
            usd_needed_sell = max_equal_coins * sell_price
        else:
            max_equal_coins = 0
            part_coins = 0
            usd_needed_buy = 0
            usd_needed_sell = 0
        
        # Format message (matching main project style)
        msg = f"🆕 **New Spread Detected!**\n\n"
        msg += f"`{symbol}` — **{spread_pct:.2f}%**\n\n"
        msg += f"📉 **BUY** on {buy_exchange} (futures)\n"
        msg += f"   Price: `${buy_price:.6f}`\n\n"
        msg += f"📈 **SELL** on {sell_exchange} (futures)\n"
        msg += f"   Price: `${sell_price:.6f}`\n\n"
        msg += f"💰 **Position (equal coins, ~${TOTAL_POSITION_USD:.0f}):**\n"
        msg += f"   Full: `{max_equal_coins:.6f}` coins\n"
        msg += f"   ÷4:   `{part_coins:.6f}` coins\n"
        msg += f"   📊 BUY: ${usd_needed_buy:.2f} | SELL: ${usd_needed_sell:.2f}\n\n"
        msg += f"⏰ {datetime.now(UTC).strftime('%H:%M:%S UTC')}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': msg,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    print(f"✅ Telegram alert sent for {symbol}")
                else:
                    print(f"❌ Failed to send Telegram alert: {response.status}")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")


async def fetch_gateio_futures() -> Dict[str, Tuple[float, float]]:
    """Fetch all Gate.io futures contracts with bid/ask prices"""
    url = "https://api.gateio.ws/api/v4/futures/usdt/tickers"
    headers = {
        'Accept': 'application/json', 
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    prices = {}  # {symbol: (bid, ask)}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                for ticker in data:
                    contract = ticker.get('contract', '')
                    highest_bid = ticker.get('highest_bid')
                    lowest_ask = ticker.get('lowest_ask')
                    
                    # Only include contracts with valid bid/ask
                    if highest_bid and lowest_ask:
                        try:
                            bid = float(highest_bid)
                            ask = float(lowest_ask)
                            if bid > 0 and ask > 0:
                                # Normalize symbol: BTC_USDT -> BTCUSDT
                                normalized = contract.replace('_', '')
                                prices[normalized] = (bid, ask)
                        except (ValueError, TypeError):
                            continue
                        
    print(f"✓ Gate.io: Fetched {len(prices)} contracts")
    return prices


async def fetch_mexc_futures() -> Dict[str, Tuple[float, float]]:
    """Fetch all MEXC futures contracts with bid/ask prices"""
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    prices = {}  # {symbol: (bid, ask)}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                if result.get('success') and result.get('data'):
                    data = result['data']
                    # Handle both list and single object responses
                    if isinstance(data, list):
                        for ticker in data:
                            symbol = ticker.get('symbol', '')
                            bid1 = ticker.get('bid1')
                            ask1 = ticker.get('ask1')
                            if bid1 and ask1:
                                try:
                                    bid = float(bid1)
                                    ask = float(ask1)
                                    if bid > 0 and ask > 0:
                                        # Normalize symbol: BTC_USDT -> BTCUSDT
                                        normalized = symbol.replace('_', '')
                                        prices[normalized] = (bid, ask)
                                except (ValueError, TypeError):
                                    continue
                    else:
                        # Single ticker response
                        symbol = data.get('symbol', '')
                        bid1 = data.get('bid1')
                        ask1 = data.get('ask1')
                        if bid1 and ask1:
                            try:
                                bid = float(bid1)
                                ask = float(ask1)
                                if bid > 0 and ask > 0:
                                    normalized = symbol.replace('_', '')
                                    prices[normalized] = (bid, ask)
                            except (ValueError, TypeError):
                                pass
                            
    print(f"✓ MEXC: Fetched {len(prices)} contracts")
    return prices


def is_blocked(symbol: str) -> bool:
    """Check if a symbol is in the blocked list"""
    blocked = CONFIG.get('blocked_tokens', [])
    return symbol in blocked or symbol.upper() in blocked


def calculate_spreads(gateio_prices: Dict[str, Tuple[float, float]], mexc_prices: Dict[str, Tuple[float, float]]) -> List[dict]:
    """Calculate bid/ask arbitrage spreads between exchanges
    
    For arbitrage:
    - Buy at the ASK price (what you pay)
    - Sell at the BID price (what you receive)
    
    Opportunity exists when one exchange's BID > another exchange's ASK
    """
    spreads = []
    min_spread = CONFIG['min_spread']
    max_spread = CONFIG['max_spread']
    
    # Find common symbols
    common_symbols = set(gateio_prices.keys()) & set(mexc_prices.keys())
    print(f"\n📊 Common symbols: {len(common_symbols)}")
    
    for symbol in common_symbols:
        # Skip blocked tokens
        if is_blocked(symbol):
            continue
        gateio_bid, gateio_ask = gateio_prices[symbol]
        mexc_bid, mexc_ask = mexc_prices[symbol]
        
        # Skip if prices are too small (likely errors)
        if min(gateio_bid, gateio_ask, mexc_bid, mexc_ask) < 0.00000001:
            continue
        
        # Check both arbitrage directions
        opportunities = []
        
        # Direction 1: Buy on MEXC (ask), Sell on Gate.io (bid)
        if gateio_bid > mexc_ask:
            spread_pct = ((gateio_bid - mexc_ask) / mexc_ask) * 100
            if min_spread <= spread_pct <= max_spread:
                opportunities.append({
                    'symbol': symbol,
                    'spread_pct': spread_pct,
                    'buy_exchange': 'MEXC',
                    'buy_price': mexc_ask,
                    'sell_exchange': 'Gate.io',
                    'sell_price': gateio_bid,
                    'gateio_bid': gateio_bid,
                    'gateio_ask': gateio_ask,
                    'mexc_bid': mexc_bid,
                    'mexc_ask': mexc_ask
                })
        
        # Direction 2: Buy on Gate.io (ask), Sell on MEXC (bid)
        if mexc_bid > gateio_ask:
            spread_pct = ((mexc_bid - gateio_ask) / gateio_ask) * 100
            if min_spread <= spread_pct <= max_spread:
                opportunities.append({
                    'symbol': symbol,
                    'spread_pct': spread_pct,
                    'buy_exchange': 'Gate.io',
                    'buy_price': gateio_ask,
                    'sell_exchange': 'MEXC',
                    'sell_price': mexc_bid,
                    'gateio_bid': gateio_bid,
                    'gateio_ask': gateio_ask,
                    'mexc_bid': mexc_bid,
                    'mexc_ask': mexc_ask
                })
        
        # Add all valid opportunities
        spreads.extend(opportunities)
    
    # Sort by spread percentage (highest first)
    spreads.sort(key=lambda x: x['spread_pct'], reverse=True)
    return spreads


def print_spreads(spreads: List[dict], timestamp: str) -> None:
    """Print spreads in a formatted table"""
    if not spreads:
        print(f"\n[{timestamp}] ❌ No arbitrage opportunities found")
        return
    
    print(f"\n{'='*100}")
    print(f"[{timestamp}] 🔥 ARBITRAGE OPPORTUNITIES - Found {len(spreads)} pairs")
    print(f"{'='*100}")
    print(f"{'Symbol':<12} {'Spread %':>9} {'Buy':<8} {'Ask Price':>14} {'Sell':<8} {'Bid Price':>14} {'Profit/Unit':>14}")
    print(f"{'-'*100}")
    
    for s in spreads:
        profit = s['sell_price'] - s['buy_price']
        print(f"{s['symbol']:<12} {s['spread_pct']:>8.2f}% {s['buy_exchange']:<8} ${s['buy_price']:>13.6f} {s['sell_exchange']:<8} ${s['sell_price']:>13.6f} ${profit:>13.6f}")
    
    print(f"{'='*100}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   • Total opportunities: {len(spreads)}")
    if spreads:
        print(f"   • Best spread: {spreads[0]['symbol']} at {spreads[0]['spread_pct']:.2f}%")
        avg_spread = sum(s['spread_pct'] for s in spreads) / len(spreads)
        print(f"   • Average spread: {avg_spread:.2f}%")


async def monitor_continuously(alert_threshold: float = None, check_interval: int = 5):
    """Continuously monitor for arbitrage opportunities and send Telegram alerts
    
    Args:
        alert_threshold: Minimum spread to send Telegram alert (uses config min_spread if None)
        check_interval: Seconds between checks (default 5)
    """
    if alert_threshold is None:
        alert_threshold = CONFIG['min_spread']
    
    print(f"🚀 Starting continuous monitoring...")
    print(f"   • Display threshold: {CONFIG['min_spread']}% (from config)")
    print(f"   • Alert threshold: {alert_threshold}%")
    print(f"   • Max spread: {CONFIG['max_spread']}%")
    print(f"   • Blocked tokens: {len(CONFIG['blocked_tokens'])}")
    print(f"   • Check interval: {check_interval}s")
    print(f"   • Telegram alerts: {'ENABLED' if TELEGRAM_TOKEN and CHAT_ID else 'DISABLED'}\n")
    
    iteration = 0
    alerted_pairs = set()  # Track which pairs we've already alerted on (reset every 100 iterations)
    
    while True:
        try:
            iteration += 1
            timestamp = datetime.now(UTC).strftime('%H:%M:%S UTC')
            
            # Clear alerted pairs cache periodically
            if iteration % 100 == 0:
                alerted_pairs.clear()
                print(f"\n🔄 [{timestamp}] Cleared alert cache (iteration {iteration})\n")
            
            # Fetch prices from both exchanges concurrently
            gateio_prices, mexc_prices = await asyncio.gather(
                fetch_gateio_futures(),
                fetch_mexc_futures()
            )
            
            # Calculate spreads
            spreads = calculate_spreads(gateio_prices, mexc_prices)
            
            # Display all spreads
            print_spreads(spreads, timestamp)
            
            # Send Telegram alerts for spreads above threshold
            if spreads and TELEGRAM_TOKEN and CHAT_ID:
                for spread in spreads:
                    if spread['spread_pct'] >= alert_threshold:
                        pair_key = f"{spread['symbol']}_{spread['buy_exchange']}_{spread['sell_exchange']}"
                        
                        # Only alert once per pair per cache cycle
                        if pair_key not in alerted_pairs:
                            await send_telegram_alert(
                                spread['symbol'],
                                spread['spread_pct'],
                                spread['buy_exchange'],
                                spread['buy_price'],
                                spread['sell_exchange'],
                                spread['sell_price']
                            )
                            alerted_pairs.add(pair_key)
                            await asyncio.sleep(1)  # Rate limit alerts
            
            # Wait before next check
            print(f"\n⏳ Waiting {check_interval}s until next check...\n")
            await asyncio.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in monitoring loop: {e}")
            print(f"⏳ Retrying in {check_interval}s...\n")
            await asyncio.sleep(check_interval)


async def single_check():
    """Run a single check (for testing)"""
    print("🚀 Running single check...\n")
    print(f"   • Using config: min={CONFIG['min_spread']}%, max={CONFIG['max_spread']}%")
    print(f"   • Blocked tokens: {CONFIG['blocked_tokens']}\n")
    
    gateio_prices, mexc_prices = await asyncio.gather(
        fetch_gateio_futures(),
        fetch_mexc_futures()
    )
    
    spreads = calculate_spreads(gateio_prices, mexc_prices)
    timestamp = datetime.now(UTC).strftime('%H:%M:%S UTC')
    print_spreads(spreads, timestamp)


if __name__ == "__main__":
    import sys
    
    # Check if user wants continuous monitoring or single check
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        asyncio.run(single_check())
    else:
        # Continuous monitoring - uses config.json for spread limits
        # Alert threshold matches config min_spread by default
        alert_at = CONFIG['min_spread']  # Alert when spread >= min_spread from config
        interval = 0  # Check every 5 seconds
        
        asyncio.run(monitor_continuously(alert_threshold=alert_at, check_interval=interval))
