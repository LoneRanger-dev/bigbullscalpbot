from kiteconnect import KiteConnect

# API credentials
API_KEY = "zfz6i2qjh9zjl26m"
API_SECRET = "esdsumpztnzmry8rl1e411b95qt86v2m"

def get_login_url():
    kite = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    print("\n1. Visit this URL to log in and authorize the app:")
    print(login_url)
    print("\n2. After login, you will be redirected to a URL. Copy the 'request_token' parameter from that URL.")
    print("   The URL will look like: https://127.0.0.1/?status=success&request_token=xxxxx")
    print("\n3. Run the automated_analysis.py script with this request token.")

if __name__ == "__main__":
    get_login_url()