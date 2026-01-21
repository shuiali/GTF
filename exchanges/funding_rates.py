import asyncio
import logging
import pytz
from typing import Dict, List
from datetime import datetime
from .binance import BinanceExchange
from .mexc import MEXCExchange
from .okx import OKXExchange
from .bybit import BybitExchange
from .htx import HTXExchange
from .gateio import GateioExchange
from .kucoin import KucoinExchange
from .bitget import BitgetExchange
# from .lbank import LBankExchange  # NEW IMPORT - DISABLED
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class FundingRateManager:
    def __init__(self):
        self.config = ConfigLoader()
        
        # All 8 exchanges enabled (LBank disabled)
        self.exchanges = {
            'Binance': BinanceExchange(),
            'MEXC': MEXCExchange(),
            'OKX': OKXExchange(),
            'Bybit': BybitExchange(),
            'HTX': HTXExchange(),
            'Gate.io': GateioExchange(),
            'KuCoin': KucoinExchange(),
            'BitGet': BitgetExchange(),
            # 'LBank': LBankExchange()  # NEW EXCHANGE - DISABLED
        }
        
        # Exchanges that support margin trading (have margin API implemented)
        self.margin_exchanges = ['Binance', 'Bybit', 'Gate.io', 'HTX', 'KuCoin', 'BitGet']

        # Remove all timeout restrictions
        for exchange in self.exchanges.values():
            exchange.request_timeout = 30.0  # Generous timeout
            exchange.rate_limit_ms = 50  # Fast rate limit

        self.last_update = None
        self.last_margin_update = None
        self.update_interval = 30
        self.funding_data = {}
        self.margin_data = {}  # New: stores margin tokens and spot prices
        self.utc = pytz.UTC

    def _get_current_time(self) -> datetime:
        return datetime.now(self.utc)

    async def update_funding_data(self):
        """Fetch funding data from all exchanges with NO TIMEOUT"""
        current_time = self._get_current_time()
        
        if (self.last_update and 
            (current_time - self.last_update).total_seconds() < self.update_interval):
            logger.info("Skipping update - too recent")
            return
        
        # Initialize funding data dict first
        self.funding_data = {}
        
        # Create all tasks for parallel execution
        all_tasks = []
        task_map = {}
        
        for exchange_name, exchange in self.exchanges.items():
            funding_task = asyncio.create_task(exchange.fetch_funding_rates())
            price_task = asyncio.create_task(exchange.fetch_prices())
            
            all_tasks.extend([funding_task, price_task])
            task_map[funding_task] = (exchange_name, 'funding_rates')
            task_map[price_task] = (exchange_name, 'prices')

        try:
            # Execute all tasks with NO TIMEOUT - let them finish naturally
            completed_results = await asyncio.gather(*all_tasks, return_exceptions=True)

            # Process results
            for i, res_or_exc in enumerate(completed_results):
                original_task = all_tasks[i] 
                exchange_name, data_type = task_map[original_task]
                
                if exchange_name not in self.funding_data:
                    self.funding_data[exchange_name] = {'funding_rates': {}, 'prices': {}}
                
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
                prices = ex_data.get('prices', {})
                
                if len(rates) > 0 and len(prices) > 0:
                    successful_exchanges.append(f"{ex_name} ({len(rates)} pairs)")
                elif len(rates) > 0 or len(prices) > 0:
                    failed_exchanges.append(f"{ex_name} (partial data)")
                else:
                    failed_exchanges.append(ex_name)
            
            # Print a clear status summary
            print("\n" + "="*60)
            print("📊 DATA FETCH STATUS")
            print("="*60)
            print(f"✅ SUCCESSFUL ({len(successful_exchanges)}/{len(self.exchanges)}): {', '.join(successful_exchanges) if successful_exchanges else 'None'}")
            if failed_exchanges:
                print(f"❌ FAILED/INCOMPLETE ({len(failed_exchanges)}): {', '.join(failed_exchanges)}")
            print(f"⏰ Last Update: {current_time.strftime('%H:%M:%S UTC')}")
            print("="*60 + "\n")
            
            logger.info(f"Update complete: {len(successful_exchanges)}/{len(self.exchanges)} exchanges operational")

    async def get_funding_opportunities(self) -> List[Dict]:
        """Get funding opportunities - PRIORITIZE BY HIGHEST RATE EXCHANGE FUNDING TIME"""
        await self.update_funding_data()
        
        # Get exchanges that have BOTH funding rates AND prices
        working_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('funding_rates', {})) > 0 and len(ex_data.get('prices', {})) > 0:
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
            symbol_prices = {}
            
            # Collect funding rates and prices for this symbol from all exchanges
            for ex_name in working_exchanges:
                rates = self.funding_data[ex_name].get('funding_rates', {})
                prices = self.funding_data[ex_name].get('prices', {})
                
                if symbol in rates and symbol in prices:
                    symbol_rates[ex_name] = rates[symbol]
                    symbol_prices[ex_name] = prices[symbol]
            
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
                    price_short = symbol_prices[ex_short]
                    price_long = symbol_prices[ex_long]
                    
                    # Net profit = funding_received - funding_paid
                    # For arbitrage, we want: rate_short - rate_long > 0
                    # This means: rate_short > rate_long (short on high funding, long on low funding)
                    profit = rate_short - rate_long
                    
                    # Only consider if profit is positive and meaningful
                    if profit > max_profit and profit > 0.0001:  # 0.01% minimum
                        max_profit = profit
                        
                        # Price spread: we buy on ex_long, sell on ex_short
                        # Positive spread means we can buy cheaper and sell higher (additional profit)
                        price_spread = ((price_short - price_long) / price_long) * 100
                        
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
        """Get price spreads between exchanges for spot arbitrage opportunities"""
        await self.update_funding_data()
        
        # Get exchanges that have price data
        working_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('prices', {})) > 0:
                working_exchanges.append(ex_name)
        
        logger.info(f"Working exchanges with price data: {working_exchanges}")
        
        if len(working_exchanges) < 2:
            logger.error(f"Not enough exchanges with price data: {working_exchanges}")
            return []
            
        spreads = []
        
        # Get all symbols that exist on at least 2 exchanges
        all_symbols = set()
        for ex_name in working_exchanges:
            prices = self.funding_data[ex_name].get('prices', {})
            all_symbols.update(prices.keys())
        
        logger.info(f"Processing {len(all_symbols)} unique symbols for price spreads")
        
        # For each symbol, find the price spread
        for symbol in all_symbols:
            symbol_prices = {}
            
            # Collect prices for this symbol from all exchanges
            for ex_name in working_exchanges:
                prices = self.funding_data[ex_name].get('prices', {})
                if symbol in prices:
                    symbol_prices[ex_name] = prices[symbol]
            
            # Need at least 2 exchanges for this symbol
            if len(symbol_prices) < 2:
                continue
            
            # Find highest and lowest prices
            highest_price = max(symbol_prices.values())
            lowest_price = min(symbol_prices.values())
            
            # Calculate spread percentage
            spread_percentage = ((highest_price - lowest_price) / lowest_price) * 100
            
            # Only consider meaningful spreads (> 0.1%)
            if spread_percentage > 0.1:
                # Find exchanges with highest and lowest prices
                highest_exchange = next(ex for ex, price in symbol_prices.items() if price == highest_price)
                lowest_exchange = next(ex for ex, price in symbol_prices.items() if price == lowest_price)
                
                spreads.append({
                    'symbol': symbol,
                    'spread_percentage': round(spread_percentage, 2),
                    'highest_price': highest_price,
                    'lowest_price': lowest_price,
                    'highest_exchange': highest_exchange,
                    'lowest_exchange': lowest_exchange,
                    'exchanges_count': len(symbol_prices)
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
        """Fetch margin tokens and spot prices from all supported exchanges"""
        current_time = self._get_current_time()
        
        if (self.last_margin_update and 
            (current_time - self.last_margin_update).total_seconds() < self.update_interval):
            logger.info("Skipping margin update - too recent")
            return
        
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
        
        # Get all exchanges with complete futures data
        futures_exchanges = []
        for ex_name, ex_data in self.funding_data.items():
            if len(ex_data.get('funding_rates', {})) > 0 and len(ex_data.get('prices', {})) > 0:
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
            prices = self.funding_data[ex_name].get('prices', {})
            
            for symbol, funding_info in rates.items():
                funding_rate = funding_info.funding_rate
                
                # Only consider NEGATIVE funding rates < -0.5% (we LONG futures to RECEIVE funding)
                if funding_rate >= -0.005:  # -0.5%
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
                
                futures_price = prices.get(symbol, 0)
                if futures_price <= 0:
                    continue
                
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