#!/usr/bin/env python3
"""
Quick test script to manually activate your subscription
Run this to give yourself free access for testing
"""

import sqlite3
from datetime import datetime, timedelta

def activate_test_subscription(user_id, username="TestUser"):
    """Manually activate subscription for testing"""
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        
        # Add/update user with active subscription
        expires = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, subscription_active, subscription_expires, payment_method) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, True, expires, 'TEST'))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Test subscription activated for user {user_id}")
        print(f"   Username: {username}")
        print(f"   Expires: {expires}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Replace with your Telegram user ID
    # You can get this by messaging @userinfobot on Telegram
    user_id = input("Enter your Telegram User ID: ")
    activate_test_subscription(int(user_id), "Admin")