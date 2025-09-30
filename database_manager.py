import sqlite3
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_file="subscribers.db"):
        self.db_file = db_file
        self.setup_database()

    def setup_database(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Subscribers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE
                )
            ''')

            # Subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    plan_type TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    payment_id TEXT,
                    amount REAL,
                    status TEXT,
                    FOREIGN KEY (chat_id) REFERENCES subscribers (chat_id)
                )
            ''')

            # Payments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    chat_id INTEGER,
                    amount REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    razorpay_order_id TEXT,
                    FOREIGN KEY (chat_id) REFERENCES subscribers (chat_id)
                )
            ''')
            
            conn.commit()

    def add_subscriber(self, chat_id, username):
        """Add a new subscriber"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO subscribers (chat_id, username)
                VALUES (?, ?)
            ''', (chat_id, username))
            conn.commit()

    def start_trial(self, chat_id):
        """Start a 2-day trial for a subscriber"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Check if user already had a trial
            cursor.execute('''
                SELECT COUNT(*) FROM subscriptions 
                WHERE chat_id = ? AND plan_type = 'trial'
            ''', (chat_id,))
            
            if cursor.fetchone()[0] > 0:
                return False, "Trial already used"

            # Add trial subscription
            start_date = datetime.now()
            end_date = start_date + timedelta(days=2)
            
            cursor.execute('''
                INSERT INTO subscriptions (chat_id, plan_type, start_date, end_date, status)
                VALUES (?, 'trial', ?, ?, 'active')
            ''', (chat_id, start_date, end_date))
            
            # Activate subscriber
            cursor.execute('''
                UPDATE subscribers SET is_active = TRUE
                WHERE chat_id = ?
            ''', (chat_id,))
            
            conn.commit()
            return True, "Trial started successfully"

    def add_subscription(self, chat_id, plan_type, payment_id, amount):
        """Add a new paid subscription"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            start_date = datetime.now()
            if plan_type == 'weekly':
                end_date = start_date + timedelta(days=7)
            else:  # monthly
                end_date = start_date + timedelta(days=30)
            
            cursor.execute('''
                INSERT INTO subscriptions (chat_id, plan_type, start_date, end_date, 
                                         payment_id, amount, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (chat_id, plan_type, start_date, end_date, payment_id, amount))
            
            # Activate subscriber
            cursor.execute('''
                UPDATE subscribers SET is_active = TRUE
                WHERE chat_id = ?
            ''', (chat_id,))
            
            conn.commit()
            return True

    def check_subscription(self, chat_id):
        """Check if a user has an active subscription"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT plan_type, end_date FROM subscriptions
                WHERE chat_id = ? AND status = 'active'
                AND end_date > CURRENT_TIMESTAMP
                ORDER BY end_date DESC LIMIT 1
            ''', (chat_id,))
            
            result = cursor.fetchone()
            if result:
                plan_type, end_date = result
                return True, plan_type, datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            return False, None, None

    def remove_expired_subscriptions(self):
        """Remove expired subscriptions and deactivate users"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Get all expired subscriptions
            cursor.execute('''
                UPDATE subscriptions 
                SET status = 'expired'
                WHERE end_date < CURRENT_TIMESTAMP 
                AND status = 'active'
            ''')
            
            # Deactivate users with no active subscriptions
            cursor.execute('''
                UPDATE subscribers SET is_active = FALSE
                WHERE chat_id NOT IN (
                    SELECT DISTINCT chat_id FROM subscriptions
                    WHERE status = 'active' AND end_date > CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def record_payment(self, payment_id, chat_id, amount, razorpay_order_id, status='pending'):
        """Record a payment"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (payment_id, chat_id, amount, razorpay_order_id, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (payment_id, chat_id, amount, razorpay_order_id, status))
            conn.commit()

    def update_payment_status(self, payment_id, status):
        """Update payment status"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE payments SET status = ?
                WHERE payment_id = ?
            ''', (status, payment_id))
            conn.commit()