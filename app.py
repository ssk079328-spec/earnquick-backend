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

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, 
            name TEXT DEFAULT 'User',
            balance FLOAT DEFAULT 0, 
            refs INT DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            method TEXT,
            status TEXT DEFAULT 'Pending',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit(); cur.close(); conn.close()

# --- ওয়েলকাম টেক্সট মডিউল ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    
    welcome_msg = f"👋 আসসালামু আলাইকুম {name}!\n\n" \
                  f"🚀 **EarnQuick Pro**-তে আপনাকে স্বাগতম।\n" \
                  f"এখানে আপনি ভিডিও অ্যাড দেখে এবং লাকি স্পিন খেলে প্রতিদিন টাকা ইনকাম করতে পারবেন।\n\n" \
                  f"💰 **প্রতি অ্যাডে:** ৫ পয়েন্ট\n" \
                  f"🎡 **লাকি স্পিন:** আনলিমিটেড সুযোগ\n" \
                  f"💳 **মিনিমাম উইথড্র:** ৫০০ পয়েন্ট (বিকাশ/নগদ)\n\n" \
                  f"নিচের বাটনে ক্লিক করে কাজ শুরু করুন! 👇"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.send_message(uid, welcome_msg, reply_markup=markup, parse_mode="Markdown")

# --- লাকি স্পিন এপিআই ---
@app.route("/spin", methods=['POST'])
def spin_earn():
    uid = request.json.get('user_id')
    win_pts = random.choice([1, 2, 5, 0, 10, 3]) # স্পিন থেকে জেতা পয়েন্ট
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (win_pts, uid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"win": win_pts})

# (বাকি এপিআই রুটগুলো আগের মতোই থাকবে: /data, /postback, /withdraw, /history, /admin-panel-secret-8145)
# ... [আগের দেওয়া app.py এর বাকি অংশ এখানে থাকবে] ...

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
