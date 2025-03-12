import telebot
import qrcode
from io import BytesIO
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Telegram Bot Token
BOT_TOKEN = "7587405941:AAHFGlgHseOSeeTqXFMtRqgNO9pc9K8ukZs"
OWNER_CHAT_ID = 8047942590  # Replace with your real Telegram ID

# Paytm QR UPI ID
PAYTM_UPI_ID = "Paytmqr2810050501011e8i45v03ot5@paytm"

# OTT options and prices
ott_options = ["Netflix", "Amazon Prime", "Disney+", "Hotstar", "SonyLiv", "ZEE5"]
price_options = {"1 Year": 500, "6 Months": 350}

# Store user data
user_data = {}

# Create bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for ott in ott_options:
        markup.add(KeyboardButton(ott))
    bot.send_message(
        message.chat.id, 
        "🎬 Welcome!\n\nSelect an OTT subscription:", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# OTT selection
@bot.message_handler(func=lambda message: message.text in ott_options)
def select_validity(message):
    user_data[message.chat.id] = {"ott": message.text}
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for validity in price_options.keys():
        markup.add(KeyboardButton(validity))
    bot.send_message(
        message.chat.id, 
        f"📺 You selected: {message.text}\n\nChoose validity:", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# Validity selection
@bot.message_handler(func=lambda message: message.text in price_options.keys())
def send_qr_code(message):
    chat_id = message.chat.id
    validity = message.text
    ott = user_data.get(chat_id, {}).get("ott", "Unknown OTT")
    amount = price_options[validity]

    user_data[chat_id]["validity"] = validity

    # Generate UPI QR Code
    upi_link = f"upi://pay?pa={PAYTM_UPI_ID}&pn=OTT Subscription&am={amount}&cu=INR"
    qr = qrcode.make(upi_link)
    qr_io = BytesIO()
    qr.save(qr_io, format="PNG")
    qr_io.seek(0)

    # Send QR Code Image
    bot.send_photo(
        chat_id, 
        qr_io, 
        caption=f"💰 Pay ₹{amount} for {ott} ({validity})\n📌 Scan this QR to pay.\n\nAfter payment, send your UTR ID.", 
        parse_mode="Markdown"
    )

# Capture UTR ID and forward to owner
@bot.message_handler(func=lambda message: message.text.isdigit() and len(message.text) >= 10)
def handle_utr(message):
    chat_id = message.chat.id
    utr_id = message.text
    ott = user_data.get(chat_id, {}).get("ott", "Unknown OTT")
    validity = user_data.get(chat_id, {}).get("validity", "Unknown Validity")

    owner_message = (
        f"🆕 *Payment Received!*\n\n"
        f"📺 OTT: {ott}\n"
        f"⏳ Validity: {validity}\n"
        f"💳 UTR ID: {utr_id}\n"
        f"👤 User ID: {chat_id}\n\n"
        f"📌 Reply to this message to send OTT details."
    )

    # Confirm payment to user
    bot.send_message(chat_id, "✅ Payment received! Your subscription will be activated soon.", parse_mode="Markdown")
    
    # Send UTR details to owner
    sent_msg = bot.send_message(OWNER_CHAT_ID, owner_message, parse_mode="Markdown")
    bot.pin_chat_message(OWNER_CHAT_ID, sent_msg.message_id)

# 📌 Owner Sends OTT Account Details (Easier)
@bot.message_handler(commands=['send'])
def send_ott_details(message):
    if message.chat.id != OWNER_CHAT_ID:
        bot.send_message(message.chat.id, "❌ You are not authorized to use this command.")
        return

    try:
        command_parts = message.text.split(" ", 2)
        if len(command_parts) < 3:
            bot.send_message(message.chat.id, "❌ Format: /send <UserID> <OTT Account Details>", parse_mode="Markdown")
            return

        user_id = command_parts[1]
        ott_details = command_parts[2]

        # Send OTT details to the user
        bot.send_message(int(user_id), f"🎉 Here are your OTT details:\n\n{ott_details}", parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ OTT details sent successfully!")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
        # 📌 Owner Can Reply to Users Multiple Times
@bot.message_handler(func=lambda message: message.reply_to_message and message.chat.id == OWNER_CHAT_ID)
def reply_to_user(message):
    try:
        # Extract user ID from original message
        original_text = message.reply_to_message.text
        user_id = int(original_text.split("👤 User ID: ")[1].split("\n")[0])

        # Send the owner's message to the user
        bot.send_message(user_id, f"📩 *Message from Admin:*\n\n{message.text}", parse_mode="Markdown")

    except Exception as e:
        bot.send_message(OWNER_CHAT_ID, f"❌ Error: {str(e)}")

# 📌 User Messages Are Forwarded to Owner
@bot.message_handler(func=lambda message: message.chat.id != OWNER_CHAT_ID)
def forward_to_owner(message):
    user_id = message.chat.id
    text = message.text

    sent_msg = bot.send_message(OWNER_CHAT_ID, f"📩 *Message from User {user_id}:*\n\n{text}", parse_mode="Markdown")
    bot.pin_chat_message(OWNER_CHAT_ID, sent_msg.message_id)
    bot.send_message(user_id, "📤 Your message has been sent to Admin.")

# Run bot
bot.polling()