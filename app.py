from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2

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
    conn = get_db(); cur = conn.cursor()
    # ডাটাবেস টেবিল এবং কলাম অটো-ফিক্স
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0
        );
        ALTER TABLE users ADD COLUMN IF NOT EXISTS parent_id BIGINT;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_new BOOLEAN DEFAULT TRUE;
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, method TEXT, num TEXT
        );
    """)
    conn.commit()
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    cur.close(); conn.close()
    return "System Ready"

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    if not uid: return jsonify({"error": "no id"}), 400
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    
    # ইউজার না থাকলে তৈরি করা
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit()
        row = (0, 0, True, None)

    # ২-লেভেল কমিশন প্রসেস (যদি ইউজার নতুন হয়)
    if row[2]: # is_new == True
        parent = row[3] # parent_id
        if parent:
            # লেভেল ১ কে ২০০ পয়েন্ট
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (parent,))
            # লেভেল ২ চেক
            cur.execute("SELECT parent_id FROM users WHERE id = %s", (parent,))
            gp = cur.fetchone()
            if gp and gp[0]:
                # লেভেল ২ কে ৫০ পয়েন্ট
                cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp[0],))
        
        # ইউজারকে পুরাতন হিসেবে মার্ক করা
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": float(res[0]), "refs": res[1]})

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid = d.get('user_id')
    p = d.get('point', 5)
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (p, uid))
    conn.commit(); cur.close(); conn.close()
    return "ok"

@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        uid = update.message.from_user.id
        # স্টার্ট কমান্ড এবং রেফারেল ট্র্যাকিং
        if update.message.text and "/start" in update.message.text:
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
            if not cur.fetchone():
                p_id = None
                args = update.message.text.split()
                if len(args) > 1 and args[1].isdigit(): p_id = int(args[1])
                cur.execute("INSERT INTO users (id, parent_id) VALUES (%s, %s)", (uid, p_id))
                conn.commit()
            
            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url="https://ssk079328-spec.github.io/earnquick-frontend/"))]]
            update.message.reply_text("EarnQuick Pro-তে স্বাগতম!", reply_markup=telegram.InlineKeyboardMarkup(btn))
            cur.close(); conn.close()

        # উইথড্র ডেটা প্রসেসিং
        elif update.message.web_app_data:
            d = json.loads(update.message.web_app_data.data)
            if d['action'] == 'withdraw':
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)", (uid, d['amt'], d['method'], d['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (d['amt'], uid))
                conn.commit(); cur.close(); conn.close()
                update.message.reply_text(f"✅ উইথড্র রিকোয়েস্ট সফল হয়েছে!\nপরিমাণ: {float(d['amt'])/200} টাকা।")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
