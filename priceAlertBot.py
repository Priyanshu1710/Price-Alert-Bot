
# # ****************************************** Version 1.0.1  --> Price Alert Bot ************************************

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

# # Token mappings with proper CoinGecko IDs
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

async def start_add_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of adding a custom token."""
    await update.message.reply_text(
        "Please enter the display name for your token (e.g., Bitcoin):",
        reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
    )
    return ADD_TOKEN_NAME

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
    user_id = update.effective_user.id

    if choice == "💰 Check Price":
        context.user_data['action'] = 'check_price' 
        await update.message.reply_text(
            "Select a cryptocurrency:",
        reply_markup=get_token_keyboard(user_id)
        )
        return TOKEN_SELECTION
        
    elif choice == "⚠️ Set Alert":
        context.user_data['action'] = 'set_alert' 
        await update.message.reply_text(
            "Select a cryptocurrency for the alert:",
            reply_markup=get_token_keyboard(user_id)
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
    
    else:
        await update.message.reply_text(
            "Please select an option from the menu below:",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View alerts command handler."""
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    
    logging.info(f"Viewing alerts for chat_id {chat_id}")
    logging.info(f"Current alerts state: {user_alerts}")
    
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
        logging.info(f"No alerts found for chat_id {chat_id}")
        await update.message.reply_text(
            "You don't have any active alerts.",
            reply_markup=get_main_menu_keyboard()
        )

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
        save_alerts()  # Save after deleting all alerts
        await update.message.reply_text(
            "All alerts have been deleted.",
            reply_markup=get_main_menu_keyboard()
        )
        return CHOOSING

    try:
        alert_index = int(choice) - 1
        if chat_id in user_alerts and 0 <= alert_index < len(user_alerts[chat_id]):
            deleted_alert = user_alerts[chat_id].pop(alert_index)
            save_alerts()  # Save after deleting an alert
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
        
        logging.info(f"Creating new alert for chat_id {chat_id}: {alert}")
        user_alerts[chat_id].append(alert)
        save_alerts()  # Save alerts after adding new one
        
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
    """Check price alerts and notify users."""
    logging.info("Starting alert check...")
    
    try:
        if not user_alerts:
            logging.info("No alerts to check")
            return
            
        logging.info(f"Found alerts for {len(user_alerts)} users")

        # Get current prices
        symbols_to_check = {alert['token_id'] for alerts in user_alerts.values() for alert in alerts}
        if not symbols_to_check:
            return

        symbols_param = str(list(symbols_to_check)).replace("'", '"').replace(" ", "")
        url = f'https://api.binance.com/api/v3/ticker/price?symbols={symbols_param}'
        
        headers = {'accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch prices: {response.text}")
            return
            
        prices = {item['symbol']: float(item['price']) for item in response.json()}
        logging.info(f"Fetched prices: {prices}")

        # Process alerts
        for chat_id, alerts in user_alerts.items():
            for alert in alerts:
                symbol = alert['token_id']
                if symbol not in prices:
                    continue
                    
                current_price = prices[symbol]
                
                try:
                    if current_price <= alert['low_price']:
                        message = (f"⚠️ Low Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                                 f"Below your alert of ${alert['low_price']:,.2f}")
                        await app.bot.send_message(chat_id=int(chat_id), text=message)
                        logging.info(f"Sent low price alert to {chat_id}")
                        
                    elif current_price >= alert['high_price']:
                        message = (f"⚠️ High Price Alert!\n{alert['token']} is now ${current_price:,.2f}\n"
                                 f"Above your alert of ${alert['high_price']:,.2f}")
                        await app.bot.send_message(chat_id=int(chat_id), text=message)
                        logging.info(f"Sent high price alert to {chat_id}")
                except Exception as e:
                    logging.error(f"Error sending alert to {chat_id}: {e}")
                    
    except Exception as e:
        logging.error(f"Error in check_alerts: {e}", exc_info=True)

def save_alerts():
    """Save alerts to a JSON file."""
    try:
        with open('alerts.json', 'w') as f:
            json.dump(user_alerts, f)
        logging.info("Alerts saved successfully")
    except Exception as e:
        logging.error(f"Error saving alerts: {e}")

def validate_alerts():
    """Validate and clean up alerts data."""
    global user_alerts
    
    logging.info("Starting alert validation...")
    invalid_chat_ids = []
    
    if not isinstance(user_alerts, dict):
        logging.warning("user_alerts is not a dictionary, resetting to empty dict")
        user_alerts = {}
        save_alerts()
        return
        
    for chat_id, alerts in user_alerts.items():
        logging.info(f"Validating alerts for chat_id {chat_id}")
        
        # Convert string chat_ids to integers
        if isinstance(chat_id, str):
            try:
                new_chat_id = int(chat_id)
                user_alerts[new_chat_id] = user_alerts.pop(chat_id)
                chat_id = new_chat_id
            except ValueError:
                invalid_chat_ids.append(chat_id)
                continue
        
        # Validate alert list
        if not isinstance(alerts, list):
            invalid_chat_ids.append(chat_id)
            continue
            
        # Filter out invalid alerts
        valid_alerts = []
        for alert in alerts:
            if isinstance(alert, dict) and all(k in alert for k in ['token', 'token_id', 'low_price', 'high_price']):
                try:
                    # Verify numeric values
                    alert['low_price'] = float(alert['low_price'])
                    alert['high_price'] = float(alert['high_price'])
                    if alert['low_price'] < alert['high_price']:
                        valid_alerts.append(alert)
                except (ValueError, TypeError):
                    continue
        
        if valid_alerts:
            user_alerts[chat_id] = valid_alerts
        else:
            invalid_chat_ids.append(chat_id)
    
    # Remove invalid entries
    for chat_id in invalid_chat_ids:
        if chat_id in user_alerts:
            del user_alerts[chat_id]
    
    # Save cleaned alerts
    save_alerts()
    logging.info(f"Alert validation complete. Valid alerts: {user_alerts}")

def clear_alerts():
    """Clear all alerts and save empty state."""
    global user_alerts
    user_alerts = {}
    save_alerts()
    logging.info("All alerts cleared")

def load_alerts():
    """Load alerts from JSON file."""
    global user_alerts
    try:
        if os.path.exists('alerts.json'):
            with open('alerts.json', 'r') as f:
                user_alerts = json.load(f)
            logging.info(f"Loaded alerts from file: {user_alerts}")
            validate_alerts()  # Validate after loading
        else:
            user_alerts = {}
            logging.info("No alerts file found, starting with empty alerts")
            save_alerts()
    except Exception as e:
        logging.error(f"Error loading alerts: {e}")
        user_alerts = {}
        save_alerts()

async def clear_all_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to clear all alerts in the system."""
    clear_alerts()
    await update.message.reply_text(
        "All alerts have been cleared from the system.",
        reply_markup=get_main_menu_keyboard()
    )

async def test_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to manually check alerts."""
    await update.message.reply_text("Manually checking alerts...")
    await check_alerts(context.application)
    await update.message.reply_text("Alert check completed. Check logs for details.")

async def debug_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show current alerts."""
    chat_id = update.effective_chat.id
    debug_text = (
        f"Alerts Debug Info:\n\n"
        f"Your chat_id: {chat_id}\n"
        f"Your alerts: {user_alerts.get(chat_id, [])}\n"
        f"All alerts: {json.dumps(user_alerts, indent=2)}\n\n"
        f"Total users with alerts: {len(user_alerts)}"
    )
    await update.message.reply_text(debug_text[:4000])

def main():
    """Initialize and run the bot."""
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='botAlert.log',
        level=logging.INFO
    )

    # Load saved data
    load_custom_tokens()
    load_alerts()

    # Initialize the bot
    app = ApplicationBuilder().token(TOKEN).build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CommandHandler("test_alerts", test_alerts)
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

    # Add handlers
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("test_alerts", test_alerts))
    app.add_handler(CommandHandler("debug_alerts", debug_alerts_command))
    app.add_handler(CommandHandler("clear_alerts", clear_all_alerts))

    # Set up error handling
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.error(f"Exception while handling an update: {context.error}")
        if update and update.message:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Sorry, something went wrong. Please try again.",
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                pass

    app.add_error_handler(error_handler)

    # Improve menu responsiveness
    async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle any unknown commands or messages."""
        await update.message.reply_text(
            "Please use the menu options below:",
            reply_markup=get_main_menu_keyboard()
        )

    # Add fallback handler for unknown inputs
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input))

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    
    def run_alerts():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(check_alerts(app))
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
        finally:
            try:
                loop.close()
            except:
                pass

    # Add jobs
    scheduler.add_job(run_alerts, 'interval', minutes=1)
    scheduler.add_job(save_alerts, 'interval', hours=1)
    scheduler.start()

    # Start the bot
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()