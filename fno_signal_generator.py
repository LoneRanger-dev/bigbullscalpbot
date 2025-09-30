from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import telebot
import logging

class FNOSignalGenerator:
    def __init__(self, api_key):
        self.kite = KiteConnect(api_key=api_key)
        self.ist = pytz.timezone('Asia/Kolkata')
        self.telegram_bot = telebot.TeleBot('8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs')
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='fno_signals.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_atm_strike(self, symbol, current_price):
        """Get the At-The-Money strike price"""
        if symbol in ['NIFTY', 'BANKNIFTY']:
            round_to = 100
        else:
            round_to = 50
        return round(current_price / round_to) * round_to

    def get_option_chain(self, symbol):
        """Fetch option chain for the symbol"""
        try:
            instruments = self.kite.search_instruments("NFO", symbol)
            df = pd.DataFrame(instruments)
            df['expiry'] = pd.to_datetime(df['expiry']).dt.date
            
            # Get current expiry
            current_date = datetime.now(self.ist).date()
            current_expiry = df[df['expiry'] > current_date]['expiry'].min()
            
            # Filter options for current expiry
            options = df[
                (df['expiry'] == current_expiry) &
                (df['instrument_type'].isin(['CE', 'PE']))
            ]
            return options
        except Exception as e:
            logging.error(f"Error fetching option chain: {str(e)}")
            return None

    def calculate_support_resistance(self, symbol, timeframe='day'):
        """Calculate support and resistance levels"""
        try:
            # Get historical data
            instrument_token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"]["instrument_token"]
            end_date = datetime.now(self.ist)
            start_date = end_date - timedelta(days=30)
            
            historical_data = self.kite.historical_data(
                instrument_token, 
                start_date, 
                end_date, 
                timeframe
            )
            
            df = pd.DataFrame(historical_data)
            
            # Calculate pivot points
            pivot = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
            r1 = 2 * pivot - df['low'].iloc[-1]
            s1 = 2 * pivot - df['high'].iloc[-1]
            
            return {
                'pivot': pivot,
                'r1': r1,
                's1': s1,
                'prev_close': df['close'].iloc[-1]
            }
        except Exception as e:
            logging.error(f"Error calculating S/R levels: {str(e)}")
            return None

    def select_strike_prices(self, symbol, current_price, trend):
        """Select optimal strike prices based on trend and price levels"""
        try:
            atm_strike = self.get_atm_strike(symbol, current_price)
            
            if trend == 'bullish':
                option_type = 'CE'
                selected_strike = atm_strike
                hedge_strike = atm_strike + (100 if symbol in ['NIFTY', 'BANKNIFTY'] else 50)
            else:  # bearish
                option_type = 'PE'
                selected_strike = atm_strike
                hedge_strike = atm_strike - (100 if symbol in ['NIFTY', 'BANKNIFTY'] else 50)
            
            return {
                'primary_strike': selected_strike,
                'hedge_strike': hedge_strike,
                'option_type': option_type
            }
        except Exception as e:
            logging.error(f"Error selecting strikes: {str(e)}")
            return None

    def analyze_trend(self, symbol):
        """Analyze trend using multiple timeframes"""
        try:
            instrument_token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"]["instrument_token"]
            end_date = datetime.now(self.ist)
            start_date = end_date - timedelta(days=5)
            
            # Get 5-minute data for intraday trend
            data = self.kite.historical_data(
                instrument_token,
                start_date,
                end_date,
                '5minute'
            )
            df = pd.DataFrame(data)
            
            # Calculate EMAs
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            
            # Determine trend
            current_price = df['close'].iloc[-1]
            ema_20 = df['ema_20'].iloc[-1]
            ema_50 = df['ema_50'].iloc[-1]
            
            if current_price > ema_20 and ema_20 > ema_50:
                trend = 'bullish'
            elif current_price < ema_20 and ema_20 < ema_50:
                trend = 'bearish'
            else:
                trend = 'neutral'
                
            return {
                'trend': trend,
                'current_price': current_price
            }
        except Exception as e:
            logging.error(f"Error analyzing trend: {str(e)}")
            return None

    def calculate_entry_levels(self, symbol, strike_info, current_price, levels):
        """Calculate entry, target, and stop-loss levels"""
        try:
            option_type = strike_info['option_type']
            strike = strike_info['primary_strike']
            
            # Calculate risk-reward levels
            if option_type == 'CE':
                entry = current_price
                target = levels['r1']
                stop_loss = levels['s1']
            else:  # PE
                entry = current_price
                target = levels['s1']
                stop_loss = levels['r1']
            
            # Calculate risk-reward ratio
            risk = abs(entry - stop_loss)
            reward = abs(target - entry)
            rr_ratio = reward / risk if risk != 0 else 0
            
            return {
                'entry': entry,
                'target': target,
                'stop_loss': stop_loss,
                'rr_ratio': rr_ratio
            }
        except Exception as e:
            logging.error(f"Error calculating entry levels: {str(e)}")
            return None

    def generate_fno_signal(self, symbol):
        """Generate complete F&O trading signal"""
        try:
            # Analyze current market conditions
            trend_analysis = self.analyze_trend(symbol)
            if not trend_analysis:
                return
            
            current_price = trend_analysis['current_price']
            trend = trend_analysis['trend']
            
            # Get support/resistance levels
            levels = self.calculate_support_resistance(symbol)
            if not levels:
                return
            
            # Select strike prices
            strike_info = self.select_strike_prices(symbol, current_price, trend)
            if not strike_info:
                return
            
            # Calculate entry levels
            entry_levels = self.calculate_entry_levels(
                symbol, strike_info, current_price, levels
            )
            if not entry_levels:
                return
            
            # Generate signal message
            signal_msg = self.format_signal_message(
                symbol, trend, strike_info, entry_levels, current_price
            )
            
            # Send signal via Telegram
            self.telegram_bot.send_message(chat_id='YOUR_CHAT_ID', text=signal_msg)
            logging.info(f"Signal sent for {symbol}")
            
        except Exception as e:
            logging.error(f"Error generating signal: {str(e)}")

    def format_signal_message(self, symbol, trend, strike_info, entry_levels, current_price):
        """Format the signal message with all necessary details"""
        trend_emoji = "🟢" if trend == 'bullish' else "🔴" if trend == 'bearish' else "⚪"
        
        message = f"""
🎯 F&O Trading Signal for {symbol}

Market Trend: {trend_emoji} {trend.upper()}
Current Price: ₹{current_price:.2f}

Option Strategy:
{strike_info['option_type']} @ Strike {strike_info['primary_strike']}
Hedge: {strike_info['hedge_strike']} {'PE' if strike_info['option_type'] == 'CE' else 'CE'}

Entry Levels:
Entry Price: ₹{entry_levels['entry']:.2f}
Target: ₹{entry_levels['target']:.2f}
Stop Loss: ₹{entry_levels['stop_loss']:.2f}
Risk-Reward: 1:{entry_levels['rr_ratio']:.2f}

⚠️ Risk Management:
• Use strict stop-loss
• Max position size: 2-3% of capital
• Book partial profits at 50% target

Valid for Intraday Only
Generated at {datetime.now(self.ist).strftime('%d-%b-%Y %H:%M:%S')} IST
"""
        return message

    def monitor_and_update(self, symbol, entry_levels):
        """Monitor active signals and send updates"""
        try:
            current_price = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"]["last_price"]
            
            # Check if target or stop-loss hit
            if current_price >= entry_levels['target']:
                update_msg = f"🎯 TARGET HIT for {symbol}\nBook Profits!"
                self.telegram_bot.send_message(chat_id='YOUR_CHAT_ID', text=update_msg)
            elif current_price <= entry_levels['stop_loss']:
                update_msg = f"⚠️ STOP-LOSS HIT for {symbol}\nExit Position!"
                self.telegram_bot.send_message(chat_id='YOUR_CHAT_ID', text=update_msg)
                
        except Exception as e:
            logging.error(f"Error monitoring signal: {str(e)}")

# Example usage
if __name__ == "__main__":
    api_key = "zfz6i2qjh9zjl26m"
    signal_generator = FNOSignalGenerator(api_key)
    
    # Generate signals for indices
    for symbol in ['NIFTY', 'BANKNIFTY']:
        signal_generator.generate_fno_signal(symbol)