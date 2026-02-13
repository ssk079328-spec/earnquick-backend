import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 

if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

# ডাটাবেজ অটো-রিসেট এবং টেবিল সেটআপ
def init_db():
    conn = get_db(); cur = conn.cursor()
    try:
        # 'name' কলাম আছে কি না পরীক্ষা
        cur.execute("SELECT name FROM users LIMIT 1;")
    except psycopg2.errors.UndefinedColumn:
        conn.rollback()
        # কলাম না থাকলে টেবিল রিসেট (আপনার এরর ফিক্স করতে এটি জরুরি)
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("""
            CREATE TABLE users (
                user_id BIGINT PRIMARY KEY, 
                name TEXT,
                balance FLOAT DEFAULT 0, 
                refs INT DEFAULT 0
            )
        """)
    except Exception:
        conn.rollback()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY, 
                name TEXT,
                balance FLOAT DEFAULT 0, 
                refs INT DEFAULT 0
            )
        """)
    conn.commit(); cur.close(); conn.close()

# --- বটের রেফারেল লজিক ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None

    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (uid,))
    if not cur.fetchone():
        # নতুন ইউজার রেজিস্ট্রেশন
        cur.execute("INSERT INTO users (user_id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        # রেফারেল বোনাস (২০০ পয়েন্ট)
        if referrer_id and referrer_id.isdigit() and int(referrer_id) != uid:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE user_id = %s", (referrer_id,))
            try:
                bot.send_message(referrer_id, "🎉 কেউ আপনার লিঙ্কে যোগ দিয়েছে! ২০০ পয়েন্ট বোনাস পেয়েছেন।")
            except: pass
        conn.commit()
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.reply_to(message, f"স্বাগতম {name}!", reply_markup=markup)
    cur.close(); conn.close()

# --- API রুটেস ---
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    name = request.args.get('name', 'User')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        conn.commit(); res = (0, 0)
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]})

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "Success"

@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid, amount = data['user_id'], int(data['amount'])
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] >= amount:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, uid))
        conn.commit()
        bot.send_message(ADMIN_ID, f"💰 Withdraw: {amount} Pts\nUser: {data['name']}\nPhone: {data['phone']}")
        return jsonify({"status": "success", "message": "সফল হয়েছে!"})
    return jsonify({"status": "error", "message": "পয়েন্ট কম!"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
