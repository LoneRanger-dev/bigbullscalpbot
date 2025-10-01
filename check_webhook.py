#!/usr/bin/env python3
"""
Check webhook status
"""

import requests

BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"

def check_webhook():
    """Check current webhook configuration"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            webhook_info = result['result']
            print("📊 Webhook Status:")
            print(f"URL: {webhook_info.get('url', 'Not set')}")
            print(f"Has Custom Certificate: {webhook_info.get('has_custom_certificate', False)}")
            print(f"Pending Updates: {webhook_info.get('pending_update_count', 0)}")
            print(f"Last Error Date: {webhook_info.get('last_error_date', 'None')}")
            print(f"Last Error Message: {webhook_info.get('last_error_message', 'None')}")
            print(f"Max Connections: {webhook_info.get('max_connections', 'Default')}")
        else:
            print("❌ Failed to get webhook info")
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_webhook()