
# ****************************************** Version 1 --> Price Alert Bot ************************************

# import requests
# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# # Telegram Bot Token
# TOKEN = ' '
# TOKEN_IDS = ['bitcoin', 'ethereum', 'cardano']

# # Function to get the price from CoinGecko
# def get_price(token_id):
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd'
#     response = requests.get(url)
#     data = response.json()
#     return data.get(token_id, {}).get('usd')

# # Define the command handler
# async def price_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not context.args:
#         await update.message.reply_text("Please provide a token name (e.g., /pricealert bitcoin).")
#         return

#     token_id = ' '.join(context.args).lower()
#     if token_id not in TOKEN_IDS:
#         await update.message.reply_text(f"Token not found. Please choose from: {', '.join(TOKEN_IDS)}")
#         return

#     price = get_price(token_id)
#     if price:
#         await update.message.reply_text(f"Current price of {token_id.capitalize()} is ${price}")
#     else:
#         await update.message.reply_text(f"Unable to fetch price for {token_id}.")

# # Main function to set up the bot
# def main():
#     app = ApplicationBuilder().token(TOKEN).build()

#     # Add command handler
#     app.add_handler(CommandHandler("pricealert", price_alert))

#     # Run the bot
#     print("Bot is running...")
#     app.run_polling()

# if __name__ == '__main__':
#     main()


# ****************************************** Version 2 ************************************

# import requests
# from telegram import Update, ReplyKeyboardMarkup
# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# # Telegram Bot Token
# TOKEN = ' '
# TOKEN_IDS = ['bitcoin', 'ethereum', 'cardano']

# # Function to get the price from CoinGecko
# def get_price(token_id):
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd'
#     response = requests.get(url)
#     data = response.json()
#     return data.get(token_id, {}).get('usd')

# # Define the command handler
# async def price_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Show the token options in a custom keyboard
#     keyboard = [[token.capitalize()] for token in TOKEN_IDS]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

#     await update.message.reply_text(
#         "Please choose a token to check its price:",
#         reply_markup=reply_markup
#     )

# # Handle token selection (message handler)
# async def handle_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     token_id = update.message.text.lower()

#     if token_id not in TOKEN_IDS:
#         await update.message.reply_text(f"Token not found. Please choose from: {', '.join(TOKEN_IDS)}")
#         return

#     price = get_price(token_id)
#     if price:
#         await update.message.reply_text(f"Current price of {token_id.capitalize()} is ${price}")
#     else:
#         await update.message.reply_text(f"Unable to fetch price for {token_id}.")

# # Main function to set up the bot
# def main():
#     app = ApplicationBuilder().token(TOKEN).build()

#     # Add command handler for '/pricealert' to show the token list
#     app.add_handler(CommandHandler("pricealert", price_alert))
    
#     # Add message handler for token selection
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_selection))

#     # Run the bot
#     print("Bot is running...")
#     app.run_polling()

# if __name__ == '__main__':
#     main()




# ****************************************** Version 3 --> showin price and Added alert for low and high ************************************


# import requests
# from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
# from apscheduler.schedulers.background import BackgroundScheduler
# import logging

# # Telegram Bot Token
# TOKEN = ' '
# TOKEN_IDS = ['bitcoin', 'ethereum', 'cardano']
# user_alerts = {}

# # Constants for ConversationHandler stages
# CHOOSING, TOKEN_SELECTION, LOW_PRICE, HIGH_PRICE = range(4)

# # Function to get the price from CoinGecko
# def get_price(token_id):
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd'
#     try:
#         response = requests.get(url)
#         data = response.json()
#         if response.status_code != 200:
#             print(f"Failed to fetch price for {token_id}: {data}")
#             return None
#         return data.get(token_id, {}).get('usd')
#     except Exception as e:
#         print(f"Error retrieving price for {token_id}: {e}")
#         return None

# # Start command handler
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     welcome_message = (
#         "Welcome to the Crypto Price Alert Bot!\n\n"
#         "Available commands:\n"
#         "/pricealert - Check current prices or set price alerts\n"
#         "/setalert - Set up price alerts\n"
#         "/viewalerts - View your current alerts\n"
#         "/help - Show this help message"
#     )
#     await update.message.reply_text(welcome_message)

# # Help command handler
# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await start(update, context)

# # View alerts command handler
# async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     chat_id = update.message.chat_id
#     if chat_id in user_alerts:
#         alert = user_alerts[chat_id]
#         await update.message.reply_text(
#             f"Your current alert for {alert['token'].capitalize()}:\n"
#             f"Low: ${alert['low_price']}\n"
#             f"High: ${alert['high_price']}"
#         )
#     else:
#         await update.message.reply_text("You don't have any active alerts.")

# # Define the command handler for /pricealert
# async def price_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[token.capitalize()] for token in TOKEN_IDS]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
#     await update.message.reply_text(
#         "Please choose a token to check its price:",
#         reply_markup=reply_markup
#     )
#     return CHOOSING

# # Handle token selection for price check
# async def handle_price_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     token_id = update.message.text.lower()
    
#     if token_id not in TOKEN_IDS:
#         await update.message.reply_text(
#             f"Invalid token. Please choose from: {', '.join(TOKEN_IDS)}",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         return ConversationHandler.END
    
#     price = get_price(token_id)
#     if price:
#         await update.message.reply_text(
#             f"Current price of {token_id.capitalize()} is ${price:,.2f}",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     else:
#         await update.message.reply_text(
#             f"Unable to fetch price for {token_id}.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     return ConversationHandler.END

# # Start the alert setup process
# async def set_alert_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[token.capitalize()] for token in TOKEN_IDS]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
#     await update.message.reply_text(
#         "Please choose a token to set a price alert:",
#         reply_markup=reply_markup
#     )
#     return TOKEN_SELECTION

# # Handle token selection for alert
# async def handle_alert_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     token_id = update.message.text.lower()
    
#     if token_id not in TOKEN_IDS:
#         await update.message.reply_text(
#             f"Invalid token. Please choose from: {', '.join(TOKEN_IDS)}",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         return ConversationHandler.END
    
#     context.user_data['selected_token'] = token_id
#     current_price = get_price(token_id)
    
#     await update.message.reply_text(
#         f"Current price of {token_id.capitalize()} is ${current_price:,.2f}\n"
#         f"Please enter your desired low price alert:",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     return LOW_PRICE

# # Handle the low price input
# async def handle_low_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         low_price = float(update.message.text)
#         context.user_data['low_price'] = low_price
        
#         await update.message.reply_text(f"Now, please enter your desired high price alert:")
#         return HIGH_PRICE
#     except ValueError:
#         await update.message.reply_text("Please enter a valid number for the low price.")
#         return LOW_PRICE

# # Handle the high price input
# async def handle_high_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         high_price = float(update.message.text)
#         token_id = context.user_data['selected_token']
#         low_price = context.user_data['low_price']
        
#         if high_price <= low_price:
#             await update.message.reply_text("High price must be greater than low price. Please enter a higher price:")
#             return HIGH_PRICE
        
#         user_alerts[update.message.chat_id] = {
#             'token': token_id,
#             'low_price': low_price,
#             'high_price': high_price
#         }
        
#         await update.message.reply_text(
#             f"Price alert set for {token_id.capitalize()}:\n"
#             f"Low: ${low_price:,.2f}\n"
#             f"High: ${high_price:,.2f}"
#         )
#         context.user_data.clear()
#         return ConversationHandler.END
#     except ValueError:
#         await update.message.reply_text("Please enter a valid number for the high price.")
#         return HIGH_PRICE

# # Function to check for price alerts
# def check_alerts(app):
#     for chat_id, alert in user_alerts.items():
#         token_id = alert['token']
#         current_price = get_price(token_id)
        
#         if current_price:
#             if current_price <= alert['low_price']:
#                 message = f"Price Alert! {token_id.capitalize()} is now ${current_price:,.2f}, below your low alert of ${alert['low_price']:,.2f}"
#                 app.bot.send_message(chat_id=chat_id, text=message)
#             elif current_price >= alert['high_price']:
#                 message = f"Price Alert! {token_id.capitalize()} is now ${current_price:,.2f}, above your high alert of ${alert['high_price']:,.2f}"
#                 app.bot.send_message(chat_id=chat_id, text=message)

# # Main function to set up the bot
# def main():
#     # Set up logging
#     logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#     logger = logging.getLogger(__name__)
    
#     # Initialize the bot
#     app = ApplicationBuilder().token(TOKEN).build()
    
#     # Price check conversation handler
#     price_check_handler = ConversationHandler(
#         entry_points=[CommandHandler('pricealert', price_alert)],
#         states={
#             CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_check)]
#         },
#         fallbacks=[]
#     )
    
#     # Alert setup conversation handler
#     alert_setup_handler = ConversationHandler(
#         entry_points=[CommandHandler('setalert', set_alert_start)],
#         states={
#             TOKEN_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_alert_token)],
#             LOW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_low_price)],
#             HIGH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_high_price)]
#         },
#         fallbacks=[]
#     )
    
#     # Add all handlers
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("help", help_command))
#     app.add_handler(CommandHandler("viewalerts", view_alerts))
#     app.add_handler(price_check_handler)
#     app.add_handler(alert_setup_handler)
    
#     # Set up the price check scheduler
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(lambda: check_alerts(app), 'interval', minutes=1)
#     scheduler.start()
    
#     # Start the bot
#     print("Bot is running...")
#     app.run_polling()

# if __name__ == '__main__':
#     main()


# ****************************************** Version 4 (Updated version) --> showin price and Added alert for low and high ************************************


# import requests
# from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
# from apscheduler.schedulers.background import BackgroundScheduler
# import logging
# import asyncio

# # Telegram Bot Token
# TOKEN = ' '

# # Token mappings with proper CoinGecko IDs
# TOKEN_IDS = {
#     'Bitcoin': 'bitcoin',
#     'Ethereum': 'ethereum',
#     'Cardano': 'cardano',
#     'Solana': 'solana',
#     'Binance': 'binancecoin',
#     'Dogecoin': 'dogecoin'
# }

# user_alerts = {}

# # Constants for ConversationHandler stages
# CHOOSING, TOKEN_SELECTION, LOW_PRICE, HIGH_PRICE = range(4)

# def get_price(token_id):
#     """Get cryptocurrency price from CoinGecko API."""
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd'
#     headers = {
#         'accept': 'application/json',
#         'User-Agent': 'Mozilla/5.0'
#     }
    
#     try:
#         response = requests.get(url, headers=headers)
#         logging.info(f"API Response for {token_id}: Status={response.status_code}")
        
#         if response.status_code == 429:  # Rate limit
#             logging.warning("Rate limit hit, waiting before retry")
#             return None
            
#         data = response.json()
#         if response.status_code != 200:
#             logging.error(f"Failed to fetch price for {token_id}: {data}")
#             return None
            
#         price = data.get(token_id, {}).get('usd')
#         logging.info(f"Price fetched for {token_id}: ${price}")
#         return price
        
#     except Exception as e:
#         logging.error(f"Error retrieving price for {token_id}: {e}")
#         return None

# def get_keyboard():
#     """Create keyboard with token options."""
#     keyboard = [[token] for token in TOKEN_IDS.keys()]
#     keyboard.append(["Cancel"])
#     return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Start command handler."""
#     welcome_message = (
#         "🚀 Welcome to the Crypto Price Alert Bot!\n\n"
#         "Available commands:\n"
#         "📊 /price - Check current cryptocurrency prices\n"
#         "🔔 /alert - Set up price alerts\n"
#         "📋 /viewalerts - View your current alerts\n"
#         "❌ /deletealerts - Delete your alerts\n"
#         "ℹ️ /help - Show this help message"
#     )
#     await update.message.reply_text(welcome_message)

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Help command handler."""
#     await start(update, context)

# async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """View alerts command handler."""
#     chat_id = update.message.chat_id
#     if chat_id in user_alerts and user_alerts[chat_id]:
#         alerts_text = "Your active price alerts:\n\n"
#         for i, alert in enumerate(user_alerts[chat_id], 1):
#             alerts_text += (
#                 f"{i}. {alert['token']}\n"
#                 f"   Low: ${alert['low_price']:,.2f}\n"
#                 f"   High: ${alert['high_price']:,.2f}\n\n"
#             )
#         await update.message.reply_text(alerts_text)
#     else:
#         await update.message.reply_text("You don't have any active alerts.")

# async def delete_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Delete alerts command handler."""
#     chat_id = update.message.chat_id
#     if chat_id in user_alerts:
#         user_alerts[chat_id] = []
#         await update.message.reply_text("All your alerts have been deleted.")
#     else:
#         await update.message.reply_text("You don't have any alerts to delete.")

# async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Price check command handler."""
#     await update.message.reply_text(
#         "Select a cryptocurrency to check its price:",
#         reply_markup=get_keyboard()
#     )
#     return CHOOSING

# async def handle_price_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle price check response."""
#     if update.message.text == "Cancel":
#         await update.message.reply_text(
#             "Operation cancelled.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         return ConversationHandler.END

#     token_name = update.message.text
#     token_id = TOKEN_IDS.get(token_name)
    
#     if not token_id:
#         await update.message.reply_text(
#             "Invalid selection. Please choose from the keyboard.",
#             reply_markup=get_keyboard()
#         )
#         return CHOOSING

#     await update.message.reply_text("Checking price... Please wait.")
    
#     price = get_price(token_id)
#     if price:
#         await update.message.reply_text(
#             f"💰 Current price of {token_name}:\n${price:,.2f}",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     else:
#         await update.message.reply_text(
#             "Sorry, couldn't fetch the price. Please try again later.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     return ConversationHandler.END

# async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Alert setup command handler."""
#     await update.message.reply_text(
#         "Select a cryptocurrency to set an alert for:",
#         reply_markup=get_keyboard()
#     )
#     return TOKEN_SELECTION

# async def handle_alert_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle token selection for alert."""
#     if update.message.text == "Cancel":
#         await update.message.reply_text(
#             "Operation cancelled.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         return ConversationHandler.END

#     token_name = update.message.text
#     token_id = TOKEN_IDS.get(token_name)
    
#     if not token_id:
#         await update.message.reply_text(
#             "Invalid selection. Please choose from the keyboard.",
#             reply_markup=get_keyboard()
#         )
#         return TOKEN_SELECTION

#     context.user_data['token'] = token_name
#     context.user_data['token_id'] = token_id
    
#     price = get_price(token_id)
#     if price:
#         await update.message.reply_text(
#             f"Current price of {token_name} is ${price:,.2f}\n"
#             f"Enter your desired low price alert:",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     else:
#         await update.message.reply_text(
#             f"Enter your desired low price alert for {token_name}:",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     return LOW_PRICE

# async def handle_low_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle low price input."""
#     try:
#         price = float(update.message.text)
#         if price <= 0:
#             await update.message.reply_text("Please enter a positive number.")
#             return LOW_PRICE
            
#         context.user_data['low_price'] = price
#         await update.message.reply_text("Now enter your desired high price alert:")
#         return HIGH_PRICE
        
#     except ValueError:
#         await update.message.reply_text("Please enter a valid number.")
#         return LOW_PRICE

# async def handle_high_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle high price input."""
#     try:
#         high_price = float(update.message.text)
#         low_price = context.user_data['low_price']
        
#         if high_price <= low_price:
#             await update.message.reply_text(
#                 "High price must be greater than low price. Please enter a higher price:"
#             )
#             return HIGH_PRICE

#         chat_id = update.message.chat_id
#         if chat_id not in user_alerts:
#             user_alerts[chat_id] = []
            
#         alert = {
#             'token': context.user_data['token'],
#             'token_id': context.user_data['token_id'],
#             'low_price': low_price,
#             'high_price': high_price
#         }
        
#         user_alerts[chat_id].append(alert)
        
#         await update.message.reply_text(
#             f"✅ Alert set successfully!\n\n"
#             f"Token: {alert['token']}\n"
#             f"Low Price: ${low_price:,.2f}\n"
#             f"High Price: ${high_price:,.2f}",
#             reply_markup=ReplyKeyboardRemove()
#         )
        
#         context.user_data.clear()
#         return ConversationHandler.END
        
#     except ValueError:
#         await update.message.reply_text("Please enter a valid number.")
#         return HIGH_PRICE

# def check_alerts(app):
#     """Check price alerts and notify users."""
#     for chat_id, alerts in user_alerts.items():
#         for alert in alerts:
#             current_price = get_price(alert['token_id'])
#             if not current_price:
#                 continue
                
#             if current_price <= alert['low_price']:
#                 asyncio.run(app.bot.send_message(
#                     chat_id=chat_id,
#                     text=f"⚠️ Low Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
#                          f"Below your alert of ${alert['low_price']:,.2f}"
#                 ))
                
#             elif current_price >= alert['high_price']:
#                 asyncio.run(app.bot.send_message(
#                     chat_id=chat_id,
#                     text=f"⚠️ High Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
#                          f"Above your alert of ${alert['high_price']:,.2f}"
#                 ))

# def main():
#     """Initialize and run the bot."""
#     # Set up logging
#     logging.basicConfig(
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         level=logging.INFO
#     )

#     # Initialize the bot
#     app = ApplicationBuilder().token(TOKEN).build()

#     # Add command handlers
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("help", help_command))
#     app.add_handler(CommandHandler("viewalerts", view_alerts))
#     app.add_handler(CommandHandler("deletealerts", delete_alerts))

#     # Price check conversation handler
#     price_handler = ConversationHandler(
#         entry_points=[CommandHandler('price', price_command)],
#         states={
#             CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_check)]
#         },
#         fallbacks=[MessageHandler(filters.Regex("^Cancel$"), lambda u, c: ConversationHandler.END)]
#     )

#     # Alert setup conversation handler
#     alert_handler = ConversationHandler(
#         entry_points=[CommandHandler('alert', alert_command)],
#         states={
#             TOKEN_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_alert_token)],
#             LOW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_low_price)],
#             HIGH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_high_price)]
#         },
#         fallbacks=[MessageHandler(filters.Regex("^Cancel$"), lambda u, c: ConversationHandler.END)]
#     )

#     app.add_handler(price_handler)
#     app.add_handler(alert_handler)

#     # Set up the price check scheduler
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(lambda: check_alerts(app), 'interval', minutes=1)
#     scheduler.start()

#     # Start the bot
#     print("Bot is running...")
#     app.run_polling()

# if __name__ == '__main__':
#     main()

# ****************************************** Version 5 (Final version) --> showin price and Added alert for low and high ************************************


import os 
from dotenv import load_dotenv
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import asyncio 


# Load environment variables
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Token mappings with proper CoinGecko IDs
TOKEN_IDS = {
    # Mapping based on binance api 
    'Bitcoin': 'BTCUSDT',
    'Ethereum': 'ETHUSDT',
    'Solana': 'SOLUSDT',
    "OM":"OMUSDT",
    "SUI":"SUIUSDT"
        # Mapping based on coingecko api 
    # 'Bitcoin': 'bitcoin',
    # 'Ethereum': 'ethereum',
    # 'Solana': 'solana',
    # "OM":"mantra-dao",
}

user_alerts = {}

# # Constants for ConversationHandler stages
# CHOOSING, TOKEN_SELECTION, LOW_PRICE, HIGH_PRICE = range(4)

# Add this new constant for delete confirmation state
CHOOSING, TOKEN_SELECTION, LOW_PRICE, HIGH_PRICE, DELETE_CONFIRMATION = range(5)


def get_main_menu_keyboard():
    """Create the main menu keyboard."""
    keyboard = [
        ["💰 Check Price", "⚠️ Set Alert"],
        ["📊 View Alerts", "❌ Delete Alerts"],
        ["ℹ️ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_token_keyboard():
    """Create keyboard with token options."""
    keyboard = [
        ["Bitcoin", "Ethereum"],
        ["Solana","OM","SUI"],
        ["🔙 Back to Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_price(token_id):
    """Get cryptocurrency price from CoinGecko API."""
    # url = f'https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd'
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={token_id}'
    headers = {
        'accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    logging.info(f"********************API Hitting in Get Price func*******************:- {url}")

    try:
        response = requests.get(url, headers=headers)
        logging.info(f"Binance API Response for {token_id}: Status={response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch price for {token_id}: {response.text}")
            return None
            
        data = response.json()
        if 'price' not in data:
            logging.error(f"Invalid response format for {token_id}: {data}")
            return None
            
        price = float(data['price'])
        logging.info(f"Price fetched for {token_id}: ${price:,.2f}")
        return price
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error retrieving price for {token_id}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing price data for {token_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving price for {token_id}: {e}")
        return None
    
    # try:
    #     response = requests.get(url, headers=headers)
    #     logging.info(f"API Response for {token_id}: Status={response.status_code}")
        
    #     if response.status_code == 429:  # Rate limit
    #         logging.warning("Rate limit hit, waiting before retry")
    #         return None
            
    #     data = response.json()
    #     if response.status_code != 200:
    #         logging.error(f"Failed to fetch price for {token_id}: {data}")
    #         return None
            
    #     price = data.get(token_id, {}).get('usd')
    #     logging.info(f"Price fetched for {token_id}: ${price}")
    #     return price
        
    # except Exception as e:
    #     logging.error(f"Error retrieving price for {token_id}: {e}")
    #     return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user_name = update.message.from_user.first_name
    welcome_message = (
        f"👋 Welcome {user_name} to the Crypto Price Alert Bot!\n\n"
        "Choose an option from the menu below:\n\n"
        "💰 Check Price - Get current cryptocurrency prices\n"
        "⚠️ Set Alert - Create price alerts\n"
        "📊 View Alerts - See your active alerts\n"
        "❌ Delete Alerts - Remove all alerts\n"
        "ℹ️ Help - Show this message"
    )
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )
    return CHOOSING

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler."""
    await start(update, context)

# async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle main menu selections."""
#     choice = update.message.text

#     if choice == "💰 Check Price":
#         context.user_data['action'] = 'check_price' 
#         await update.message.reply_text(
#             "Select a cryptocurrency:",
#             reply_markup=get_token_keyboard()
#         )
#         return TOKEN_SELECTION
        
#     elif choice == "⚠️ Set Alert":
#         context.user_data['action'] = 'set_alert' 
#         await update.message.reply_text(
#             "Select a cryptocurrency for the alert:",
#             reply_markup=get_token_keyboard()
#         )
#         return TOKEN_SELECTION
        
#     elif choice == "📊 View Alerts":
#         await view_alerts(update, context)
#         return CHOOSING
        
#     elif choice == "❌ Delete Alerts":
#         await delete_alerts(update, context)
#         return CHOOSING
        
#     elif choice == "ℹ️ Help":
#         await help_command(update, context)
#         return CHOOSING
    
#     return CHOOSING


async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections."""
    choice = update.message.text

    if choice == "💰 Check Price":
        context.user_data['action'] = 'check_price' 
        await update.message.reply_text(
            "Select a cryptocurrency:",
            reply_markup=get_token_keyboard()
        )
        return TOKEN_SELECTION
        
    elif choice == "⚠️ Set Alert":
        context.user_data['action'] = 'set_alert' 
        await update.message.reply_text(
            "Select a cryptocurrency for the alert:",
            reply_markup=get_token_keyboard()
        )
        return TOKEN_SELECTION
        
    elif choice == "📊 View Alerts":
        await view_alerts(update, context)
        return CHOOSING
        
    elif choice == "❌ Delete Alerts":
        return await start_delete_process(update, context)
        
    elif choice == "ℹ️ Help":
        await help_command(update, context)
        return CHOOSING
    
    return CHOOSING


# Add new functions for the delete process
async def start_delete_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the delete alert process."""
    chat_id = update.message.chat_id
    
    if chat_id not in user_alerts or not user_alerts[chat_id]:
        await update.message.reply_text(
            "You don't have any alerts to delete.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

    # Show all alerts with numbers
    alerts_text = "Select the alert number you want to delete:\n\n"
    for i, alert in enumerate(user_alerts[chat_id], 1):
        alerts_text += (
            f"#{i}\n"
            f"Token: {alert['token']}\n"
            f"Low: ${alert['low_price']:,.2f}\n"
            f"High: ${alert['high_price']:,.2f}\n\n"
        )
    
    # Create keyboard with alert numbers and back button
    keyboard = []
    # Create rows with 3 numbers each
    num_alerts = len(user_alerts[chat_id])
    for i in range(0, num_alerts, 3):
        row = [str(j) for j in range(i + 1, min(i + 4, num_alerts + 1))]
        keyboard.append(row)
    
    keyboard.append(["Delete All"])
    keyboard.append(["🔙 Back to Menu"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(alerts_text, reply_markup=reply_markup)
    context.user_data['action'] = 'delete_alert'  # Set the context for delete action
    return DELETE_CONFIRMATION



# async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """View alerts command handler."""
#     chat_id = update.message.chat_id
#     if chat_id in user_alerts and user_alerts[chat_id]:
#         alerts_text = "Your active price alerts:\n\n"
#         for i, alert in enumerate(user_alerts[chat_id], 1):
#             alerts_text += (
#                 f"{i}. {alert['token']}\n"
#                 f"   Low: ${alert['low_price']:,.2f}\n"
#                 f"   High: ${alert['high_price']:,.2f}\n\n"
#             )
#         await update.message.reply_text(
#             alerts_text,
#             reply_markup=get_main_menu_keyboard()
#         )
#     else:
#         await update.message.reply_text(
#             "You don't have any active alerts.",
#             reply_markup=get_main_menu_keyboard()
#         )

async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View alerts command handler with numbered list."""
    chat_id = update.message.chat_id
    if chat_id in user_alerts and user_alerts[chat_id]:
        alerts_text = "Your active price alerts:\n\n"
        for i, alert in enumerate(user_alerts[chat_id], 1):
            alerts_text += (
                f"📍 Alert #{i}\n"
                f"Token: {alert['token']}\n"
                f"Low: ${alert['low_price']:,.2f}\n"
                f"High: ${alert['high_price']:,.2f}\n\n"
            )
        await update.message.reply_text(
            alerts_text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "You don't have any active alerts.",
            reply_markup=get_main_menu_keyboard()
        )

# async def delete_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Delete alerts command handler."""
#     chat_id = update.message.chat_id
#     if chat_id in user_alerts:
#         user_alerts[chat_id] = []
#         await update.message.reply_text(
#             "All your alerts have been deleted.",
#             reply_markup=get_main_menu_keyboard()
#         )
#     else:
#         await update.message.reply_text(
#             "You don't have any alerts to delete.",
#             reply_markup=get_main_menu_keyboard()
#         )

async def delete_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete alerts command handler with selection."""
    chat_id = update.message.chat_id
    
    if chat_id not in user_alerts or not user_alerts[chat_id]:
        await update.message.reply_text(
            "You don't have any alerts to delete.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

    # Show all alerts with numbers
    alerts_text = "Select the alert number you want to delete:\n\n"
    for i, alert in enumerate(user_alerts[chat_id], 1):
        alerts_text += (
            f"#{i}\n"
            f"Token: {alert['token']}\n"
            f"Low: ${alert['low_price']:,.2f}\n"
            f"High: ${alert['high_price']:,.2f}\n\n"
        )
    
    # Create keyboard with alert numbers and back button
    keyboard = [[str(i)] for i in range(1, len(user_alerts[chat_id]) + 1)]
    keyboard.append(["Delete All"])
    keyboard.append(["🔙 Back to Menu"])
    
    await update.message.reply_text(
        alerts_text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DELETE_CONFIRMATION

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the deletion confirmation."""
    choice = update.message.text
    chat_id = update.message.chat_id

    if choice == "🔙 Back to Menu":
        await update.message.reply_text(
            "Returned to main menu.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

    if choice == "Delete All":
        user_alerts[chat_id] = []
        await update.message.reply_text(
            "All alerts have been deleted.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

    try:
        alert_index = int(choice) - 1
        if chat_id in user_alerts and 0 <= alert_index < len(user_alerts[chat_id]):
            deleted_alert = user_alerts[chat_id].pop(alert_index)
            await update.message.reply_text(
                f"✅ Alert deleted successfully!\n\n"
                f"Deleted alert for {deleted_alert['token']}\n"
                f"Low: ${deleted_alert['low_price']:,.2f}\n"
                f"High: ${deleted_alert['high_price']:,.2f}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Invalid alert number. Please select a valid number.",
                reply_markup=get_main_menu_keyboard()
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please select a number from the list.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return CHOOSING

async def handle_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle token selection."""
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    token_name = update.message.text
    token_id = TOKEN_IDS.get(token_name)
    
    if not token_id:
        await update.message.reply_text(
            "Invalid selection. Please choose from the keyboard.",
            reply_markup=get_token_keyboard()
        )
        return TOKEN_SELECTION

    # Store token info
    context.user_data['token'] = token_name
    context.user_data['token_id'] = token_id

    # Check if this is a price check or alert setting
    action = context.user_data.get('action')

    if action == 'set_alert':
        # Setting an alert
        price = get_price(token_id)
        if price:
            await update.message.reply_text(
                f"Current price of {token_name} is ${price:,.2f}\n"
                f"Enter your desired low price alert:",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                f"Enter your desired low price alert for {token_name}:",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
            )
        return LOW_PRICE
    else:
        # Price check
        await update.message.reply_text("Checking price... Please wait.")
        price = get_price(token_id)
        if price:
            await update.message.reply_text(
                f"💰 Current price of {token_name}:\n${price:,.2f}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "Sorry, couldn't fetch the price. Please try again later.",
                reply_markup=get_main_menu_keyboard()
            )
        return CHOOSING

async def handle_low_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle low price input."""
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    try:
        price = float(update.message.text)
        if price <= 0:
            await update.message.reply_text(
                "Please enter a positive number.",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
            )
            return LOW_PRICE
            
        context.user_data['low_price'] = price
        await update.message.reply_text(
            "Now enter your desired high price alert:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return HIGH_PRICE
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return LOW_PRICE

async def handle_high_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle high price input."""
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    try:
        high_price = float(update.message.text)
        low_price = context.user_data['low_price']
        
        if high_price <= low_price:
            await update.message.reply_text(
                "High price must be greater than low price. Please enter a higher price:",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
            )
            return HIGH_PRICE

        chat_id = update.message.chat_id
        if chat_id not in user_alerts:
            user_alerts[chat_id] = []
            
        alert = {
            'token': context.user_data['token'],
            'token_id': context.user_data['token_id'],
            'low_price': low_price,
            'high_price': high_price
        }
        
        user_alerts[chat_id].append(alert)
        
        await update.message.reply_text(
            f"✅ Alert set successfully!\n\n"
            f"Token: {alert['token']}\n"
            f"Low Price: ${low_price:,.2f}\n"
            f"High Price: ${high_price:,.2f}",
            reply_markup=get_main_menu_keyboard()
        )
        
        context.user_data.clear()
        return CHOOSING
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return HIGH_PRICE

def check_alerts(app):
    """Check price alerts and notify users with a single API request."""
    if not user_alerts:  # If no alerts exist
        return
        
    # Collect all unique symbols to check
    symbols_to_check = set()
    for alerts in user_alerts.values():
        for alert in alerts:
            symbol = alert['token_id'].upper()  # Convert to Binance format
            symbols_to_check.add(symbol)
    
    if not symbols_to_check:
        return
        
    # Create URL for batch price request
    symbols_param = str(list(symbols_to_check)).replace("'", '"').replace(" ", "")  # Convert to JSON format
    url = f'https://api.binance.com/api/v3/ticker/price?symbols={symbols_param}'
    
    headers = {
        'accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    logging.info(f"******************** API Hitting in check alert func ********************:-{url}")
    try:
        # Fetch all prices in one request
        response = requests.get(url, headers=headers)
        logging.info(f"Batch API Response Status={response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch prices: {response.text}")
            return
            
        data = response.json()
        
        # Create price lookup dictionary
        prices = {item['symbol']: float(item['price']) for item in data}
        
        # Check alerts using fetched prices
        for chat_id, alerts in user_alerts.items():
            for alert in alerts:
                symbol = alert['token_id'].upper()
                current_price = prices.get(symbol)
                
                if not current_price:
                    continue
                    
                if current_price <= alert['low_price']:
                    asyncio.run(app.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Low Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                             f"Below your alert of ${alert['low_price']:,.2f}"
                    ))
                    
                elif current_price >= alert['high_price']:
                    asyncio.run(app.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ High Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                             f"Above your alert of ${alert['high_price']:,.2f}"
                    ))
                    
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error retrieving prices: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing price data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in check_alerts: {e}")


                # Keep-alive function

# def main():
#     """Initialize and run the bot."""
#     # Set up logging
#     logging.basicConfig(
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         filename='botAlert.log',
#         level=logging.INFO
#     )

#     # Initialize the bot
#     app = ApplicationBuilder().token(TOKEN).build()

#     # Create conversation handler
#     conv_handler = ConversationHandler(
#         entry_points=[
#             CommandHandler("start", start),
#             CommandHandler("help", help_command)
#         ],
#         states={
#             CHOOSING: [
#                 MessageHandler(
#                     filters.TEXT & ~filters.COMMAND,
#                     handle_menu_choice
#                 )
#             ],
#             TOKEN_SELECTION: [
#                 MessageHandler(
#                     filters.TEXT & ~filters.COMMAND,
#                     handle_token_selection
#                 )
#             ],
#             LOW_PRICE: [
#                 MessageHandler(
#                     filters.TEXT & ~filters.COMMAND,
#                     handle_low_price
#                 )
#             ],
#             HIGH_PRICE: [
#                 MessageHandler(
#                     filters.TEXT & ~filters.COMMAND,
#                     handle_high_price
#                 )
#             ],
#             DELETE_CONFIRMATION: [
#                 MessageHandler(
#                     filters.TEXT & ~filters.COMMAND,
#                     handle_delete_confirmation
#                 )
#             ]
#         },
#         fallbacks=[
#             CommandHandler("start", start),
#             CommandHandler("help", help_command)
#         ]
#     )

#     # Add the conversation handler
#     app.add_handler(conv_handler)

#     # Set up the price check scheduler
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(lambda: check_alerts(app), 'interval', minutes=1)
#     scheduler.start()

#     # Start the bot
#     print("Bot is running...")
#     app.run_polling()



# Update your main function's conversation handler:
def main():
    """Initialize and run the bot."""
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='botAlert.log',
        level=logging.INFO
    )

    # Initialize the bot
    app = ApplicationBuilder().token(TOKEN).build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help_command)
        ],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_menu_choice
                )
            ],
            TOKEN_SELECTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_token_selection
                )
            ],
            LOW_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_low_price
                )
            ],
            HIGH_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_high_price
                )
            ],
            DELETE_CONFIRMATION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_delete_confirmation
                )
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("help", help_command)
        ],
        name='my_conversation',
        persistent=False
    )

    # Add the conversation handler
    app.add_handler(conv_handler)

    # Set up the price check scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_alerts(app), 'interval', minutes=1)
    scheduler.start()

    # Start the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()