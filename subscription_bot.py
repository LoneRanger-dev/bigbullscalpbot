import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from database_manager import DatabaseManager
from datetime import datetime

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize database manager
db = DatabaseManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    else:
        keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "❌ No active subscription. Get started with our plans!"
        await update.message.reply_text(message, reply_markup=reply_markup)
        return
    
    await update.message.reply_text(message)

async def trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start free trial"""
    chat_id = update.effective_chat.id
    success, message = db.start_trial(chat_id)
    
    if success:
        await update.message.reply_text(
            "✅ Trial activated successfully!\n"
            "You now have 2 days of full access to our signals.\n"
            "Use /status to check your subscription status."
        )
    else:
        keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ {message}\n"
            "Check out our subscription plans:",
            reply_markup=reply_markup
        )

async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(plans_text, reply_markup=reply_markup)
    elif hasattr(update, 'callback_query'):
        await update.callback_query.message.reply_text(plans_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'trial':
        chat_id = update.effective_chat.id
        success, message = db.start_trial(chat_id)
        
        if success:
            await query.message.reply_text(
                "✅ Trial activated successfully!\n"
                "You now have 2 days of full access to our signals.\n"
                "Use /status to check your subscription status."
            )
        else:
            keyboard = [[InlineKeyboardButton("View Plans", callback_data='plans')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"❌ {message}\n"
                "Check out our subscription plans:",
                reply_markup=reply_markup
            )
    
    elif query.data == 'plans':
        await plans(update, context)
    
    elif query.data == 'status':
        await status(update, context)

def run_bot(token: str):
    """Run the bot"""
    application = ApplicationBuilder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('trial', trial))
    application.add_handler(CommandHandler('plans', plans))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    application.run_polling()