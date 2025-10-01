#!/usr/bin/env python3
"""
ABSOLUTE MINIMAL TEST BOT
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Minimal start command"""
    await update.message.reply_text("🎉 BOT IS WORKING! 🎉\n\nSuccess! The bot is responding!")

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def setup_bot():
    """Setup bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        
        def run_bot():
            logger.info("Starting bot...")
            application.run_polling()
            
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started!")
        
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    logger.info("Starting minimal test bot...")
    setup_bot()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)