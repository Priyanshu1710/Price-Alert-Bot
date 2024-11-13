
# ****************************************** Version 1.0.1  --> Price Alert Bot ************************************

import os 
from dotenv import load_dotenv
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import asyncio
import json


# Load environment variables
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Token mappings with proper CoinGecko IDs
DEFAULT_TOKENS = {
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

# Store user-specific custom tokens
user_custom_tokens = {}  # Format: {user_id: {token_name: symbol}}


# Add new state for token deletion
CHOOSING, TOKEN_SELECTION, LOW_PRICE, HIGH_PRICE, DELETE_CONFIRMATION, ADD_TOKEN_NAME, ADD_TOKEN_SYMBOL, DELETE_TOKEN = range(8)

def get_main_menu_keyboard():
    """Create the main menu keyboard."""
    keyboard = [
        ["💰 Check Price", "⚠️ Set Alert"],
        ["📊 View Alerts", "❌ Delete Alerts"],
        ["➕ Add Custom Token", "🗑 Delete Token"],
        ["ℹ️ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_tokens(user_id):
    """Get combined default and user-specific tokens."""
    user_tokens = DEFAULT_TOKENS.copy()
    if user_id in user_custom_tokens:
        user_tokens.update(user_custom_tokens[user_id])
    return user_tokens

def save_custom_tokens():
    """Save user-specific custom tokens to a file."""
    try:
        with open('user_custom_tokens.json', 'w') as f:
            json.dump(user_custom_tokens, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving custom tokens: {e}")

def load_custom_tokens():
    """Load user-specific custom tokens from file."""
    global user_custom_tokens
    try:
        if os.path.exists('user_custom_tokens.json'):
            with open('user_custom_tokens.json', 'r') as f:
                user_custom_tokens = json.load(f)
    except Exception as e:
        logging.error(f"Error loading custom tokens: {e}")

def get_token_keyboard(user_id):
    """Create keyboard with token options including user-specific tokens."""
    user_tokens = get_user_tokens(user_id)
    # Create rows of 3 tokens each
    token_rows = []
    tokens = list(user_tokens.keys())
    for i in range(0, len(tokens), 3):
        token_rows.append(tokens[i:i+3])
    token_rows.append(["🔙 Back to Menu"])
    return ReplyKeyboardMarkup(token_rows, resize_keyboard=True)

# Add these new functions for custom token handling
async def start_add_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of adding a custom token."""
    await update.message.reply_text(
        "Please enter the display name for your token (e.g., Bitcoin):",
        reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
    )
    return ADD_TOKEN_NAME

# Also update any other functions that use get_token_keyboard
async def handle_token_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the custom token name input."""
    user_id = update.effective_user.id  # Get user ID
    
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    token_name = update.message.text
    user_tokens = get_user_tokens(user_id)  # Get user-specific tokens
    
    if token_name in user_tokens:
        await update.message.reply_text(
            f"Token name '{token_name}' already exists. Please choose a different name.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return ADD_TOKEN_NAME

    context.user_data['custom_token_name'] = token_name
    await update.message.reply_text(
        f"Now enter the Binance trading symbol for {token_name} (e.g., BTCUSDT):\n\n"
        "Make sure to:\n"
        "1. Use uppercase letters\n"
        "2. Include USDT suffix\n"
        "3. Check Binance for correct symbol",
        reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
    )
    return ADD_TOKEN_SYMBOL

async def handle_token_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the Binance symbol input and validate it."""
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    user_id = update.effective_user.id
    symbol = update.message.text.upper()
    token_name = context.user_data.get('custom_token_name')

    # Validate the symbol with Binance API
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    headers = {
        'accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Initialize user's custom tokens if not exists
            if user_id not in user_custom_tokens:
                user_custom_tokens[user_id] = {}
            
            # Add to user's custom tokens
            user_custom_tokens[user_id][token_name] = symbol
            
            # Save to file
            save_custom_tokens()
            
            await update.message.reply_text(
                f"✅ Successfully added custom token:\n"
                f"Name: {token_name}\n"
                f"Symbol: {symbol}\n\n"
                f"You can now use this token for price checks and alerts!",
                reply_markup=get_main_menu_keyboard()
            )
            
            return CHOOSING
        else:
            await update.message.reply_text(
                f"❌ Invalid symbol. '{symbol}' was not found on Binance.\n"
                "Please check the symbol and try again.",
                reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
            )
            return ADD_TOKEN_SYMBOL
            
    except Exception as e:
        logging.error(f"Error validating symbol: {e}")
        await update.message.reply_text(
            "Error validating symbol. Please try again.",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return ADD_TOKEN_SYMBOL

async def handle_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle token selection."""
    user_id = update.effective_user.id  # Get user ID
    
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    token_name = update.message.text
    user_tokens = get_user_tokens(user_id)  # Get user-specific tokens
    token_id = user_tokens.get(token_name)
    
    if not token_id:
        await update.message.reply_text(
            "Invalid selection. Please choose from the keyboard.",
            reply_markup=get_token_keyboard(user_id)  # Pass user_id
        )
        return TOKEN_SELECTION

    # Store token info
    context.user_data['token'] = token_name
    context.user_data['token_id'] = token_id

    # Check if this is a price check or alert setting
    action = context.user_data.get('action')

    if action == 'set_alert':
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

async def start_delete_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of deleting a token."""
    user_id = update.effective_user.id
    
    if user_id not in user_custom_tokens or not user_custom_tokens[user_id]:
        await update.message.reply_text(
            "You don't have any custom tokens to delete.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING
    
    # Get user's custom tokens
    custom_tokens = user_custom_tokens[user_id]
    
    # Create message showing deletable tokens
    token_list = "Select a token to delete:\n\n"
    for i, (token_name, symbol) in enumerate(custom_tokens.items(), 1):
        token_list += f"#{i} {token_name} ({symbol})\n"
    
    # Create keyboard with token numbers
    keyboard = []
    num_tokens = len(custom_tokens)
    for i in range(0, num_tokens, 3):
        row = [str(j) for j in range(i + 1, min(i + 4, num_tokens + 1))]
        keyboard.append(row)
    keyboard.append(["🔙 Back to Menu"])
    
    context.user_data['custom_tokens'] = list(custom_tokens.items())
    
    await update.message.reply_text(
        token_list,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DELETE_TOKEN

async def handle_token_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the token deletion process."""
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING
    
    user_id = update.effective_user.id
    
    try:
        index = int(update.message.text) - 1
        custom_tokens = context.user_data.get('custom_tokens', [])
        
        if 0 <= index < len(custom_tokens):
            token_name, symbol = custom_tokens[index]
            
            # Remove from user's custom tokens
            if user_id in user_custom_tokens and token_name in user_custom_tokens[user_id]:
                del user_custom_tokens[user_id][token_name]
                
                # Save updated tokens
                save_custom_tokens()
                
                await update.message.reply_text(
                    f"✅ Successfully deleted token:\n"
                    f"Name: {token_name}\n"
                    f"Symbol: {symbol}",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await update.message.reply_text(
                    "Token not found in your custom list.",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await update.message.reply_text(
                "Invalid selection. Please choose a valid number.",
                reply_markup=get_main_menu_keyboard()
            )
    except ValueError:
        await update.message.reply_text(
            "Invalid input. Please select a number from the list.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return CHOOSING

# Price fetching function
def get_price(token_id):
    """Get cryptocurrency price from Binance API."""
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
        "➕ Add Custom Token - Add your own tokens\n"
        "🗑 Delete Token - Remove custom tokens\n"
        "ℹ️ Help - Show this message"
    )
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )
    return CHOOSING

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler."""
    user_id = update.effective_user.id
    await start(update, context)

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections."""
    choice = update.message.text
    user_id = update.effective_user.id  # Get user ID

    if choice == "💰 Check Price":
        context.user_data['action'] = 'check_price' 
        await update.message.reply_text(
            "Select a cryptocurrency:",
            reply_markup=get_token_keyboard(user_id)  # Pass user_id
        )
        return TOKEN_SELECTION
        
    elif choice == "⚠️ Set Alert":
        context.user_data['action'] = 'set_alert' 
        await update.message.reply_text(
            "Select a cryptocurrency for the alert:",
            reply_markup=get_token_keyboard(user_id)  # Pass user_id
        )
        return TOKEN_SELECTION
        
    elif choice == "📊 View Alerts":
        await view_alerts(update, context)
        return CHOOSING
        
    elif choice == "❌ Delete Alerts":
        return await start_delete_process(update, context)
        
    elif choice == "➕ Add Custom Token":
        return await start_add_token(update, context)
        
    elif choice == "🗑 Delete Token":
        return await start_delete_token(update, context)
        
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

# Helper function to validate Binance symbol
async def validate_binance_symbol(symbol):
    """Validate if a symbol exists on Binance."""
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    headers = {
        'accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except:
        return False

# Update view_alerts function
async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View alerts command handler."""
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    
    if chat_id in user_alerts and user_alerts[chat_id]:
        alerts_text = "Your active price alerts:\n\n"
        user_tokens = get_user_tokens(user_id)
        
        for i, alert in enumerate(user_alerts[chat_id], 1):
            token_name = alert['token']
            token_id = user_tokens.get(token_name)
            
            if token_id:  # Only show alerts for tokens that still exist
                alerts_text += (
                    f"{i}. {alert['token']}\n"
                    f"   Low: ${alert['low_price']:,.2f}\n"
                    f"   High: ${alert['high_price']:,.2f}\n\n"
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
    user_id = update.effective_user.id
    
    if update.message.text == "🔙 Back to Menu":
        await start(update, context)
        return CHOOSING

    token_name = update.message.text
    user_tokens = get_user_tokens(user_id)
    token_id = user_tokens.get(token_name)
    
    if not token_id:
        await update.message.reply_text(
            "Invalid selection. Please choose from the keyboard.",
            reply_markup=get_token_keyboard(user_id)
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

async def check_alerts(app):
    """Check price alerts and notify users with a single API request."""
    if not user_alerts:  # If no alerts exist
        return
        
    # Collect all unique symbols to check
    symbols_to_check = set()
    user_alert_mapping = {}  # Keep track of which symbols belong to which alerts
    
    for chat_id, alerts in user_alerts.items():
        for alert in alerts:
            symbol = alert['token_id']
            symbols_to_check.add(symbol)
            if symbol not in user_alert_mapping:
                user_alert_mapping[symbol] = []
            user_alert_mapping[symbol].append((chat_id, alert))
    
    if not symbols_to_check:
        return
        
    # Create URL for batch price request
    symbols_param = str(list(symbols_to_check)).replace("'", '"').replace(" ", "")
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
        messages_to_send = []
        for symbol, price_data in prices.items():
            if symbol in user_alert_mapping:
                for chat_id, alert in user_alert_mapping[symbol]:
                    current_price = price_data
                    
                    if current_price <= alert['low_price']:
                        messages_to_send.append({
                            'chat_id': chat_id,
                            'text': f"⚠️ Low Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                                   f"Below your alert of ${alert['low_price']:,.2f}"
                        })
                    elif current_price >= alert['high_price']:
                        messages_to_send.append({
                            'chat_id': chat_id,
                            'text': f"⚠️ High Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                                   f"Above your alert of ${alert['high_price']:,.2f}"
                        })
        
        # Send all messages
        for msg in messages_to_send:
            try:
                asyncio.run(app.bot.send_message(
                    chat_id=msg['chat_id'],
                    text=msg['text']
                ))
            except Exception as e:
                logging.error(f"Error sending alert to {msg['chat_id']}: {e}")
                    
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error retrieving prices: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing price data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in check_alerts: {e}")

def main():
    """Initialize and run the bot."""
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='botAlert.log',
        level=logging.INFO
    )

    # Load custom tokens at startup
    load_custom_tokens()

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
            ],
            ADD_TOKEN_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_token_name
                )
            ],
            ADD_TOKEN_SYMBOL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_token_symbol
                )
            ],
            DELETE_TOKEN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_token_deletion
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