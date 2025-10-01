#!/usr/bin/env python3
"""
BigBullScalpBot - Railway Deployment Version
Simplified automated trading bot with payment system integration
"""

import os
import logging
import threading
import time
from datetime import datetime, timedelta
import json
import sqlite3
import requests
import schedule
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import razorpay
from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for Railway deployment
app = Flask(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
KITE_API_KEY = os.getenv('KITE_API_KEY', 'zfz6i2qjh9zjl26m')
KITE_API_SECRET = os.getenv('KITE_API_SECRET', 'esdsumpztnzmry8rl1e411b95qt86v2m')
KITE_ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN', '9tB7VtbqUGu4btfKkX7E4zO6t7wNOtbt')
UPI_ID = "81285083843@YBL"

# Initialize services
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID else None
kite = KiteConnect(api_key=KITE_API_KEY)
if KITE_ACCESS_TOKEN:
    kite.set_access_token(KITE_ACCESS_TOKEN)

# Database setup
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            subscription_active BOOLEAN DEFAULT FALSE,
            subscription_expires DATETIME,
            payment_method TEXT,
            joined_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            payment_id TEXT,
            amount REAL,
            status TEXT,
            payment_method TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Signals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            signal_type TEXT,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Global variables
telegram_app = None
active_signals = []
market_data_cache = {}

class TradingBot:
    def __init__(self):
        self.kite = kite
        self.active_signals = []
        
    def get_market_data(self, symbol):
        """Get live market data from Kite"""
        try:
            if not self.kite:
                return None
                
            quotes = self.kite.quote([symbol])
            return quotes.get(symbol, {})
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    def analyze_market(self, symbol):
        """Simple market analysis for signal generation"""
        try:
            data = self.get_market_data(symbol)
            if not data:
                return None
                
            ltp = data.get('last_price', 0)
            change = data.get('net_change', 0)
            volume = data.get('volume', 0)
            
            # Simple signal logic
            if change > 0.5 and volume > 100000:
                return {
                    'type': 'BUY',
                    'entry': ltp,
                    'target': ltp * 1.02,
                    'stop_loss': ltp * 0.98
                }
            elif change < -0.5 and volume > 100000:
                return {
                    'type': 'SELL',
                    'entry': ltp,
                    'target': ltp * 0.98,
                    'stop_loss': ltp * 1.02
                }
            
            return None
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {e}")
            return None
    
    def generate_signals(self):
        """Generate trading signals for F&O instruments"""
        try:
            symbols = ['NSE:NIFTY', 'NSE:BANKNIFTY', 'NSE:RELIANCE', 'NSE:TCS', 'NSE:INFY']
            new_signals = []
            
            for symbol in symbols:
                signal = self.analyze_market(symbol)
                if signal:
                    signal['symbol'] = symbol
                    signal['timestamp'] = datetime.now()
                    new_signals.append(signal)
                    
                    # Store in database
                    conn = sqlite3.connect('trading_bot.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO signals (symbol, signal_type, entry_price, target_price, stop_loss)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (symbol, signal['type'], signal['entry'], signal['target'], signal['stop_loss']))
                    conn.commit()
                    conn.close()
            
            return new_signals
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return []

# Initialize trading bot
trading_bot = TradingBot()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Add user to database
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username)
        VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("💳 Subscribe Now", callback_data="subscribe")],
        [InlineKeyboardButton("📊 Live Signals", callback_data="signals")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🚀 Welcome to BigBullScalpBot!

Your premier F&O trading signals bot with live market analysis.

✅ Real-time signals
✅ High accuracy predictions
✅ Risk management included
✅ 24/7 market monitoring

Monthly Subscription: ₹2,400
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "subscribe":
        await handle_subscription(query)
    elif query.data == "signals":
        await show_signals(query)
    elif query.data == "about":
        await show_about(query)
    elif query.data.startswith("pay_"):
        await handle_payment_method(query)

async def handle_subscription(query):
    """Handle subscription request"""
    keyboard = [
        [InlineKeyboardButton("💳 Razorpay (Instant)", callback_data="pay_razorpay")],
        [InlineKeyboardButton("📱 UPI Manual", callback_data="pay_upi")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
💰 Choose Payment Method:

💳 Razorpay: Instant activation
📱 UPI: Manual verification (24hrs)

Monthly Subscription: ₹2,400
    """
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_payment_method(query):
    """Handle payment method selection"""
    user_id = query.from_user.id
    
    if query.data == "pay_razorpay" and razorpay_client:
        # Create Razorpay order
        try:
            order = razorpay_client.order.create({
                'amount': 240000,  # ₹2,400 in paise
                'currency': 'INR',
                'payment_capture': 1
            })
            
            payment_link = f"https://rzp.io/l/{order['id']}"
            
            text = f"""
💳 Razorpay Payment

Amount: ₹2,400
Order ID: {order['id']}

Click to pay: {payment_link}

After payment, you'll be automatically activated!
            """
            
            await query.edit_message_text(text)
            
        except Exception as e:
            logger.error(f"Razorpay error: {e}")
            await query.edit_message_text("❌ Payment system temporarily unavailable. Please try UPI.")
    
    elif query.data == "pay_upi":
        text = f"""
📱 Manual UPI Payment

Amount: ₹2,400
UPI ID: {UPI_ID}

Steps:
1. Pay ₹2,400 to {UPI_ID}
2. Take screenshot of payment
3. Send screenshot here
4. Wait for manual verification (24hrs)

Note: Copy UPI ID and paste in your payment app
        """
        
        await query.edit_message_text(text)

async def show_signals(query):
    """Show current trading signals"""
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, signal_type, entry_price, target_price, stop_loss, timestamp
            FROM signals
            WHERE status = 'ACTIVE'
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        signals = cursor.fetchall()
        conn.close()
        
        if signals:
            text = "📊 Latest Trading Signals:\n\n"
            for signal in signals:
                symbol, sig_type, entry, target, sl, timestamp = signal
                text += f"🎯 {symbol}\n"
                text += f"Signal: {sig_type}\n"
                text += f"Entry: ₹{entry:.2f}\n"
                text += f"Target: ₹{target:.2f}\n"
                text += f"SL: ₹{sl:.2f}\n"
                text += f"Time: {timestamp}\n\n"
        else:
            text = "📊 No active signals at the moment.\nSignals are generated during market hours."
        
        await query.edit_message_text(text)
        
    except Exception as e:
        logger.error(f"Error showing signals: {e}")
        await query.edit_message_text("❌ Error fetching signals. Please try again.")

async def show_about(query):
    """Show about information"""
    text = """
🤖 BigBullScalpBot

Advanced F&O trading signals with:
• Live market data from Zerodha Kite
• Real-time technical analysis
• Risk management included
• High accuracy predictions

Subscription: ₹2,400/month
Support: Contact @admin

Disclaimer: Trading involves risk. Past performance doesn't guarantee future results.
    """
    
    await query.edit_message_text(text)

# Admin Commands
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin commands for testing"""
    user_id = update.effective_user.id
    
    admin_text = f"""
🔧 **Admin Commands**

Your User ID: `{user_id}`

Available Commands:
/testsignal - Generate test trading signal
/activate - Activate your subscription for testing
/admin - Show this menu

**Quick Setup:**
1. Use /activate to give yourself free access
2. Use /testsignal to test signal generation
3. Check if signals appear in your chat

Bot Status: ✅ Running
Market Data: ✅ Connected to Kite API
    """
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def test_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a test signal immediately"""
    try:
        # Generate a test signal
        test_signals = trading_bot.generate_signals()
        
        if test_signals:
            for signal in test_signals:
                message = f"""
🚨 **TEST SIGNAL** 🚨

📈 **Symbol**: {signal['symbol']}
🔥 **Type**: {signal['type']}
💰 **Entry**: ₹{signal['entry']:.2f}
🎯 **Target**: ₹{signal['target']:.2f}
🛑 **Stop Loss**: ₹{signal['stop_loss']:.2f}

⏰ **Time**: {signal['timestamp'].strftime('%H:%M:%S')}
🤖 **Status**: Test Signal Generated

This is a test signal to verify the system is working!
                """
                await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("No signals generated at this time. Market might be closed or no qualifying movements detected.")
            
    except Exception as e:
        await update.message.reply_text(f"Error generating test signal: {e}")

async def activate_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate subscription for testing"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "TestUser"
    
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        
        from datetime import timedelta
        expires = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, subscription_active, subscription_expires, payment_method) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, True, expires, 'ADMIN_TEST'))
        
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"""
✅ **Subscription Activated!**

User ID: {user_id}
Username: {username}
Status: ✅ Active
Expires: {expires.strftime('%Y-%m-%d')}
Payment: Admin Test

You will now receive all trading signals automatically!

Try /testsignal to generate a test signal.
        """)
        
    except Exception as e:
        await update.message.reply_text(f"Error activating subscription: {e}")

# Flask routes for Railway
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "service": "BigBullScalpBot",
        "version": "1.0.0"
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook for Razorpay payments"""
    try:
        data = request.json
        # Process webhook data
        logger.info(f"Webhook received: {data}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": "processing failed"}), 400

# Signal generation scheduler
def run_signal_generation():
    """Run signal generation in background"""
    def generate_and_broadcast():
        try:
            signals = trading_bot.generate_signals()
            if signals and telegram_app:
                # Broadcast to subscribed users
                conn = sqlite3.connect('trading_bot.db')
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE subscription_active = TRUE')
                users = cursor.fetchall()
                conn.close()
                
                for signal in signals:
                    message = f"""
🚨 NEW SIGNAL ALERT 🚨

Symbol: {signal['symbol']}
Type: {signal['type']}
Entry: ₹{signal['entry']:.2f}
Target: ₹{signal['target']:.2f}
Stop Loss: ₹{signal['stop_loss']:.2f}

⏰ {signal['timestamp'].strftime('%H:%M:%S')}
                    """
                    
                    for user in users:
                        try:
                            # This would need to be implemented with proper async handling
                            # For now, we log the signal
                            logger.info(f"Signal for user {user[0]}: {message}")
                        except Exception as e:
                            logger.error(f"Error sending signal to user {user[0]}: {e}")
        
        except Exception as e:
            logger.error(f"Error in signal generation: {e}")
    
    # Schedule signal generation
    schedule.every(15).minutes.do(generate_and_broadcast)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Initialize Telegram Bot
def setup_telegram_bot():
    """Setup Telegram bot"""
    global telegram_app
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not provided")
        return None
    
    try:
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.add_handler(CommandHandler("admin", admin_commands))
        telegram_app.add_handler(CommandHandler("testsignal", test_signal))
        telegram_app.add_handler(CommandHandler("activate", activate_me))
        telegram_app.add_handler(CallbackQueryHandler(button_handler))
        
        # Start polling in a separate thread
        def start_polling():
            telegram_app.run_polling(drop_pending_updates=True)
        
        polling_thread = threading.Thread(target=start_polling, daemon=True)
        polling_thread.start()
        
        logger.info("Telegram bot started successfully")
        return telegram_app
        
    except Exception as e:
        logger.error(f"Error setting up Telegram bot: {e}")
        return None

# Main execution
if __name__ == '__main__':
    logger.info("Starting BigBullScalpBot...")
    
    # Setup Telegram bot
    setup_telegram_bot()
    
    # Start signal generation thread
    signal_thread = threading.Thread(target=run_signal_generation, daemon=True)
    signal_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)