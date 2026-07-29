import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot Setup
TOKEN = "8692725311:AAHZv5uAsKe2iUesrhYxw9rX97wfPboJDDM"
ADMIN_CHAT_ID = "8520115054"
UPI_ID = "ra99hu99-1@okaxis"
QR_IMAGE_URL = "https://i.ibb.co/QvjF8yHB/IMG-20260729-WA0000.jpg"

bot = telebot.TeleBot(TOKEN)
active_users = set()

# Bot polling function (runs in background)
def run_bot():
    print("Bot polling started...")
    bot.infinity_polling(skip_pending=True)

# Start Bot Thread
threading.Thread(target=run_bot, daemon=True).start()

# Flask Web Server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is Running Active 24/7!"

# 1. Start Command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    active_users.add(message.chat.id)
    welcome_text = (
        "👋 Welcome to Our Video Collection Store!\n\n"
        "Aapko kitni videos chahiye? Niche diye gaye plans me se apna plan select karein:\n\n"
        "✨ Plan 1: 1,000 Videos = ₹49\n"
        "✨ Plan 2: 2,000 Videos = ₹199\n"
        "✨ Plan 3: 5,000 Videos = ₹299\n\n"
        "👉 Niche button par click karke apna plan select karein."
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 1000 Videos - ₹49", callback_data="plan_49"))
    markup.add(InlineKeyboardButton("📦 2000 Videos - ₹199", callback_data="plan_199"))
    markup.add(InlineKeyboardButton("📦 5000 Videos - ₹299", callback_data="plan_299"))
    bot.reply_to(message, welcome_text, reply_markup=markup)

# 2. Plan Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('plan_'))
def handle_plan(call):
    active_users.add(call.message.chat.id)
    price = call.data.split('_')[1]
    msg_text = (
        f"✅ Aapne ₹{price} wala plan select kiya hai.\n\n"
        "1️⃣ Upar diye gaye QR Code ko scan karein ya niche di gayi UPI ID par payment karein:\n"
        f"👉 UPI ID: {UPI_ID}\n\n"
        "2️⃣ Payment karne ke baad, payment ka Screenshot yahin chat me bhej dein.\n\n"
        "3️⃣ Hum payment confirm karke aapko videos ka link bhej denge! ⚡"
    )
    bot.answer_callback_query(call.id)
    try:
        bot.send_photo(call.message.chat.id, QR_IMAGE_URL, caption=msg_text)
    except Exception:
        bot.send_message(call.message.chat.id, msg_text)

# 3. Screenshot Handler
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    active_users.add(message.chat.id)
    user = message.from_user
    username = f"@{user.username}" if user.username else "No Username"
    bot.reply_to(message, "✅ Aapka screenshot mil gaya hai!\n\nHum payment confirm karke jald se jald aapko videos ka link bhej rahe hain.")
    admin_msg = (
        f"🔔 NEW PAYMENT SCREENSHOT!\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"💬 Username: {username}\n\n"
        f"👇 Link bhejne ke liye niche wala text copy karke bhein:\n"
        f"/send {user.id} YOUR_LINK_HERE"
    )
    bot.send_message(ADMIN_CHAT_ID, admin_msg)
    bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)

# 4. Text Message Forwarding
@bot.message_handler(func=lambda m: True, content_types=['text'])
def forward_text_to_admin(message):
    if str(message.chat.id) == ADMIN_CHAT_ID:
        return
    active_users.add(message.chat.id)
    user = message.from_user
    username = f"@{user.username}" if user.username else "No Username"
    admin_text = f"📩 NEW USER MESSAGE!\n\n👤 From: {user.first_name} ({username})\n🆔 User ID: {user.id}\n\n💬 Message: {message.text}"
    bot.send_message(ADMIN_CHAT_ID, admin_text)

# 5. Send Command (FIXED - NO MARKDOWN ERROR)
@bot.message_handler(commands=['send'])
def send_course_link(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    try:
        text_parts = message.text.split(maxsplit=2)
        target_user_id = text_parts[1].strip()
        course_link = text_parts[2].strip()
        
        customer_msg = (
            "🎉 Payment Confirmed!\n\n"
            f"Aapki videos ka link yeh raha:\n👉 {course_link}\n\n"
            "Humare sath judne ke liye dhanyawad!"
        )
        bot.send_message(target_user_id, customer_msg)
        bot.reply_to(message, f"✅ Success! User ({target_user_id}) ko link bhej diya gaya hai.")
    except Exception as e:
        bot.reply_to(message, f"❌ Format Sahi Karein:\n`/send User_ID Link`\n\nError Details: {str(e)}")

# 6. Broadcast Command
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    try:
        broadcast_text = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Format: `/broadcast Aapka Message`")
        return
    success_count = 0
    fail_count = 0
    for uid in list(active_users):
        try:
            bot.send_message(uid, broadcast_text)
            success_count += 1
        except Exception:
            fail_count += 1
    bot.send_message(ADMIN_CHAT_ID, f"✅ Broadcast Completed!\n\n🎯 Success: {success_count}\n❌ Failed: {fail_count}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
