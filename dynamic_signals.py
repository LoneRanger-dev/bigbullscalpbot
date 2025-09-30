import telebot
import time as time_module
from datetime import datetime
import pytz
import numpy as np
from typing import Dict, List, Tuple

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

class DynamicSignalGenerator:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.ist = pytz.timezone('Asia/Kolkata')
        self.last_signal_time = None
        self.min_signal_gap = 300  # Minimum 5 minutes between signals
        
    def calculate_technical_indicators(self, candles: List[Dict]) -> Dict:
        """Calculate all technical indicators"""
        try:
            close_prices = np.array([candle['close'] for candle in candles])
            high_prices = np.array([candle['high'] for candle in candles])
            low_prices = np.array([candle['low'] for candle in candles])
            volume = np.array([candle['volume'] for candle in candles])
            
            # RSI
            delta = np.diff(close_prices)
            gain = (delta * 0).copy()
            loss = (delta * 0).copy()
            gain[delta > 0] = delta[delta > 0]
            loss[delta < 0] = -delta[delta < 0]
            avg_gain = np.mean(gain[-14:])
            avg_loss = np.mean(loss[-14:])
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            # Moving Averages
            sma20 = np.mean(close_prices[-20:])
            sma50 = np.mean(close_prices[-50:])
            ema9 = np.mean(close_prices[-9:])  # Simplified EMA
            
            # MACD
            ema12 = np.mean(close_prices[-12:])
            ema26 = np.mean(close_prices[-26:])
            macd = ema12 - ema26
            signal = np.mean(close_prices[-9:])
            macd_hist = macd - signal
            
            # Volume Analysis
            vol_sma20 = np.mean(volume[-20:])
            vol_ratio = volume[-1] / vol_sma20
            
            # Bollinger Bands
            bb_std = np.std(close_prices[-20:])
            bb_middle = sma20
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            
            # ADX (Simplified)
            tr = np.maximum(high_prices[-14:] - low_prices[-14:],
                          np.maximum(abs(high_prices[-14:] - close_prices[-15:-1]),
                                   abs(low_prices[-14:] - close_prices[-15:-1])))
            atr = np.mean(tr)
            
            # Support and Resistance
            recent_highs = sorted(high_prices[-5:], reverse=True)
            recent_lows = sorted(low_prices[-5:])
            
            return {
                'close': close_prices[-1],
                'rsi': rsi,
                'sma20': sma20,
                'sma50': sma50,
                'ema9': ema9,
                'macd': macd,
                'macd_hist': macd_hist,
                'signal': signal,
                'vol_ratio': vol_ratio,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'atr': atr,
                'support_levels': recent_lows[:2],
                'resistance_levels': recent_highs[:2]
            }
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
            return None

    def check_option_buying_setup(self, indicators: Dict) -> Tuple[bool, str, Dict]:
        """Check for CE/PE buying opportunities"""
        try:
            current_price = indicators['close']
            
            # CE Buying Setup
            ce_conditions = [
                indicators['rsi'] > 50,  # Bullish momentum
                indicators['macd'] > indicators['signal'],  # MACD crossover
                current_price > indicators['sma20'],  # Above 20 SMA
                indicators['vol_ratio'] > 1.2,  # Above average volume
                current_price > indicators['bb_middle']  # Above BB middle
            ]
            
            # PE Buying Setup
            pe_conditions = [
                indicators['rsi'] < 50,  # Bearish momentum
                indicators['macd'] < indicators['signal'],  # MACD crossover
                current_price < indicators['sma20'],  # Below 20 SMA
                indicators['vol_ratio'] > 1.2,  # Above average volume
                current_price < indicators['bb_middle']  # Below BB middle
            ]
            
            ce_strength = sum(ce_conditions)
            pe_strength = sum(pe_conditions)
            
            # Strong CE Setup
            if ce_strength >= 4:
                entry = current_price
                target1 = entry + (indicators['atr'] * 1.5)
                target2 = entry + (indicators['atr'] * 2.5)
                stop_loss = entry - (indicators['atr'] * 0.8)
                
                return True, "CE", {
                    'entry': entry,
                    'target1': target1,
                    'target2': target2,
                    'stop_loss': stop_loss,
                    'strength': ce_strength,
                    'setup_type': 'Strong Bullish'
                }
                
            # Strong PE Setup
            elif pe_strength >= 4:
                entry = current_price
                target1 = entry - (indicators['atr'] * 1.5)
                target2 = entry - (indicators['atr'] * 2.5)
                stop_loss = entry + (indicators['atr'] * 0.8)
                
                return True, "PE", {
                    'entry': entry,
                    'target1': target1,
                    'target2': target2,
                    'stop_loss': stop_loss,
                    'strength': pe_strength,
                    'setup_type': 'Strong Bearish'
                }
                
            # Potential Setup Building
            elif ce_strength == 3 or pe_strength == 3:
                levels = {
                    'next_resistance': indicators['resistance_levels'][0],
                    'next_support': indicators['support_levels'][0],
                    'strong_resistance': indicators['resistance_levels'][1],
                    'strong_support': indicators['support_levels'][1],
                    'ce_strength': ce_strength,
                    'pe_strength': pe_strength
                }
                return False, "BUILDING", levels
                
            return False, "NO_SETUP", {}
            
        except Exception as e:
            print(f"Error checking setup: {str(e)}")
            return False, "ERROR", {}

    def send_signal(self, signal_type: str, data: Dict):
        """Send trading signal to Telegram"""
        try:
            current_time = datetime.now(self.ist)
            
            # Check if enough time has passed since last signal
            if self.last_signal_time and \
               (current_time - self.last_signal_time).total_seconds() < self.min_signal_gap:
                return
            
            if signal_type == "CE":
                message = f"""
🚨 *STRONG BUY SIGNAL (CE)* - {current_time.strftime('%H:%M')}

📈 *Setup Type:* {data['setup_type']}
• Confidence: {data['strength']}/5 stars
• Pattern: Bullish Momentum + Volume Confirmation

🎯 *Trading Levels:*
• Entry Zone: {data['entry']:.2f}-{data['entry']+5:.2f}
• Target 1: {data['target1']:.2f} ({data['target1']-data['entry']:.1f} points)
• Target 2: {data['target2']:.2f} ({data['target2']-data['entry']:.1f} points)
• Stop Loss: {data['stop_loss']:.2f} ({data['entry']-data['stop_loss']:.1f} points)

⚡ *Quick Facts:*
• Risk:Reward = 1:{((data['target1']-data['entry'])/(data['entry']-data['stop_loss'])):.1f}
• Momentum: Strong Bullish
• Volume: Above Average

#BuySignal #OptionTrading #CE"""

            elif signal_type == "PE":
                message = f"""
🚨 *STRONG SELL SIGNAL (PE)* - {current_time.strftime('%H:%M')}

📉 *Setup Type:* {data['setup_type']}
• Confidence: {data['strength']}/5 stars
• Pattern: Bearish Momentum + Volume Confirmation

🎯 *Trading Levels:*
• Entry Zone: {data['entry']:.2f}-{data['entry']-5:.2f}
• Target 1: {data['target1']:.2f} ({data['entry']-data['target1']:.1f} points)
• Target 2: {data['target2']:.2f} ({data['entry']-data['target2']:.1f} points)
• Stop Loss: {data['stop_loss']:.2f} ({data['stop_loss']-data['entry']:.1f} points)

⚡ *Quick Facts:*
• Risk:Reward = 1:{((data['entry']-data['target1'])/(data['stop_loss']-data['entry'])):.1f}
• Momentum: Strong Bearish
• Volume: Above Average

#SellSignal #OptionTrading #PE"""

            elif signal_type == "BUILDING":
                message = f"""
👀 *Potential Setup Building* - {current_time.strftime('%H:%M')}

📊 *Market Structure:*
• Next Resistance: {data['next_resistance']:.2f}
• Strong Resistance: {data['strong_resistance']:.2f}
• Next Support: {data['next_support']:.2f}
• Strong Support: {data['strong_support']:.2f}

💡 *Possible Setups:*
• CE Strength: {data['ce_strength']}/5
• PE Strength: {data['pe_strength']}/5

⏳ *Wait for:*
• Break above {data['next_resistance']:.2f} for CE
• Break below {data['next_support']:.2f} for PE
• Volume confirmation
• Momentum alignment

#TradingSetup #WatchList"""

            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            self.last_signal_time = current_time
            print(f"Signal sent at {current_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error sending signal: {str(e)}")

    def monitor_market(self):
        """Continuously monitor market for setups"""
        print("Starting market monitor...")
        print("Will send signals when strong setups form.")
        print("Looking for:")
        print("1. Strong CE/PE setups (4-5 conditions met)")
        print("2. Building setups (3 conditions met)")
        print("3. Key level breaks with momentum")
        
        while True:
            try:
                current_time = datetime.now(self.ist)
                
                # Check if market is open (9:15 AM to 3:30 PM IST on weekdays)
                if current_time.weekday() < 5 and \
                   ((current_time.hour == 9 and current_time.minute >= 15) or \
                    (current_time.hour > 9 and current_time.hour < 15) or \
                    (current_time.hour == 15 and current_time.minute <= 30)):
                    
                    # Get market data using MCP Kite tools
                    quotes = mcp_kite_get_quotes(["NSE:NIFTY 50"])
                    nifty_data = quotes["NSE:NIFTY 50"]
                    
                    # Get historical data for calculations
                    hist_data = mcp_kite_get_historical_data(
                        instrument_token=256265,  # Nifty 50
                        interval="minute",
                        from_date=(current_time - timedelta(days=1)).strftime('%Y-%m-%d'),
                        to_date=current_time.strftime('%Y-%m-%d')
                    )
                    
                    # Calculate indicators
                    indicators = self.calculate_technical_indicators(hist_data)
                    
                    if indicators:
                        # Check for setups
                        has_setup, setup_type, setup_data = self.check_option_buying_setup(indicators)
                        
                        if has_setup or setup_type == "BUILDING":
                            self.send_signal(setup_type, setup_data)
                
                # Sleep for 1 minute before next check
                time_module.sleep(60)
                
            except KeyboardInterrupt:
                print("\nStopping market monitor...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                time_module.sleep(60)

if __name__ == "__main__":
    monitor = DynamicSignalGenerator()
    monitor.monitor_market()