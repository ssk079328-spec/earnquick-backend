import os, telebot, psycopg2, threading, random
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

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

# ডাটাবেজ অটো-ফিক্স মডিউল
def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, 
            name TEXT DEFAULT 'User',
            balance FLOAT DEFAULT 0, 
            refs INT DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            method TEXT,
            status TEXT DEFAULT 'Pending',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit(); cur.close(); conn.close()

# --- ওয়েলকাম মেসেজ ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    msg = f"👋 স্বাগতম {name}!\n\nভিডিও দেখে এবং স্পিন খেলে ইনকাম শুরু করুন।\n💰 প্রতি অ্যাড: ৫ পয়েন্ট\n🎡 স্পিন: আনলিমিটেড"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.send_message(uid, msg, reply_markup=markup)

# --- এপিআই রুটস ---
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    name = request.args.get('name', 'User')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, name FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id, name) VALUES (%s, %s)", (uid, name))
        conn.commit(); res = (0, name)
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "name": res[1]})

@app.route("/spin", methods=['POST'])
def spin():
    uid = request.json.get('user_id')
    win = random.choice([1, 2, 5, 0, 10])
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (win, uid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"win": win})

@app.route("/withdraw", methods=['POST'])
def withdraw():
    d = request.json
    uid, amt, method, phn = d['user_id'], int(d['amount']), d['method'], d['phone']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
    if cur.fetchone()[0] >= amt:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amt, uid))
        cur.execute("INSERT INTO withdrawals (user_id, amount, method) VALUES (%s, %s, %s)", (uid, amt, method))
        conn.commit()
        bot.send_message(ADMIN_ID, f"💰 New Withdraw: {amt} Pts\nVia: {method}\nPh: {phn}\nID: {uid}")
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route("/history")
def history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT amount, method, status FROM withdrawals WHERE user_id = %s ORDER BY id DESC", (uid,))
    res = [{"amount": r[0], "method": r[1], "status": r[2]} for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(res)

@app.route("/admin-panel-secret-8145")
def admin():
    with open('admin.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
