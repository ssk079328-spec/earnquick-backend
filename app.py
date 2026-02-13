import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import types
import threading

# --- কনফিগারেশন ---
TOKEN = os.environ.get("BOT_TOKEN") 
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675  # আপনার আইডি সেট করে দেওয়া হয়েছে

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL)

# ডাটাবেস টেবিল তৈরি
def init_db():
    try:
        conn = get_db(); cur = conn.cursor()
        # ইউজার টেবিল
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                name TEXT,
                balance FLOAT DEFAULT 0,
                refs INT DEFAULT 0
            );
        """)
        # উইথড্র টেবিল
        cur.execute("""
            CREATE TABLE IF NOT EXISTS withdraws (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                name TEXT,
                method TEXT,
                phone TEXT,
                amount INT,
                status TEXT DEFAULT 'Pending',
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

@app.route("/")
def home():
    return "<h1>EarnQuick Backend is Live!</h1>", 200

# ইউজারের ডাটা দেখার রুট
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
        res = cur.fetchone()
        cur.close(); conn.close()
        if res:
            return jsonify({"balance": res[0], "refs": res[1]})
        return jsonify({"balance": 0, "refs": 0})
    except:
        return jsonify({"balance": 0, "refs": 0})

# উইথড্র রিকোয়েস্ট রিসিভ করার রুট
@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid = data.get('user_id')
    amount = int(data.get('amount'))
    method = data.get('method')
    phone = data.get('phone')
    name = data.get('name')

    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = %s", (uid,))
    user_data = cur.fetchone()
    
    if user_data and user_data[0] >= amount:
        if amount >= 1000:
            # ব্যালেন্স কমানো
            cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, uid))
            # উইথড্র রিকোয়েস্ট সেভ করা
            cur.execute("INSERT INTO withdraws (user_id, name, method, phone, amount) VALUES (%s, %s, %s, %s, %s)", 
                        (uid, name, method, phone, amount))
            conn.commit()
            
            # এডমিনকে (আপনাকে) নোটিফিকেশন পাঠানো
            admin_msg = (f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
                         f"👤 নাম: {name}\n"
                         f"🆔 আইডি: `{uid}`\n"
                         f"💰 পরিমাণ: {amount} পয়েন্ট\n"
                         f"📱 মেথড: {method}\n"
                         f"📞 নাম্বার: `{phone}`\n"
                         f"🕒 সময়: সদ্য প্রাপ্ত")
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
            
            msg = "আপনার রিকোয়েস্টটি সফলভাবে এডমিনের কাছে পাঠানো হয়েছে।"
            status = "success"
        else:
            msg = "দুঃখিত, সর্বনিম্ন ১০০০ পয়েন্ট হতে হবে।"
            status = "error"
    else:
        msg = "আপনার পর্যাপ্ত ব্যালেন্স নেই।"
        status = "error"
    
    cur.close(); conn.close()
    return jsonify({"status": status, "message": msg})

# অ্যাড দেখলে পয়েন্ট অ্যাড হওয়ার রুট
@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if uid:
        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
            conn.commit(); cur.close(); conn.close()
            return "OK", 200
        except: return "DB Error", 500
    return "Error", 400

# টেলিগ্রাম বট লজিক (স্টার্ট বাটন)
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    # রেফারেল হ্যান্ডলিং
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        if ref_id and ref_id.isdigit() and int(ref_id) != uid:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (int(ref_id),))
            try:
                bot.send_message(ref_id, f"🎊 অভিনন্দন! আপনার রেফারে {name} জয়েন করেছে। আপনি ২০০ পয়েন্ট বোনাস পেয়েছেন।")
            except: pass
        conn.commit()
    cur.close(); conn.close()
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📱 ওপেন অ্যাপ", web_app=types.WebAppInfo("https://newsnetwork24.42web.io/"))
    markup.add(btn)
    bot.send_message(message.chat.id, f"স্বাগতম {name}!\nEarnQuick Pro-তে কাজ করে প্রতিদিন টাকা আয় করুন।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
