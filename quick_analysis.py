import telebot
from datetime import datetime
import pytz

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

def send_market_analysis():
    try:
        # Initialize bot
        bot = telebot.TeleBot(BOT_TOKEN)
        ist = pytz.timezone('Asia/Kolkata')
        
        # Get market data using MCP Kite tools
        from mcp_kite_get_ltp import get_ltp
        from mcp_kite_get_quotes import get_quotes

        # Get LTP (Last Traded Price)
        ltp_data = get_ltp(["NSE:NIFTY 50"])
        quotes_data = get_quotes(["NSE:NIFTY 50"])
        
        nifty_data = quotes_data["NSE:NIFTY 50"]
        nifty_ltp = ltp_data["NSE:NIFTY 50"]
        
        # Generate analysis
        analysis = f"""
🔍 *Market Analysis* - {datetime.now(ist).strftime('%d %b %Y')}

📊 *Nifty 50 Overview:*
• Current Price: {nifty_data['last_price']:.2f}
• Day's Change: {nifty_data['net_change']:.2f}
• Day's High: {nifty_data['ohlc']['high']:.2f}
• Day's Low: {nifty_data['ohlc']['low']:.2f}
• Opening Price: {nifty_data['ohlc']['open']:.2f}
• Previous Close: {nifty_data['ohlc']['close']:.2f}

💡 *Quick Analysis:*
• Trend: {"Bullish" if nifty_data['net_change'] > 0 else "Bearish"}
• Strength: {"Strong" if abs(nifty_data['net_change']) > 100 else "Moderate"}

#NiftyAnalysis #Trading"""

        # Send to Telegram
        bot.send_message(CHAT_ID, analysis, parse_mode='Markdown')
        print("Analysis sent successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_market_analysis()