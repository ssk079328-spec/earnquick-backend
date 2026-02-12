from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

# Credentials - Render Environment Variables থেকে আসবে
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
ADMIN_ID = 8145444675 # আপনার আইডি

bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init():
    conn = get_db(); cur = conn.cursor()
    # ডাটাবেস টেবিল ও কলাম অটো-ফিক্স/তৈরি
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY, 
            balance NUMERIC DEFAULT 0, 
            refs INTEGER DEFAULT 0,
            parent_id BIGINT,
            is_new BOOLEAN DEFAULT TRUE,
            last_bonus DATE
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, 
            user_id BIGINT, 
            amount NUMERIC, 
            method TEXT, 
            num TEXT, 
            status TEXT DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY, 
            user_id BIGINT, 
            type TEXT, 
            amount NUMERIC, 
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit(); cur.close(); conn.close()
    return "🚀 EarnQuick Pro Full System Live & Repaired!"

# --- Monetag Postback রুট ---
@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    amount = request.args.get('amount', 0) # Monetag থেকে আসা ডলার প্রাইজ
    
    if uid and uid.isdigit():
        conn = get_db(); cur = conn.cursor()
        # অ্যাড দেখার জন্য ৫ পয়েন্ট রিওয়ার্ড
        cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
        cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Monetag Ad', 5)", (int(uid),))
        conn.commit(); cur.close(); conn.close()
        return "OK", 200
    return "Invalid Data", 400

# --- ইউজার ডাটা এবং রেফারেল লজিক ---
@app.route("/data")
def data():
    uid = request.args.get('user_id')
    if not uid: return "ID Missing", 400
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit(); row = (0, 0, True, None)
    
    # ২-লেভেল রেফার কমিশন (একবারই কাজ করবে)
    if row[2] and row[3]: # is_new == True and parent_id exists
        cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (row[3],))
        cur.execute("SELECT parent_id FROM users WHERE id = %s", (row[3],))
        gp = cur.fetchone()
        if gp and gp[0]: # লেভেল ২ (দাদা রেফার)
            cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp[0],))
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone(); cur.close(); conn.close()
    return jsonify({"balance": float(res[0]), "refs": res[1]})

# --- ডেইলি বোনাস ---
@app.route("/claim_bonus", methods=['POST'])
def claim_bonus():
    uid = request.json.get('user_id')
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT last_bonus FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] == today:
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "আজ অলরেডি বোনাস নিয়েছেন!"})
    
    cur.execute("UPDATE users SET balance = balance + 50, last_bonus = %s WHERE id = %s", (today, uid))
    cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Daily Bonus', 50)", (uid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "message": "৫০ পয়েন্ট বোনাস পেয়েছেন!"})

# --- এডমিন প্যানেল ---
@app.route("/admin/all_data")
def admin_data():
    admin_id = request.args.get('admin_id')
    if str(admin_id) != str(ADMIN_ID): return "Access Denied", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, balance, refs FROM users ORDER BY balance DESC LIMIT 50")
    u_list = cur.fetchall()
    cur.execute("SELECT id, user_id, amount, method, num FROM withdrawals WHERE status = 'Pending' ORDER BY id DESC")
    w_list = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({
        "users": [{"id":r[0], "bal":float(r[1]), "ref":r[2]} for r in u_list],
        "withdrawals": [{"id":r[0], "uid":r[1], "amt":float(r[2]), "method":r[3], "num":r[4]} for r in w_list]
    })

@app.route("/admin/approve", methods=['POST'])
def approve_payment():
    d = request.json
    if str(d.get('admin_id')) != str(ADMIN_ID): return "Unauthorized", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE withdrawals SET status = 'Success' WHERE id = %s", (d.get('w_id'),))
    conn.commit(); cur.close(); conn.close()
    return "Paid Successfully"

# --- ইতিহাস ---
@app.route("/history")
def get_history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT type, amount, status FROM (
            SELECT 'Withdraw' as type, amount, status, id FROM withdrawals WHERE user_id = %s
            UNION ALL
            SELECT 'Earning' as type, amount, 'Success' as status, id FROM history WHERE user_id = %s
        ) as combined ORDER BY id DESC LIMIT 20
    """, (uid, uid))
    rows = cur.fetchall(); cur.close(); conn.close()
    return jsonify([{"type": r[0], "amount": float(r[1]), "status": r[2]} for r in rows])

# --- টেলিগ্রাম ওয়েব হুক ---
@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        uid = update.message.from_user.id
        if "/start" in update.message.text:
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
            update.message.reply_text(f"স্বাগতম {update.message.from_user.first_name}! অনলাইনে আয়ের সেরা প্ল্যাটফর্মে আপনাকে স্বাগতম।", reply_markup=telegram.InlineKeyboardMarkup(btn))
            cur.close(); conn.close()
        
        elif update.message.web_app_data:
            d = json.loads(update.message.web_app_data.data)
            if d['action'] == 'withdraw':
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)", (uid, d['amt'], d['method'], d['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (d['amt'], uid))
                conn.commit(); cur.close(); conn.close()
                bot.send_message(chat_id=uid, text=f"✅ উইথড্র রিকোয়েস্ট সফল! {float(d['amt'])/200} টাকা দ্রুত আপনার {d['method']} নাম্বারে পাঠিয়ে দেওয়া হবে।")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
