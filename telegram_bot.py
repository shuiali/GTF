import os
import warnings
import pytz

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
            # 'LBank': 'https://lbank.com/futures/{symbol}'  # NEW EXCHANGE URL - DISABLED
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
        welcome_msg = f"""
🤖 **Funding Arbitrage Bot - All Exchanges Active!**

📊 Track funding rate differences across 8 major exchanges:
• Binance • OKX • Bybit • MEXC
• HTX • Gate.io • KuCoin • BitGet

**Current Mode:** `{current_mode}`

**Commands:**
/funding - Current arbitrage opportunities (respects mode)
/setmode - Change arbitrage mode
/spreads - Price spreads between exchanges
/next - Next funding payment times
/help - Show help message

⚡ Real-time data from all exchanges!
🔄 Updates every 30 seconds automatically.
"""
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        current_mode = self.config.arbitrage_mode
        help_msg = f"""
📋 **Available Commands:**

**/funding** - Display top funding opportunities
Current mode: `{current_mode}`

**/setmode** - Change arbitrage mode:
• `futures-futures` - Short high rate, Long low rate
• `spot-futures` - Spot vs Futures arbitrage
• `futures-margin` - Long negative funding, Short margin

**/spreads** - Show price spreads between exchanges
Find coins with significant price differences

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
        """Handle futures-margin funding mode"""
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

        # Cache opportunities for callback handling
        self.cached_margin_opportunities = opportunities
        
        # Create inline keyboard with opportunity buttons
        keyboard = []
        for i, opp in enumerate(opportunities[:20], 1):  # Show top 20
            funding_rate = opp['funding_rate']
            button_text = f"{opp['symbol']} ({funding_rate:.4f}%)"
            callback_data = f"margin_{i-1}"  # Use index for callback
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "💰 **Futures-Margin Arbitrage (Negative Funding):**\n\n"
        message += "Strategy: LONG futures + SHORT margin\n"
        message += "Click any button for details:\n\n"
        
        # Show summary of top 5
        for i, opp in enumerate(opportunities[:5], 1):
            funding = opp['funding_rate']
            futures_ex = opp['futures_exchange']
            margin_ex = opp['margin_exchange']
            message += f"{i}. **{opp['symbol']}**: {funding:.4f}% ({futures_ex}→{margin_ex})\n"
        
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
        """Handle /spreads command - show price spreads between exchanges"""
        try:
            await update.message.reply_text("🔄 Fetching latest price data from all 8 exchanges...")
            
            price_spreads = await self.funding_manager.get_price_spreads()
            if not price_spreads:
                await update.message.reply_text("❌ No price spread data found at the moment.")
                return

            # Cache price spreads for callback handling
            self.cached_price_spreads = price_spreads
            
            # Create inline keyboard with price spread buttons
            keyboard = []
            for i, spread in enumerate(price_spreads[:20], 1):  # Show top 20
                spread_pct = spread['spread_percentage']
                button_text = f"{spread['symbol']} ({spread_pct:.2f}%)"
                callback_data = f"spread_{i-1}"  # Use index for callback
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = "💹 **Top Price Spreads (Futures):**\n\n"
            message += "Click any button to see detailed analysis:\n\n"
            
            # Show summary of top 5
            for i, spread in enumerate(price_spreads[:5], 1):
                spread_pct = spread['spread_percentage']
                high_ex = spread['highest_exchange']
                low_ex = spread['lowest_exchange']
                message += f"{i}. **{spread['symbol']}**: {spread_pct:.2f}% ({high_ex} → {low_ex})\n"
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )
                
        except Exception as e:
            logger.error(f"Error in spreads command: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error fetching spread data: {str(e)}")

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
                message += "Strategy: LONG futures + SHORT margin\n"
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
                
        except Exception as e:
            logger.error(f"Error in button callback: {str(e)}", exc_info=True)
            await query.edit_message_text(f"❌ Error loading details: {str(e)}")

    async def _get_all_exchange_data_for_symbol(self, symbol: str) -> dict:
        """Get funding rates and prices for a symbol from all exchanges"""
        result = {}
        
        for ex_name, ex_data in self.funding_manager.funding_data.items():
            rates = ex_data.get('funding_rates', {})
            prices = ex_data.get('prices', {})
            
            if symbol in rates and symbol in prices:
                funding_info = rates[symbol]
                price = prices[symbol]
                
                result[ex_name] = {
                    'funding_rate': funding_info.funding_rate,
                    'price': price,
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
            
            # Format price
            price_str = f"{data['price']:.4f}".rjust(9)
            
            # Format time remaining as HH:MM
            time_remaining = self._calculate_time_remaining(data['next_funding'])
            time_str = time_remaining.rjust(6)
            
            msg += f"{ex_display} {rate_str} {price_str}  {time_str}\n"
        
        msg += "```"
        
        return msg

    def _format_detailed_price_spread(self, spread: dict, all_data: dict) -> str:
        """Format detailed price spread message"""
        symbol = spread['symbol']
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Top spread section
        msg += "**TOP PRICE SPREAD**\n"
        high_ex = spread['highest_exchange'].lower()
        low_ex = spread['lowest_exchange'].lower()
        
        high_url = self._format_exchange_url(spread['highest_exchange'], symbol)
        low_url = self._format_exchange_url(spread['lowest_exchange'], symbol)
        
        msg += f"BUY [{low_ex}]({low_url}) - SELL [{high_ex}]({high_url})\n\n"
        
        # Spread info
        msg += f"**Спред цен:** {spread['spread_percentage']:.2f}%\n"
        msg += f"**Высшая цена:** ${spread['highest_price']:.4f} ({spread['highest_exchange']})\n"
        msg += f"**Низшая цена:** ${spread['lowest_price']:.4f} ({spread['lowest_exchange']})\n\n"
        
        # All exchanges table
        msg += "**Все биржи:**\n"
        msg += "```\n"
        msg += "Биржа       Цена      Отклонение\n"
        msg += "──────────────────────────────────\n"
        
        # Sort exchanges by price (highest first)
        sorted_exchanges = sorted(
            all_data.items(), 
            key=lambda x: x[1]['price'], 
            reverse=True
        )
        
        avg_price = sum(data['price'] for data in all_data.values()) / len(all_data)
        
        for ex_name, data in sorted_exchanges:
            # Format exchange name (max 9 chars)
            ex_display = ex_name.lower()[:9].ljust(9)
            
            # Format price
            price_str = f"${data['price']:.4f}".rjust(10)
            
            # Format deviation from average
            deviation = ((data['price'] - avg_price) / avg_price) * 100
            dev_str = f"{deviation:+.2f}%".rjust(8)
            
            msg += f"{ex_display} {price_str}  {dev_str}\n"
        
        msg += "```"
        
        return msg

    def _format_detailed_margin_opportunity(self, opp: dict) -> str:
        """Format detailed margin arbitrage opportunity message"""
        symbol = opp['symbol']
        base_token = opp['base_token']
        
        # Format symbol for display
        if symbol.endswith('USDT'):
            display_symbol = f"{symbol[:-4]}-USDT"
        else:
            display_symbol = symbol
        
        # Build message
        msg = f"**Монета: {display_symbol}**\n\n"
        
        # Strategy section
        msg += "**💹 FUTURES-MARGIN ARBITRAGE**\n"
        msg += "Strategy: LONG futures + SHORT margin\n\n"
        
        futures_ex = opp['futures_exchange']
        margin_ex = opp['margin_exchange']
        
        futures_url = self._format_exchange_url(futures_ex, symbol)
        spot_symbol_formatted = f"{base_token}-USDT" if margin_ex != 'Gate.io' else f"{base_token}_USDT"
        margin_url = self.spot_urls.get(margin_ex, '#').format(symbol=spot_symbol_formatted)
        
        msg += f"📈 LONG [{futures_ex.lower()}]({futures_url}) (futures)\n"
        msg += f"📉 SHORT [{margin_ex.lower()}]({margin_url}) (margin)\n\n"
        
        # Key metrics
        msg += "**Показатели:**\n"
        msg += f"• Funding Rate: **{opp['funding_rate']:.4f}%** (negative = you receive)\n"
        msg += f"• Profit per period: **{opp['funding_profit']:.4f}%**\n"
        msg += f"• Price Spread: {opp['price_spread']:+.4f}%\n\n"
        
        # Prices
        msg += "**Цены:**\n"
        msg += f"• Futures ({futures_ex}): ${opp['futures_price']:.4f}\n"
        msg += f"• Spot ({margin_ex}): ${opp['spot_price']:.4f}\n\n"
        
        # Next funding
        time_remaining = self._calculate_time_remaining(opp['next_funding'])
        msg += f"⏰ Next funding: **{time_remaining}**\n\n"
        
        # Explanation
        msg += "**Как работает:**\n"
        msg += "```\n"
        msg += "1. LONG futures (получаем funding)\n"
        msg += "2. SHORT margin (без funding)\n"
        msg += "3. Позиции хеджированы\n"
        msg += "4. Profit = |funding rate|\n"
        msg += "```"
        
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

    def run(self) -> None:
        """Start the bot"""
        try:
            app = (
                ApplicationBuilder()
                .token(self.config.telegram_bot_token)
                .job_queue(None)
                .build()
            )

            # Add command handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("help", self.help_command))
            app.add_handler(CommandHandler("funding", self.funding_command))
            app.add_handler(CommandHandler("setmode", self.setmode_command))  # NEW: Mode selection
            app.add_handler(CommandHandler("spreads", self.spreads_command))
            app.add_handler(CommandHandler("next", self.next_funding_command))
            
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