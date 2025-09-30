import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import telebot
from kiteconnect import KiteConnect
import requests
from bs4 import BeautifulSoup
import schedule
import pytz
import ta
import logging

# Configure logging
logging.basicConfig(filename='trading_signals.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Your Credentials
BOT_TOKEN = "8415230764:AAF0Aaqb21Vkq9eWifB_wHDtkm37WrjJRcs"
CHAT_ID = "7973202689"
API_KEY = "zfz6i2qjh9zjl26m"
API_SECRET = "esdsumpztnzmry8rl1e411b95qt86v2m"

class MarketAnalysis:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.kite = self.initialize_kite()
        self.ist = pytz.timezone('Asia/Kolkata')

    def initialize_kite(self):
        kite = KiteConnect(api_key=API_KEY)
        print("Please visit this URL to authorize:", kite.login_url())
        print("After authorization, enter the request token here:")
        request_token = input()
        try:
            data = kite.generate_session(request_token, api_secret=API_SECRET)
            kite.set_access_token(data["access_token"])
            print("Authentication successful!")
            return kite
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            raise

    def get_global_market_status(self):
        try:
            # Fetch global indices data
            indices = {
                'S&P 500': '^GSPC',
                'Dow Jones': '^DJI',
                'Nasdaq': '^IXIC',
                'FTSE': '^FTSE',
                'Nikkei': '^N225',
                'Hang Seng': '^HSI'
            }
            
            global_status = []
            for name, symbol in indices.items():
                url = f"https://finance.yahoo.com/quote/{symbol}"
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                try:
                    price = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'}).text
                    change = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'}).text
                    global_status.append(f"{name}: {price} ({change})")
                except:
                    continue
            
            return "\n".join(global_status)
        except Exception as e:
            logging.error(f"Error fetching global markets: {str(e)}")
            return "Unable to fetch global market data"

    def get_important_news(self):
        try:
            news_sources = [
                'https://economictimes.indiatimes.com/markets/stocks',
                'https://www.moneycontrol.com/news/business/markets/',
                'https://www.reuters.com/markets/global-market-data/',
                'https://www.bloomberg.com/markets/stocks'
            ]
            
            all_news = []
            for source in news_sources:
                response = requests.get(source)
                soup = BeautifulSoup(response.text, 'html.parser')
                headlines = soup.find_all(['h1', 'h2', 'h3'], limit=5)
                for h in headlines:
                    if h.find('a'):
                        title = h.text.strip()
                        link = h.find('a').get('href')
                        if not link.startswith('http'):
                            link = source + link
                        all_news.append((title, link))
            
            # Filter for important keywords
            important_keywords = ['war', 'crisis', 'fed', 'interest rate', 'rbi', 'gdp', 
                                'inflation', 'earning', 'result', 'policy', 'crude', 'oil']
            filtered_news = []
            for title, link in all_news:
                if any(keyword in title.lower() for keyword in important_keywords):
                    filtered_news.append((title, link))
            
            return filtered_news[:5]  # Return top 5 relevant news
        except Exception as e:
            logging.error(f"Error fetching news: {str(e)}")
            return []

    def send_morning_analysis(self):
        try:
            global_markets = self.get_global_market_status()
            
            # Get SGX Nifty data
            nifty_futures = self.kite.quote("NSE:NIFTY 50")
            
            message = f"""
🌅 *Pre-Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

🌎 *Global Markets:*
{global_markets}

📈 *SGX Nifty:* {nifty_futures['last_price']:.2f}
Change: {(nifty_futures['change']):.2f}%

🔮 *Market Outlook:*
• Global Market Sentiment: {'Positive' if global_markets.count('+') > global_markets.count('-') else 'Negative'}
• Expected Gap Opening: {'Up' if nifty_futures['change'] > 0 else 'Down'}

⚠️ *Key Events Today:*
• Check economic calendar
• Monitor global cues
• Watch sector-specific news

#PreMarketAnalysis #NiftyOutlook
"""
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"Error in morning analysis: {str(e)}")

    def send_evening_news(self):
        try:
            important_news = self.get_important_news()
            
            message = f"""
🌙 *End of Day Market News* - {datetime.now(self.ist).strftime('%d %b %Y')}

📰 *Top Impact News for Tomorrow:*

"""
            for i, (title, link) in enumerate(important_news, 1):
                message += f"{i}. [{title}]({link})\n\n"

            message += """
🔍 *Focus Areas for Tomorrow:*
• Monitor these developments
• Check global market reactions
• Plan trades accordingly

#MarketNews #TradingSetup
"""
            self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"Error in evening news: {str(e)}")

    def check_trading_signals(self):
        try:
            if not self.is_market_hour():
                return

            df = self.get_market_data()
            if df is not None:
                df = self.calculate_indicators(df)
                signals = self.generate_trading_signal(df)
                if signals:  # Only send if there's a strong signal
                    self.bot.send_message(CHAT_ID, signals, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Error in trading signals: {str(e)}")

    def is_market_hour(self):
        now = datetime.now(self.ist)
        if now.weekday() >= 5:  # Weekend
            return False
        market_start = now.replace(hour=9, minute=15, second=0)
        market_end = now.replace(hour=15, minute=30, second=0)
        return market_start <= now <= market_end

    def run(self):
        # Schedule tasks
        schedule.every().day.at("08:30").do(self.send_morning_analysis)
        schedule.every().day.at("15:45").do(self.post_market_analysis)
        schedule.every().day.at("18:30").do(self.send_evening_news)
        schedule.every(5).minutes.do(self.check_trading_signals)

        print("Market Analysis System Started...")
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    try:
        market_analysis = MarketAnalysis()
        market_analysis.run()
    except KeyboardInterrupt:
        print("\nStopping market analysis system...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        logging.critical(f"Fatal error: {str(e)}")