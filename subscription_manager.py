import sqlite3
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler
)
import razorpay
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='subscription_bot.log'
)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
RAZORPAY_KEY = "rzp_test_RNyVizHsPGSNQy"
RAZORPAY_SECRET = "o2XWXVnqsxnN5j08FnIAvO3i"

# Subscription Plans (in INR)
PLANS = {
    'trial': {'price': 0, 'days': 2},
    'weekly': {'price': 350, 'days': 7},
    'monthly': {'price': 900, 'days': 30}
}

class SubscriptionManager:
    def __init__(self):
        self.setup_database()
        self.razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
        self.ist = pytz.timezone('Asia/Kolkata')

    def setup_database(self):
        """Initialize SQLite database for subscriber management"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        # Add had_trial column to subscribers table
        try:
            c.execute('ALTER TABLE subscribers ADD COLUMN had_trial BOOLEAN DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create subscribers table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                subscription_type TEXT,
                start_date TEXT,
                end_date TEXT,
                payment_id TEXT,
                is_active BOOLEAN
            )
        ''')
        
        # Create payments table
        c.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount INTEGER,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        # Check if user already had a trial
        had_trial = await self.check_previous_trial(update.message.from_user.id)
        
        keyboard = []
        if not had_trial:
            keyboard.append([InlineKeyboardButton("Start 2-Day Free Trial", callback_data='subscribe_trial')])
        
        keyboard.append([
            InlineKeyboardButton("Weekly (₹350)", callback_data='subscribe_weekly'),
            InlineKeyboardButton("Monthly (₹900)", callback_data='subscribe_monthly')
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = """
🚀 Welcome to BigBullScalpBot Premium!

Choose your subscription plan:

Weekly Plan (₹350):
• 7 days access
• Real-time trading signals
• Pre-market analysis
• Post-market analysis
• Pro trading setups

Monthly Plan (₹900):
• 30 days access
• All weekly features
• Priority signal delivery
• Enhanced support
• Better value for money

Select your plan below:
"""
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def check_previous_trial(self, user_id: int) -> bool:
        """Check if user has already used trial period"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        c.execute('SELECT had_trial FROM subscribers WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        conn.close()
        return bool(result and result[0])

    async def handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle subscription button clicks"""
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        plan_type = query.data.split('_')[1]  # 'weekly' or 'monthly'
        amount = PLANS[plan_type]['price']
        
        # Create Razorpay order
        try:
            order = self.razorpay_client.order.create({
                'amount': amount * 100,  # Amount in paise
                'currency': 'INR',
                'payment_capture': 1
            })
            
            payment_link = f"https://razorpay.com/payment/{order['id']}"
            
            keyboard = [[InlineKeyboardButton("Pay Now", url=payment_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Great choice! Please complete the payment of ₹{amount} for your {plan_type} subscription.",
                reply_markup=reply_markup
            )
            
            # Store order details
            self.store_payment(order['id'], user_id, amount, 'pending')
            
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            await query.edit_message_text("Sorry, there was an error processing your request. Please try again later.")

    def store_payment(self, payment_id, user_id, amount, status):
        """Store payment details in database"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO payments (payment_id, user_id, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, user_id, amount, status, datetime.now(self.ist).isoformat()))
        
        conn.commit()
        conn.close()

    def activate_subscription(self, user_id, chat_id, plan_type, payment_id):
        """Activate subscription after successful payment"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        start_date = datetime.now(self.ist)
        end_date = start_date + timedelta(days=PLANS[plan_type]['days'])
        
        c.execute('''
            INSERT OR REPLACE INTO subscribers 
            (user_id, chat_id, subscription_type, start_date, end_date, payment_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, chat_id, plan_type, start_date.isoformat(), end_date.isoformat(), payment_id, True))
        
        conn.commit()
        conn.close()

    async def handle_payment_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verify payment webhook from Razorpay"""
        try:
            data = json.loads(update.message.text)
            
            # Verify payment signature
            if self.verify_payment_signature(data):
                payment_id = data['payment_id']
                order_id = data['order_id']
                
                # Update payment status
                conn = sqlite3.connect('subscribers.db')
                c = conn.cursor()
                
                c.execute('UPDATE payments SET status = ? WHERE payment_id = ?', 
                         ('completed', payment_id))
                
                # Get user details
                c.execute('SELECT user_id, amount FROM payments WHERE payment_id = ?', 
                         (payment_id,))
                user_data = c.fetchone()
                
                if user_data:
                    user_id, amount = user_data
                    plan_type = 'monthly' if amount == 900 else 'weekly'
                    
                    # Activate subscription
                    self.activate_subscription(user_id, update.message.chat_id, plan_type, payment_id)
                    
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"🎉 Thank you! Your {plan_type} subscription is now active.\n\nYou will now receive:\n- Pre-market analysis\n- Real-time trading signals\n- Post-market analysis\n\nHappy trading! 📈"
                    )
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")

    def verify_payment_signature(self, data):
        """Verify Razorpay payment signature"""
        try:
            self.razorpay_client.utility.verify_payment_signature(data)
            return True
        except Exception as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            return False

    async def check_subscription(self, user_id: int) -> bool:
        """Check if a user has an active subscription"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM subscribers 
            WHERE user_id = ? AND is_active = 1 
            AND datetime(end_date) > datetime('now')
        ''', (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        return bool(result)

    async def remove_expired_subscriptions(self):
        """Remove expired subscriptions"""
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        
        # Get expired subscriptions
        c.execute('''
            SELECT user_id, chat_id FROM subscribers 
            WHERE is_active = 1 AND datetime(end_date) <= datetime('now')
        ''')
        
        expired = c.fetchall()
        
        # Deactivate expired subscriptions
        c.execute('''
            UPDATE subscribers 
            SET is_active = 0 
            WHERE datetime(end_date) <= datetime('now')
        ''')
        
        conn.commit()
        conn.close()
        
        # Notify users
        for user_id, chat_id in expired:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Your subscription has expired. To continue receiving signals, please renew your subscription using /start command."
                )
            except Exception as e:
                logger.error(f"Error notifying user {user_id}: {str(e)}")

async def main():
    """Initialize and start the bot"""
    subscription_manager = SubscriptionManager()
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", subscription_manager.start_command))
    application.add_handler(CallbackQueryHandler(subscription_manager.handle_subscription_callback))
    
    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())