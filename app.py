from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os
import json
import psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

# --- সেটিংস (Render-এর Environment Variables থেকে আসবে) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# ⭐ আপনার GitHub Pages-এর লিঙ্ক (তৈরি করার পর এখানে বসাবেন)
WEB_APP_URL = "https://ssk079328-spec.github.io/earnquick-backend/"
BOT_USERNAME = "@EarnQuick_Official_bot"

bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def setup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            balance NUMERIC(10, 2) DEFAULT 0.00,
            ads_today INTEGER DEFAULT 0,
            refs INTEGER DEFAULT 0,
            last_ad_date DATE
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC(10, 2), method TEXT, number TEXT
        );
    """)
    conn.commit()
    bot.set_webhook(url=RENDER_URL + WEBHOOK_PATH)
    cur.close()
    conn.close()
    return "Backend Connected!"

@app.route("/data", methods=['GET'])
def user_data():
    uid = request.args.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance, ads_today, refs, last_ad_date FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    if row:
        b, a, r, d = row
        if d != date.today(): a = 0
        res = {"balance": float(b), "ads": a, "refs": r}
    else:
        res = {"balance": 0.00, "ads": 0, "refs": 0}
    cur.close()
    conn.close()
    return jsonify(res)

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        uid = update.message.from_user.id
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING", (uid,))
        conn.commit()

        if update.message.text and "/start" in update.message.text:
            msg = update.message.text.split()
            if len(msg) > 1 and msg[1].isdigit():
                ref_id = int(msg[1])
                if ref_id != uid:
                    cur.execute("UPDATE users SET balance = balance + 5, refs = refs + 1 WHERE id = %s", (ref_id,))
                    conn.commit()

            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url=WEB_APP_URL))]]
            update.message.reply_text("EarnQuick-এ স্বাগতম!", reply_markup=telegram.InlineKeyboardMarkup(btn))
        
        elif update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            if data['action'] == 'ad':
                cur.execute("UPDATE users SET balance = balance + 20, ads_today = ads_today + 1, last_ad_date = %s WHERE id = %s", (date.today(), uid))
            elif data['action'] == 'withdraw':
                cur.execute("INSERT INTO withdrawals (user_id, amount, method, number) VALUES (%s, %s, %s, %s)", (uid, data['amt'], data['method'], data['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (data['amt'], uid))
            conn.commit()
            update.message.reply_text("সফল হয়েছে! ✅")
            
        cur.close()
        conn.close()
    return "ok"

if __name__ == "__main__":
    app.run()
