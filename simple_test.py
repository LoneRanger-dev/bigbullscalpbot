import telebot

# Your credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Send a simple test message
test_message = "🎯 Test Message: If you can see this, your trading bot is connected successfully!"

try:
    bot.send_message(CHAT_ID, test_message)
    print("Message sent! Check your Telegram.")
except Exception as e:
    print(f"Error: {str(e)}")