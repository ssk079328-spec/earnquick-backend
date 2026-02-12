from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2

app = Flask(__name__)
CORS(app)

# আপনার তথ্য দিয়ে সেট করা
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
ADMIN_ID = 8145444675  # আপনার কনফার্ম করা আইডি

bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0, parent_id BIGINT, is_new BOOLEAN DEFAULT TRUE);
        CREATE TABLE IF NOT EXISTS withdrawals (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, method TEXT, num TEXT, status TEXT DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id BIGINT, type TEXT, amount NUMERIC, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    cur.close(); conn.close()
    return "🔥 Admin & System Active"

@app.route("/admin/withdrawals")
def admin_withdrawals():
    admin_id = request.args.get('admin_id')
    if str(admin_id) != str(ADMIN_ID): return "Access Denied", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, user_id, amount, method, num, status FROM withdrawals WHERE status = 'Pending' ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"id":r[0], "uid":r[1], "amt":float(r[2]), "method":r[3], "num":r[4], "status":r[5]} for r in rows])

@app.route("/admin/approve", methods=['POST'])
def approve_payment():
    d = request.json
    if str(d.get('admin_id')) != str(ADMIN_ID): return "Unauthorized", 403
    wid = d.get('w_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE withdrawals SET status = 'Success' WHERE id = %s", (wid,))
    conn.commit(); cur.close(); conn.close()
    return "Paid Successfully"

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit()
        row = (0, 0, True, None)
    
    if row[2] and row[3]: # Referral Commission Logic
        cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (row[3],))
        cur.execute("SELECT parent_id FROM users WHERE id = %s", (row[3],))
        gp = cur.fetchone()
        if gp and gp[0]: cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp[0],))
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": float(res[0]), "refs": res[1]})

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid, p = d.get('user_id'), d.get('point')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (p, uid))
    cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Ad View', %s)", (uid, p))
    conn.commit(); cur.close(); conn.close()
    return "ok"

@app.route("/history")
def get_history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT type, amount, status FROM (SELECT 'Withdraw' as type, amount, status, id FROM withdrawals WHERE user_id = %s UNION ALL SELECT 'Earning' as type, amount, 'Success' as status, id FROM history WHERE user_id = %s) as combined ORDER BY id DESC LIMIT 15", (uid, uid))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"type": r[0], "amount": float(r[1]), "status": r[2]} for r in rows])

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
                args = update.message.text.split()
                if len(args) > 1 and args[1].isdigit(): p_id = int(args[1])
                cur.execute("INSERT INTO users (id, parent_id) VALUES (%s, %s)", (uid, p_id))
                conn.commit()
            web_url = "https://ssk079328-spec.github.io/earnquick-frontend/"
            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url=web_url))]]
            update.message.reply_text(f"স্বাগতম {update.message.from_user.first_name}! আয় শুরু করতে নিচে ক্লিক করুন।", reply_markup=telegram.InlineKeyboardMarkup(btn))
            cur.close(); conn.close()
        elif update.message.web_app_data:
            d = json.loads(update.message.web_app_data.data)
            if d['action'] == 'withdraw':
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)", (uid, d['amt'], d['method'], d['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (d['amt'], uid))
                conn.commit(); cur.close(); conn.close()
                update.message.reply_text(f"✅ উইথড্র সফল! {float(d['amt'])/200} টাকা দ্রুত পাঠিয়ে দেওয়া হবে।")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
