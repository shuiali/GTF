import asyncio
import logging
import pytz
import concurrent.futures
import threading
from typing import Dict, List, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from .binance import BinanceExchange
from .mexc import MEXCExchange
from .okx import OKXExchange
from .bybit import BybitExchange
from .htx import HTXExchange
from .gateio import GateioExchange
from .kucoin import KucoinExchange
from .bitget import BitgetExchange
from .bingx import BingXExchange
from .coinex import CoinExExchange
from .xt import XTExchange
from .bitmart import BitMartExchange
from .lbank import LBankExchange
from .ourbit import OurBitExchange
from .blofin import BloFinExchange
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class ExchangePath:
    """Represents a directional arbitrage path between two exchanges"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float  # ASK price on buy exchange (we buy at ask)
    sell_price: float  # BID price on sell exchange (we sell at bid)
    spread_percentage: float
    buy_market: str = 'futures'  # futures or margin
    sell_market: str = 'futures'
    buy_volume: float = 0
    sell_volume: float = 0
    
    @property
    def path_id(self) -> str:
        """Unique identifier for this path"""
        return f"{self.symbol}:{self.buy_exchange}_{self.buy_market}->{self.sell_exchange}_{self.sell_market}"


@dataclass 
class SymbolExchangeGraph:
    """Graph of all exchange paths for a symbol using bid/ask prices"""
    symbol: str
    exchanges: Dict[str, Dict] = field(default_factory=dict)  # {exchange: {bid, ask, volume, market}}
    paths: List[ExchangePath] = field(default_factory=list)  # All directional paths
    
    def add_exchange(self, exchange: str, bid: float, ask: float, volume: float, market: str = 'futures'):
        """Add an exchange node to the graph with bid/ask prices"""
        self.exchanges[exchange] = {
            'bid': bid,
            'ask': ask,
            'volume': volume,
            'market': market
        }
    
    def build_all_paths(self, min_spread: float = 0, max_spread: float = 100) -> List[ExchangePath]:
        """Build all possible bidirectional paths between exchanges using bid/ask"""
        self.paths = []
        exchange_list = list(self.exchanges.keys())
        
        # Generate all directional pairs (A→B and B→A are distinct)
        for i, ex_a in enumerate(exchange_list):
            for j, ex_b in enumerate(exchange_list):
                if i == j:
                    continue
                
                data_a = self.exchanges[ex_a]
                data_b = self.exchanges[ex_b]
                
                # Path: Buy on A (at ASK), Sell on B (at BID)
                # We BUY at the ASK price, we SELL at the BID price
                buy_price = data_a['ask']   # Buy at ask on exchange A
                sell_price = data_b['bid']   # Sell at bid on exchange B
                
                if buy_price <= 0 or sell_price <= 0:
                    continue
                
                # Spread = (sell_bid - buy_ask) / buy_ask * 100
                # This is the REAL spread accounting for bid/ask
                spread = ((sell_price - buy_price) / buy_price) * 100
                
                # Only include profitable paths (sell > buy) within limits
                if spread > min_spread and spread <= max_spread:
                    path = ExchangePath(
                        symbol=self.symbol,
                        buy_exchange=ex_a,
                        sell_exchange=ex_b,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        spread_percentage=round(spread, 4),
                        buy_market=data_a['market'],
                        sell_market=data_b['market'],
                        buy_volume=data_a['volume'],
                        sell_volume=data_b['volume']
                    )
                    self.paths.append(path)
        
        return self.paths

class FundingRateManager:
    def __init__(self):
        self.config = ConfigLoader()
        
        # All 8 exchanges enabled (LBank disabled due to data quality)
        self.exchanges = {
            'Binance': BinanceExchange(),
            'MEXC': MEXCExchange(),
            'OKX': OKXExchange(),
            'Bybit': BybitExchange(),
            'Gate.io': GateioExchange(),
            'KuCoin': KucoinExchange(),
            'BitGet': BitgetExchange(),
            'BingX': BingXExchange(),
            'CoinEx': CoinExExchange(),
            'XT': XTExchange(),
            'BitMart': BitMartExchange(),
            'LBank': LBankExchange(),
            'OurBit': OurBitExchange(),
            'BloFin': BloFinExchange(),
        }
        
        # Minimum 24h volume in USDT to include a token
        self.min_volume_usdt = 250000  # 50k USDT
        
        # Exchanges that support margin trading (have margin API implemented)
        self.margin_exchanges = ['Binance', 'Bybit', 'BitGet']

        # Remove all timeout restrictions
        for exchange in self.exchanges.values():
            exchange.request_timeout = 30.0  # Generous timeout
            exchange.rate_limit_ms = 0  # NO rate limit for max speed

        self.last_update = None
        self.last_margin_update = None
        self.update_interval = 0  # NO INTERVAL - always fetch fresh
        self.funding_data = {}
        self.margin_data = {}  # New: stores margin tokens and spot prices
        self.utc = pytz.UTC
        
        # Thread pool for concurrent execution
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=32)
        self._fetch_lock = threading.Lock()
        
        # Monitoring: Track known paths to detect new spreads
        self.known_spread_paths: Set[str] = set()  # Set of path_ids we've seen
        self.last_spreads: Dict[str, float] = {}  # path_id -> last spread percentage

    def _get_current_time(self) -> datetime:
        return datetime.now(self.utc)

    async def update_funding_data(self, prices_only: bool = False):
        """Fetch funding data from all exchanges EXTREMELY FAST with parallel execution
        
        Args:
            prices_only: If True, only fetch order books (for spread calculations)
        """
        current_time = self._get_current_time()
        
        # NO INTERVAL CHECK - always fetch fresh data
        
        # Initialize funding data dict first
        self.funding_data = {}
        
        # Create all tasks for MAXIMUM parallel execution
        all_tasks = []
        task_map = {}
        
        for exchange_name, exchange in self.exchanges.items():
            # Always fetch order books and volumes (needed for spreads with bid/ask)
            order_book_task = asyncio.create_task(exchange.fetch_order_book())
            volume_task = asyncio.create_task(exchange.fetch_volumes())
            
            all_tasks.extend([order_book_task, volume_task])
            task_map[order_book_task] = (exchange_name, 'order_books')
            task_map[volume_task] = (exchange_name, 'volumes')
            
            # Only fetch funding rates if NOT in prices_only mode
            if not prices_only:
                funding_task = asyncio.create_task(exchange.fetch_funding_rates())
                all_tasks.append(funding_task)
                task_map[funding_task] = (exchange_name, 'funding_rates')

        try:
            # Execute ALL tasks in parallel with NO TIMEOUT
            completed_results = await asyncio.gather(*all_tasks, return_exceptions=True)

            # Process results
            for i, res_or_exc in enumerate(completed_results):
                original_task = all_tasks[i] 
                exchange_name, data_type = task_map[original_task]
                
                if exchange_name not in self.funding_data:
                    self.funding_data[exchange_name] = {'funding_rates': {}, 'order_books': {}, 'volumes': {}}
                
                if isinstance(res_or_exc, Exception):
                    logger.debug(f"{exchange_name} {data_type} failed: {str(res_or_exc)}")
                elif res_or_exc:
                    if len(res_or_exc) > 0:
                        self.funding_data[exchange_name][data_type] = res_or_exc
                else:
                    logger.debug(f"{exchange_name} {data_type} returned empty result")

        except Exception as e:
            logger.error(f"Error updating funding data: {str(e)}", exc_info=True)
        finally:
            self.last_update = current_time
            
            # Create a clear status summary
            successful_exchanges = []
            failed_exchanges = []
            
            for ex_name, ex_data in self.funding_data.items():
                rates = ex_data.get('funding_rates', {})
                order_books = ex_data.get('order_books', {})
                volumes = ex_data.get('volumes', {})
                
                # In prices_only mode, success = order_books available
                # In full mode, success = both rates AND order_books available
                if prices_only:
                    if len(order_books) > 0:
                        successful_exchanges.append(f"{ex_name} ({len(order_books)} bid/ask, {len(volumes)} vols)")
                    else:
                        failed_exchanges.append(ex_name)
                else:
                    if len(rates) > 0 and len(order_books) > 0:
                        successful_exchanges.append(f"{ex_name} ({len(rates)} rates, {len(order_books)} bid/ask, {len(volumes)} vols)")
                    elif len(rates) > 0 or len(order_books) > 0:
                        failed_exchanges.append(f"{ex_name} (partial data)")
                    else:
                        failed_exchanges.append(ex_name)
            
            # Print a clear status summary
            mode_str = "BID/ASK ONLY ⚡" if prices_only else "FULL DATA"
            print("\n" + "="*60)
            print(f"📊 DATA FETCH STATUS ({mode_str})")
            print("="*60)
            print(f"✅ SUCCESSFUL ({len(successful_exchanges)}/{len(self.exchanges)}):")
            for ex in successful_exchanges:
                print(f"   • {ex}")
            if failed_exchanges:
                print(f"❌ FAILED/INCOMPLETE ({len(failed_exchanges)}): {', '.join(failed_exchanges)}")
            print(f"⏰ Last Update: {current_time.strftime('%H:%M:%S UTC')}")
            print("="*60 + "\n")
            
            logger.info(f"Update complete: {len(successful_exchanges)}/{len(self.exchanges)} exchanges operational")

    async def get_funding_opportunities(self) -> List[Dict]:
        """Get funding opportunities - PRIORITIZE BY HIGHEST RATE EXCHANGE FUNDING TIME"""
        await self.update_funding_data()
        
        # Get exchanges that have BOTH funding rates AND order_books
        working_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('funding_rates', {})) > 0 and len(ex_data.get('order_books', {})) > 0:
                working_exchanges.append(ex_name)
        
        logger.info(f"Working exchanges with complete data: {working_exchanges}")
        
        if len(working_exchanges) < 2:
            logger.error(f"Not enough exchanges with data: {working_exchanges}")
            return []
            
        opportunities = []
        
        # Get all symbols that exist on at least 2 exchanges
        all_symbols = set()
        for ex_name in working_exchanges:
            rates = self.funding_data[ex_name].get('funding_rates', {})
            all_symbols.update(rates.keys())
        
        logger.info(f"Processing {len(all_symbols)} unique symbols across {len(working_exchanges)} exchanges")
        
        # For each symbol, find the MAXIMUM arbitrage profit
        for symbol in all_symbols:
            symbol_rates = {}
            symbol_order_books = {}
            
            # Collect funding rates and order books for this symbol from all exchanges
            for ex_name in working_exchanges:
                rates = self.funding_data[ex_name].get('funding_rates', {})
                order_books = self.funding_data[ex_name].get('order_books', {})
                volumes = self.funding_data[ex_name].get('volumes', {})
                
                if symbol in rates and symbol in order_books:
                    # Smart volume filtering - only filter if we have actual volume data
                    volume = volumes.get(symbol, float('inf'))  # Default to infinity if no volume data
                    if volume >= self.min_volume_usdt or volume == float('inf'):
                        symbol_rates[ex_name] = rates[symbol]
                        symbol_order_books[ex_name] = order_books[symbol]
            
            # Need at least 2 exchanges for this symbol
            if len(symbol_rates) < 2:
                continue
            
            # Find the MAXIMUM arbitrage profit for this symbol
            max_profit = 0
            best_opportunity = None
            
            # Strategy: Go LONG on exchange with LOWEST funding rate (receive less negative funding)
            #          Go SHORT on exchange with HIGHEST funding rate (receive more positive funding)
            # Profit = (SHORT_exchange_funding) - (LONG_exchange_funding)
            
            exchange_names = list(symbol_rates.keys())
            for i in range(len(exchange_names)):
                for j in range(len(exchange_names)):
                    if i == j:
                        continue
                    
                    # Exchange i = SHORT position (receive funding)
                    # Exchange j = LONG position (pay funding)
                    ex_short = exchange_names[i]
                    ex_long = exchange_names[j]
                    
                    rate_short = symbol_rates[ex_short].funding_rate  # We RECEIVE this
                    rate_long = symbol_rates[ex_long].funding_rate    # We PAY this
                    
                    # Use bid/ask for accurate spread calculation:
                    # SHORT on ex_short: we sell, so we hit the BID price
                    # LONG on ex_long: we buy, so we hit the ASK price
                    bid_short = symbol_order_books[ex_short]['bid']  # We sell at bid
                    ask_long = symbol_order_books[ex_long]['ask']     # We buy at ask
                    
                    # Net profit = funding_received - funding_paid
                    # For arbitrage, we want: rate_short - rate_long > 0
                    # This means: rate_short > rate_long (short on high funding, long on low funding)
                    profit = rate_short - rate_long
                    
                    # Only consider if profit is positive and meaningful
                    if profit > max_profit and profit > 0.0001:  # 0.01% minimum
                        max_profit = profit
                        
                        # Price spread using bid/ask: we buy at ask on ex_long, sell at bid on ex_short
                        # Spread = (bid_short - ask_long) / ask_long * 100
                        # Positive = profitable price spread, Negative = cost to enter
                        price_spread = ((bid_short - ask_long) / ask_long) * 100
                        
                        # PRIORITIZE BY HIGHEST RATE EXCHANGE FUNDING TIME
                        # Use the funding time from the exchange with the higher rate (SHORT position)
                        priority_funding_time = symbol_rates[ex_short].next_funding_time
                        
                        best_opportunity = {
                            'symbol': symbol,
                            'funding_rate_high': round(rate_short * 100, 4),    # SHORT here (high funding)
                            'funding_rate_low': round(rate_long * 100, 4),     # LONG here (low funding)
                            'exchange_high': ex_short,  # SHORT position exchange
                            'exchange_low': ex_long,    # LONG position exchange  
                            'price_spread': round(price_spread, 4),
                            'bid_price': bid_short,
                            'ask_price': ask_long,
                            'next_funding': priority_funding_time,  # Use highest rate exchange funding time
                            'spread_magnitude': round(max_profit * 100, 4)  # For sorting
                        }
            
            # Add the best opportunity for this symbol
            if best_opportunity:
                opportunities.append(best_opportunity)
                logger.debug(f"Best opportunity for {symbol}: SHORT {best_opportunity['exchange_high']} ({best_opportunity['funding_rate_high']}%) - LONG {best_opportunity['exchange_low']} ({best_opportunity['funding_rate_low']}%) = {best_opportunity['spread_magnitude']}%")
        
        logger.info(f"Found {len(opportunities)} funding opportunities")
        
        # Sort by profit magnitude (largest first)
        return sorted(opportunities, key=lambda x: x['spread_magnitude'], reverse=True)

    async def get_price_spreads(self) -> List[Dict]:
        """Get price spreads between exchanges for spot arbitrage opportunities - USING BID/ASK"""
        await self.update_funding_data()
        
        # Get exchanges that have order book data
        working_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('order_books', {})) > 0:
                working_exchanges.append(ex_name)
        
        logger.info(f"Working exchanges with order book data: {working_exchanges}")
        
        if len(working_exchanges) < 2:
            logger.error(f"Not enough exchanges with order book data: {working_exchanges}")
            return []
            
        spreads = []
        
        # Get all symbols that exist on at least 2 exchanges
        all_symbols = set()
        for ex_name in working_exchanges:
            order_books = self.funding_data[ex_name].get('order_books', {})
            all_symbols.update(order_books.keys())
        
        logger.info(f"Processing {len(all_symbols)} unique symbols for price spreads")
        
        # For each symbol, find the price spread using bid/ask
        for symbol in all_symbols:
            symbol_order_books = {}
            
            # Collect order books for this symbol from all exchanges
            for ex_name in working_exchanges:
                order_books = self.funding_data[ex_name].get('order_books', {})
                if symbol in order_books:
                    symbol_order_books[ex_name] = order_books[symbol]
            
            # Need at least 2 exchanges for this symbol
            if len(symbol_order_books) < 2:
                continue
            
            # Find best spread: max(sell_bid) - min(buy_ask)
            # We sell at BID price, buy at ASK price
            best_sell = None
            best_sell_ex = None
            best_buy = None
            best_buy_ex = None
            
            for ex_name, ob in symbol_order_books.items():
                bid = ob.get('bid', 0)
                ask = ob.get('ask', 0)
                
                if bid > 0:
                    if best_sell is None or bid > best_sell:
                        best_sell = bid
                        best_sell_ex = ex_name
                
                if ask > 0:
                    if best_buy is None or ask < best_buy:
                        best_buy = ask
                        best_buy_ex = ex_name
            
            if best_sell and best_buy and best_sell > 0 and best_buy > 0:
                # Calculate spread percentage: (sell_bid - buy_ask) / buy_ask * 100
                spread_percentage = ((best_sell - best_buy) / best_buy) * 100
                
                # Only consider meaningful spreads (> 0.1%)
                if spread_percentage > 0.1:
                    spreads.append({
                        'symbol': symbol,
                        'spread_percentage': round(spread_percentage, 2),
                        'sell_bid': best_sell,
                        'buy_ask': best_buy,
                        'sell_exchange': best_sell_ex,
                        'buy_exchange': best_buy_ex,
                        'exchanges_count': len(symbol_order_books)
                    })
        
        logger.info(f"Found {len(spreads)} price spreads")
        
        # Sort by spread percentage (largest first)
        return sorted(spreads, key=lambda x: x['spread_percentage'], reverse=True)

    async def get_next_funding_times(self) -> Dict[str, datetime]:
        """Get next funding times from all exchanges"""
        await self.update_funding_data()
        
        times = {}
        for exchange_name, data in self.funding_data.items():
            rates = data.get('funding_rates', {})
            if rates:
                first_rate_info = next(iter(rates.values()), None)
                if first_rate_info:
                    times[exchange_name] = first_rate_info.next_funding_time
        
        return times

    async def update_margin_data(self):
        """Fetch margin tokens and spot prices from all supported exchanges - NO INTERVAL CHECK"""
        current_time = self._get_current_time()
        
        # NO INTERVAL CHECK - always fetch fresh data
        
        # Initialize margin data dict
        self.margin_data = {}
        
        # Create tasks for margin exchanges only
        all_tasks = []
        task_map = {}
        
        for exchange_name in self.margin_exchanges:
            if exchange_name not in self.exchanges:
                continue
            exchange = self.exchanges[exchange_name]
            
            margin_task = asyncio.create_task(exchange.fetch_margin_tokens())
            spot_task = asyncio.create_task(exchange.fetch_spot_prices())
            
            all_tasks.extend([margin_task, spot_task])
            task_map[margin_task] = (exchange_name, 'margin_tokens')
            task_map[spot_task] = (exchange_name, 'spot_prices')
        
        try:
            completed_results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            for i, res_or_exc in enumerate(completed_results):
                original_task = all_tasks[i]
                exchange_name, data_type = task_map[original_task]
                
                if exchange_name not in self.margin_data:
                    self.margin_data[exchange_name] = {'margin_tokens': {}, 'spot_prices': {}}
                
                if isinstance(res_or_exc, Exception):
                    logger.debug(f"{exchange_name} {data_type} failed: {str(res_or_exc)}")
                elif res_or_exc:
                    if len(res_or_exc) > 0:
                        self.margin_data[exchange_name][data_type] = res_or_exc
                else:
                    logger.debug(f"{exchange_name} {data_type} returned empty result")
        
        except Exception as e:
            logger.error(f"Error updating margin data: {str(e)}", exc_info=True)
        finally:
            self.last_margin_update = current_time
            
            # Log status
            successful = []
            for ex_name, ex_data in self.margin_data.items():
                tokens = len(ex_data.get('margin_tokens', {}))
                prices = len(ex_data.get('spot_prices', {}))
                if tokens > 0 and prices > 0:
                    successful.append(f"{ex_name} ({tokens} tokens, {prices} prices)")
            
            print(f"\n📊 MARGIN DATA: {', '.join(successful) if successful else 'None'}\n")
            logger.info(f"Margin update complete: {len(successful)}/{len(self.margin_exchanges)} exchanges")

    async def get_margin_opportunities(self) -> List[Dict]:
        """
        Get futures-margin arbitrage opportunities (spot-futures spread).
        Strategy: For NEGATIVE funding rates:
        - LONG on futures (receive funding when rate is negative)
        - SHORT on margin (sell spot without funding costs)
        
        Returns grouped opportunities by token with all exchange combinations.
        Best margin exchange is the one with price spread closest to 0%.
        """
        await self.update_funding_data()
        await self.update_margin_data()
        
        # Get all exchanges with complete futures data (using order_books now)
        futures_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('funding_rates', {})) > 0 and len(ex_data.get('order_books', {})) > 0:
                futures_exchanges.append(ex_name)
        
        # Get all margin tokens available across exchanges
        all_margin_tokens = set()
        margin_exchange_tokens = {}  # {exchange: {token: True}}
        for ex_name, ex_data in self.margin_data.items():
            margin_tokens = ex_data.get('margin_tokens', {})
            all_margin_tokens.update(margin_tokens.keys())
            margin_exchange_tokens[ex_name] = margin_tokens
        
        logger.info(f"Futures exchanges: {futures_exchanges}")
        logger.info(f"Total margin tokens available: {len(all_margin_tokens)}")
        
        if not futures_exchanges or not all_margin_tokens:
            logger.error("Not enough data for margin opportunities")
            return []
        
        # Group opportunities by token symbol
        token_opportunities = {}  # {symbol: {'best': {...}, 'all_exchanges': {...}}}
        
        # For each futures symbol with NEGATIVE funding
        for ex_name in futures_exchanges:
            rates = self.funding_data[ex_name].get('funding_rates', {})
            order_books = self.funding_data[ex_name].get('order_books', {})
            volumes = self.funding_data[ex_name].get('volumes', {})
            
            for symbol, funding_info in rates.items():
                funding_rate = funding_info.funding_rate
                
                # Only consider NEGATIVE funding rates < -0.5% (we LONG futures to RECEIVE funding)
                if funding_rate >= -0.005:  # -0.5%
                    continue
                
                # Smart volume filtering - only filter if we have actual volume data
                volume = volumes.get(symbol, float('inf'))
                if volume < self.min_volume_usdt and volume != float('inf'):
                    continue
                
                # Extract base token (e.g., BTC from BTCUSDT)
                base_token = None
                if symbol.endswith('USDT'):
                    base_token = symbol[:-4]
                elif symbol.endswith('USD'):
                    base_token = symbol[:-3]
                else:
                    continue
                
                # Check if this token is available on any margin exchange
                if base_token not in all_margin_tokens:
                    continue
                
                # Use mid price from order book for margin comparisons
                ob = order_books.get(symbol, {})
                bid = ob.get('bid', 0)
                ask = ob.get('ask', 0)
                if bid <= 0 or ask <= 0:
                    continue
                futures_price = (bid + ask) / 2  # Mid price for margin comparison
                
                # Initialize token entry if not exists
                if symbol not in token_opportunities:
                    token_opportunities[symbol] = {
                        'symbol': symbol,
                        'base_token': base_token,
                        'futures_exchanges': {},  # {ex_name: {rate, price, next_funding}}
                        'margin_exchanges': {},   # {ex_name: {price, spread}}
                    }
                
                # Add futures exchange data
                token_opportunities[symbol]['futures_exchanges'][ex_name] = {
                    'funding_rate': funding_rate,
                    'price': futures_price,
                    'next_funding': funding_info.next_funding_time
                }
        
        # Now collect margin data for all tokens we found
        for symbol, token_data in token_opportunities.items():
            base_token = token_data['base_token']
            
            for margin_ex in self.margin_data.keys():
                margin_tokens = self.margin_data[margin_ex].get('margin_tokens', {})
                spot_prices = self.margin_data[margin_ex].get('spot_prices', {})
                
                if base_token not in margin_tokens:
                    continue
                
                # Look for spot price (try multiple formats)
                spot_symbol_variants = [
                    f"{base_token}USDT",
                    f"{base_token}USD",
                    f"{base_token}-USDT",
                    f"{base_token}_USDT",
                ]
                
                spot_price = 0
                for spot_symbol in spot_symbol_variants:
                    if spot_symbol in spot_prices:
                        spot_price = spot_prices[spot_symbol]
                        break
                
                if spot_price > 0:
                    token_data['margin_exchanges'][margin_ex] = {
                        'price': spot_price
                    }
        
        # Build final opportunities list
        opportunities = []
        
        for symbol, token_data in token_opportunities.items():
            if not token_data['futures_exchanges'] or not token_data['margin_exchanges']:
                continue
            
            # Find the best futures exchange (most negative funding rate = highest profit)
            best_futures_ex = None
            best_funding_rate = 0  # Looking for most negative
            
            for ex_name, ex_data in token_data['futures_exchanges'].items():
                if ex_data['funding_rate'] < best_funding_rate:
                    best_funding_rate = ex_data['funding_rate']
                    best_futures_ex = ex_name
            
            if not best_futures_ex:
                continue
            
            best_futures_data = token_data['futures_exchanges'][best_futures_ex]
            futures_price = best_futures_data['price']
            
            # Calculate spreads for all margin exchanges and find the one closest to 0%
            best_margin_ex = None
            best_spread = float('inf')  # Looking for closest to 0
            
            for margin_ex, margin_data in token_data['margin_exchanges'].items():
                spot_price = margin_data['price']
                # Spread = (spot - futures) / futures * 100
                price_spread = ((spot_price - futures_price) / futures_price) * 100
                margin_data['spread'] = price_spread
                
                # Find margin exchange with spread closest to 0%
                if abs(price_spread) < abs(best_spread):
                    best_spread = price_spread
                    best_margin_ex = margin_ex
            
            if not best_margin_ex:
                continue
            
            best_margin_data = token_data['margin_exchanges'][best_margin_ex]
            funding_profit = abs(best_funding_rate) * 100  # Convert to percentage
            
            opportunities.append({
                'symbol': symbol,
                'base_token': token_data['base_token'],
                'funding_rate': round(best_funding_rate * 100, 4),  # In percentage
                'funding_profit': round(funding_profit, 4),
                'futures_exchange': best_futures_ex,
                'futures_price': futures_price,
                'margin_exchange': best_margin_ex,
                'spot_price': best_margin_data['price'],
                'price_spread': round(best_spread, 4),
                'next_funding': best_futures_data['next_funding'],
                'spread_magnitude': round(funding_profit, 4),  # For sorting (higher = better)
                # NEW: Include all exchange data for detailed view
                'all_futures_exchanges': token_data['futures_exchanges'],
                'all_margin_exchanges': token_data['margin_exchanges'],
            })
        
        logger.info(f"Found {len(opportunities)} margin arbitrage opportunities")
        
        # Sort by funding profit (highest absolute negative rate first)
        return sorted(opportunities, key=lambda x: x['spread_magnitude'], reverse=True)

    async def get_cross_market_spreads(self, mode: str = 'futures-futures') -> List[Dict]:
        """
        Get price spreads across different market types - OPTIMIZED FOR SPEED.
        Only fetches the data needed for the specific mode.
        
        Modes:
        - futures-futures: Compare futures prices across all exchanges (PRICES ONLY)
        - margin-futures: Compare margin (spot) prices vs futures prices
        - futures-margin: Same as margin-futures but reversed perspective
        
        Returns list of best spread opportunities.
        """
        if mode == 'futures-futures':
            # SPEED OPTIMIZATION: Only fetch prices for futures-futures mode
            await self.update_funding_data(prices_only=True)
        else:
            # For margin modes, need both futures and margin data
            await asyncio.gather(
                self.update_funding_data(prices_only=True),
                self.update_margin_data()
            )
        
        if mode == 'futures-futures':
            return await self._get_futures_futures_spreads()
        elif mode in ['margin-futures', 'futures-margin']:
            return await self._get_margin_futures_spreads(mode)
        else:
            return []
    
    async def _get_futures_futures_spreads(self) -> List[Dict]:
        """
        Build complete bidirectional exchange-pair mapping for all symbols.
        Generates ALL possible directional arbitrage paths (A→B and B→A are distinct).
        Uses bid/ask prices for accurate spread calculation.
        Returns all feasible arbitrage routes per symbol.
        """
        # Get min/max spread limits from config
        min_spread = self.config.min_spread
        max_spread = self.config.max_spread
        
        # Get exchanges that have order book data
        working_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('order_books', {})) > 0:
                working_exchanges.append(ex_name)
        
        logger.info(f"Futures exchanges with bid/ask data: {working_exchanges}")
        print(f"\n🔍 BUILDING EXCHANGE-PAIR GRAPH (BID/ASK): {len(working_exchanges)} exchanges")
        
        if len(working_exchanges) < 2:
            logger.error(f"Not enough futures exchanges with order book data")
            return []
        
        # Build symbol->exchange graph for all symbols
        symbol_graphs: Dict[str, SymbolExchangeGraph] = {}
        
        # Collect all symbols and their order books across all exchanges
        all_symbols = set()
        for ex_name in working_exchanges:
            order_books = self.funding_data[ex_name].get('order_books', {})
            all_symbols.update(order_books.keys())
        
        print(f"   Total unique symbols: {len(all_symbols)}")
        
        # Build the graph for each symbol
        for symbol in all_symbols:
            graph = SymbolExchangeGraph(symbol=symbol)
            
            for ex_name in working_exchanges:
                order_books = self.funding_data[ex_name].get('order_books', {})
                volumes = self.funding_data[ex_name].get('volumes', {})
                
                if symbol in order_books:
                    ob = order_books[symbol]
                    bid = ob.get('bid', 0)
                    ask = ob.get('ask', 0)
                    volume = volumes.get(symbol, float('inf'))
                    
                    # Filter out zero or invalid prices
                    if bid and bid > 0.0000001 and ask and ask > 0.0000001:
                        # Only filter by volume if we have actual volume data
                        if volume < self.min_volume_usdt and volume != float('inf'):
                            continue
                        graph.add_exchange(ex_name, bid, ask, volume, 'futures')
            
            # Only keep graphs with 2+ exchanges
            if len(graph.exchanges) >= 2:
                symbol_graphs[symbol] = graph
        
        print(f"   Symbols with 2+ exchanges: {len(symbol_graphs)}")
        
        # Calculate total possible exchange pairs
        num_exchanges = len(working_exchanges)
        total_possible_pairs = num_exchanges * (num_exchanges - 1)  # Directional pairs
        print(f"   Possible exchange pairs (directional): {total_possible_pairs}")
        
        # Build all paths for all symbols and collect profitable ones
        all_paths: List[ExchangePath] = []
        spreads = []
        
        for symbol, graph in symbol_graphs.items():
            # Build all directional paths for this symbol
            paths = graph.build_all_paths(min_spread, max_spread)
            all_paths.extend(paths)
            
            # Convert paths to spread format for compatibility
            for path in paths:
                # Build all_prices in consistent format with bid/ask
                all_prices_formatted = {}
                for ex_name, data in graph.exchanges.items():
                    all_prices_formatted[f"{ex_name}_{data['market']}"] = {
                        'exchange': ex_name,
                        'market': data['market'],
                        'bid': data['bid'],
                        'ask': data['ask'],
                        'symbol': symbol
                    }
                
                spreads.append({
                    'symbol': symbol,
                    'spread_percentage': path.spread_percentage,
                    'sell_bid': path.sell_price,    # Sell at bid on sell exchange
                    'buy_ask': path.buy_price,      # Buy at ask on buy exchange
                    'highest_exchange': path.sell_exchange,
                    'highest_market': path.sell_market,
                    'lowest_exchange': path.buy_exchange,
                    'lowest_market': path.buy_market,
                    'all_prices': all_prices_formatted,
                    'exchanges_count': len(graph.exchanges),
                    'futures_count': len(graph.exchanges),
                    'margin_count': 0,
                    'mode': 'futures-futures',
                    'path_id': path.path_id,
                    'buy_volume': path.buy_volume,
                    'sell_volume': path.sell_volume,
                    # Include full graph data for analysis
                    'all_exchanges': list(graph.exchanges.keys()),
                    'all_paths_count': len(paths)
                })
        
        print(f"   Total profitable paths found: {len(all_paths)}")
        print(f"   Spreads within limits ({min_spread}% - {max_spread}%): {len(spreads)}")
        
        # Store the graph data for monitoring
        self._symbol_graphs = symbol_graphs
        
        logger.info(f"Found {len(spreads)} futures-futures spread paths")
        return sorted(spreads, key=lambda x: x['spread_percentage'], reverse=True)
    
    def detect_new_spreads(self, spreads: List[Dict]) -> List[Dict]:
        """
        Compare current spreads against known spreads to detect new opportunities.
        Returns list of newly appearing spreads.
        """
        new_spreads = []
        
        for spread in spreads:
            path_id = spread.get('path_id')
            if not path_id:
                # Generate path_id for legacy format
                path_id = f"{spread['symbol']}:{spread['lowest_exchange']}_futures->{spread['highest_exchange']}_futures"
            
            # Check if this is a new path we haven't seen
            if path_id not in self.known_spread_paths:
                new_spreads.append(spread)
                self.known_spread_paths.add(path_id)
                self.last_spreads[path_id] = spread['spread_percentage']
            else:
                # Check if spread has significantly increased (optional: alert on large changes)
                last_spread = self.last_spreads.get(path_id, 0)
                if spread['spread_percentage'] > last_spread * 1.5:  # 50% increase
                    spread['spread_increase'] = spread['spread_percentage'] - last_spread
                    new_spreads.append(spread)
                self.last_spreads[path_id] = spread['spread_percentage']
        
        return new_spreads
    
    def get_exchange_pair_summary(self) -> Dict:
        """
        Get summary of all exchange pairs and their symbol coverage.
        Returns a map of exchange-pair -> list of tradable symbols.
        """
        if not hasattr(self, '_symbol_graphs') or not self._symbol_graphs:
            return {}
        
        pair_map: Dict[str, List[str]] = {}
        
        for symbol, graph in self._symbol_graphs.items():
            exchanges = list(graph.exchanges.keys())
            
            # Generate all directional pairs
            for ex_a in exchanges:
                for ex_b in exchanges:
                    if ex_a != ex_b:
                        pair_key = f"{ex_a} → {ex_b}"
                        if pair_key not in pair_map:
                            pair_map[pair_key] = []
                        pair_map[pair_key].append(symbol)
        
        return pair_map
    
    async def _get_margin_futures_spreads(self, mode: str) -> List[Dict]:
        """
        Get price spreads between margin (spot) and futures markets.
        Compares all combinations of margin exchanges with futures exchanges.
        Uses order book data (bid/ask) for futures.
        """
        # Get min/max spread limits from config
        min_spread = self.config.min_spread
        max_spread = self.config.max_spread
        
        # Get futures exchanges with order book data
        futures_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('order_books', {})) > 0:
                futures_exchanges.append(ex_name)
        
        # Get margin exchanges with spot price data
        margin_exchanges_data = {}
        for ex_name, ex_data in self.margin_data.items():
            spot_prices = ex_data.get('spot_prices', {})
            margin_tokens = ex_data.get('margin_tokens', {})
            if len(spot_prices) > 0 and len(margin_tokens) > 0:
                margin_exchanges_data[ex_name] = {
                    'spot_prices': spot_prices,
                    'margin_tokens': margin_tokens
                }
        
        logger.info(f"Futures exchanges: {futures_exchanges}")
        logger.info(f"Margin exchanges: {list(margin_exchanges_data.keys())}")
        
        if not futures_exchanges or not margin_exchanges_data:
            logger.error("Not enough data for margin-futures spreads")
            return []
        
        spreads = []
        
        # Build a map of all tradable symbols
        # Get all base tokens from futures (e.g., BTC from BTCUSDT)
        futures_tokens = {}  # {base_token: {exchange: {symbol, bid, ask}}}
        
        for ex_name in futures_exchanges:
            order_books = self.funding_data[ex_name].get('order_books', {})
            volumes = self.funding_data[ex_name].get('volumes', {})
            for symbol, ob in order_books.items():
                bid = ob.get('bid', 0)
                ask = ob.get('ask', 0)
                # Filter out zero or invalid prices; smart volume filtering
                volume = volumes.get(symbol, float('inf'))  # Default to infinity if no volume data
                if not bid or bid <= 0.0000001 or not ask or ask <= 0.0000001:
                    continue
                # Only filter by volume if we have actual volume data
                if volume < self.min_volume_usdt and volume != float('inf'):
                    continue
                    
                base_token = None
                if symbol.endswith('USDT'):
                    base_token = symbol[:-4]
                elif symbol.endswith('USD'):
                    base_token = symbol[:-3]
                
                if base_token:
                    if base_token not in futures_tokens:
                        futures_tokens[base_token] = {}
                    futures_tokens[base_token][ex_name] = {
                        'symbol': symbol,
                        'bid': bid,
                        'ask': ask,
                        'market': 'futures'
                    }
        
        # Get margin/spot prices
        margin_tokens = {}  # {base_token: {exchange: {symbol, price}}}
        
        for ex_name, ex_data in margin_exchanges_data.items():
            spot_prices = ex_data['spot_prices']
            tradable_tokens = ex_data['margin_tokens']
            
            for symbol, price in spot_prices.items():
                # Filter out zero or invalid prices
                if not price or price <= 0.0000001:
                    continue
                    
                base_token = None
                if symbol.endswith('USDT'):
                    base_token = symbol[:-4]
                elif symbol.endswith('USD'):
                    base_token = symbol[:-3]
                elif '_USDT' in symbol:
                    base_token = symbol.split('_')[0]
                elif '-USDT' in symbol:
                    base_token = symbol.split('-')[0]
                
                if base_token and base_token in tradable_tokens:
                    if base_token not in margin_tokens:
                        margin_tokens[base_token] = {}
                    margin_tokens[base_token][ex_name] = {
                        'symbol': symbol,
                        'price': price,
                        'market': 'margin'
                    }
        
        # Find tokens available on both futures and margin
        common_tokens = set(futures_tokens.keys()) & set(margin_tokens.keys())
        logger.info(f"Common tokens for margin-futures: {len(common_tokens)}")
        
        for base_token in common_tokens:
            futures_data = futures_tokens[base_token]
            margin_data = margin_tokens[base_token]
            
            # Combine all prices from both markets
            # For futures, use mid price (average of bid/ask)
            all_prices = {}
            
            for ex_name, data in futures_data.items():
                bid = data.get('bid', 0)
                ask = data.get('ask', 0)
                if bid > 0.0000001 and ask > 0.0000001:
                    mid_price = (bid + ask) / 2
                    all_prices[f"{ex_name}_futures"] = {
                        'exchange': ex_name,
                        'market': 'futures',
                        'price': mid_price,
                        'bid': bid,
                        'ask': ask,
                        'symbol': data['symbol']
                    }
            
            for ex_name, data in margin_data.items():
                if data['price'] > 0.0000001:  # Double-check valid prices
                    all_prices[f"{ex_name}_margin"] = {
                        'exchange': ex_name,
                        'market': 'margin',
                        'price': data['price'],
                        'symbol': data['symbol']
                    }
            
            if len(all_prices) < 2:
                continue
            
            # Find best spread (highest price vs lowest price across all markets)
            prices_list = [(k, v['price'], v['exchange'], v['market']) for k, v in all_prices.items()]
            prices_list.sort(key=lambda x: x[1], reverse=True)
            
            highest = prices_list[0]
            lowest = prices_list[-1]
            
            highest_price = highest[1]
            lowest_price = lowest[1]
            
            # Skip if lowest price is too small (likely bad data)
            if lowest_price < 0.0000001:
                continue
            
            spread_percentage = ((highest_price - lowest_price) / lowest_price) * 100
            
            # Apply min/max spread filters
            if spread_percentage < min_spread or spread_percentage > max_spread:
                continue
            
            # Determine if this is a cross-market spread
            is_cross_market = highest[3] != lowest[3]  # Different markets
            
            # Get first available futures symbol for display
            first_futures = next(iter(futures_data.values()))
            display_symbol = first_futures['symbol']
            
            spreads.append({
                'symbol': display_symbol,
                'base_token': base_token,
                'spread_percentage': round(spread_percentage, 4),
                'highest_price': highest_price,
                'lowest_price': lowest_price,
                'highest_exchange': highest[2],
                'highest_market': highest[3],
                'lowest_exchange': lowest[2],
                'lowest_market': lowest[3],
                'is_cross_market': is_cross_market,
                'all_prices': all_prices,
                'futures_count': len(futures_data),
                'margin_count': len(margin_data),
                'mode': mode
                })
        
        logger.info(f"Found {len(spreads)} {mode} spreads")
        return sorted(spreads, key=lambda x: x['spread_percentage'], reverse=True)