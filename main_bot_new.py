import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler
from database_manager import DatabaseManager
import asyncio
import schedule
import time
import threading
from datetime import datetime

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

async def main():
    """Main function to run the bot"""
    # Start subscription checker in a separate thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token("8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs").build()
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('trial', trial))
    application.add_handler(CommandHandler('plans', plans))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot until you press Ctrl-C
    await application.run_polling()