from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
from telegram.ext import Updater, CommandHandler
import asyncio
import schedule
import time
from telegram import Bot
import logging
import pytz
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='trading_system.log'
)
logger = logging.getLogger(__name__)

# Constants
API_KEY = "zfz6i2qjh9zjl26m"
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

class EnhancedTradingSystem:
    def __init__(self):
        self.kite = KiteConnect(api_key=API_KEY)
        self.bot = Bot(token=BOT_TOKEN)
        self.ist = pytz.timezone('Asia/Kolkata')
        self.traded_strikes = set()  # Track trades to avoid duplicates
        self.setup_parameters()

    def setup_parameters(self):
        """Initialize trading parameters"""
        # Technical Analysis Parameters
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.ema_fast = 9
        self.ema_slow = 21
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.volume_threshold = 1.5
        
        # Risk Management
        self.max_risk_percent = 2.0
        self.reward_ratio = 2.0
        self.max_trades_per_day = 3

    def get_market_data(self, symbol="NIFTY 50", interval="5minute", days=5):
        """Fetch market data from Kite"""
        try:
            end_date = datetime.now(self.ist)
            start_date = end_date - timedelta(days=days)
            
            instrument_token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"]["instrument_token"]
            historical_data = self.kite.historical_data(
                instrument_token,
                start_date,
                end_date,
                interval
            )
            
            return pd.DataFrame(historical_data)
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None

    def get_pre_market_data(self):
        """Fetch pre-market data including global markets"""
        try:
            # Get SGX Nifty data
            sgx_nifty = self.kite.ltp(["SGX:NIFTY-I"])
            
            # Get global market data
            global_indices = {
                "US": ["^GSPC", "^DJI", "^IXIC"],  # S&P 500, Dow, Nasdaq
                "Asia": ["^N225", "^HSI"],  # Nikkei, Hang Seng
                "Europe": ["^FTSE", "^GDAXI"]  # FTSE, DAX
            }
            
            global_data = {}
            for region, indices in global_indices.items():
                region_data = {}
                for index in indices:
                    try:
                        quote = self.kite.quote(f"GLOBAL:{index}")
                        region_data[index] = {
                            'close': quote['last_price'],
                            'change': quote['net_change']
                        }
                    except Exception as e:
                        logger.error(f"Error fetching {index}: {str(e)}")
                global_data[region] = region_data
            
            return {
                'sgx_nifty': sgx_nifty,
                'global_markets': global_data
            }
        except Exception as e:
            logger.error(f"Error in pre-market data: {str(e)}")
            return None

    async def send_pre_market_analysis(self):
        """Generate and send pre-market analysis"""
        try:
            pre_market_data = self.get_pre_market_data()
            if not pre_market_data:
                return
            
            # Analyze global market influence
            global_sentiment = self.analyze_global_markets(pre_market_data['global_markets'])
            
            # Get SGX Nifty status
            sgx_status = self.analyze_sgx_nifty(pre_market_data['sgx_nifty'])
            
            # Get important news and events
            news = self.get_important_news()
            
            message = f"""
🌅 Pre-Market Analysis - {datetime.now(self.ist).strftime('%d-%b-%Y')}

🌎 Global Markets:
{self.format_global_markets(pre_market_data['global_markets'])}

📈 SGX Nifty: {sgx_status}

📰 Important Market News:
{news}

🎯 Expected Market Behavior:
• Gap Opening: {self.calculate_gap_opening()}
• Trend Expectation: {global_sentiment['trend']}
• Volatility Expectation: {global_sentiment['volatility']}

⚠️ Key Levels for Today:
Support: {self.calculate_key_levels()['support']}
Resistance: {self.calculate_key_levels()['resistance']}

💡 Trading Strategy:
{self.generate_pre_market_strategy()}

#PreMarket #NiftyAnalysis
"""
            await self.bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info("Pre-market analysis sent successfully")
            
        except Exception as e:
            logger.error(f"Error in pre-market analysis: {str(e)}")

    def analyze_global_markets(self, global_data):
        """Analyze global market influence"""
        # Implementation for global market analysis
        sentiment = {
            'trend': 'Neutral',
            'volatility': 'Normal',
            'strength': 0
        }
        
        # Analyze each region
        for region, data in global_data.items():
            positive_count = sum(1 for idx in data.values() if idx['change'] > 0)
            negative_count = len(data) - positive_count
            
            if positive_count > negative_count:
                sentiment['strength'] += 1
            elif negative_count > positive_count:
                sentiment['strength'] -= 1
                
        # Determine overall trend
        if sentiment['strength'] > 1:
            sentiment['trend'] = 'Bullish'
        elif sentiment['strength'] < -1:
            sentiment['trend'] = 'Bearish'
            
        return sentiment

    def check_pro_trading_setup(self, data):
        """Check for professional trading setups"""
        try:
            df = data.copy()
            
            # Calculate technical indicators
            df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
            df['ema_fast'] = talib.EMA(df['close'], timeperiod=self.ema_fast)
            df['ema_slow'] = talib.EMA(df['close'], timeperiod=self.ema_slow)
            macd, signal, hist = talib.MACD(df['close'], 
                                          fastperiod=self.macd_fast, 
                                          slowperiod=self.macd_slow, 
                                          signalperiod=self.macd_signal)
            df['macd'] = macd
            df['macd_signal'] = signal
            df['macd_hist'] = hist
            
            # Volume analysis
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            volume_surge = df['volume'].iloc[-1] > df['volume_sma'].iloc[-1] * self.volume_threshold
            
            # Price action
            current_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]
            
            # Trading setups
            setups = []
            
            # Bullish setup conditions
            if (df['rsi'].iloc[-1] < self.rsi_oversold and
                df['ema_fast'].iloc[-1] > df['ema_fast'].iloc[-2] and
                df['macd_hist'].iloc[-1] > df['macd_hist'].iloc[-2] and
                volume_surge):
                setups.append({
                    'type': 'BULLISH',
                    'strength': 'HIGH',
                    'entry': current_candle['close'],
                    'stop_loss': min(current_candle['low'], prev_candle['low']),
                    'target1': current_candle['close'] + (current_candle['close'] - min(current_candle['low'], prev_candle['low'])),
                    'target2': current_candle['close'] + 2 * (current_candle['close'] - min(current_candle['low'], prev_candle['low'])),
                    'option_type': 'CE'
                })
                
            # Bearish setup conditions
            elif (df['rsi'].iloc[-1] > self.rsi_overbought and
                  df['ema_fast'].iloc[-1] < df['ema_fast'].iloc[-2] and
                  df['macd_hist'].iloc[-1] < df['macd_hist'].iloc[-2] and
                  volume_surge):
                setups.append({
                    'type': 'BEARISH',
                    'strength': 'HIGH',
                    'entry': current_candle['close'],
                    'stop_loss': max(current_candle['high'], prev_candle['high']),
                    'target1': current_candle['close'] - (max(current_candle['high'], prev_candle['high']) - current_candle['close']),
                    'target2': current_candle['close'] - 2 * (max(current_candle['high'], prev_candle['high']) - current_candle['close']),
                    'option_type': 'PE'
                })
                
            return setups
            
        except Exception as e:
            logger.error(f"Error in pro trading setup: {str(e)}")
            return []

    def select_option_strike(self, current_price, setup_type):
        """Select the optimal option strike price and get premium data"""
        try:
            # Round to nearest 50/100
            strike_interval = 100 if current_price > 10000 else 50
            atm_strike = round(current_price / strike_interval) * strike_interval
            
            if setup_type == 'BULLISH':
                # For CE, select slightly OTM strike
                selected_strike = atm_strike
                option_symbol = f"NIFTY{datetime.now(self.ist).strftime('%d%b').upper()}C{selected_strike}"
                
                # Get option premium data
                quote = self.kite.quote([f"NFO:{option_symbol}"])
                premium = quote[f"NFO:{option_symbol}"]["last_price"] if quote else None
                
                return {
                    'strike': selected_strike,
                    'type': 'CE',
                    'premium': premium,
                    'symbol': option_symbol,
                    'hedge_strike': atm_strike + strike_interval,
                    'hedge_type': 'PE'
                }
            else:  # BEARISH
                # For PE, select slightly OTM strike
                selected_strike = atm_strike
                option_symbol = f"NIFTY{datetime.now(self.ist).strftime('%d%b').upper()}P{selected_strike}"
                
                # Get option premium data
                quote = self.kite.quote([f"NFO:{option_symbol}"])
                premium = quote[f"NFO:{option_symbol}"]["last_price"] if quote else None
                
                return {
                    'strike': selected_strike,
                    'type': 'PE',
                    'premium': premium,
                    'symbol': option_symbol,
                    'hedge_strike': atm_strike - strike_interval,
                    'hedge_type': 'CE'
                }
                
        except Exception as e:
            logger.error(f"Error selecting strike: {str(e)}")
            return None

    async def monitor_and_send_signals(self):
        """Continuous monitoring for trading setups"""
        try:
            while self.is_market_hours():
                # Get latest market data
                data = self.get_market_data(interval="5minute", days=1)
                if data is None:
                    continue
                
                # Check for trading setups
                setups = self.check_pro_trading_setup(data)
                
                for setup in setups:
                    # Select option strike
                    option_data = self.select_option_strike(
                        data['close'].iloc[-1],
                        setup['type']
                    )
                    
                    if option_data and self.validate_trade(setup, option_data):
                        await self.send_trading_signal(setup, option_data)
                        
                # Wait for 1 minute before next check
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Error in monitoring: {str(e)}")

    async def send_trading_signal(self, setup, option_data):
        """Send trading signal to Telegram"""
        try:
            risk_reward = abs(setup['target1'] - setup['entry']) / abs(setup['entry'] - setup['stop_loss'])
            
            # Calculate premium targets and stop-loss
            premium_target1 = option_data['premium'] * 1.3  # 30% profit
            premium_target2 = option_data['premium'] * 1.5  # 50% profit
            premium_sl = option_data['premium'] * 0.7      # 30% loss
            
            action = "BUY" if setup['type'] == "BULLISH" else "SELL"
            
            message = f"""
🎯 NIFTY OPTIONS SIGNAL ALERT!
Time: {datetime.now(self.ist).strftime('%H:%M:%S')}

💫 TRADE SETUP: {setup['type']} ({setup['strength']})

🎯 MAIN TRADE:
{action} {option_data['symbol']}
Strike: {option_data['strike']} {option_data['type']}

� PREMIUM LEVELS:
Entry Price: {option_data['premium']:.1f}
Target 1: {premium_target1:.1f} (+30%)
Target 2: {premium_target2:.1f} (+50%)
Stop Loss: {premium_sl:.1f} (-30%)

📈 SPOT LEVELS:
Current: {setup['entry']:.2f}
Target 1: {setup['target1']:.2f}
Target 2: {setup['target2']:.2f}
Stop Loss: {setup['stop_loss']:.2f}

🛡️ HEDGE TRADE (Optional):
Buy 1 lot {option_data['hedge_type']} @ {option_data['hedge_strike']}

📊 CONFIRMATION:
• RSI: Extreme {setup['type'].lower()} zone
• EMA: Fresh crossover
• MACD: Strong momentum
• Volume: Above average

⚠️ RISK MANAGEMENT:
• Strict stop-loss at premium {premium_sl:.1f}
• Book 50% at first target
• Trail SL for remaining position
• Max lot size: 1-2 lots

⏰ Valid for Intraday Only
#NiftyOptions #{option_data['type']} #Trading
"""
            await self.bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info(f"Trading signal sent for {option_data['type']} @ {option_data['strike']}")
            
        except Exception as e:
            logger.error(f"Error sending signal: {str(e)}")

    def is_market_hours(self):
        """Check if current time is within market hours"""
        now = datetime.now(self.ist)
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_start <= now <= market_end

    def validate_trade(self, setup, option_data):
        """Validate if the trade should be taken"""
        # Check if we've already traded this strike today
        strike_key = f"{option_data['strike']}_{option_data['type']}"
        if strike_key in self.traded_strikes:
            return False
            
        # Check risk-reward ratio
        risk_reward = abs(setup['target1'] - setup['entry']) / abs(setup['entry'] - setup['stop_loss'])
        if risk_reward < self.reward_ratio:
            return False
            
        # Add to traded strikes if validated
        self.traded_strikes.add(strike_key)
        return True

    async def run(self):
        """Main function to run the trading system"""
        try:
            # Schedule pre-market analysis
            schedule.every().day.at("08:30").do(self.send_pre_market_analysis)
            
            # Start monitoring at market open
            schedule.every().day.at("09:15").do(self.monitor_and_send_signals)
            
            while True:
                schedule.run_pending()
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in main run: {str(e)}")

if __name__ == "__main__":
    # Initialize and run the trading system
    trading_system = EnhancedTradingSystem()
    asyncio.run(trading_system.run())