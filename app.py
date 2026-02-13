import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

# পরিবেশ ভেরিয়েবল
TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 

# Postgres URL ফিক্স
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

# ডাটাবেজ ফিক্স এবং টেবিল সেটআপ
def init_db():
    conn = get_db(); cur = conn.cursor()
    try:
        # লগের এরর ফিক্স করতে কলামগুলো চেক করা হচ্ছে
        cur.execute("SELECT name FROM users LIMIT 1;")
        print("Database structure is already correct.")
    except Exception:
        # যদি 'name' কলাম না থাকে তবে টেবিলটি নতুনভাবে তৈরি করা হবে
        conn.rollback()
        print("Fixing database structure...")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("""
            CREATE TABLE users (
                user_id BIGINT PRIMARY KEY, 
                name TEXT,
                balance FLOAT DEFAULT 0, 
                refs INT DEFAULT 0
            )
        """)
        conn.commit()
    finally:
        cur.close(); conn.close()

# --- বটের রেফারেল এবং অটো-রেজিস্ট্রেশন লজিক ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None

    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (uid,))
    if not cur.fetchone():
        # নতুন ইউজারদের জন্য ডাটাবেজ এন্ট্রি
        cur.execute("INSERT INTO users (user_id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        # রেফারেল বোনাস লজিক
        if referrer_id and referrer_id.isdigit() and int(referrer_id) != uid:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE user_id = %s", (referrer_id,))
            try: bot.send_message(referrer_id, "🎉 কেউ আপনার লিঙ্কে যোগ দিয়েছে! ২০০ পয়েন্ট বোনাস পেয়েছেন।")
            except: pass
        conn.commit()
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.reply_to(message, f"স্বাগতম {name}! আপনার অ্যাকাউন্ট এখন প্রস্তুত।", reply_markup=markup)
    cur.close(); conn.close()

# --- API Endpoints ---
@app.route("/")
def home(): return "EarnQuick Backend Live"

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    name = request.args.get('name', 'User')
    if not uid: return jsonify({"error": "No ID"}), 400
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    
    if not res:
        # অটো-রেজিস্ট্রেশন যদি বটের মাধ্যমে না হয়ে থাকে
        cur.execute("INSERT INTO users (user_id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        conn.commit()
        res = (0, 0)
    
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]})

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if not uid: return "Error", 400
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "Success"

@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid, amount = data['user_id'], int(data['amount'])
    method, phone = data['method'], data['phone']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] >= amount:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, uid))
        conn.commit()
        bot.send_message(ADMIN_ID, f"💰 **Withdraw Request!**\nUser: {data['name']}\nAmt: {amount}\nPh: {phone}\nVia: {method}")
        return jsonify({"status": "success", "message": "উইথড্র রিকোয়েস্ট সফল!"})
    return jsonify({"status": "error", "message": "পয়েন্ট পর্যাপ্ত নয়!"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
