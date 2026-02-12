import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import types
import threading

# --- সিকিউর কনফিগারেশন (Render Dashboard থেকে আসবে) ---
TOKEN = os.environ.get("BOT_TOKEN") 
DB_URL = os.environ.get("DATABASE_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL)

# অটোমেটিক টেবিল তৈরি
def init_db():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                name TEXT,
                balance FLOAT DEFAULT 0,
                refs INT DEFAULT 0
            );
        """)
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        if ref_id and ref_id.isdigit() and int(ref_id) != uid:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (int(ref_id),))
            bot.send_message(ref_id, f"🎊 {name} জয়েন করেছে! ২০০ পয়েন্ট বোনাস।")
        conn.commit()
    cur.close(); conn.close()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 ওপেন অ্যাপ", web_app=types.WebAppInfo("https://newsnetwork24.42web.io/")))
    bot.send_message(message.chat.id, f"স্বাগতম {name}!", reply_markup=markup)

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]}) if res else jsonify({"balance": 0, "refs": 0})

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if uid:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
        conn.commit(); cur.close(); conn.close()
        return "OK", 200
    return "Error", 400

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
