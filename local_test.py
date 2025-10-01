#!/usr/bin/env python3
"""
DIRECT TEST - Run bot locally to see if it works
"""

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 SUCCESS! Bot is working locally!")

async def main():
    """Run bot locally"""
    print("🚀 Starting local test...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("✅ Bot configured, starting polling...")
    print("Send /start to your bot now!")
    
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())