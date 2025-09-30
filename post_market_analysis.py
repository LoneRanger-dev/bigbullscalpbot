def post_market_analysis(self):
    try:
        # Get Nifty data
        nifty_data = self.kite.quote("NSE:NIFTY 50")
        nifty_close = nifty_data['last_price']
        nifty_change = nifty_data['change']
        
        # Get top gainers and losers
        gainers_losers = self.get_top_movers()
        
        # Get sector performance
        sector_performance = self.analyze_sectors()
        
        # Get FII/DII data
        institutional_data = self.get_institutional_data()
        
        # Get any major results announced today
        results_impact = self.analyze_results_impact()
        
        message = f"""
🔍 *Post Market Analysis* - {datetime.now(self.ist).strftime('%d %b %Y')}

📊 *Market Overview:*
• Nifty Close: {nifty_close:.2f}
• Change: {nifty_change:.2f} ({(nifty_change/nifty_close * 100):.2f}%)
• Market Breadth: {gainers_losers['advance_decline']}

💹 *Top Gainers:*"""

        for stock in gainers_losers['top_gainers'][:3]:
            message += f"""
• {stock['symbol']}: +{stock['change_pct']:.2f}%
  Volume: {stock['volume_change']}% of avg
  Reason: {stock['movement_reason']}"""

        message += "\n\n📉 *Top Losers:*"
        for stock in gainers_losers['top_losers'][:3]:
            message += f"""
• {stock['symbol']}: {stock['change_pct']:.2f}%
  Volume: {stock['volume_change']}% of avg
  Reason: {stock['movement_reason']}"""

        message += "\n\n🔄 *Sector Performance:*"
        for sector, data in sector_performance.items():
            message += f"""
• {sector}: {data['change']:.2f}%
  Leaders: {data['top_stock']} ({data['top_stock_change']:.2f}%)"""

        message += f"""

💰 *Institutional Activity:*
• FII: {institutional_data['fii']} Cr
• DII: {institutional_data['dii']} Cr
• Impact: {institutional_data['impact']}

📈 *Major Result Impact:*"""
        
        for company in results_impact:
            message += f"""
• {company['name']}:
  - Results: {company['results_vs_estimate']}
  - Stock Impact: {company['price_impact']}%
  - Sector Impact: {company['sector_impact']}"""

        message += """

🎯 *Key Takeaways:*"""
        
        # Add market analysis based on data
        if nifty_change > 0:
            if institutional_data['fii'] > 0:
                message += "\n• Market up with strong FII buying support"
            else:
                message += "\n• Market up despite FII selling, showing domestic strength"
        else:
            if institutional_data['fii'] < 0:
                message += "\n• Market down with FII selling pressure"
            else:
                message += "\n• Market down despite FII buying, showing weak sentiment"

        # Add sector-specific analysis
        strongest_sector = max(sector_performance.items(), key=lambda x: x[1]['change'])
        weakest_sector = min(sector_performance.items(), key=lambda x: x[1]['change'])
        message += f"""
• {strongest_sector[0]} leading the market ({strongest_sector[1]['change']:.2f}%)
• {weakest_sector[0]} showing weakness ({weakest_sector[1]['change']:.2f}%)"""

        # Add result impact analysis
        if results_impact:
            message += "\n• Results season impact:"
            for company in results_impact:
                message += f"\n  - {company['name']}: {company['analysis']}"

        message += """

📊 *Tomorrow's Outlook:*
• Check global market reaction
• Monitor {strongest_sector[0]} momentum
• Watch institutional flow
• Key levels updated in next signal

#PostMarketAnalysis #MarketInsights
"""
        self.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Error in post market analysis: {str(e)}")

def get_top_movers(self):
    try:
        nifty_500_stocks = self.kite.instruments("NSE")
        gainers = []
        losers = []
        advance = 0
        decline = 0
        
        for stock in nifty_500_stocks:
            if stock['segment'] == 'NSE':
                quote = self.kite.quote(f"NSE:{stock['tradingsymbol']}")
                change_pct = (quote['last_price'] - quote['prev_close']) / quote['prev_close'] * 100
                
                stock_data = {
                    'symbol': stock['tradingsymbol'],
                    'change_pct': change_pct,
                    'volume_change': (quote['volume'] / quote['average_volume'] * 100),
                    'movement_reason': self.analyze_stock_movement(stock['tradingsymbol'])
                }
                
                if change_pct > 0:
                    advance += 1
                    gainers.append(stock_data)
                else:
                    decline += 1
                    losers.append(stock_data)
        
        return {
            'top_gainers': sorted(gainers, key=lambda x: x['change_pct'], reverse=True),
            'top_losers': sorted(losers, key=lambda x: x['change_pct']),
            'advance_decline': f"A/D: {advance}/{decline}"
        }
    except Exception as e:
        logging.error(f"Error getting top movers: {str(e)}")
        return {'top_gainers': [], 'top_losers': [], 'advance_decline': "N/A"}

def analyze_stock_movement(self, symbol):
    try:
        # Fetch news for the stock
        url = f"https://www.moneycontrol.com/stocks/company-info/{symbol}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        news = soup.find_all('div', {'class': 'news-item'})
        
        # Keywords to check in news
        positive_keywords = ['better than expected', 'strong growth', 'buy rating', 'upgrade']
        negative_keywords = ['downgrade', 'weak results', 'sell rating', 'below estimates']
        
        for item in news:
            text = item.text.lower()
            if any(keyword in text for keyword in positive_keywords):
                return "Positive news/analyst ratings"
            elif any(keyword in text for keyword in negative_keywords):
                return "Negative news/analyst ratings"
        
        return "Regular market movement"
    except:
        return "Technical factors"

def analyze_sectors(self):
    sectors = {
        'NIFTY BANK': 'Banking',
        'NIFTY IT': 'IT',
        'NIFTY AUTO': 'Auto',
        'NIFTY PHARMA': 'Pharma',
        'NIFTY METAL': 'Metal'
    }
    
    sector_data = {}
    for index, sector in sectors.items():
        try:
            quote = self.kite.quote(f"NSE:{index}")
            sector_data[sector] = {
                'change': (quote['last_price'] - quote['prev_close']) / quote['prev_close'] * 100,
                'top_stock': self.get_sector_leader(sector),
                'top_stock_change': self.get_stock_change(self.get_sector_leader(sector))
            }
        except:
            continue
    
    return sector_data

def analyze_results_impact(self):
    try:
        # Fetch today's results
        url = "https://www.moneycontrol.com/stocks/earnings/results_announced.php"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for row in soup.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 4:
                company_name = cols[0].text.strip()
                expected_eps = float(cols[2].text.strip() or 0)
                actual_eps = float(cols[3].text.strip() or 0)
                
                # Get stock price impact
                quote = self.kite.quote(f"NSE:{company_name.replace(' ', '')}")
                price_impact = (quote['last_price'] - quote['prev_close']) / quote['prev_close'] * 100
                
                results.append({
                    'name': company_name,
                    'results_vs_estimate': 'Beat' if actual_eps > expected_eps else 'Miss',
                    'price_impact': price_impact,
                    'sector_impact': self.get_sector_impact(company_name),
                    'analysis': self.analyze_result_impact(actual_eps, expected_eps, price_impact)
                })
        
        return results
    except Exception as e:
        logging.error(f"Error analyzing results: {str(e)}")
        return []

def analyze_result_impact(self, actual, expected, price_impact):
    if actual > expected:
        if price_impact > 0:
            return "Strong results led to positive price action"
        else:
            return "Good results but weak market sentiment"
    else:
        if price_impact < 0:
            return "Weak results led to selling pressure"
        else:
            return "Results missed but stock showing resilience"

# Update the run method to include post-market analysis
def run(self):
    schedule.every().day.at("08:30").do(self.send_morning_analysis)
    schedule.every().day.at("15:45").do(self.post_market_analysis)  # Added post-market analysis
    schedule.every().day.at("18:30").do(self.send_evening_news)
    schedule.every(5).minutes.do(self.check_trading_signals)

    print("Market Analysis System Started...")