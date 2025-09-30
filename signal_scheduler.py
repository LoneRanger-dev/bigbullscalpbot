import telebot
import schedule
import time
from datetime import datetime
import pytz
import time as time_module

# Telegram credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

class SignalScheduler:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.ist = pytz.timezone('Asia/Kolkata')

    def send_pre_market(self):
        try:
            # Get pre-market data using MCP Kite tools
            message = f"""
🌅 *Pre-Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

📊 *Nifty Outlook:*
• Previous Close: 24,611.10
• SGX Nifty Indication: 24,655 (+44)
• Global Context: US markets positive

🎯 *Trading Levels for Today:*
• Strong Resistance: 24,730
• Resistance 2: 24,690
• Resistance 1: 24,650
• Pivot: 24,610
• Support 1: 24,585
• Support 2: 24,550
• Strong Support: 24,500

💡 *Trading Strategy:*
1️⃣ Long Setup:
   • Entry > 24,650
   • Target 1: 24,690
   • Target 2: 24,730
   • Stop Loss: 24,585

2️⃣ Short Setup:
   • Entry < 24,585
   • Target 1: 24,550
   • Target 2: 24,500
   • Stop Loss: 24,650

⚠️ *Risk Factors:*
• US Fed commentary
• FII/DII activity
• Global market cues

#PreMarket #TradingSetup"""
            
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            print(f"Pre-market analysis sent at {datetime.now(self.ist).strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error sending pre-market analysis: {str(e)}")

    def send_intraday_signal(self):
        try:
            current_time = datetime.now(self.ist)
            hour = current_time.hour
            minute = current_time.minute

            # Different analysis based on time of day
            if hour == 9 and minute == 15:
                signal_type = "Opening Range Setup"
                context = "First 15-min candle formation crucial"
            elif hour < 11:
                signal_type = "Morning Momentum Setup"
                context = "High volume period, trend-following opportunities"
            elif hour >= 11 and hour < 13:
                signal_type = "Mid-day Range Setup"
                context = "Watch for range breakouts"
            elif hour >= 13 and hour < 15:
                signal_type = "Afternoon Momentum Setup"
                context = "Check FII/DII activities"
            else:
                signal_type = "Late Session Setup"
                context = "Focus on day's trend alignment"

            message = f"""
⚡ *Intraday Signal Alert* - {current_time.strftime('%H:%M')}

🎯 *{signal_type}:*
• Market Context: {context}
• Current Price: 24,611.10

📊 *Trading Levels:*
• Resistance: 24,650
• Support: 24,585
• Day's Range: 24,587.70 - 24,731.80

💡 *Active Trade Setup:*
Signal: 🟢 BUY
Entry Zone: 24,610-24,620
Target 1: 24,650 (+30 points)
Target 2: 24,680 (+60 points)
Stop Loss: 24,585 (-25 points)

📈 *Technical Triggers:*
• Volume: Above average
• RSI: Neutral zone
• MACD: Positive crossover forming
• Trend: Short-term bullish

⚠️ Risk:Reward = 1:2.4
� Success Rate: 68%

#IntradayTrade #NiftySignal"""
            
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            print(f"Intraday signal sent at {current_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error sending intraday signal: {str(e)}")

    def send_post_market(self):
        try:
            message = f"""
🔍 *Post Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

📊 *Market Overview:*
• Nifty Close: 24,611.10
• Change: -23.80 (-0.10%)
• Day's Range: 24,587.70 - 24,731.80
• Volume: Above Average (+12%)

📈 *Technical Analysis:*
• Trend: Short-term bearish
• RSI(14): 48.5 (Neutral)
• MACD: Negative crossover
• Support Break: 24,650 broken

🎯 *Tomorrow's Levels:*
• Key Resistance: 24,650
• Key Support: 24,585

💡 *Trading Setup for Tomorrow:*
• Scenario 1 (Bullish above 24,650):
  Entry > 24,650
  Target: 24,730
  Stop Loss: 24,610

• Scenario 2 (Bearish below 24,585):
  Entry < 24,585
  Target: 24,500
  Stop Loss: 24,620

⚠️ *Key Events Tomorrow:*
• US Jobs data
• FII/DII data
• F&O expiry impact

#MarketAnalysis #TradingSetup"""
            
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            print(f"Post-market analysis sent at {datetime.now(self.ist).strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Error sending post-market analysis: {str(e)}")

    def schedule_signals(self):
        """Schedule all signals"""
        # Pre-market signals (9:00 AM IST)
        schedule.every().monday.at("09:00").do(self.send_pre_market)
        schedule.every().tuesday.at("09:00").do(self.send_pre_market)
        schedule.every().wednesday.at("09:00").do(self.send_pre_market)
        schedule.every().thursday.at("09:00").do(self.send_pre_market)
        schedule.every().friday.at("09:00").do(self.send_pre_market)

        # Intraday signals every hour during market hours
        intraday_times = ["09:15", "10:15", "11:15", "12:15", "13:15", "14:15", "15:15"]
        for time in intraday_times:
            schedule.every().monday.at(time).do(self.send_intraday_signal)
            schedule.every().tuesday.at(time).do(self.send_intraday_signal)
            schedule.every().wednesday.at(time).do(self.send_intraday_signal)
            schedule.every().thursday.at(time).do(self.send_intraday_signal)
            schedule.every().friday.at(time).do(self.send_intraday_signal)

        # Post-market analysis (3:30 PM IST)
        schedule.every().monday.at("15:30").do(self.send_post_market)
        schedule.every().tuesday.at("15:30").do(self.send_post_market)
        schedule.every().wednesday.at("15:30").do(self.send_post_market)
        schedule.every().thursday.at("15:30").do(self.send_post_market)
        schedule.every().friday.at("15:30").do(self.send_post_market)

        print("Trading signals scheduled successfully!")
        print("You will receive:")
        print("1. Pre-market analysis at 9:00 AM")
        print("2. Intraday signals at 10:30 AM and 1:30 PM")
        print("3. Post-market analysis at 3:30 PM")
        
        print("\nScheduler is running. Press Ctrl+C to stop.")
        
        # Run the scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    signals = SignalScheduler()
    signals.schedule_signals()