import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import types
import threading

# --- কনফিগারেশন (সঠিক তথ্য দিন) ---
TOKEN = "YOUR_BOT_TOKEN" 
DB_URL = "postgresql://earnquick_backend_user:nxsBqFbwGhoq5ryV3AkYssb0QsdkBZXT@dpg-d66lfvumcj7s73dlip5g-a.singapore-postgres.render.com/earnquick_backend"
ADMIN_ID = 8145444675 # আপনার টেলিগ্রাম আইডি

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL)

# --- অটোমেটিক ডাটাবেস টেবিল তৈরি ---
def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            name TEXT,
            balance INT DEFAULT 0,
            refs INT DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            type TEXT,
            amount INT,
            status TEXT DEFAULT 'Success',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            number TEXT,
            method TEXT,
            status TEXT DEFAULT 'Pending'
        );
    """)
    conn.commit(); cur.close(); conn.close()

# --- টেলিগ্রাম বট কমান্ডস ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        if ref_id and ref_id.isdigit() and int(ref_id) != uid:
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (int(ref_id),))
            bot.send_message(ref_id, f"🎊 অভিনন্দন! আপনার রেফারে {name} জয়েন করেছে। ২০০ পয়েন্ট যোগ হয়েছে।")
        conn.commit()
    cur.close(); conn.close()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 ওপেন অ্যাপ", web_app=types.WebAppInfo("https://newsnetwork24.42web.io/")))
    bot.send_message(message.chat.id, f"স্বাগতম {name}! কাজ শুরু করতে অ্যাপটি ওপেন করুন।", reply_markup=markup)

# --- এপিআই এন্ডপয়েন্ট (অ্যাপের জন্য) ---

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]}) if res else jsonify({"balance": 0, "refs": 0})

@app.route("/history")
def get_history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT type, amount, status FROM history WHERE user_id = %s ORDER BY id DESC LIMIT 10", (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"type": r[0], "amount": r[1], "status": r[2]} for r in rows])

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if uid:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
        cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Ad View', 5)", (int(uid),))
        conn.commit(); cur.close(); conn.close()
        return "OK", 200
    return "Error", 400

@app.route("/withdraw", methods=['POST'])
def withdraw():
    d = request.json
    uid, amt, num, method = d['user_id'], int(d['amt']), d['num'], d['method']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = %s", (uid,))
    bal = cur.fetchone()[0]
    if bal >= amt:
        cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amt, uid))
        cur.execute("INSERT INTO withdrawals (user_id, amount, number, method) VALUES (%s, %s, %s, %s)", (uid, amt, num, method))
        cur.execute("INSERT INTO history (user_id, type, amount, status) VALUES (%s, 'Withdrawal', %s, 'Pending')", (uid, amt))
        conn.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Insufficient Balance"})

# --- এডমিন এপিআই ---
@app.route("/admin/all_data")
def admin_data():
    if int(request.args.get('admin_id')) != ADMIN_ID: return "Unauthorized", 401
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM withdrawals WHERE status = 'Pending'")
    withdrawals = cur.fetchall()
    cur.execute("SELECT id, name, balance FROM users LIMIT 100")
    users = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({
        "withdrawals": [{"id": w[0], "user_id": w[1], "amt": w[2], "num": w[3], "method": w[4]} for w in withdrawals],
        "users": [{"id": u[0], "name": u[1], "bal": u[2]} for u in users]
    })

@app.route("/admin/approve", methods=['POST'])
def approve():
    d = request.json
    if int(d['admin_id']) != ADMIN_ID: return "Error", 401
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE withdrawals SET status = 'Success' WHERE id = %s", (d['w_id'],))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
