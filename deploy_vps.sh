#!/bin/bash
# Simple VPS Deployment Script
# Run this on any Ubuntu/Debian VPS

echo "=== BigBullScalpBot VPS Deployment ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-pip python3.11-venv git

# Clone repository
git clone https://github.com/LoneRanger-dev/bigbullscalpbot.git
cd bigbullscalpbot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
BOT_TOKEN=your_telegram_bot_token_here
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
KITE_API_KEY=zfz6i2qjh9zjl26m
KITE_API_SECRET=esdsumpztnzmry8rl1e411b95qt86v2m
KITE_ACCESS_TOKEN=9tB7VtbqUGu4btfKkX7E4zO6t7wNOtbt
PORT=8000
EOF

echo "Edit .env file with your actual tokens!"
echo "Then run: python main.py"

# Create systemd service
sudo tee /etc/systemd/system/bigbullscalpbot.service > /dev/null <<EOF
[Unit]
Description=BigBullScalpBot Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable bigbullscalpbot

echo "=== Deployment Complete ==="
echo "1. Edit .env file: nano .env"
echo "2. Start service: sudo systemctl start bigbullscalpbot"
echo "3. Check status: sudo systemctl status bigbullscalpbot"
echo "4. View logs: sudo journalctl -u bigbullscalpbot -f"