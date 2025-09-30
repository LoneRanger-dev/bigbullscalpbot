from kiteconnect import KiteConnect

def get_access_token():
    """
    Get access token using API credentials
    """
    api_key = "zfz6i2qjh9zjl26m"
    api_secret = "esdsumpztnzmry8rl1e411b95qt86v2m"
    
    kite = KiteConnect(api_key=api_key)
    
    # Get the login URL
    print("1. Visit this URL to log in:")
    print(kite.login_url())
    print("\n2. After login, Zerodha will redirect you to your redirect URL.")
    print("3. Copy the request_token parameter from that URL.")
    
    # Get the request token from user
    request_token = input("\nEnter the request_token: ")
    
    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=api_secret)
        kite.set_access_token(data["access_token"])
        print("\nLogin successful!")
        print(f"Access Token: {data['access_token']}")
        return data["access_token"]
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

if __name__ == "__main__":
    access_token = get_access_token()
    if access_token:
        print("\nSave this access token in your automated_analysis.py file")