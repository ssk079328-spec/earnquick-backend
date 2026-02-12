from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os
import psycopg2
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
            id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0, last_date DATE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    return "Backend is Active!"

@app.route("/data", methods=['GET'])
def data():
    uid = request.args.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit()
        res = {"balance": 0, "refs": 0}
    else:
        res = {"balance": float(row[0]), "refs": row[1]}
    cur.close()
    conn.close()
    return jsonify(res)

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid = d.get('user_id')
    point = d.get('point')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (point, uid))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        uid = update.message.from_user.id
        text = update.message.text
        if "/start" in text:
            msg = text.split()
            if len(msg) > 1: # রেফারেল চেক
                ref_id = msg[1]
                conn = get_db()
                cur = conn.cursor()
                cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (ref_id,))
                conn.commit()
                cur.close()
                conn.close()
            
            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url="https://ssk079328-spec.github.io/earnquick-frontend/"))]]
            update.message.reply_text("স্বাগতম!", reply_markup=telegram.InlineKeyboardMarkup(btn))
    return "ok"

if __name__ == "__main__":
    app.run()
