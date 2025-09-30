import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler
from database_manager import DatabaseManager
from subscription_bot import start, status, trial, plans, button_callback
import asyncio
import schedule
import time
import threading
from datetime import datetimeging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from database_manager import DatabaseManager
from subscription_bot_new import run_bot
from datetime import datetime
import asyncio
import schedule
import time
import threading

# Initialize logging and database
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
db = DatabaseManager()

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send trading signal only to active subscribers"""
    chat_id = update.effective_chat.id
    is_active, plan_type, _ = db.check_subscription(chat_id)
    
    if not is_active:
        keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ No active subscription. Subscribe to receive signals:",
            reply_markup=reply_markup
        )
        return
    
    # If user has active subscription, proceed with signal generation and sending
    # Your existing signal generation code here
    pass

def check_expired_subscriptions():
    """Periodic task to check and remove expired subscriptions"""
    db.remove_expired_subscriptions()

def run_schedule():
    """Run the scheduler for subscription checks"""
    schedule.every().hour.do(check_expired_subscriptions)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """Main function to run the bot"""
    # Start subscription checker in a separate thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Run the bot
    TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"  # Bot token
    run_bot(TOKEN)

if __name__ == '__main__':
    main()