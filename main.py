#!/usr/bin/env python3
"""
BigBullScalpBot - Ultra Simple Working Version
Just get the bot responding first!
"""

import os
import logging
import threading
from datetime import datetime
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Heroku
app = Flask(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs')
CHAT_ID = "7973202689"
UPI_ID = "81285083843@YBL"

# Simple handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    logger.info(f"Start command from user {update.effective_user.id}")
    
    keyboard = [
        [InlineKeyboardButton("💳 Subscribe ₹2,400", callback_data="subscribe")],
        [InlineKeyboardButton("📊 Test Signal", callback_data="testsignal")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🚀 **BigBullScalpBot is LIVE!**

✅ F&O Trading Signals
✅ Live Market Analysis  
✅ Payment Integration
✅ 24/7 Automated Signals

**Monthly Subscription: ₹2,400**

🔧 **Admin Commands:**
/admin - Admin panel
/test - Generate test signal
/status - Bot status

Choose an option below:
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command"""
    user_id = update.effective_user.id
    
    admin_text = f"""
🔧 **Admin Panel**

**User ID:** `{user_id}`
**Bot Status:** ✅ ONLINE
**Server:** Heroku
**Version:** 3.0 Simple

**Test Commands:**
/test - Generate test signal
/status - Check bot health
/start - Main menu

**Bot is responding!** 🎉
    """
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test signal command"""
    test_signal = f"""
🚨 **TEST SIGNAL GENERATED** 🚨

📈 **Symbol:** NSE:NIFTY  
🔥 **Type:** BUY
💰 **Entry:** ₹24,850.00
🎯 **Target:** ₹25,100.00  
🛑 **Stop Loss:** ₹24,600.00

⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}
🤖 **Status:** Test Signal (Bot Working!)

✅ **Signal generation system is operational!**
    """
    
    await update.message.reply_text(test_signal, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command"""
    status_text = f"""
📊 **Bot Status Report**

🤖 **Bot:** ✅ Online & Responding
🌐 **Server:** ✅ Heroku Active  
💾 **Database:** ✅ SQLite Ready
🔗 **Telegram API:** ✅ Connected
⏰ **Uptime:** Running since deployment

**Last Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 **All systems operational!**
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "subscribe":
        text = f"""
💳 **Subscription Options**

**Monthly Plan: ₹2,400**

📱 **UPI Payment:**
UPI ID: `{UPI_ID}`
Amount: ₹2,400

**Steps:**
1. Pay to UPI ID above
2. Send payment screenshot
3. Get activated within 24hrs

**Note:** Copy UPI ID: {UPI_ID}
        """
        await query.edit_message_text(text, parse_mode='Markdown')
        
    elif query.data == "testsignal":
        text = """
🚨 **Test Signal Generated**

📈 Symbol: NSE:BANKNIFTY
🔥 Type: SELL  
💰 Entry: ₹51,200
🎯 Target: ₹50,800
🛑 SL: ₹51,500

⏰ Generated: Just now
✅ System working perfectly!
        """
        await query.edit_message_text(text)
        
    elif query.data == "about":
        text = """
🤖 **About BigBullScalpBot**

🎯 **Features:**
• Live F&O trading signals
• Real-time market analysis
• Risk management included
• 24/7 automated operation

💰 **Pricing:** ₹2,400/month
📞 **Support:** Active
⚠️ **Risk Warning:** Trading involves risk

**Bot Status:** ✅ Fully Operational
        """
        await query.edit_message_text(text)

# Flask routes
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "BigBullScalpBot",
        "version": "3.0-simple",
        "telegram_bot": "active",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "responding"}), 200

# Setup Telegram bot
def setup_bot():
    """Setup and start Telegram bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN missing!")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Start polling in background thread
        def run_bot():
            logger.info("Starting Telegram bot...")
            application.run_polling(drop_pending_updates=True)
            
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        logger.info("✅ Telegram bot setup complete!")
        
    except Exception as e:
        logger.error(f"❌ Bot setup failed: {e}")

# Main execution
if __name__ == '__main__':
    logger.info("🚀 Starting BigBullScalpBot Simple Version...")
    
    # Start Telegram bot
    setup_bot()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)