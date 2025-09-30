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
        
        # Get Nifty data
        from mcp_kite_get_quotes import mcp_kite_get_quotes
        quotes = mcp_kite_get_quotes({
            "instruments": ["NSE:NIFTY 50"]
        })
        nifty_data = quotes["NSE:NIFTY 50"]

        message = f"""
🔍 *Market Update* - {datetime.now(ist).strftime('%d %b %Y')}

📊 *Nifty 50:*
• Price: {nifty_data['last_price']:.2f}
• Change: {nifty_data['net_change']:.2f}
• Day's Range: {nifty_data['ohlc']['low']:.2f} - {nifty_data['ohlc']['high']:.2f}

#MarketUpdate"""

        # Send to Telegram
        bot.send_message(CHAT_ID, message, parse_mode='Markdown')
        print("Market update sent successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_market_update()