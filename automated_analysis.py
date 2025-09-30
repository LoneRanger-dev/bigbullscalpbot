import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import telebot
import time
import schedule
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# Market timing constants
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
PRE_MARKET = "08:30"

# Trading parameters
RISK_PERCENT = 2  # Risk per trade
RR_RATIO = 2  # Risk-Reward ratio
MAX_TRADES_PER_DAY = 3

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

# Constants
NIFTY_TOKEN = 256265  # Nifty 50 instrument token

class AutomatedAnalysis:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.ist = pytz.timezone('Asia/Kolkata')
        self.fno_symbols = ['NIFTY', 'BANKNIFTY']  # Add more symbols as needed
        self.active_trades = []
        self.trades_today = 0
        self.last_signal_time = None
        self.min_signal_gap = 900  # 15 minutes in seconds

    def get_market_data(self) -> Dict:
        """Fetch current market data using MCP Kite tools"""
        try:
            # Using mcp_kite tools to get data
            quotes = mcp_kite_get_quotes({"instruments": ["NSE:NIFTY 50"]})
            nifty_data = quotes["NSE:NIFTY 50"]
            
            return {
                'close': nifty_data['last_price'],
                'change': nifty_data['net_change'],
                'change_percent': (nifty_data['net_change'] / nifty_data['ohlc']['close']) * 100,
                'high': nifty_data['ohlc']['high'],
                'low': nifty_data['ohlc']['low'],
                'open': nifty_data['ohlc']['open'],
                'prev_close': nifty_data['ohlc']['close'],
                'volume': nifty_data.get('volume', 0)
            }
        except Exception as e:
            print(f"Error fetching market data: {str(e)}")
            return None

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate various technical indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Moving averages
        sma20 = df['close'].rolling(window=20).mean()
        sma50 = df['close'].rolling(window=50).mean()
        
        # Bollinger Bands
        bb_middle = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)

        return {
            'rsi': rsi.iloc[-1],
            'sma20': sma20.iloc[-1],
            'sma50': sma50.iloc[-1],
            'bb_upper': bb_upper.iloc[-1],
            'bb_middle': bb_middle.iloc[-1],
            'bb_lower': bb_lower.iloc[-1]
        }

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Calculate support and resistance levels using multiple methods"""
        # Method 1: Pivot Points
        pivot = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
        r1 = 2 * pivot - df['low'].iloc[-1]
        r2 = pivot + (df['high'].iloc[-1] - df['low'].iloc[-1])
        s1 = 2 * pivot - df['high'].iloc[-1]
        s2 = pivot - (df['high'].iloc[-1] - df['low'].iloc[-1])
        
        # Method 2: Recent swing highs/lows
        highs = df['high'].rolling(window=10).max()
        lows = df['low'].rolling(window=10).min()
        
        supports = sorted([s1, s2, lows.iloc[-1]])
        resistances = sorted([r1, r2, highs.iloc[-1]], reverse=True)
        
        return (supports, resistances)

    def analyze_price_action(self, df: pd.DataFrame) -> Dict:
        """Detailed price action analysis"""
        # Trend analysis
        sma20 = df['close'].rolling(window=20).mean()
        ema50 = df['close'].ewm(span=50).mean()
        
        # Enhanced trend analysis for F&O
        trend = "Strong Bullish" if df['close'].iloc[-1] > sma20.iloc[-1] and sma20.iloc[-1] > ema50.iloc[-1] else \
               "Bullish" if df['close'].iloc[-1] > sma20.iloc[-1] else \
               "Strong Bearish" if df['close'].iloc[-1] < sma20.iloc[-1] and sma20.iloc[-1] < ema50.iloc[-1] else \
               "Bearish"
        
        # Volatility
        atr = df['high'].rolling(window=14).max() - df['low'].rolling(window=14).min()
        volatility = "High" if atr.iloc[-1] > atr.mean() else "Moderate"
        
        # Volume analysis
        vol_sma = df['volume'].rolling(window=20).mean()
        volume_trend = "Above Average" if df['volume'].iloc[-1] > vol_sma.iloc[-1] else "Below Average"
        
        # Candlestick patterns (basic)
        last_candle = df.iloc[-1]
        body = abs(last_candle['close'] - last_candle['open'])
        upper_wick = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        lower_wick = min(last_candle['open'], last_candle['close']) - last_candle['low']
        
        pattern = "Doji" if body < (upper_wick + lower_wick) / 2 else (
            "Bullish" if last_candle['close'] > last_candle['open'] else "Bearish"
        )
        
        return {
            'trend': trend,
            'volatility': volatility,
            'volume_trend': volume_trend,
            'pattern': pattern
        }

    def generate_analysis(self) -> str:
        """Generate complete market analysis with enhanced indicators"""
        try:
            market_data = self.get_market_data()
            if not market_data:
                return "Error: Unable to fetch market data"

            # Get historical data for technical analysis
            today = datetime.now(self.ist).date()
            hist_data = self.kite.historical_tokenwise(
                tokens=[NIFTY_TOKEN],
                from_date=today - timedelta(days=5),
                to_date=today,
                interval="minute"
            )
            df = pd.DataFrame(hist_data[str(NIFTY_TOKEN)])
            
            # Get all analysis components
            indicators = self.calculate_technical_indicators(df)
            supports, resistances = self.calculate_support_resistance(df)
            price_action = self.analyze_price_action(df)
            
            analysis = f"""
🔍 *Post Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

📊 *Market Overview:*
• Nifty Close: {market_data['close']:.2f}
• Change: {market_data['change']:.2f} ({market_data['change_percent']:.2f}%)
• Day's Range: {market_data['low']:.2f} - {market_data['high']:.2f}
• Volume: {market_data['volume']:,.0f} ({price_action['volume_trend']})

📈 *Technical Analysis:*
• Trend: {price_action['trend']}
• Pattern: {price_action['pattern']} candle
• RSI(14): {indicators['rsi']:.2f}
• Moving Averages:
  - SMA20: {indicators['sma20']:.2f}
  - SMA50: {indicators['sma50']:.2f}
• Bollinger Bands:
  - Upper: {indicators['bb_upper']:.2f}
  - Middle: {indicators['bb_middle']:.2f}
  - Lower: {indicators['bb_lower']:.2f}

🎯 *Key Levels:*
• Resistance Levels:
  R1: {resistances[0]:.2f}
  R2: {resistances[1]:.2f}

• Support Levels:
  S1: {supports[0]:.2f}
  S2: {supports[1]:.2f}

💡 *Trading Setup:*
• Long Setup:
  Entry > {resistances[0]:.2f}
  Target: {resistances[1]:.2f}
  Stop Loss: {supports[0]:.2f}

• Short Setup:
  Entry < {supports[0]:.2f}
  Target: {supports[1]:.2f}
  Stop Loss: {resistances[0]:.2f}

⚠️ *Market Context:*
• Volatility: {price_action['volatility']}
• Volume Profile: {price_action['volume_trend']}
• Risk Level: {"High" if price_action['volatility'] == "High" else "Moderate"}

#NiftyAnalysis #Trading #MarketStrategy"""
            return analysis
            
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            return None

    def generate_fno_signals(self) -> str:
        """Generate F&O specific trading signals"""
        try:
            signals = []
            for symbol in self.fno_symbols:
                market_data = self.get_market_data()
                if not market_data:
                    continue
                
                # Get technical indicators and analysis
                df = pd.DataFrame(market_data, index=[0])  # Convert to DataFrame for analysis
                price_action = self.analyze_price_action(df)
                indicators = self.calculate_technical_indicators(df)
                supports, resistances = self.calculate_support_resistance(df)
                
                # Get optimal strikes
                strikes = self.get_optimal_strikes(symbol, market_data['close'], price_action['trend'])
                if not strikes:
                    continue
                
                signal = f"""
🎯 *F&O Signal - {symbol}*
Time: {datetime.now(self.ist).strftime('%H:%M:%S')}

📊 *Market Context:*
• Current Price: {market_data['close']:.2f}
• Trend: {price_action['trend']}
• RSI: {indicators['rsi']:.2f}

🎯 *Option Strategy:*
• {strikes['option_type']} @ Strike {strikes['primary_strike']}
• Hedge: {strikes['hedge_strike']} {'PE' if strikes['option_type'] == 'CE' else 'CE'}

📍 *Entry Levels:*
• Entry near: {market_data['close']:.2f}
• Target 1: {resistances[0]:.2f if strikes['option_type'] == 'CE' else supports[0]:.2f}
• Target 2: {resistances[1]:.2f if strikes['option_type'] == 'CE' else supports[1]:.2f}
• Stop Loss: {supports[0]:.2f if strikes['option_type'] == 'CE' else resistances[0]:.2f}

⚠️ *Risk Management:*
• Use strict stop-loss
• Position Size: 2-3% of capital
• Book partial at first target

Valid for Intraday Only
#FnO #{symbol} #Trading
"""
                signals.append(signal)
            
            return "\n\n".join(signals)
        except Exception as e:
            print(f"Error generating F&O signals: {str(e)}")
            return None

    def send_analysis(self):
        """Send market analysis to Telegram"""
        try:
            analysis = self.generate_analysis()
            if analysis:
                self.bot.send_message(CHAT_ID, analysis, parse_mode='Markdown')
                print("Analysis sent successfully!")
            else:
                print("Failed to generate analysis")
        except Exception as e:
            print(f"Error sending analysis: {str(e)}")
            
    def send_fno_signals(self):
        """Send F&O signals to Telegram"""
        try:
            signals = self.generate_fno_signals()
            if signals:
                self.bot.send_message(CHAT_ID, signals, parse_mode='Markdown')
                print("F&O signals sent successfully!")
            else:
                print("Failed to generate F&O signals")
        except Exception as e:
            print(f"Error sending F&O signals: {str(e)}")

    def get_optimal_strikes(self, symbol: str, current_price: float, trend: str) -> Dict:
        """Select optimal strike prices for F&O trading"""
        try:
            # Round to nearest strike
            strike_interval = 100 if symbol in ['NIFTY', 'BANKNIFTY'] else 50
            atm_strike = round(current_price / strike_interval) * strike_interval
            
            if 'Strong' in trend:
                if 'Bullish' in trend:
                    primary_strike = atm_strike
                    hedge_strike = atm_strike + strike_interval
                    option_type = 'CE'
                else:  # Strong Bearish
                    primary_strike = atm_strike
                    hedge_strike = atm_strike - strike_interval
                    option_type = 'PE'
            else:
                if 'Bullish' in trend:
                    primary_strike = atm_strike - strike_interval
                    hedge_strike = atm_strike
                    option_type = 'CE'
                else:  # Bearish
                    primary_strike = atm_strike + strike_interval
                    hedge_strike = atm_strike
                    option_type = 'PE'
            
            return {
                'primary_strike': primary_strike,
                'hedge_strike': hedge_strike,
                'option_type': option_type
            }
        except Exception as e:
            print(f"Error selecting strikes: {str(e)}")
            return None

    def generate_pre_market_analysis(self) -> str:
        """Generate pre-market analysis including global cues and important events"""
        try:
            # Get SGX Nifty data using Kite API
            quotes = self.get_market_data()
            if not quotes:
                return None

            # Get global market data
            global_indices = [
                "NIFTY 50",
                "BANKNIFTY",
                "NIFTY IT",  # Key sector indices
                "NIFTY BANK",
                "NIFTY AUTO"
            ]
            
            analysis = f"""
🌅 *Pre-Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

🌏 *Global Market Impact:*
• SGX Nifty: {quotes.get('close', 'N/A')} ({quotes.get('change_percent', 0):.2f}%)
• Key Levels for Today:
  - Support: {quotes.get('support', 'N/A')}
  - Resistance: {quotes.get('resistance', 'N/A')}

📊 *Expected Market Breadth:*
• Advance-Decline Ratio: {quotes.get('adv_dec_ratio', 'N/A')}
• FII/DII Activity: {quotes.get('fii_activity', 'N/A')}

🎯 *Trading Strategy for Today:*
• Trend Analysis: {quotes.get('trend', 'N/A')}
• Volatility Expectation: {quotes.get('volatility', 'N/A')}
• Key Sectors to Watch: {', '.join(quotes.get('key_sectors', []))}

⚠️ *Important Events Today:*
{quotes.get('events', 'No major events')}

#PreMarket #TradingStrategy"""
            return analysis
        except Exception as e:
            print(f"Error generating pre-market analysis: {str(e)}")
            return None

    def check_pro_trading_setup(self, symbol: str) -> Dict:
        """Check for professional trading setups based on multiple factors"""
        try:
            market_data = self.get_market_data()
            if not market_data:
                return None

            # Calculate technical indicators
            df = pd.DataFrame([market_data])
            indicators = self.calculate_technical_indicators(df)
            price_action = self.analyze_price_action(df)
            supports, resistances = self.calculate_support_resistance(df)

            # Define setup conditions
            setup = {
                'valid': False,
                'type': None,
                'entry': None,
                'stop_loss': None,
                'targets': [],
                'probability': 0,
                'option_strike': None,
                'option_type': None
            }

            # Check bullish setup
            bullish_conditions = [
                indicators['rsi'] < 40,  # Oversold
                price_action['trend'] in ['Bullish', 'Strong Bullish'],
                market_data['close'] > indicators['sma20'],
                market_data['volume'] > market_data['volume_sma20']
            ]

            # Check bearish setup
            bearish_conditions = [
                indicators['rsi'] > 60,  # Overbought
                price_action['trend'] in ['Bearish', 'Strong Bearish'],
                market_data['close'] < indicators['sma20'],
                market_data['volume'] > market_data['volume_sma20']
            ]

            if sum(bullish_conditions) >= 3:
                setup.update({
                    'valid': True,
                    'type': 'BULLISH',
                    'entry': market_data['close'],
                    'stop_loss': supports[0],
                    'targets': resistances[:2],
                    'probability': (sum(bullish_conditions) / len(bullish_conditions)) * 100,
                    'option_type': 'CE'
                })
            elif sum(bearish_conditions) >= 3:
                setup.update({
                    'valid': True,
                    'type': 'BEARISH',
                    'entry': market_data['close'],
                    'stop_loss': resistances[0],
                    'targets': supports[:2],
                    'probability': (sum(bearish_conditions) / len(bearish_conditions)) * 100,
                    'option_type': 'PE'
                })

            if setup['valid']:
                # Calculate optimal strike price
                strikes = self.get_optimal_strikes(symbol, market_data['close'], setup['type'])
                if strikes:
                    setup['option_strike'] = strikes['primary_strike']

            return setup
        except Exception as e:
            print(f"Error checking pro setup: {str(e)}")
            return None

    def monitor_continuous_signals(self):
        """Continuously monitor for trading setups and generate signals"""
        while True:
            now = datetime.now(self.ist)
            current_time = now.strftime("%H:%M")

            # Only check during market hours
            if MARKET_OPEN <= current_time <= MARKET_CLOSE:
                # Check if we can generate new signals
                if self.trades_today < MAX_TRADES_PER_DAY:
                    for symbol in self.fno_symbols:
                        setup = self.check_pro_trading_setup(symbol)
                        if setup and setup['valid']:
                            # Ensure minimum gap between signals
                            if not self.last_signal_time or \
                               (time.time() - self.last_signal_time) >= self.min_signal_gap:
                                self.generate_and_send_signal(symbol, setup)
                                self.last_signal_time = time.time()
                                self.trades_today += 1

            # Reset trade counter at market close
            elif current_time > MARKET_CLOSE:
                self.trades_today = 0
                self.active_trades = []

            time.sleep(60)  # Check every minute

    def schedule_analysis(self):
        """Schedule all analysis tasks"""
        # Pre-market analysis (8:30 AM IST)
        schedule.every().monday.at(PRE_MARKET).do(self.send_pre_market_analysis)
        schedule.every().tuesday.at(PRE_MARKET).do(self.send_pre_market_analysis)
        schedule.every().wednesday.at(PRE_MARKET).do(self.send_pre_market_analysis)
        schedule.every().thursday.at(PRE_MARKET).do(self.send_pre_market_analysis)
        schedule.every().friday.at(PRE_MARKET).do(self.send_pre_market_analysis)

        # Post-market analysis (3:30 PM IST)
        schedule.every().monday.at(MARKET_CLOSE).do(self.send_post_market_analysis)
        schedule.every().tuesday.at(MARKET_CLOSE).do(self.send_post_market_analysis)
        schedule.every().wednesday.at(MARKET_CLOSE).do(self.send_post_market_analysis)
        schedule.every().thursday.at(MARKET_CLOSE).do(self.send_post_market_analysis)
        schedule.every().friday.at(MARKET_CLOSE).do(self.send_post_market_analysis)

        # Start continuous monitoring in a separate thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.monitor_continuous_signals)
        
        print("Analysis scheduled for 3:30 PM IST on weekdays")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

    def generate_post_market_analysis(self) -> str:
        """Generate detailed post-market analysis with movement reasons"""
        try:
            market_data = self.get_market_data()
            if not market_data:
                return None

            # Get sector performance
            sector_performance = self.get_sector_performance()
            
            # Get FII/DII data
            institutional_data = self.get_institutional_data()

            analysis = f"""
🔍 *Post Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

📈 *Market Movement Summary:*
• Closing: {market_data['close']:.2f} ({market_data['change_percent']:.2f}%)
• Volume: {market_data['volume']:,.0f} ({market_data.get('volume_trend', 'N/A')})
• Range: {market_data['low']:.2f} - {market_data['high']:.2f}

💫 *Key Movement Factors:*
{self.analyze_market_movement_factors()}

📊 *Sector Performance:*
{self.format_sector_performance(sector_performance)}

💰 *Institutional Activity:*
• FII: {institutional_data.get('fii', 'N/A')}
• DII: {institutional_data.get('dii', 'N/A')}

📈 *Market Breadth:*
• Advance/Decline: {market_data.get('advance_decline', 'N/A')}
• New Highs/Lows: {market_data.get('new_highs_lows', 'N/A')}

🔮 *Tomorrow's Outlook:*
{self.generate_next_day_outlook()}

#PostMarket #MarketAnalysis"""
            return analysis
        except Exception as e:
            print(f"Error generating post-market analysis: {str(e)}")
            return None

    def send_pre_market_analysis(self):
        """Send pre-market analysis to Telegram"""
        try:
            analysis = self.generate_pre_market_analysis()
            if analysis:
                self.bot.send_message(CHAT_ID, analysis, parse_mode='Markdown')
                print("Pre-market analysis sent successfully!")
            else:
                print("Failed to generate pre-market analysis")
        except Exception as e:
            print(f"Error sending pre-market analysis: {str(e)}")

    def send_post_market_analysis(self):
        """Send post-market analysis to Telegram"""
        try:
            analysis = self.generate_post_market_analysis()
            if analysis:
                self.bot.send_message(CHAT_ID, analysis, parse_mode='Markdown')
                print("Post-market analysis sent successfully!")
            else:
                print("Failed to generate post-market analysis")
        except Exception as e:
            print(f"Error sending post-market analysis: {str(e)}")

if __name__ == "__main__":
    analyzer = AutomatedAnalysis()
    # First time setup: Get request token through Kite Connect login
    # analyzer.authenticate(request_token="your_request_token")
    
    analyzer.schedule_analysis()