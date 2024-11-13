# 🤖 Crypto Price Alert Bot

A Telegram bot for real-time cryptocurrency price tracking and custom alerts.

## 🚀 Features (v1.0.1)

- 💰 Real-time cryptocurrency price checking
- ⚠️ Custom price alerts (high/low thresholds)
- 🔄 Minute-by-minute price monitoring
- ➕ User-specific custom token support
- 💾 Persistent alert storage

## 📈 Supported Cryptocurrencies

Default tokens supported:
- Bitcoin (BTCUSDT)
- Ethereum (ETHUSDT)
- Solana (SOLUSDT)
- OM Token (OMUSDT)
- SUI (SUIUSDT)
- Custom user-added tokens

## 🛠️ Installation

1. Clone the repository
```bash
git clone https://github.com/Priyanshu1710/Price-Alert-Bot.git
cd Price-Alert-Bot

```

2. Install required packages
```bash
pip install -r requirements.txt
```

3. Set up environment variables
Create a `.env` file with:
```env
BOT_TOKEN=your_telegram_bot_token
```

4. Run the bot
```bash
python priceAlertBot.py
```

## 📦 Requirements

- python-telegram-bot==20.7
- python-dotenv==1.0.0
- requests==2.31.0
- APScheduler==3.10.4

## 💡 Usage

1. **Check Price**
   - Click "💰 Check Price"
   - Select cryptocurrency
   - Get real-time price

2. **Set Alert**
   - Click "⚠️ Set Alert"
   - Select cryptocurrency
   - Set high/low price thresholds
   - Receive notifications when crossed

3. **Custom Tokens**
   - Add your own tokens
   - Use Binance trading pairs
   - Manage personal token list

4. **Manage Alerts**
   - View active alerts
   - Delete specific alerts
   - Clear all alerts

## 🤝 Commands

- `/start` - Start the bot
- `/help` - Show help message

## 🔑 Key Functions

```python
def get_price(token_id):
    """Get cryptocurrency price from Binance API"""

def check_alerts(app):
    """Check price alerts and notify users"""

def handle_token_selection(update, context):
    """Handle token selection and price checks"""
```

## 📱 Bot Interface

The bot uses an intuitive keyboard interface with options:
- 💰 Check Price
- ⚠️ Set Alert
- 📊 View Alerts
- ❌ Delete Alerts
- ➕ Add Custom Token
- 🗑️ Delete Token
- ℹ️ Help

## 🔄 Updates

### Version 1.0.1
- Added price checking functionality
- Implemented high/low price alerts
- Added custom token support
- Integrated Binance API
- Added user-specific token management

## 🚀 Future Updates Planned

- [ ] Price trend analysis
- [ ] Multiple exchange support
- [ ] Chart visualization
- [ ] Portfolio tracking
- [ ] Price alerts with percentage changes

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Your Name
- GitHub: [@Priyanshu1710](https://github.com/Priyanshu1710)
- Email: guptapriyanshu1710@gmail.com

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Binance API](https://binance-docs.github.io/apidocs)

---
Made with ❤️ for crypto enthusiasts