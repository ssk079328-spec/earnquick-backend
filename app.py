import os, telebot, psycopg2, threading
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

# ডাটাবেজ ফিক্সিং লজিক
def init_db():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM users LIMIT 1;")
    except:
        conn.rollback()
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
    cur.close(); conn.close()

# --- ROUTES ---
@app.route("/")
def home(): return "Backend is Live!"

@app.route("/admin-panel-secret-8145")
def admin_panel():
    with open('admin.html', 'r') as f:
        return render_template_string(f.read())

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

# বটের স্টার্ট লজিক
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, name) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (uid, name))
    conn.commit(); cur.close(); conn.close()
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.reply_to(message, f"স্বাগতম {name}!", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
