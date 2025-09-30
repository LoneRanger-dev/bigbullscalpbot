from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime
import pytz

def setup_kite():
    api_key = "zfz6i2qjh9zjl26m"  # Your API key
    kite = KiteConnect(api_key=api_key)
    return kite

def get_fno_instruments(kite, symbol):
    """
    Search for F&O instruments for a given symbol
    """
    try:
        # Search for instruments
        instruments = kite.search_instruments("NFO", symbol)
        
        if not instruments:
            print(f"No F&O instruments found for {symbol}")
            return None
        
        # Convert to DataFrame for better visualization
        df = pd.DataFrame(instruments)
        df['expiry'] = pd.to_datetime(df['expiry']).dt.date
        return df
    except Exception as e:
        print(f"Error fetching F&O instruments: {str(e)}")
        return None

def get_live_prices(kite, instrument_tokens):
    """
    Get live LTP for multiple instruments
    """
    try:
        ticks = kite.quote(instrument_tokens)
        return ticks
    except Exception as e:
        print(f"Error fetching live prices: {str(e)}")
        return None

def main():
    # Initialize Kite
    kite = setup_kite()
    
    # Example: Get NIFTY options
    symbol = "NIFTY"  # You can change this to any stock/index
    
    print(f"\nFetching F&O instruments for {symbol}...")
    instruments_df = get_fno_instruments(kite, symbol)
    
    if instruments_df is not None:
        print("\nAvailable instruments:")
        # Filter for current month's expiry
        current_month = datetime.now(pytz.timezone('Asia/Kolkata')).date().replace(day=1)
        current_expiry = instruments_df[instruments_df['expiry'] >= current_month].iloc[0]['expiry']
        
        # Filter options for current expiry
        current_options = instruments_df[
            (instruments_df['expiry'] == current_expiry) &
            (instruments_df['instrument_type'].isin(['CE', 'PE']))
        ]
        
        print("\nCurrent month options:")
        print(current_options[['tradingsymbol', 'strike', 'instrument_type', 'expiry']].to_string())
        
        # Get live prices for some strikes
        print("\nFetching live prices...")
        instrument_tokens = current_options['instrument_token'].tolist()[:5]  # Take first 5 strikes as example
        live_prices = get_live_prices(kite, instrument_tokens)
        
        if live_prices:
            for token, quote in live_prices.items():
                print(f"\nInstrument: {quote['instrument_token']}")
                print(f"LTP: {quote['last_price']}")
                print(f"Open: {quote['ohlc']['open']}")
                print(f"High: {quote['ohlc']['high']}")
                print(f"Low: {quote['ohlc']['low']}")
                print(f"Close: {quote['ohlc']['close']}")

if __name__ == "__main__":
    main()