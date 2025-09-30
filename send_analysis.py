import telebot
import time

# Telegram Credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

def send_market_analysis():
    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        
        analysis = """
🔍 *Post Market Analysis* - 30 Sep 2025

📊 *Market Overview:*
• Nifty Close: 24,611.10
• Change: -23.80 (-0.10%)
• Day's Range: 24,587.70 - 24,731.80
• Opening Gap: Up (24,691.95 vs 24,634.90)

📈 *Day's Price Action:*
1. Morning Session:
   - Gap-up opening at 24,691.95
   - Initial profit booking
   - Support at 24,618.95

2. Mid-Session:
   - Recovery towards 24,680
   - Range-bound trading
   - Moderate volumes

3. Closing Hour:
   - Selling pressure emerged
   - Day's low: 24,587.70
   - Minor recovery at close

🎯 *Key Levels for Tomorrow:*
• Resistance:
  R1: 24,731.80 (Today's High)
  R2: 24,690.00
  R3: 24,750.00

• Support:
  S1: 24,587.70 (Today's Low)
  S2: 24,550.00
  S3: 24,500.00

💡 *Trading Strategy:*
1. Buy Setup:
   Entry > 24,635
   Target: 24,690 → 24,730
   Stop Loss: 24,585

2. Sell Setup:
   Entry < 24,585
   Target: 24,550 → 24,500
   Stop Loss: 24,635

⚠️ *Risk Factors:*
• Global cues
• F&O expiry effects
• FII/DII activity

#NiftyAnalysis #Trading #MarketStrategy"""

        bot.send_message(CHAT_ID, analysis, parse_mode='Markdown')
        print("Analysis sent successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    send_market_analysis()