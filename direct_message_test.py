#!/usr/bin/env python3
"""
Direct message test to your chat ID
"""

import requests

BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

def send_test_message():
    """Send test message directly to your chat"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': CHAT_ID,
        'text': '🎉 DIRECT MESSAGE TEST 🎉\n\nYour bot token is working!\nBot can send messages directly.\n\nIf you see this, the bot is functional!',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Message sent successfully!")
            print(f"Message ID: {result['result']['message_id']}")
        else:
            print("❌ Failed to send message")
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("📱 Sending test message to your Telegram...")
    send_test_message()