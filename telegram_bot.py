import os
import warnings
import pytz
from typing import List, Dict

# Suppress deprecation warnings FIRST
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'

# CRITICAL FIX: Patch APScheduler BEFORE any other imports
import apscheduler.util

def fixed_get_localzone():
    """Override APScheduler's get_localzone to always return pytz.UTC"""
    return pytz.UTC

def fixed_astimezone(obj):
    """Override astimezone to handle timezone conversion properly"""
    if obj is None:
        return pytz.UTC
    if hasattr(obj, 'zone'):  # pytz timezone
        return obj
    # For any other timezone object, just return pytz.UTC
    return pytz.UTC

# Replace both problematic functions
apscheduler.util.get_localzone = fixed_get_localzone
apscheduler.util.astimezone = fixed_astimezone

# Now safe to import everything else
import logging
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from utils.config_loader import ConfigLoader
from exchanges.funding_rates import FundingRateManager
from datetime import datetime

# Configure logging - suppress verbose libraries
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for monitoring funding rates across exchanges"""
    
    def __init__(self):
        """Initialize bot with configuration and funding manager"""
        self.config = ConfigLoader()
        self.funding_manager = FundingRateManager()
        self.utc = pytz.UTC
        self.cached_opportunities = []  # Cache for callback handling
        self.cached_price_spreads = []  # Cache for price spread handling
        self.cached_margin_opportunities = []  # Cache for margin opportunities
        self.cached_cross_spreads = []  # Cache for cross-market spreads
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_interval = 0  # NO INTERVAL - continuous monitoring
        self.monitoring_task = None
        self.app = None  # Will be set in run()
        
        # Exchange URLs for linking
        self.exchange_urls = {
            'Binance': 'https://www.binance.com/en/futures/{symbol}',
            'MEXC': 'https://futures.mexc.com/exchange/{symbol}',
            'OKX': 'https://www.okx.com/trade-swap/{symbol}',
            'Bybit': 'https://www.bybit.com/trade/usdt/{symbol}',
            'HTX': 'https://www.htx.com/en-us/contract/swap/{symbol}',
            'Gate.io': 'https://www.gate.io/trade/{symbol}',
            'KuCoin': 'https://www.kucoin.com/futures/trade/{symbol}M',
            'BitGet': 'https://www.bitget.com/futures/usdt/{symbol}',
            'BingX': 'https://www.bingx.com/en/perpetual/{symbol}/',
            'LBank': 'https://www.lbank.com/futures/trade/{symbol}',
            'OurBit': 'https://futures.ourbit.com/exchange/{symbol}',
            'BloFin': 'https://blofin.com/futures/en/{symbol}',
        }
        
        # Spot URLs for margin trading
        self.spot_urls = {
            'Binance': 'https://www.binance.com/en/trade/{symbol}',
            'Bybit': 'https://www.bybit.com/trade/spot/{symbol}',
            'Gate.io': 'https://www.gate.io/trade/{symbol}',
            'HTX': 'https://www.htx.com/en-us/trade/{symbol}',
            'KuCoin': 'https://www.kucoin.com/trade/{symbol}',
            'BitGet': 'https://www.bitget.com/spot/{symbol}',
        }
    
    def _is_symbol_blocked(self, symbol: str) -> bool:
        """Check if a symbol is blocked"""
        blocked_tokens = self.config.blocked_tokens
        symbol_upper = symbol.upper()
        for blocked in blocked_tokens:
            blocked_upper = blocked.upper()
            # Check exact match or if symbol starts with blocked token
            if symbol_upper == blocked_upper or symbol_upper.startswith(blocked_upper):
                return True
        return False
        
    def _get_current_time(self) -> datetime:
        """Get current time in UTC"""
        return datetime.now(self.utc)

    def _format_exchange_url(self, exchange: str, symbol: str) -> str:
        """Format exchange URL for given symbol"""
        if exchange in self.exchange_urls:
            # Convert symbol format for different exchanges
            if exchange == 'MEXC':
                formatted_symbol = symbol.replace('USDT', '_USDT')
            elif exchange == 'Gate.io':
                formatted_symbol = symbol.replace('USDT', '_USDT')
            elif exchange == 'KuCoin':
                formatted_symbol = symbol  # Will add M suffix in URL template
            elif exchange == 'BingX':
                # BingX uses BTC-USDT format in URLs
                if 'USDT' in symbol and '-' not in symbol:
                    formatted_symbol = symbol.replace('USDT', '-USDT')
                else:
                    formatted_symbol = symbol
            elif exchange == 'OurBit':
                # OurBit uses BTC_USDT format in URLs
                formatted_symbol = symbol.replace('USDT', '_USDT')
            elif exchange == 'BloFin':
                # BloFin uses BTC-USDT format in URLs
                if 'USDT' in symbol and '-' not in symbol:
                    formatted_symbol = symbol.replace('USDT', '-USDT')
                else:
                    formatted_symbol = symbol
            else:
                formatted_symbol = symbol
            
            return self.exchange_urls[exchange].format(symbol=formatted_symbol)
        return "#"

    def _calculate_time_remaining(self, target_time: datetime) -> str:
        """Calculate exact time remaining until target time"""
        now = self._get_current_time()
        
        # Ensure target_time is timezone-aware and in UTC
        if target_time.tzinfo is None:
            target_time = self.utc.localize(target_time)
        elif target_time.tzinfo != self.utc:
            target_time = target_time.astimezone(self.utc)
        
        # If target time is in the past, calculate next occurrence
        if target_time <= now:
            # For funding rates, they typically occur every 8 hours
            # Find the next 8-hour boundary (00:00, 08:00, 16:00 UTC)
            current_hour = now.hour
            if current_hour < 8:
                next_funding_hour = 8
            elif current_hour < 16:
                next_funding_hour = 16
            else:
                next_funding_hour = 24  # Next day at 00:00
            
            target_time = now.replace(hour=next_funding_hour % 24, minute=0, second=0, microsecond=0)
            if next_funding_hour == 24:
                target_time = target_time.replace(day=target_time.day + 1)
        
        remaining = target_time - now
        total_seconds = int(remaining.total_seconds())
        
        if total_seconds <= 0:
            return "00:00"
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        return f"{hours:02d}:{minutes:02d}"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        current_mode = self.config.arbitrage_mode
        spread_mode = self.config.spread_mode
        welcome_msg = f"""
🤖 **Funding Arbitrage Bot - All Exchanges Active!**

📊 Track funding rate differences across 8 major exchanges:
• Binance • OKX • Bybit • MEXC
• HTX • Gate.io • KuCoin • BitGet

**Current Mode:** `{current_mode}`
**Spread Mode:** `{spread_mode}`

**Commands:**
/funding - Current arbitrage opportunities (respects mode)
/setmode - Change arbitrage mode
/spread - Price spreads between exchanges
/setspreadmode - Change spread mode
/next - Next funding payment times
/help - Show help message

⚡ Real-time data from all exchanges!
🔄 Min 24h volume: 250k USDT
"""
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        current_mode = self.config.arbitrage_mode
        spread_mode = self.config.spread_mode
        min_spread = self.config.min_spread
        max_spread = self.config.max_spread
        monitoring_status = "🟢 Active" if self.monitoring_active else "🔴 Inactive"
        help_msg = f"""
📋 **Available Commands:**

**/funding** - Display top funding opportunities
Current mode: `{current_mode}`

**/setmode** - Change arbitrage mode:
• `futures-futures` - Short high rate, Long low rate
• `spot-futures` - Spot vs Futures arbitrage
• `futures-margin` - Long negative funding, Short margin

**/spread** - Show price spreads between exchanges
Mode: `{spread_mode}` | Limits: `{min_spread}%` - `{max_spread}%`

**/setspreadmode** - Change spread comparison mode:
• `futures-futures` - Compare futures prices
• `margin-futures` - Compare margin/spot vs futures
• `futures-margin` - Compare futures vs margin/spot

**/setspreadlimits** `<min> <max>` - Set spread filters
Example: `/setspreadlimits 0.5 30`

**/block** `<symbol>` - Block/unblock a token
Example: `/block BTCUSDT` (toggle block)
Use `/block list` to see blocked tokens

**/monitor** - Start/stop spread monitoring
Status: {monitoring_status}
Alerts on NEW spread opportunities!

**/pairs** - Show exchange pair coverage map

**/next** - Countdown to next funding payments

**Modes Explained:**
📈 **futures-futures**: Classic funding arb between exchanges
📊 **futures-margin**: For NEGATIVE funding rates:
  - LONG futures (receive funding)
  - SHORT on margin (no funding cost)
  - Min funding: 0.5%

**All 8 Exchanges:**
Binance, OKX, Bybit, MEXC, HTX, Gate.io, KuCoin, BitGet
"""
        await update.message.reply_text(help_msg, parse_mode='Markdown')

    async def funding_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /funding command with inline buttons - respects current mode"""
        try:
            current_mode = self.config.arbitrage_mode
            
            if current_mode == 'futures-margin':
                await self._handle_margin_funding(update)
            else:
                await self._handle_futures_funding(update)
                
        except Exception as e:
            logger.error(f"Error in funding command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error fetching data: {str(e)}")
    
    async def _handle_futures_funding(self, update: Update) -> None:
        """Handle futures-futures funding mode"""
        await update.message.reply_text("🔄 Fetching latest funding data from all 9 exchanges...")
        
        opportunities = await self.funding_manager.get_funding_opportunities()
        if not opportunities:
            await update.message.reply_text("❌ No funding opportunities found at the moment.")
            return

        # Filter blocked tokens
        opportunities = [opp for opp in opportunities if not self._is_symbol_blocked(opp['symbol'])]
        
        if not opportunities:
            await update.message.reply_text("❌ No opportunities found (all tokens blocked).")
            return

        # Cache opportunities for callback handling
        self.cached_opportunities = opportunities
        
        # Create inline keyboard with opportunity buttons
        keyboard = []
        for i, opp in enumerate(opportunities[:20], 1):  # Show top 20
            spread = opp['spread_magnitude']
            button_text = f"{opp['symbol']} ({spread:.4f}%)"
            callback_data = f"detail_{i-1}"  # Use index for callback
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "💰 **Top Funding Opportunities (Futures-Futures):**\n\n"
        message += "Click any button to see detailed analysis:\n\n"
        
        # Show summary of top 5
        for i, opp in enumerate(opportunities[:5], 1):
            spread = opp['spread_magnitude']
            message += f"{i}. **{opp['symbol']}**: {spread:.4f}% profit\n"
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )
    
    async def _handle_margin_funding(self, update: Update) -> None:
        """Handle futures-margin funding mode (similar to futures-futures display)"""
        await update.message.reply_text("🔄 Fetching margin arbitrage data (futures + margin)...")
        
        opportunities = await self.funding_manager.get_margin_opportunities()
        if not opportunities:
            await update.message.reply_text(
                "❌ No margin arbitrage opportunities found.\n\n"
                "This mode requires:\n"
                "• Negative funding rate < -0.5%\n"
                "• Token available on margin trading"
            )
            return

        # Filter blocked tokens
        opportunities = [opp for opp in opportunities if not self._is_symbol_blocked(opp['symbol'])]
        
        if not opportunities:
            await update.message.reply_text("❌ No opportunities found (all tokens blocked).")
            return

        # Cache opportunities for callback handling
        self.cached_margin_opportunities = opportunities
        
        # Create inline keyboard with opportunity buttons
        keyboard = []
        for i, opp in enumerate(opportunities[:20], 1):  # Show top 20
            funding_rate = opp['funding_rate']
            num_futures = len(opp.get('all_futures_exchanges', {}))
            num_margin = len(opp.get('all_margin_exchanges', {}))
            # Show exchanges count like in futures-futures mode
            button_text = f"{opp['symbol']} ({funding_rate:.4f}%) [{num_futures}F/{num_margin}M]"
            callback_data = f"margin_{i-1}"  # Use index for callback
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "💰 **Futures-Margin Arbitrage (Negative Funding):**\n\n"
        message += "_Best margin = closest spread to 0%_\n"
        message += "Click any button for details:\n\n"
        
        # Show summary of top 5 with more details
        for i, opp in enumerate(opportunities[:5], 1):
            funding = opp['funding_rate']
            futures_ex = opp['futures_exchange']
            margin_ex = opp['margin_exchange']
            spread = opp['price_spread']
            num_futures = len(opp.get('all_futures_exchanges', {}))
            num_margin = len(opp.get('all_margin_exchanges', {}))
            message += f"{i}. **{opp['symbol']}**: {funding:.4f}%\n"
            message += f"   └ {futures_ex}→{margin_ex} | Spread: {spread:+.2f}% | [{num_futures}F/{num_margin}M]\n"
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )
    
    async def setmode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setmode command - show mode selection buttons"""
        current_mode = self.config.arbitrage_mode
        
        keyboard = [
            [InlineKeyboardButton("📈 Futures-Futures", callback_data="mode_futures-futures")],
            [InlineKeyboardButton("📊 Spot-Futures", callback_data="mode_spot-futures")],
            [InlineKeyboardButton("💹 Futures-Margin", callback_data="mode_futures-margin")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""
⚙️ **Select Arbitrage Mode:**

Current mode: `{current_mode}`

**Modes:**
📈 **Futures-Futures**: Classic funding rate arbitrage
   SHORT on high rate, LONG on low rate

📊 **Spot-Futures**: Spot vs Futures arbitrage
   Buy spot, Short futures (or vice versa)

💹 **Futures-Margin**: For NEGATIVE funding rates
   LONG futures (receive funding) + SHORT margin
   Min funding: 0.5%
"""
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def spreads_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /spread command - show price spreads between exchanges based on spread mode"""
        try:
            spread_mode = self.config.spread_mode
            mode_display = {
                'futures-futures': 'Futures-Futures',
                'margin-futures': 'Margin-Futures',
                'futures-margin': 'Futures-Margin'
            }
            
            await update.message.reply_text(f"⚡ Fetching {mode_display.get(spread_mode, spread_mode)} spreads (FAST - prices only)...")
            
            price_spreads = await self.funding_manager.get_cross_market_spreads(spread_mode)
            if not price_spreads:
                await update.message.reply_text(
                    f"❌ No {mode_display.get(spread_mode, spread_mode)} spread data found.\n\n"
                    "Try changing the mode with /setspreadmode"
                )
                return

            # Filter out blocked tokens
            filtered_spreads = [s for s in price_spreads if not self._is_symbol_blocked(s['symbol'])]
            
            # Group by symbol - keep only the best spread per symbol
            symbol_best_spread: Dict[str, dict] = {}
            for spread in filtered_spreads:
                symbol = spread['symbol']
                if symbol not in symbol_best_spread:
                    symbol_best_spread[symbol] = spread
                elif spread['spread_percentage'] > symbol_best_spread[symbol]['spread_percentage']:
                    symbol_best_spread[symbol] = spread
            
            # Convert back to sorted list
            grouped_spreads = sorted(
                symbol_best_spread.values(), 
                key=lambda x: x['spread_percentage'], 
                reverse=True
            )
            
            # Cache grouped spreads for callback handling
            self.cached_cross_spreads = grouped_spreads
            
            # Create inline keyboard with price spread buttons (one per symbol)
            keyboard = []
            for i, spread in enumerate(grouped_spreads[:20], 1):  # Show top 20
                spread_pct = spread['spread_percentage']
                high_ex = spread['highest_exchange']
                low_ex = spread['lowest_exchange']
                high_market = spread.get('highest_market', 'futures')[0].upper()  # F or M
                low_market = spread.get('lowest_market', 'futures')[0].upper()
                
                button_text = f"{spread['symbol']} ({spread_pct:.2f}%) [{high_ex[:3]}{high_market}→{low_ex[:3]}{low_market}]"
                callback_data = f"cspread_{i-1}"  # Cross-spread index
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get mode emoji
            mode_emoji = "📈" if spread_mode == 'futures-futures' else "💹"
            
            blocked_tokens = self.config.blocked_tokens
            blocked_info = f"\n🚫 Blocked: {len(blocked_tokens)} tokens" if blocked_tokens else ""
            
            total_found = len(filtered_spreads)
            total_symbols = len(grouped_spreads)
            message = f"{mode_emoji} **Top Price Spreads ({mode_display.get(spread_mode, spread_mode)}):**{blocked_info}\n"
            message += f"📊 Found **{total_found}** spreads across **{total_symbols}** symbols\n\n"
            message += "_Click any button to see detailed analysis:_\n\n"
            
            # Show summary of top 5
            for i, spread in enumerate(grouped_spreads[:5], 1):
                spread_pct = spread['spread_percentage']
                high_ex = spread['highest_exchange']
                low_ex = spread['lowest_exchange']
                high_market = spread.get('highest_market', 'futures')
                low_market = spread.get('lowest_market', 'futures')
                all_paths = spread.get('all_paths_count', 0)
                
                paths_info = f" ({all_paths} paths)" if all_paths > 1 else ""
                message += f"{i}. **{spread['symbol']}**: {spread_pct:.2f}%{paths_info}\n"
                message += f"   └ {high_ex}({high_market}) → {low_ex}({low_market})\n"
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )
                
        except Exception as e:
            logger.error(f"Error in spread command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error fetching spread data: {str(e)}")

    async def setspreadmode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setspreadmode command - show spread mode selection buttons"""
        current_mode = self.config.spread_mode
        
        keyboard = [
            [InlineKeyboardButton("📈 Futures-Futures", callback_data="spreadmode_futures-futures")],
            [InlineKeyboardButton("💹 Margin-Futures", callback_data="spreadmode_margin-futures")],
            [InlineKeyboardButton("📊 Futures-Margin", callback_data="spreadmode_futures-margin")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""
⚙️ **Select Spread Mode:**

Current mode: `{current_mode}`

**Modes:**
📈 **Futures-Futures**: Compare futures prices across exchanges
   BUY on low price exchange, SELL on high price exchange

💹 **Margin-Futures**: Compare margin(spot) vs futures prices
   Find cross-market price differences

📊 **Futures-Margin**: Same as Margin-Futures (reversed view)
   Useful for seeing futures vs spot spreads
"""
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def setspreadlimits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setspreadlimits command - set min and max spread thresholds"""
        try:
            args = context.args
            current_min = self.config.min_spread
            current_max = self.config.max_spread
            
            if not args:
                # Show current settings and usage
                message = f"""
⚙️ **Spread Limits Configuration**

**Current Settings:**
• Min Spread: `{current_min}%`
• Max Spread: `{current_max}%`

**Usage:**
`/setspreadlimits <min> <max>`

**Examples:**
`/setspreadlimits 0.5 30` - Show spreads 0.5% to 30%
`/setspreadlimits 1 20` - Show spreads 1% to 20%
`/setspreadlimits 0.1 100` - Show spreads 0.1% to 100%

_Higher max values include potentially bad data (e.g., exchanges with price 0)_
"""
                await update.message.reply_text(message, parse_mode='Markdown')
                return
            
            if len(args) < 2:
                await update.message.reply_text("❌ Please provide both min and max values.\nUsage: `/setspreadlimits <min> <max>`", parse_mode='Markdown')
                return
            
            try:
                min_spread = float(args[0])
                max_spread = float(args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid numbers. Please use decimal values like `0.5` or `30`", parse_mode='Markdown')
                return
            
            if min_spread < 0 or max_spread < 0:
                await update.message.reply_text("❌ Spread limits must be positive numbers.")
                return
            
            if min_spread >= max_spread:
                await update.message.reply_text("❌ Min spread must be less than max spread.")
                return
            
            if self.config.set_spread_limits(min_spread, max_spread):
                await update.message.reply_text(
                    f"✅ Spread limits updated!\n\n"
                    f"• Min: `{min_spread}%`\n"
                    f"• Max: `{max_spread}%`\n\n"
                    f"Use /spread to see filtered results.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Failed to save spread limits. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in setspreadlimits command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button clicks for detailed opportunity view"""
        query = update.callback_query
        
        # Try to answer the callback, but don't crash if it's too old
        try:
            await query.answer()
        except Exception as answer_error:
            logger.debug(f"Failed to answer callback query: {answer_error}")
            # Continue anyway, the query might still be valid for editing the message
        
        try:
            # Handle mode selection
            if query.data.startswith("mode_"):
                new_mode = query.data.replace("mode_", "")
                if self.config.set_arbitrage_mode(new_mode):
                    await query.edit_message_text(
                        f"✅ Mode changed to: `{new_mode}`\n\nUse /funding to see opportunities.",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text("❌ Failed to change mode. Please try again.")
                return
            
            # Handle spread mode selection
            if query.data.startswith("spreadmode_"):
                new_mode = query.data.replace("spreadmode_", "")
                if self.config.set_spread_mode(new_mode):
                    await query.edit_message_text(
                        f"✅ Spread mode changed to: `{new_mode}`\n\nUse /spread to see price spreads.",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text("❌ Failed to change spread mode. Please try again.")
                return
            
            # Handle monitoring buttons
            if query.data == "monitor_start":
                if self.monitoring_active:
                    await query.edit_message_text("ℹ️ Monitoring is already active!")
                else:
                    self.monitoring_active = True
                    asyncio.create_task(self._monitoring_loop())
                    await query.edit_message_text(
                        f"✅ **Monitoring Started - CONTINUOUS MODE!**\n\n"
                        f"• ⚡ NO INTERVAL - Maximum speed scanning\n"
                        f"• Will alert on new spread opportunities\n"
                        f"• Use `/monitor stop` to stop",
                        parse_mode='Markdown'
                    )
                return
            
            if query.data == "monitor_stop":
                if not self.monitoring_active:
                    await query.edit_message_text("ℹ️ Monitoring is not active!")
                else:
                    self.monitoring_active = False
                    await query.edit_message_text("⏹️ **Monitoring Stopped**", parse_mode='Markdown')
                return
            
            if query.data == "monitor_interval":
                await query.edit_message_text(
                    "⚡ **Continuous Monitoring Active**\n\n"
                    "Interval setting removed - monitoring runs at maximum speed!\n\n"
                    "Use `/monitor stop` to stop monitoring.",
                    parse_mode='Markdown'
                )
                return
            
            # Handle "Back to funding" button
            if query.data == "back_to_funding":
                # Recreate the main funding opportunities list
                if not self.cached_opportunities:
                    await query.edit_message_text("❌ No cached funding data. Please run /funding again.")
                    return
                
                # Create inline keyboard with opportunity buttons
                keyboard = []
                for i, opp in enumerate(self.cached_opportunities[:20], 1):  # Show top 20
                    spread = opp['spread_magnitude']
                    button_text = f"{opp['symbol']} ({spread:.4f}%)"
                    callback_data = f"detail_{i-1}"  # Use index for callback
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = "💰 **Top Funding Opportunities:**\n\n"
                message += "Click any button to see detailed analysis:\n\n"
                
                # Show summary of top 5
                for i, opp in enumerate(self.cached_opportunities[:5], 1):
                    spread = opp['spread_magnitude']
                    message += f"{i}. **{opp['symbol']}**: {spread:.4f}% profit\n"
                
                await query.edit_message_text(
                    message, 
                    parse_mode='Markdown', 
                    reply_markup=reply_markup
                )
                return
            
            # Handle "Back to margin" button
            if query.data == "back_to_margin":
                if not self.cached_margin_opportunities:
                    await query.edit_message_text("❌ No cached margin data. Please run /funding again.")
                    return
                
                keyboard = []
                for i, opp in enumerate(self.cached_margin_opportunities[:20], 1):
                    funding_rate = opp['funding_rate']
                    button_text = f"{opp['symbol']} ({funding_rate:.4f}%)"
                    callback_data = f"margin_{i-1}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = "💰 **Futures-Margin Arbitrage (Negative Funding):**\n\n"
                message += "Click any button for details:\n\n"
                
                for i, opp in enumerate(self.cached_margin_opportunities[:5], 1):
                    funding = opp['funding_rate']
                    futures_ex = opp['futures_exchange']
                    margin_ex = opp['margin_exchange']
                    message += f"{i}. **{opp['symbol']}**: {funding:.4f}% ({futures_ex}→{margin_ex})\n"
                
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            # Handle "Back to spreads" button
            if query.data == "back_to_spreads":
                # Recreate the main price spreads list
                if not self.cached_price_spreads:
                    await query.edit_message_text("❌ No cached spread data. Please run /spreads again.")
                    return
                
                # Create inline keyboard with price spread buttons
                keyboard = []
                for i, spread in enumerate(self.cached_price_spreads[:20], 1):  # Show top 20
                    spread_pct = spread['spread_percentage']
                    button_text = f"{spread['symbol']} ({spread_pct:.2f}%)"
                    callback_data = f"spread_{i-1}"  # Use index for callback
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = "💹 **Top Price Spreads (Futures):**\n\n"
                message += "Click any button to see detailed analysis:\n\n"
                
                # Show summary of top 5
                for i, spread in enumerate(self.cached_price_spreads[:5], 1):
                    spread_pct = spread['spread_percentage']
                    high_ex = spread['highest_exchange']
                    low_ex = spread['lowest_exchange']
                    message += f"{i}. **{spread['symbol']}**: {spread_pct:.2f}% ({high_ex} → {low_ex})\n"
                
                await query.edit_message_text(
                    message, 
                    parse_mode='Markdown', 
                    reply_markup=reply_markup
                )
                return
            
            # Handle "Back to cross spreads" button
            if query.data == "back_to_cspreads":
                if not self.cached_cross_spreads:
                    await query.edit_message_text("❌ No cached spread data. Please run /spread again.")
                    return
                
                spread_mode = self.config.spread_mode
                mode_display = {
                    'futures-futures': 'Futures-Futures',
                    'margin-futures': 'Margin-Futures',
                    'futures-margin': 'Futures-Margin'
                }
                
                keyboard = []
                for i, spread in enumerate(self.cached_cross_spreads[:20], 1):
                    spread_pct = spread['spread_percentage']
                    high_ex = spread['highest_exchange']
                    low_ex = spread['lowest_exchange']
                    high_market = spread.get('highest_market', 'futures')[0].upper()
                    low_market = spread.get('lowest_market', 'futures')[0].upper()
                    
                    button_text = f"{spread['symbol']} ({spread_pct:.2f}%) [{high_ex[:3]}{high_market}→{low_ex[:3]}{low_market}]"
                    callback_data = f"cspread_{i-1}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                mode_emoji = "📈" if spread_mode == 'futures-futures' else "💹"
                message = f"{mode_emoji} **Top Price Spreads ({mode_display.get(spread_mode, spread_mode)}):**\n\n"
                message += "_Click any button to see detailed analysis:_\n\n"
                
                for i, spread in enumerate(self.cached_cross_spreads[:5], 1):
                    spread_pct = spread['spread_percentage']
                    high_ex = spread['highest_exchange']
                    low_ex = spread['lowest_exchange']
                    high_market = spread.get('highest_market', 'futures')
                    low_market = spread.get('lowest_market', 'futures')
                    is_cross = spread.get('is_cross_market', False)
                    
                    cross_marker = "🔀" if is_cross else ""
                    message += f"{i}. **{spread['symbol']}**: {spread_pct:.2f}%\n"
                    message += f"   └ {high_ex}({high_market}) → {low_ex}({low_market}) {cross_marker}\n"
                
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            # Parse callback data for funding details
            if query.data.startswith("detail_"):
                index = int(query.data.split("_")[1])
                
                if index >= len(self.cached_opportunities):
                    await query.edit_message_text("❌ Opportunity data expired. Please run /funding again.")
                    return
                
                opp = self.cached_opportunities[index]
                
                # Get all exchange data for this symbol
                all_exchange_data = await self._get_all_exchange_data_for_symbol(opp['symbol'])
                
                # Format detailed message
                detailed_msg = self._format_detailed_opportunity(opp, all_exchange_data)
                
                # Add Back button
                back_button = InlineKeyboardButton("⬅️ Back", callback_data="back_to_funding")
                reply_markup = InlineKeyboardMarkup([[back_button]])
                
                await query.edit_message_text(
                    detailed_msg, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            
            # Parse callback data for margin details
            elif query.data.startswith("margin_"):
                index = int(query.data.split("_")[1])
                
                if index >= len(self.cached_margin_opportunities):
                    await query.edit_message_text("❌ Margin data expired. Please run /funding again.")
                    return
                
                opp = self.cached_margin_opportunities[index]
                
                # Format detailed margin message
                detailed_msg = self._format_detailed_margin_opportunity(opp)
                
                # Add Back button
                back_button = InlineKeyboardButton("⬅️ Back", callback_data="back_to_margin")
                reply_markup = InlineKeyboardMarkup([[back_button]])
                
                await query.edit_message_text(
                    detailed_msg,
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            
            # Parse callback data for price spread details
            elif query.data.startswith("spread_"):
                index = int(query.data.split("_")[1])
                
                if index >= len(self.cached_price_spreads):
                    await query.edit_message_text("❌ Spread data expired. Please run /spreads again.")
                    return
                
                spread = self.cached_price_spreads[index]
                
                # Get all exchange data for this symbol
                all_exchange_data = await self._get_all_exchange_data_for_symbol(spread['symbol'])
                
                # Format detailed message
                detailed_msg = self._format_detailed_price_spread(spread, all_exchange_data)
                
                # Add Back button
                back_button = InlineKeyboardButton("⬅️ Back", callback_data="back_to_spreads")
                reply_markup = InlineKeyboardMarkup([[back_button]])
                
                await query.edit_message_text(
                    detailed_msg, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            
            # Parse callback data for cross-market spread details
            elif query.data.startswith("cspread_"):
                index = int(query.data.split("_")[1])
                
                if index >= len(self.cached_cross_spreads):
                    await query.edit_message_text("❌ Spread data expired. Please run /spread again.")
                    return
                
                spread = self.cached_cross_spreads[index]
                
                # Format detailed message
                detailed_msg = self._format_detailed_cross_spread(spread)
                
                # Add Back button
                back_button = InlineKeyboardButton("⬅️ Back", callback_data="back_to_cspreads")
                reply_markup = InlineKeyboardMarkup([[back_button]])
                
                await query.edit_message_text(
                    detailed_msg, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
        except Exception as e:
            logger.error(f"Error in button callback: {str(e)}", exc_info=True)
            await query.edit_message_text(f"❌ Error loading details: {str(e)}")

    async def _get_all_exchange_data_for_symbol(self, symbol: str) -> dict:
        """Get funding rates and bid/ask prices for a symbol from all exchanges"""
        result = {}
        
        for ex_name, ex_data in self.funding_manager.funding_data.items():
            rates = ex_data.get('funding_rates', {})
            order_books = ex_data.get('order_books', {})
            
            if symbol in rates and symbol in order_books:
                funding_info = rates[symbol]
                ob = order_books[symbol]
                
                result[ex_name] = {
                    'funding_rate': funding_info.funding_rate,
                    'bid': ob.get('bid', 0),
                    'ask': ob.get('ask', 0),
                    'next_funding': funding_info.next_funding_time
                }
        
        return result

    def _format_detailed_opportunity(self, opp: dict, all_data: dict) -> str:
        """Format detailed opportunity message with CORRECT direction"""
        symbol = opp['symbol']
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Top funding section - CORRECTED
        msg += "**TOP FUNDING**\n"
        short_ex = opp['exchange_high'].lower()  # SHORT position (high funding rate)
        long_ex = opp['exchange_low'].lower()    # LONG position (low funding rate)
        
        short_url = self._format_exchange_url(opp['exchange_high'], symbol)
        long_url = self._format_exchange_url(opp['exchange_low'], symbol)
        
        msg += f"LONG [{long_ex}]({long_url}) - SHORT [{short_ex}]({short_url})\n\n"
        
        # Spreads - CORRECTED
        profit = opp['spread_magnitude']
        msg += f"**Спред ставок:** {profit:.4f}%\n"
        msg += f"**Спред цен:** {opp['price_spread']:+.4f}%\n\n"
        
        # All exchanges table
        msg += "**Остальные биржи:**\n"
        msg += "```\n"
        msg += "Биржа       Ставка     Цена    Время\n"
        msg += "────────────────────────────────────\n"
        
        # Sort exchanges by funding rate (highest first)
        sorted_exchanges = sorted(
            all_data.items(), 
            key=lambda x: x[1]['funding_rate'], 
            reverse=True
        )
        
        for ex_name, data in sorted_exchanges:
            # Format exchange name (max 9 chars)
            ex_display = ex_name.lower()[:9].ljust(9)
            
            # Format funding rate
            rate_str = f"{data['funding_rate']*100:+.3f}".rjust(8)
            
            # Format bid/ask prices
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
            price_str = f"{mid_price:.4f}".rjust(9)
            
            # Format time remaining as HH:MM
            time_remaining = self._calculate_time_remaining(data['next_funding'])
            time_str = time_remaining.rjust(6)
            
            msg += f"{ex_display} {rate_str} {price_str}  {time_str}\n"
        
        msg += "```"
        
        return msg

    def _format_detailed_price_spread(self, spread: dict, all_data: dict) -> str:
        """Format detailed price spread message using bid/ask"""
        symbol = spread['symbol']
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Top spread section - Updated for bid/ask
        msg += "**TOP PRICE SPREAD (BID/ASK)**\n"
        buy_ex = spread.get('buy_exchange', spread.get('lowest_exchange', '')).lower()
        sell_ex = spread.get('sell_exchange', spread.get('highest_exchange', '')).lower()
        
        buy_url = self._format_exchange_url(spread.get('buy_exchange', spread.get('lowest_exchange', '')), symbol)
        sell_url = self._format_exchange_url(spread.get('sell_exchange', spread.get('highest_exchange', '')), symbol)
        
        msg += f"BUY [{buy_ex}]({buy_url}) - SELL [{sell_ex}]({sell_url})\n\n"
        
        # Spread info - Updated for bid/ask
        msg += f"**Спред цен:** {spread['spread_percentage']:.2f}%\n"
        sell_bid = spread.get('sell_bid', spread.get('highest_price', 0))
        buy_ask = spread.get('buy_ask', spread.get('lowest_price', 0))
        msg += f"**Продажа (bid):** ${sell_bid:.4f} ({sell_ex})\n"
        msg += f"**Покупка (ask):** ${buy_ask:.4f} ({buy_ex})\n\n"
        
        # All exchanges table
        msg += "**Все биржи:**\n"
        msg += "```\n"
        msg += "Биржа       Bid       Ask    Spread\n"
        msg += "────────────────────────────────────\n"
        
        # Sort exchanges by bid price (highest first)
        sorted_exchanges = sorted(
            all_data.items(), 
            key=lambda x: x[1].get('bid', 0), 
            reverse=True
        )
        
        # Calculate average mid price for deviation
        mid_prices = [(data.get('bid', 0) + data.get('ask', 0)) / 2 for data in all_data.values() if data.get('bid', 0) > 0]
        avg_price = sum(mid_prices) / len(mid_prices) if mid_prices else 0
        
        for ex_name, data in sorted_exchanges:
            # Format exchange name (max 9 chars)
            ex_display = ex_name.lower()[:9].ljust(9)
            
            # Format bid/ask
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            bid_str = f"${bid:.4f}".rjust(9) if bid > 0 else "N/A".rjust(9)
            ask_str = f"${ask:.4f}".rjust(9) if ask > 0 else "N/A".rjust(9)
            
            # Format spread (ask-bid for the exchange)
            if bid > 0 and ask > 0:
                ex_spread = ((ask - bid) / bid) * 100
                spread_str = f"{ex_spread:.3f}%".rjust(7)
            else:
                spread_str = "N/A".rjust(7)
            
            msg += f"{ex_display} {bid_str} {ask_str} {spread_str}\n"
        
        msg += "```"
        
        return msg

    def _format_detailed_margin_opportunity(self, opp: dict) -> str:
        """Format detailed margin arbitrage opportunity message (similar to futures-futures format)"""
        symbol = opp['symbol']
        base_token = opp['base_token']
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Top recommendation section (best combo)
        msg += "**TOP MARGIN ARBITRAGE**\n"
        futures_ex = opp['futures_exchange']
        margin_ex = opp['margin_exchange']
        
        futures_url = self._format_exchange_url(futures_ex, symbol)
        spot_symbol_formatted = f"{base_token}-USDT" if margin_ex != 'Gate.io' else f"{base_token}_USDT"
        margin_url = self.spot_urls.get(margin_ex, '#').format(symbol=spot_symbol_formatted)
        
        msg += f"LONG [{futures_ex.lower()}]({futures_url}) - SHORT [{margin_ex.lower()}]({margin_url})\n\n"
        
        # Key metrics
        msg += f"**Funding Rate:** {opp['funding_rate']:.4f}% (получаем)\n"
        msg += f"**Спред цен:** {opp['price_spread']:+.4f}%\n\n"
        
        # All futures exchanges table
        all_futures = opp.get('all_futures_exchanges', {})
        if all_futures:
            msg += "**Futures биржи:**\n"
            msg += "```\n"
            msg += "Биржа       Ставка     Цена    Время\n"
            msg += "────────────────────────────────────\n"
            
            # Sort by funding rate (most negative first - best to LONG)
            sorted_futures = sorted(
                all_futures.items(),
                key=lambda x: x[1]['funding_rate']
            )
            
            for ex_name, data in sorted_futures:
                ex_display = ex_name.lower()[:9].ljust(9)
                rate_str = f"{data['funding_rate']*100:+.3f}".rjust(8)
                price_str = f"{data['price']:.4f}".rjust(9)
                time_remaining = self._calculate_time_remaining(data['next_funding'])
                time_str = time_remaining.rjust(6)
                
                # Mark the best (most negative) with indicator
                indicator = "◀" if ex_name == futures_ex else " "
                msg += f"{ex_display} {rate_str} {price_str}  {time_str}{indicator}\n"
            
            msg += "```\n"
        
        # All margin exchanges table
        all_margin = opp.get('all_margin_exchanges', {})
        if all_margin:
            msg += "**Margin:**\n"
            msg += "```\n"
            msg += "Биржа       Цена      Спред\n"
            msg += "─────────────────────────────\n"
            
            # Get best futures price for spread calculation
            best_futures_price = opp['futures_price']
            
            # Sort by spread (closest to 0 first - best)
            sorted_margin = sorted(
                all_margin.items(),
                key=lambda x: abs(x[1].get('spread', float('inf')))
            )
            
            for ex_name, data in sorted_margin:
                ex_display = ex_name.lower()[:9].ljust(9)
                price_str = f"{data['price']:.4f}".rjust(9)
                spread = data.get('spread', ((data['price'] - best_futures_price) / best_futures_price) * 100)
                spread_str = f"{spread:+.2f}%".rjust(7)
                
                # Mark the best (closest to 0%) with indicator
                indicator = "◀" if ex_name == margin_ex else " "
                msg += f"{ex_display} {price_str}  {spread_str}{indicator}\n"
            
            msg += "```\n"
        
        # Next funding time
        time_remaining = self._calculate_time_remaining(opp['next_funding'])
        msg += f"⏰ Next funding: **{time_remaining}**\n\n"
        
        return msg

    def _format_detailed_cross_spread(self, spread: dict) -> str:
        """Format detailed cross-market spread message (futures-futures, margin-futures, futures-margin)"""
        symbol = spread['symbol']
        mode = spread.get('mode', 'futures-futures')
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Top spread section
        mode_display = {
            'futures-futures': 'FUTURES-FUTURES SPREAD',
            'margin-futures': 'MARGIN-FUTURES SPREAD',
            'futures-margin': 'FUTURES-MARGIN SPREAD'
        }
        msg += f"**TOP {mode_display.get(mode, 'PRICE SPREAD')}**\n"
        
        high_ex = spread['highest_exchange']
        low_ex = spread['lowest_exchange']
        high_market = spread.get('highest_market', 'futures')
        low_market = spread.get('lowest_market', 'futures')
        
        # Format URLs based on market type
        if high_market == 'futures':
            high_url = self._format_exchange_url(high_ex, symbol)
        else:
            base_token = spread.get('base_token', symbol[:-4] if symbol.endswith('USDT') else symbol)
            spot_symbol = f"{base_token}-USDT" if high_ex != 'Gate.io' else f"{base_token}_USDT"
            high_url = self.spot_urls.get(high_ex, '#').format(symbol=spot_symbol)
        
        if low_market == 'futures':
            low_url = self._format_exchange_url(low_ex, symbol)
        else:
            base_token = spread.get('base_token', symbol[:-4] if symbol.endswith('USDT') else symbol)
            spot_symbol = f"{base_token}-USDT" if low_ex != 'Gate.io' else f"{base_token}_USDT"
            low_url = self.spot_urls.get(low_ex, '#').format(symbol=spot_symbol)
        
        msg += f"BUY [{low_ex.lower()}]({low_url}) ({low_market}) → SELL [{high_ex.lower()}]({high_url}) ({high_market})\n\n"
        
        # Spread info
        is_cross_market = spread.get('is_cross_market', False)
        cross_marker = "🔀 Cross-Market" if is_cross_market else "📊 Same Market"
        
        # Use sell_bid and buy_ask for futures-futures, fallback to highest_price/lowest_price for margin modes
        sell_price = spread.get('sell_bid') or spread.get('highest_price', 0)
        buy_price = spread.get('buy_ask') or spread.get('lowest_price', 0)
        
        msg += f"**Спред цен:** {spread['spread_percentage']:.4f}%\n"
        msg += f"**Sell BID:** ${sell_price:.4f} ({high_ex} {high_market})\n"
        msg += f"**Buy ASK:** ${buy_price:.4f} ({low_ex} {low_market})\n"
        msg += f"**Тип:** {cross_marker}\n\n"
        
        # All prices table
        all_prices = spread.get('all_prices', {})
        if all_prices:
            msg += "**Все цены (Bid / Ask):**\n"
            msg += "```\n"
            msg += "Биржа       Рынок    Bid        Ask        Mid\n"
            msg += "────────────────────────────────────────────────\n"
            
            # Calculate mid prices for sorting and deviation
            mid_prices = []
            for data in all_prices.values():
                bid = data.get('bid', data.get('price', 0))
                ask = data.get('ask', data.get('price', 0))
                mid = (bid + ask) / 2 if bid and ask else data.get('price', 0)
                mid_prices.append(mid)
            avg_price = sum(mid_prices) / len(mid_prices) if mid_prices else 1
            
            # Sort by mid price (highest first)
            def get_mid(item):
                data = item[1]
                bid = data.get('bid', data.get('price', 0))
                ask = data.get('ask', data.get('price', 0))
                return (bid + ask) / 2 if bid and ask else data.get('price', 0)
            
            sorted_prices = sorted(
                all_prices.items(),
                key=get_mid,
                reverse=True
            )
            
            for key, data in sorted_prices:
                ex_name = data['exchange']
                market = data['market']
                bid = data.get('bid', data.get('price', 0))
                ask = data.get('ask', data.get('price', 0))
                mid = (bid + ask) / 2 if bid and ask else data.get('price', 0)
                
                ex_display = ex_name.lower()[:9].ljust(9)
                market_display = market[:6].ljust(6)
                bid_str = f"${bid:.4f}" if bid else "  N/A  "
                ask_str = f"${ask:.4f}" if ask else "  N/A  "
                mid_str = f"${mid:.4f}"
                
                # Mark sell and buy exchanges
                if ex_name == high_ex and market == high_market:
                    indicator = " SELL▲"
                elif ex_name == low_ex and market == low_market:
                    indicator = " BUY▼"
                else:
                    indicator = ""
                
                msg += f"{ex_display} {market_display} {bid_str} {ask_str} {mid_str}{indicator}\n"
            
            msg += "```\n"
        
        # Summary
        futures_count = spread.get('futures_count', 0)
        margin_count = spread.get('margin_count', 0)
        if futures_count or margin_count:
            msg += f"📊 Futures: {futures_count} | Margin: {margin_count}\n"
        
        # Show path info if available
        all_paths = spread.get('all_paths_count', 0)
        if all_paths:
            msg += f"🔀 Total paths for this symbol: {all_paths}\n"
        
        return msg

    async def next_funding_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /next command"""
        try:
            next_fundings = await self.funding_manager.get_next_funding_times()
            
            if not next_fundings:
                await update.message.reply_text("❌ No funding time data available.")
                return
                
            message = "⏰ **Next Funding Payments (All Exchanges):**\n\n"
            
            for exchange, funding_time in sorted(next_fundings.items()):
                time_remaining = self._calculate_time_remaining(funding_time)
                message += f"🏛️ **{exchange}**: {time_remaining}\n"

            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in next funding command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error fetching funding times: {str(e)}")

    async def block_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /block command - block/unblock tokens from spread results"""
        try:
            args = context.args if context.args else []
            blocked = self.config.blocked_tokens
            
            if not args:
                # Show help and current blocked list
                if blocked:
                    blocked_list = ", ".join(blocked)
                    message = f"""
🚫 **Blocked Tokens** ({len(blocked)})

`{blocked_list}`

**Commands:**
`/block <symbol>` - Toggle block (add/remove)
`/block list` - Show blocked tokens
`/block clear` - Unblock all tokens

**Example:**
`/block BTCUSDT` - Block BTCUSDT
`/block ETHUSDT` - Block ETHUSDT
"""
                else:
                    message = """
🚫 **Block Tokens**

No tokens blocked.

**Commands:**
`/block <symbol>` - Block a token
`/block list` - Show blocked tokens

**Example:**
`/block BTCUSDT` - Block BTCUSDT from results
"""
                await update.message.reply_text(message, parse_mode='Markdown')
                return
            
            action = args[0].upper()
            
            if action == 'LIST':
                if blocked:
                    blocked_list = "\n".join([f"• `{t}`" for t in blocked])
                    await update.message.reply_text(
                        f"🚫 **Blocked Tokens** ({len(blocked)}):\n\n{blocked_list}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text("✅ No tokens blocked.")
                return
            
            if action == 'CLEAR':
                for token in blocked.copy():
                    self.config.unblock_token(token)
                await update.message.reply_text("✅ All tokens unblocked!")
                return
            
            # Toggle block for the symbol
            symbol = action
            if self.config.is_token_blocked(symbol):
                self.config.unblock_token(symbol)
                await update.message.reply_text(f"✅ **{symbol}** unblocked!", parse_mode='Markdown')
            else:
                self.config.block_token(symbol)
                await update.message.reply_text(f"🚫 **{symbol}** blocked!", parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in block command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /monitor command - start/stop spread monitoring"""
        try:
            args = context.args if context.args else []
            
            if not args:
                # Show current status and buttons
                status = "🟢 **Active**" if self.monitoring_active else "🔴 **Inactive**"
                keyboard = [
                    [InlineKeyboardButton("▶️ Start Monitoring", callback_data="monitor_start")],
                    [InlineKeyboardButton("⏹️ Stop Monitoring", callback_data="monitor_stop")],
                    [InlineKeyboardButton("⚙️ Set Interval", callback_data="monitor_interval")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"""
🔔 **Spread Monitoring - CONTINUOUS MODE**

Status: {status}
Mode: `⚡ NO INTERVAL - Maximum Speed`

**How it works:**
• ⚡ CONTINUOUS scanning (no delay between checks)
• 🚀 Optimized fetching (prices only, no funding data)
• 🔔 Instant alerts on NEW spread opportunities
• 📈 Also alerts when existing spreads increase by 50%+

**Commands:**
`/monitor start` - Start continuous monitoring
`/monitor stop` - Stop monitoring
"""
                await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
                return
            
            action = args[0].lower()
            
            if action == 'start':
                await self._start_monitoring(update)
            elif action == 'stop':
                await self._stop_monitoring(update)
            else:
                await update.message.reply_text("❌ Invalid command. Use `/monitor start` or `/monitor stop`", parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in monitor command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def _start_monitoring(self, update: Update) -> None:
        """Start the monitoring background task"""
        if self.monitoring_active:
            await update.message.reply_text("ℹ️ Monitoring is already active!")
            return
        
        self.monitoring_active = True
        
        # Start the monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        await update.message.reply_text(
            f"✅ **Monitoring Started - CONTINUOUS MODE!**\n\n"
            f"• ⚡ NO INTERVAL - Maximum speed scanning\n"
            f"• Will alert on new spread opportunities\n"
            f"• Use `/monitor stop` to stop",
            parse_mode='Markdown'
        )

    async def _stop_monitoring(self, update: Update) -> None:
        """Stop the monitoring background task"""
        if not self.monitoring_active:
            await update.message.reply_text("ℹ️ Monitoring is not active!")
            return
        
        self.monitoring_active = False
        await update.message.reply_text("⏹️ **Monitoring Stopped**", parse_mode='Markdown')

    async def _monitoring_loop(self) -> None:
        """Background loop that checks for new spreads - CONTINUOUS, NO INTERVAL"""
        logger.info("Monitoring loop started - CONTINUOUS MODE")
        
        while self.monitoring_active:
            try:
                # Fetch current spreads - FAST (prices only for spread mode)
                spread_mode = self.config.spread_mode
                spreads = await self.funding_manager.get_cross_market_spreads(spread_mode)
                
                if spreads:
                    # Filter blocked tokens
                    spreads = [s for s in spreads if not self._is_symbol_blocked(s['symbol'])]
                    
                    # Detect new spreads
                    new_spreads = self.funding_manager.detect_new_spreads(spreads)
                    
                    if new_spreads:
                        # Send alerts for new spreads
                        await self._send_new_spread_alerts(new_spreads)
                
                # MINIMAL delay just to yield control - effectively continuous
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error only
        
        logger.info("Monitoring loop stopped")

    async def _send_new_spread_alerts(self, new_spreads: List[dict]) -> None:
        """Send Telegram alerts for new spread opportunities"""
        if not self.app:
            return
        
        chat_id = self.config.telegram_chat_id
        if not chat_id:
            return
        
        # Position sizing
        TOTAL_POSITION_USD = 50.0
        NUM_PARTS = 4
        
        # Send summary if many new spreads found
        if len(new_spreads) > 10:
            try:
                summary_msg = f"🔔 **{len(new_spreads)} new spread opportunities found!**\n"
                summary_msg += f"Showing top 10 alerts below."
                await self.app.bot.send_message(
                    chat_id=chat_id, text=summary_msg,
                    parse_mode='Markdown', disable_web_page_preview=True
                )
            except Exception:
                pass
        
        for spread in new_spreads[:10]:  # Limit to 10 alerts at once
            try:
                is_increase = 'spread_increase' in spread
                
                if is_increase:
                    emoji = "📈"
                    title = "Spread Increased!"
                    extra_info = f"Increased by: **+{spread['spread_increase']:.2f}%**"
                else:
                    emoji = "🆕"
                    title = "New Spread Detected!"
                    extra_info = ""
                
                # Get prices - support both futures-futures keys (buy_ask/sell_bid)
                # and margin keys (lowest_price/highest_price)
                buy_price = spread.get('buy_ask') or spread.get('lowest_price', 0)
                sell_price = spread.get('sell_bid') or spread.get('highest_price', 0)
                
                buy_exchange = spread.get('lowest_exchange', '')
                sell_exchange = spread.get('highest_exchange', '')
                buy_market = spread.get('lowest_market', 'futures')
                sell_market = spread.get('highest_market', 'futures')
                
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
                
                msg = f"{emoji} **{title}**\n\n"
                msg += f"`{spread['symbol']}` — **{spread['spread_percentage']:.2f}%**\n\n"
                
                msg += f"📉 **BUY** on {buy_exchange} ({buy_market})\n"
                msg += f"   Ask: `${buy_price:.6f}`\n\n"
                msg += f"📈 **SELL** on {sell_exchange} ({sell_market})\n"
                msg += f"   Bid: `${sell_price:.6f}`\n\n"
                
                msg += f"💰 **Position (equal coins, ~${TOTAL_POSITION_USD:.0f}):**\n"
                msg += f"   Full: `{max_equal_coins:.6f}` coins\n"
                msg += f"   ÷4:   `{part_coins:.6f}` coins\n"
                msg += f"   📊 BUY: ${usd_needed_buy:.2f} | SELL: ${usd_needed_sell:.2f}\n\n"
                
                if extra_info:
                    msg += f"ℹ️ {extra_info}\n\n"
                
                buy_url = self._format_exchange_url(buy_exchange, spread['symbol'])
                sell_url = self._format_exchange_url(sell_exchange, spread['symbol'])
                
                msg += f"🔗 [Open {buy_exchange}]({buy_url}) | [Open {sell_exchange}]({sell_url})"
                
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error sending spread alert for {spread.get('symbol', '?')}: {str(e)}")

    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pairs command - show exchange pair coverage map"""
        try:
            await update.message.reply_text("🔄 Building exchange-pair map...")
            
            # Get the pair summary from funding manager
            pair_map = self.funding_manager.get_exchange_pair_summary()
            
            if not pair_map:
                # Need to fetch data first
                await self.funding_manager.get_cross_market_spreads('futures-futures')
                pair_map = self.funding_manager.get_exchange_pair_summary()
            
            if not pair_map:
                await update.message.reply_text("❌ No pair data available. Try `/spread` first.", parse_mode='Markdown')
                return
            
            # Sort by number of symbols
            sorted_pairs = sorted(pair_map.items(), key=lambda x: len(x[1]), reverse=True)
            
            message = "🔀 **Exchange Pair Coverage Map**\n\n"
            message += "Shows how many symbols are tradable between each exchange pair:\n\n"
            
            # Show top 20 pairs
            for pair_key, symbols in sorted_pairs[:20]:
                message += f"**{pair_key}**: {len(symbols)} symbols\n"
            
            message += f"\n📊 Total exchange pairs: {len(pair_map)}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in pairs command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    def run(self) -> None:
        """Start the bot"""
        try:
            app = (
                ApplicationBuilder()
                .token(self.config.telegram_bot_token)
                .job_queue(None)
                .build()
            )
            
            # Store app reference for monitoring alerts
            self.app = app

            # Add command handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("help", self.help_command))
            app.add_handler(CommandHandler("funding", self.funding_command))
            app.add_handler(CommandHandler("setmode", self.setmode_command))
            app.add_handler(CommandHandler("spread", self.spreads_command))
            app.add_handler(CommandHandler("spreads", self.spreads_command))  # Alias for /spread
            app.add_handler(CommandHandler("setspreadmode", self.setspreadmode_command))
            app.add_handler(CommandHandler("setspreadlimits", self.setspreadlimits_command))
            app.add_handler(CommandHandler("next", self.next_funding_command))
            app.add_handler(CommandHandler("block", self.block_command))
            app.add_handler(CommandHandler("monitor", self.monitor_command))
            app.add_handler(CommandHandler("pairs", self.pairs_command))
            
            # Add callback query handler for buttons
            app.add_handler(CallbackQueryHandler(self.button_callback))

            # Start the bot
            logger.info("🤖 Starting Funding Arbitrage Bot with ALL 9 EXCHANGES...")
            # Drop pending updates to avoid processing old button clicks
            app.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()