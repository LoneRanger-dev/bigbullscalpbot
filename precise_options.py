import telebot
import time as time_module
from datetime import datetime, timedelta
import pytz
import numpy as np
from typing import Dict, List, Tuple
import math

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

class PreciseOptionSignals:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.ist = pytz.timezone('Asia/Kolkata')
        self.last_signal_time = None
        self.min_signal_gap = 300  # 5 minutes minimum between signals
        
    def get_nearest_strikes(self, current_price: float) -> Tuple[List[float], List[float]]:
        """Calculate nearest optimal strike prices"""
        base_strike = round(current_price / 50) * 50  # Round to nearest 50
        
        ce_strikes = [
            base_strike,
            base_strike + 50,
            base_strike + 100
        ]
        
        pe_strikes = [
            base_strike,
            base_strike - 50,
            base_strike - 100
        ]
        
        return ce_strikes, pe_strikes

    def calculate_option_greeks(self, spot: float, strike: float, time_to_expiry: float,
                              volatility: float, is_call: bool) -> Dict:
        """Calculate basic option Greeks for better strike selection"""
        try:
            # Basic Black-Scholes calculations
            time_sqrt = np.sqrt(time_to_expiry)
            d1 = (np.log(spot/strike) + (0.1 + volatility**2/2)*time_to_expiry) / (volatility*time_sqrt)
            
            # Delta calculation (probability of profit)
            if is_call:
                delta = np.exp(-0.1*time_to_expiry) * norm_cdf(d1)
            else:
                delta = -np.exp(-0.1*time_to_expiry) * norm_cdf(-d1)
            
            return {
                'delta': abs(delta),
                'probability': abs(delta) * 100  # Convert to percentage
            }
        except:
            return {'delta': 0.5, 'probability': 50}

    def analyze_price_action(self, candles: List[Dict]) -> Dict:
        """Detailed price action analysis for precise entries"""
        try:
            close_prices = np.array([c['close'] for c in candles])
            high_prices = np.array([c['high'] for c in candles])
            low_prices = np.array([c['low'] for c in candles])
            volume = np.array([c['volume'] for c in candles])
            
            # Recent momentum
            last_5_candles = close_prices[-5:]
            momentum = (last_5_candles[-1] - last_5_candles[0]) / last_5_candles[0] * 100
            
            # Volume analysis
            recent_vol_avg = np.mean(volume[-5:])
            vol_surge = volume[-1] / recent_vol_avg
            
            # Volatility
            recent_ranges = high_prices[-5:] - low_prices[-5:]
            avg_range = np.mean(recent_ranges)
            current_range = high_prices[-1] - low_prices[-1]
            
            # Price levels
            key_price = close_prices[-1]
            recent_high = np.max(high_prices[-5:])
            recent_low = np.min(low_prices[-5:])
            
            return {
                'current_price': key_price,
                'momentum': momentum,
                'vol_surge': vol_surge,
                'volatility': current_range/avg_range,
                'recent_high': recent_high,
                'recent_low': recent_low
            }
        except Exception as e:
            print(f"Error in price analysis: {str(e)}")
            return None

    def get_optimal_strike(self, analysis: Dict, direction: str) -> Dict:
        """Select the most optimal strike price based on conditions"""
        try:
            current_price = analysis['current_price']
            momentum = analysis['momentum']
            volatility = analysis['volatility']
            
            ce_strikes, pe_strikes = self.get_nearest_strikes(current_price)
            time_to_expiry = self.get_time_to_expiry()  # Days to expiry in years
            
            if direction == "CE":
                strikes = ce_strikes
                # For CE, prefer strikes closer to spot in high momentum
                if momentum > 0.5:  # Strong upward momentum
                    preferred_index = 0  # ATM
                elif momentum > 0.2:  # Moderate momentum
                    preferred_index = 1  # OTM
                else:  # Weak momentum
                    preferred_index = 2  # Far OTM
                    
            else:  # PE
                strikes = pe_strikes
                # For PE, prefer strikes closer to spot in high momentum
                if momentum < -0.5:  # Strong downward momentum
                    preferred_index = 0  # ATM
                elif momentum < -0.2:  # Moderate momentum
                    preferred_index = 1  # OTM
                else:  # Weak momentum
                    preferred_index = 2  # Far OTM
            
            selected_strike = strikes[preferred_index]
            
            # Calculate probability of profit
            greeks = self.calculate_option_greeks(
                current_price, selected_strike, time_to_expiry,
                volatility * 0.2, direction == "CE"
            )
            
            return {
                'strike': selected_strike,
                'probability': greeks['probability'],
                'momentum_score': abs(momentum),
                'type': 'ATM' if preferred_index == 0 else ('OTM' if preferred_index == 1 else 'Far OTM')
            }
            
        except Exception as e:
            print(f"Error selecting strike: {str(e)}")
            return None

    def calculate_risk_levels(self, analysis: Dict, strike_info: Dict, direction: str) -> Dict:
        """Calculate precise entry, target, and stop-loss levels"""
        try:
            current_price = analysis['current_price']
            volatility = analysis['volatility']
            momentum = analysis['momentum']
            
            # ATR-based level calculation
            atr = (analysis['recent_high'] - analysis['recent_low']) / 5
            
            if direction == "CE":
                entry_price = current_price + (atr * 0.2)  # Slight buffer for confirmation
                stop_loss = max(current_price - (atr * 1.5), analysis['recent_low'])
                target1 = entry_price + (atr * 2)
                target2 = entry_price + (atr * 3)
                
                # Adjust based on momentum
                if momentum > 0.5:
                    target1 += atr * 0.5
                    target2 += atr * 1
                
            else:  # PE
                entry_price = current_price - (atr * 0.2)
                stop_loss = min(current_price + (atr * 1.5), analysis['recent_high'])
                target1 = entry_price - (atr * 2)
                target2 = entry_price - (atr * 3)
                
                # Adjust based on momentum
                if momentum < -0.5:
                    target1 -= atr * 0.5
                    target2 -= atr * 1
            
            # Calculate risk-reward ratios
            risk = abs(entry_price - stop_loss)
            reward1 = abs(target1 - entry_price)
            reward2 = abs(target2 - entry_price)
            
            return {
                'entry': entry_price,
                'stop_loss': stop_loss,
                'target1': target1,
                'target2': target2,
                'risk_reward1': round(reward1/risk, 2),
                'risk_reward2': round(reward2/risk, 2),
                'atr': atr
            }
            
        except Exception as e:
            print(f"Error calculating risk levels: {str(e)}")
            return None

    def get_market_sentiment(self) -> Dict:
        """Analyze broader market sentiment"""
        try:
            # Get PCR ratio and market breadth data from Kite
            quotes = mcp_kite_get_quotes(["NSE:NIFTY 50", "NSE:NIFTYIT", "NSE:BANKNIFTY"])
            
            # Analyze sector performance
            banknifty = quotes["NSE:BANKNIFTY"]
            it_index = quotes["NSE:NIFTYIT"]
            
            sentiment = "Bullish" if banknifty['net_change'] > 0 and it_index['net_change'] > 0 else \
                       "Bearish" if banknifty['net_change'] < 0 and it_index['net_change'] < 0 else \
                       "Mixed"
                       
            return {
                'sentiment': sentiment,
                'bank_change': banknifty['net_change'],
                'it_change': it_index['net_change']
            }
            
        except Exception as e:
            print(f"Error getting sentiment: {str(e)}")
            return None

    def send_precise_signal(self, direction: str, strike_info: Dict, risk_levels: Dict, 
                          analysis: Dict, sentiment: Dict):
        """Send detailed option trading signal"""
        try:
            current_time = datetime.now(self.ist)
            
            # Check signal gap
            if self.last_signal_time and \
               (current_time - self.last_signal_time).total_seconds() < self.min_signal_gap:
                return
                
            # Format the signal message
            signal_type = "CE BUYING" if direction == "CE" else "PE BUYING"
            trend = "BULLISH" if direction == "CE" else "BEARISH"
            
            message = f"""
🎯 *PRECISE {signal_type} OPPORTUNITY*
Time: {current_time.strftime('%H:%M')}

📊 *Option Strike Details:*
• Strike Price: {strike_info['strike']}
• Strike Type: {strike_info['type']}
• Success Probability: {strike_info['probability']:.1f}%
• Momentum Score: {strike_info['momentum_score']:.1f}

⚡ *Entry Parameters:*
• Spot Entry Zone: {risk_levels['entry']:.2f}
• Current Market: {analysis['current_price']:.2f}
• Volatility Factor: {analysis['volatility']:.2f}x

🎯 *Trade Levels:*
• Entry Price: {risk_levels['entry']:.2f}
• Target 1: {risk_levels['target1']:.2f} (R:R = 1:{risk_levels['risk_reward1']})
• Target 2: {risk_levels['target2']:.2f} (R:R = 1:{risk_levels['risk_reward2']})
• Stop Loss: {risk_levels['stop_loss']:.2f}

📈 *Market Context:*
• Trend: {trend}
• Volume Surge: {analysis['vol_surge']:.1f}x
• BankNifty: {sentiment['bank_change']:.2f}
• IT Index: {sentiment['it_change']:.2f}
• Overall: {sentiment['sentiment']}

⚠️ *Risk Management:*
• Position Size: 1-2% of capital
• Use strict stop-loss
• Trail profits after Target 1

#OptionTrading #{direction} #PreciseEntry"""
            
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            self.last_signal_time = current_time
            print(f"Precise signal sent at {current_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error sending signal: {str(e)}")

    def monitor_options(self):
        """Monitor market for precise option trading setups"""
        print("Starting precise options monitor...")
        print("Looking for high-probability setups with:")
        print("1. Clear trend alignment")
        print("2. Optimal strike selection")
        print("3. Risk-reward > 1:2")
        print("4. Volume confirmation")
        
        while True:
            try:
                current_time = datetime.now(self.ist)
                
                # Check market hours
                if current_time.weekday() < 5 and \
                   ((current_time.hour == 9 and current_time.minute >= 15) or \
                    (current_time.hour > 9 and current_time.hour < 15) or \
                    (current_time.hour == 15 and current_time.minute <= 30)):
                    
                    # Get market data
                    quotes = mcp_kite_get_quotes(["NSE:NIFTY 50"])
                    nifty_data = quotes["NSE:NIFTY 50"]
                    
                    # Get recent candles
                    hist_data = mcp_kite_get_historical_data(
                        instrument_token=256265,
                        interval="minute",
                        from_date=(current_time - timedelta(days=1)).strftime('%Y-%m-%d'),
                        to_date=current_time.strftime('%Y-%m-%d')
                    )
                    
                    # Analyze price action
                    analysis = self.analyze_price_action(hist_data)
                    if not analysis:
                        continue
                        
                    # Get market sentiment
                    sentiment = self.get_market_sentiment()
                    if not sentiment:
                        continue
                    
                    # Check for CE setup
                    if analysis['momentum'] > 0.2 and analysis['vol_surge'] > 1.2:
                        strike_info = self.get_optimal_strike(analysis, "CE")
                        if strike_info and strike_info['probability'] > 60:
                            risk_levels = self.calculate_risk_levels(analysis, strike_info, "CE")
                            if risk_levels and risk_levels['risk_reward1'] >= 2:
                                self.send_precise_signal("CE", strike_info, risk_levels, 
                                                       analysis, sentiment)
                    
                    # Check for PE setup
                    elif analysis['momentum'] < -0.2 and analysis['vol_surge'] > 1.2:
                        strike_info = self.get_optimal_strike(analysis, "PE")
                        if strike_info and strike_info['probability'] > 60:
                            risk_levels = self.calculate_risk_levels(analysis, strike_info, "PE")
                            if risk_levels and risk_levels['risk_reward1'] >= 2:
                                self.send_precise_signal("PE", strike_info, risk_levels, 
                                                       analysis, sentiment)
                
                # Sleep for 30 seconds before next check
                time_module.sleep(30)
                
            except KeyboardInterrupt:
                print("\nStopping options monitor...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                time_module.sleep(30)

if __name__ == "__main__":
    monitor = PreciseOptionSignals()
    monitor.monitor_options()