import telebot

# Your Telegram Credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

def send_test_signal():
    try:
        # Initialize bot
        bot = telebot.TeleBot(BOT_TOKEN)
        
        # Test message
        message = """
🔔 *Market Analysis Signal Test*

Testing connection to your Telegram...
If you receive this message, the bot is working correctly!

Reply with 'OK' if you received this message.
"""
        
        # Send message
        bot.send_message(CHAT_ID, message, parse_mode='Markdown')
        print("Test message sent successfully!")
        
    except Exception as e:
        print(f"Error sending message: {str(e)}")

if __name__ == "__main__":
    send_test_signal()