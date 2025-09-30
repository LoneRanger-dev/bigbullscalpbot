import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import telebot
from kiteconnect import KiteConnect
import requests
import ta
import logging

# Configure logging
logging.basicConfig(filename='trading_signals.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Your Telegram Credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

# Your Zerodha Credentials
API_KEY = "zfz6i2qjh9zjl26m"
API_SECRET = "esdsumpztnzmry8rl1e411b95qt86v2m"

class TradingSignals:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.kite = self.initialize_kite()
        
    def initialize_kite(self):
        kite = KiteConnect(api_key=API_KEY)
        # You'll need to complete the authentication process
        # kite.set_access_token(access_token)
        return kite
    
    def calculate_indicators(self, df):
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['BB_Upper'] = bollinger.bollinger_hband()
        df['BB_Lower'] = bollinger.bollinger_lband()
        
        # Supertrend (custom calculation)
        atr_period = 10
        atr_multiplier = 3
        
        df['TR'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).true_range()
        df['ATR'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        
        df['Basic_Upper_Band'] = (df['high'] + df['low']) / 2 + (atr_multiplier * df['ATR'])
        df['Basic_Lower_Band'] = (df['high'] + df['low']) / 2 - (atr_multiplier * df['ATR'])
        
        return df
    
    def get_market_data(self):
        try:
            # Nifty 50 instrument token
            instrument_token = 256265
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)
            
            data = self.kite.historical_data(
                instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval='5minute'
            )
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Error fetching market data: {str(e)}")
            return None

    def generate_trading_signal(self, df):
        if df is None or len(df) < 20:
            return "Insufficient data for analysis"
            
        current_price = df['close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_Signal'].iloc[-1]
        bb_upper = df['BB_Upper'].iloc[-1]
        bb_lower = df['BB_Lower'].iloc[-1]
        
        # Calculate support and resistance
        recent_high = df['high'].max()
        recent_low = df['low'].min()
        pivot = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
        
        signal_message = f"""
🎯 *NIFTY 50 Trading Signals* - {datetime.now().strftime('%d %b %Y %H:%M')}

💰 *Current Price:* ₹{current_price:.2f}

📊 *Technical Indicators:*
• RSI: {rsi:.2f} ({'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'})
• MACD: {'Bullish' if macd > macd_signal else 'Bearish'} {'(Crossover)' if abs(macd - macd_signal) < 0.5 else ''}
• Bollinger Bands:
  Upper: {bb_upper:.2f}
  Lower: {bb_lower:.2f}

📍 *Key Levels:*
• Resistance 2: {recent_high:.2f}
• Resistance 1: {(pivot + recent_high)/2:.2f}
• Pivot: {pivot:.2f}
• Support 1: {(pivot + recent_low)/2:.2f}
• Support 2: {recent_low:.2f}

⚡️ *Trading Setup:*"""

        # Generate trading signals
        if rsi < 30 and current_price < bb_lower and macd > macd_signal:
            signal_message += f"""
🟢 *Strong Buy Signal*
Entry Zone: {current_price:.2f} - {current_price * 1.002:.2f}
Target 1: {current_price * 1.005:.2f}
Target 2: {current_price * 1.008:.2f}
Stop Loss: {current_price * 0.997:.2f}"""
        
        elif rsi > 70 and current_price > bb_upper and macd < macd_signal:
            signal_message += f"""
🔴 *Strong Sell Signal*
Entry Zone: {current_price:.2f} - {current_price * 0.998:.2f}
Target 1: {current_price * 0.995:.2f}
Target 2: {current_price * 0.992:.2f}
Stop Loss: {current_price * 1.003:.2f}"""
        
        else:
            signal_message += """
⚪️ *Neutral Zone - Wait for Better Setup*
• Watch for breakout above resistance
• Watch for breakdown below support"""

        signal_message += "\n\n⚠️ *Risk Management:*\n• Always use stop loss\n• Follow your trading plan\n• Max risk per trade: 1%"
        
        return signal_message

    def send_signal(self, message):
        try:
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            logging.info("Signal sent successfully")
        except Exception as e:
            logging.error(f"Error sending signal: {str(e)}")

    def run(self):
        print("Starting trading signals system...")
        logging.info("Trading signals system started")
        
        while True:
            try:
                # Get market data
                df = self.get_market_data()
                if df is not None:
                    # Calculate indicators
                    df = self.calculate_indicators(df)
                    
                    # Generate and send signal
                    signal = self.generate_trading_signal(df)
                    self.send_signal(signal)
                    
                    # Wait for 5 minutes before next update
                    time.sleep(300)
                else:
                    logging.warning("No data received, waiting before retry...")
                    time.sleep(60)
                    
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    try:
        trading_signals = TradingSignals()
        trading_signals.run()
    except KeyboardInterrupt:
        print("\nStopping trading signals system...")
        logging.info("Trading signals system stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        logging.critical(f"Fatal error: {str(e)}")