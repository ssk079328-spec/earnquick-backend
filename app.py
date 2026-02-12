from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0, 
            parent_id BIGINT, is_new BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, method TEXT, num TEXT, status TEXT DEFAULT 'Pending'
        );
    """)
    conn.commit()
    cur.close(); conn.close()
    return "System Ready!"

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    
    # ২-লেভেল কমিশন লজিক
    if row and row[2]:
        parent = row[3]
        if parent:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (parent,))
            cur.execute("SELECT parent_id FROM users WHERE id = %s", (parent,))
            g_parent = cur.fetchone()
            if g_parent and g_parent[0]:
                cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (g_parent[0],))
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": float(res[0]), "refs": res[1]})

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (d['point'], d['user_id']))
    conn.commit(); cur.close(); conn.close()
    return "ok"

@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        uid = update.message.from_user.id
        if update.message.text and "/start" in update.message.text:
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
            if not cur.fetchone():
                p_id = None
                msg = update.message.text.split()
                if len(msg) > 1: p_id = msg[1]
                cur.execute("INSERT INTO users (id, parent_id) VALUES (%s, %s)", (uid, p_id))
                conn.commit()
            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url="https://ssk079328-spec.github.io/earnquick-frontend/"))]]
            update.message.reply_text("স্বাগতম!", reply_markup=telegram.InlineKeyboardMarkup(btn))
        elif update.message.web_app_data:
            d = json.loads(update.message.web_app_data.data)
            if d['action'] == 'withdraw':
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)", (uid, d['amt'], d['method'], d['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (d['amt'], uid))
                conn.commit(); cur.close(); conn.close()
                update.message.reply_text(f"✅ উইথড্র রিকোয়েস্ট জমা হয়েছে! পরিমাণ: {float(d['amt'])/200} টাকা।")
    return "ok"

if __name__ == "__main__":
    app.run()
