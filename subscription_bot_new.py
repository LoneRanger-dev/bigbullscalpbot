import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from database_manager import DatabaseManager
from datetime import datetime

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize database manager
db = DatabaseManager()

def start(update: Update, context: CallbackContext):
    """Handle the /start command"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    # Add user to database
    db.add_subscriber(chat_id, username)
    
    keyboard = [
        [InlineKeyboardButton("Start Free Trial", callback_data='trial')],
        [InlineKeyboardButton("View Plans", callback_data='plans')],
        [InlineKeyboardButton("Check Status", callback_data='status')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 Welcome to BigBullScalpBot!\n\n"
        "Get professional F&O trading signals with precise strike prices.\n\n"
        "Choose an option:"
    )
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup)

def status(update: Update, context: CallbackContext):
    """Check subscription status"""
    chat_id = update.effective_chat.id
    is_active, plan_type, end_date = db.check_subscription(chat_id)
    
    if is_active:
        remaining_days = (end_date - datetime.now()).days
        message = (
            f"✅ Active Subscription\n"
            f"Plan: {plan_type.title()}\n"
            f"Expires in: {remaining_days} days\n"
            f"End Date: {end_date.strftime('%Y-%m-%d')}"
        )
        update.message.reply_text(message)
    else:
        keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "❌ No active subscription. Get started with our plans!",
            reply_markup=reply_markup
        )

def trial(update: Update, context: CallbackContext):
    """Start free trial"""
    chat_id = update.effective_chat.id
    success, message = db.start_trial(chat_id)
    
    if success:
        update.message.reply_text(
            "✅ Trial activated successfully!\n"
            "You now have 2 days of full access to our signals.\n"
            "Use /status to check your subscription status."
        )
    else:
        keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"❌ {message}\n"
            "Check out our subscription plans:",
            reply_markup=reply_markup
        )

def plans(update: Update, context: CallbackContext):
    """Show subscription plans"""
    plans_text = (
        "📊 Available Plans\n\n"
        "🎁 Trial Plan\n"
        "• 2 Days Free\n"
        "• Full Access\n"
        "• Basic Support\n\n"
        "📅 Weekly Plan - ₹350\n"
        "• 7 Days Access\n"
        "• Full Features\n"
        "• Priority Support\n"
        "• Performance Reports\n\n"
        "🌟 Monthly Plan - ₹900\n"
        "• 30 Days Access\n"
        "• All Features\n"
        "• Premium Support\n"
        "• Strategy Insights\n"
        "• Best Value!"
    )
    
    keyboard = [
        [InlineKeyboardButton("Start Free Trial", callback_data='trial')],
        [InlineKeyboardButton("Subscribe Now", url='https://loneranger-dev.github.io/bigbullscalpbot/payment.html')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'message'):
        update.message.reply_text(plans_text, reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text(plans_text, reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext):
    """Handle button callbacks"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'trial':
        chat_id = update.effective_chat.id
        success, message = db.start_trial(chat_id)
        
        if success:
            query.message.reply_text(
                "✅ Trial activated successfully!\n"
                "You now have 2 days of full access to our signals.\n"
                "Use /status to check your subscription status."
            )
        else:
            keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(
                f"❌ {message}\n"
                "Check out our subscription plans:",
                reply_markup=reply_markup
            )
    
    elif query.data == 'plans':
        plans(update, context)
    
    elif query.data == 'status':
        status(update, context)

def run_bot(token: str):
    """Run the bot"""
    updater = Updater(token)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('status', status))
    dp.add_handler(CommandHandler('trial', trial))
    dp.add_handler(CommandHandler('plans', plans))
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    updater.start_polling()
    updater.idle()