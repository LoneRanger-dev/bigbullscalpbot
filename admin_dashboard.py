#!/usr/bin/env python3
"""
Admin Dashboard for BigBullScalpBot
Monitor signals, users, and revenue
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string

app = Flask(__name__)

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BigBullScalpBot - Admin Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { opacity: 0.9; }
        .signals-table { width: 100%; border-collapse: collapse; }
        .signals-table th, .signals-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .signals-table th { background-color: #f8f9fa; }
        .buy { color: #28a745; font-weight: bold; }
        .sell { color: #dc3545; font-weight: bold; }
        .refresh-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🤖 BigBullScalpBot Admin Dashboard</h1>
            <p>Last updated: {{ current_time }}</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ active_subscribers }}</div>
                <div class="stat-label">Active Subscribers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">₹{{ monthly_revenue }}</div>
                <div class="stat-label">Monthly Revenue</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ signals_today }}</div>
                <div class="stat-label">Signals Today</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Recent Signals</h2>
            <table class="signals-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Type</th>
                        <th>Entry</th>
                        <th>Target</th>
                        <th>Stop Loss</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for signal in recent_signals %}
                    <tr>
                        <td>{{ signal.timestamp }}</td>
                        <td>{{ signal.symbol }}</td>
                        <td class="{{ signal.signal_type.lower() }}">{{ signal.signal_type }}</td>
                        <td>₹{{ "%.2f"|format(signal.entry_price) }}</td>
                        <td>₹{{ "%.2f"|format(signal.target_price) }}</td>
                        <td>₹{{ "%.2f"|format(signal.stop_loss) }}</td>
                        <td>{{ signal.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>💰 Revenue Analysis</h2>
            <p><strong>Average Revenue Per User:</strong> ₹2,400/month</p>
            <p><strong>Churn Rate:</strong> ~5%/month</p>
            <p><strong>Growth Rate:</strong> {{ growth_rate }}%/month</p>
            <p><strong>Projected Annual Revenue:</strong> ₹{{ projected_annual }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard to monitor bot performance"""
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_active = TRUE')
        active_subscribers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM signals WHERE DATE(timestamp) = DATE("now")')
        signals_today = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT * FROM signals 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        recent_signals = cursor.fetchall()
        
        conn.close()
        
        # Calculate revenue
        monthly_revenue = active_subscribers * 2400
        projected_annual = monthly_revenue * 12
        growth_rate = 15  # Estimated growth rate
        
        # Format signals
        signals_data = []
        for signal in recent_signals:
            signals_data.append({
                'timestamp': signal[6],
                'symbol': signal[1],
                'signal_type': signal[2],
                'entry_price': signal[3],
                'target_price': signal[4],
                'stop_loss': signal[5],
                'status': signal[7]
            })
        
        return render_template_string(ADMIN_DASHBOARD_HTML,
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_users=total_users,
            active_subscribers=active_subscribers,
            monthly_revenue=f"{monthly_revenue:,}",
            signals_today=signals_today,
            recent_signals=signals_data,
            growth_rate=growth_rate,
            projected_annual=f"{projected_annual:,}"
        )
        
    except Exception as e:
        return f"Dashboard Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)