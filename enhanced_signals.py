#!/usr/bin/env python3
"""
Enhanced Signal Generation for BigBullScalpBot
Add more sophisticated analysis and custom triggers
"""

import os
import requests
import json
from datetime import datetime, time
import pytz

class EnhancedSignalGenerator:
    def __init__(self):
        self.kite_api_key = os.getenv('KITE_API_KEY')
        self.kite_access_token = os.getenv('KITE_ACCESS_TOKEN')
        self.ist = pytz.timezone('Asia/Kolkata')
        
    def is_market_open(self):
        """Check if market is currently open"""
        now = datetime.now(self.ist)
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Check if it's a weekday and within market hours
        if now.weekday() < 5 and market_open <= current_time <= market_close:
            return True
        return False
    
    def get_advanced_signals(self):
        """Generate more sophisticated signals"""
        if not self.is_market_open():
            return []
        
        symbols = [
            'NSE:NIFTY50',
            'NSE:BANKNIFTY', 
            'NSE:RELIANCE',
            'NSE:TCS',
            'NSE:INFY',
            'NSE:HDFCBANK',
            'NSE:ICICIBANK',
            'NSE:SBIN',
            'NSE:ITC',
            'NSE:HINDUNILVR'
        ]
        
        signals = []
        
        for symbol in symbols:
            try:
                # Get live market data
                data = self.fetch_market_data(symbol)
                if data:
                    signal = self.analyze_advanced_signal(symbol, data)
                    if signal:
                        signals.append(signal)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        return signals
    
    def fetch_market_data(self, symbol):
        """Fetch real-time market data"""
        # This would integrate with your Kite Connect API
        # Placeholder for actual implementation
        return {
            'last_price': 100.0,
            'change': 2.5,
            'volume': 150000,
            'high': 102.0,
            'low': 98.0,
            'open': 99.0
        }
    
    def analyze_advanced_signal(self, symbol, data):
        """Advanced signal analysis"""
        ltp = data.get('last_price', 0)
        change_percent = (data.get('change', 0) / ltp) * 100
        volume = data.get('volume', 0)
        high = data.get('high', ltp)
        low = data.get('low', ltp)
        
        # Advanced signal logic
        if change_percent > 1.5 and volume > 200000:
            # Strong bullish signal
            return {
                'symbol': symbol,
                'type': 'BUY',
                'strength': 'STRONG',
                'entry': ltp,
                'target1': ltp * 1.02,
                'target2': ltp * 1.04, 
                'stop_loss': ltp * 0.98,
                'reason': f'Strong bullish momentum: +{change_percent:.1f}% with high volume',
                'confidence': 85
            }
        elif change_percent > 0.8 and volume > 100000:
            # Moderate bullish signal
            return {
                'symbol': symbol,
                'type': 'BUY',
                'strength': 'MODERATE',
                'entry': ltp,
                'target1': ltp * 1.015,
                'target2': ltp * 1.025,
                'stop_loss': ltp * 0.985,
                'reason': f'Moderate bullish trend: +{change_percent:.1f}%',
                'confidence': 70
            }
        elif change_percent < -1.5 and volume > 200000:
            # Strong bearish signal
            return {
                'symbol': symbol,
                'type': 'SELL',
                'strength': 'STRONG',
                'entry': ltp,
                'target1': ltp * 0.98,
                'target2': ltp * 0.96,
                'stop_loss': ltp * 1.02,
                'reason': f'Strong bearish momentum: {change_percent:.1f}% with high volume',
                'confidence': 85
            }
        
        return None

# Enhanced signal formatting for Telegram
def format_enhanced_signal(signal):
    """Format signal for Telegram broadcast"""
    strength_emoji = {
        'STRONG': '🔥',
        'MODERATE': '⚡',
        'WEAK': '💡'
    }
    
    type_emoji = {
        'BUY': '🟢',
        'SELL': '🔴'
    }
    
    message = f"""
{strength_emoji.get(signal['strength'], '📊')} **{signal['type']} SIGNAL** {type_emoji.get(signal['type'], '📈')}

📈 **Symbol**: {signal['symbol']}
💰 **Entry**: ₹{signal['entry']:.2f}
🎯 **Target 1**: ₹{signal['target1']:.2f}
🎯 **Target 2**: ₹{signal['target2']:.2f}
🛑 **Stop Loss**: ₹{signal['stop_loss']:.2f}

📊 **Confidence**: {signal['confidence']}%
💡 **Reason**: {signal['reason']}

⏰ Time: {datetime.now().strftime('%H:%M:%S')}

⚠️ **Risk Management**: Trade with proper position sizing
    """
    
    return message

if __name__ == "__main__":
    generator = EnhancedSignalGenerator()
    signals = generator.get_advanced_signals()
    
    for signal in signals:
        print(format_enhanced_signal(signal))
        print("-" * 50)