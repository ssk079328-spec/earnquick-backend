import telebot
from telebot import typesimport os
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
import psycopg2

app = Flask(__name__)
CORS(app)

TOKEN = "YOUR_BOT_TOKEN" # আপনার বটের টোকেন দিন
bot = telebot.TeleBot(TOKEN)
DB_URL = "YOUR_POSTGRESQL_URL" # রেন্ডার ডাটাবেস ইউআরএল

def get_db():
    return psycopg2.connect(DB_URL)

# ১. বটের মাধ্যমে রেফারাল সিস্টেম
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
    user_exists = cur.fetchone()

    if not user_exists:
        # নতুন ইউজার হলে ডাটাবেসে সেভ এবং রেফারারকে ২০০ পয়েন্ট
        cur.execute("INSERT INTO users (id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        if ref_id and ref_id.isdigit():
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (int(ref_id),))
            bot.send_message(ref_id, f"🎊 আপনার লিঙ্কে একজন নতুন ইউজার জয়েন করেছে! ২০০ পয়েন্ট যোগ হয়েছে।")
        conn.commit()
    
    cur.close(); conn.close()
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📱 ওপেন অ্যাপ", web_app=telebot.types.WebAppInfo("https://newsnetwork24.42web.io/")))
    bot.send_message(message.chat.id, f"স্বাগতম {name}! কাজ শুরু করতে নিচের বাটনে ক্লিক করুন।", reply_markup=markup)

# ২. মনিট্যাগ পোস্টব্যাক (অটোমেটিক পয়েন্ট)
@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if uid:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
        conn.commit(); cur.close(); conn.close()
        return "OK", 200
    return "Error", 400

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    data = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": data[0], "refs": data[1]}) if data else jsonify({"balance": 0, "refs": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
