#!/usr/bin/env python3
"""
Test if bot token is working
"""

import requests

def test_bot_token(token):
    """Test if bot token works"""
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data.get('result', {})
            print("✅ BOT TOKEN IS VALID!")
            print(f"Bot Name: {bot_info.get('first_name')}")
            print(f"Username: @{bot_info.get('username')}")
            print(f"Bot ID: {bot_info.get('id')}")
            return True
        else:
            print("❌ BOT TOKEN IS INVALID!")
            print(f"Error: {data.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR CHECKING TOKEN: {e}")
        return False

if __name__ == "__main__":
    bot_token = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
    print("🔍 Testing bot token...")
    test_bot_token(bot_token)