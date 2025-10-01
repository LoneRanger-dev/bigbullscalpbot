#!/usr/bin/env python3
"""
HEROKU OPTIMIZED - Webhook version instead of polling
"""

import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
WEBHOOK_URL = "https://bigbullscalptradingbot.herokuapp.com"

# Flask app
app = Flask(__name__)

# Bot setup
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    logger.info(f"Start command from user {update.effective_user.id}")
    
    message = """
🎉 **BOT IS WORKING!** 🎉

✅ Heroku deployment successful
✅ Webhook configured  
✅ Bot responding to commands

🤖 **BigBullScalpBot Status:**
- Version: Webhook v1.0
- Server: Heroku
- Status: Online

**Commands:**
/start - This message
/test - Test signal
/about - About bot

Your trading bot is now LIVE! 🚀
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command"""
    await update.message.reply_text("""
🚨 **TEST SIGNAL** 🚨

📈 Symbol: NSE:NIFTY
🔥 Type: BUY  
💰 Entry: ₹24,850
🎯 Target: ₹25,100
🛑 SL: ₹24,600

✅ Signal system operational!
    """)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command"""
    await update.message.reply_text("""
🤖 **BigBullScalpBot**

🎯 F&O Trading Signals
💰 Monthly: ₹2,400
📱 UPI: 81285083843@YBL

Status: ✅ ONLINE
    """)

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("test", test_command))
application.add_handler(CommandHandler("about", about_command))

@app.route('/')
def home():
    return """
    <h1>BigBullScalpBot is ONLINE! ✅</h1>
    <p>Bot Username: @Bigbulscalp_bot</p>
    <p>Status: Webhook Active</p>
    <p>Commands: /start, /test, /about</p>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook updates"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        
        # Process update asynchronously
        import asyncio
        asyncio.run(application.process_update(update))
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR", 500

@app.route('/health')
def health():
    return "Bot is healthy!", 200

@app.route('/setwebhook')
def set_webhook():
    """Set webhook URL"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        result = bot.set_webhook(url=webhook_url)
        if result:
            return f"Webhook set successfully: {webhook_url}"
        else:
            return "Failed to set webhook"
    except Exception as e:
        return f"Error setting webhook: {e}"

if __name__ == '__main__':
    logger.info("🚀 Starting BigBullScalpBot with webhook...")
    
    # Set webhook on startup
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)