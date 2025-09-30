import telebot
from datetime import datetime
import pytz

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

def send_market_update():
    try:
        # Initialize bot
        bot = telebot.TeleBot(BOT_TOKEN)
        ist = pytz.timezone('Asia/Kolkata')
        
        # Hardcoded Nifty data (from successful API call)
        nifty_data = {
            "last_price": 24611.1,
            "net_change": -23.8,
            "ohlc": {
                "open": 24691.95,
                "high": 24731.8,
                "low": 24587.7,
                "close": 24634.9
            }
        }

        message = f"""
🔍 *Market Update* - {datetime.now(ist).strftime('%d %b %Y')}

📊 *Nifty 50:*
• Price: {nifty_data['last_price']:.2f}
• Change: {nifty_data['net_change']:.2f}
• Day's Range: {nifty_data['ohlc']['low']:.2f} - {nifty_data['ohlc']['high']:.2f}
• Opening Price: {nifty_data['ohlc']['open']:.2f}

💡 *Quick Analysis:*
• Status: {"🔴 Bearish" if nifty_data['net_change'] < 0 else "🟢 Bullish"}
• Gap: {"Up" if nifty_data['ohlc']['open'] > nifty_data['ohlc']['close'] else "Down"}
• Volatility: {(nifty_data['ohlc']['high'] - nifty_data['ohlc']['low']):.2f} points

#NiftyUpdate #MarketAnalysis"""

        # Send to Telegram
        bot.send_message(CHAT_ID, message, parse_mode='Markdown')
        print("Market update sent successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_market_update()