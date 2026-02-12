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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0, 
            parent_id BIGINT, is_new BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, method TEXT, num TEXT
        );
    """)
    conn.commit()
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    cur.close(); conn.close()
    return "Ready"

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    if row and row[2]:
        parent = row[3]
        if parent:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (parent,))
            cur.execute("SELECT parent_id FROM users WHERE id = %s", (parent,))
            gp = cur.fetchone()
            if gp and gp[0]: cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp[0],))
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": float(res[0]) if res else 0, "refs": res[1] if res else 0})

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid = d.get('user_id')
    p = d.get('point')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (p, uid))
    conn.commit(); cur.close(); conn.close()
    return "ok"

@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.web_app_data:
        d = json.loads(update.message.web_app_data.data)
        if d['action'] == 'withdraw':
            uid = update.message.from_user.id
            conn = get_db(); cur = conn.cursor()
            cur.execute("INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)", (uid, d['amt'], d['method'], d['num']))
            cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (d['amt'], uid))
            conn.commit(); cur.close(); conn.close()
            update.message.reply_text("✅ উইথড্র রিকোয়েস্ট সফল!")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
