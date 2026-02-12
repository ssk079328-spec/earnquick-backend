from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 

bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, balance NUMERIC DEFAULT 0, refs INTEGER DEFAULT 0, parent_id BIGINT, is_new BOOLEAN DEFAULT TRUE, last_bonus DATE);
        CREATE TABLE IF NOT EXISTS withdrawals (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, method TEXT, num TEXT, status TEXT DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id BIGINT, type TEXT, amount NUMERIC, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit(); cur.close(); conn.close()
    return "🚀 EarnQuick Pro Live!"

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if uid and uid.isdigit():
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (int(uid),))
        cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Monetag Ad', 5)", (int(uid),))
        conn.commit(); cur.close(); conn.close()
        return "OK", 200
    return "Invalid", 400

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit(); row = (0, 0, True, None)
    
    if row[2] and row[3]: 
        cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (row[3],))
        cur.execute("SELECT parent_id FROM users WHERE id = %s", (row[3],))
        gp = cur.fetchone()
        if gp and gp[0]: cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp[0],))
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone(); cur.close(); conn.close()
    return jsonify({"balance": float(res[0]), "refs": res[1]})

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid, p = d.get('user_id'), d.get('point')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (uid,))
    cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Ad View', %s)", (uid, p))
    conn.commit(); cur.close(); conn.close()
    return "ok"

@app.route("/claim_bonus", methods=['POST'])
def claim_bonus():
    uid = request.json.get('user_id')
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT last_bonus FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] == today:
        return jsonify({"success": False, "message": "আজ অলরেডি নিয়েছেন!"})
    cur.execute("UPDATE users SET balance = balance + 50, last_bonus = %s WHERE id = %s", (today, uid))
    cur.execute("INSERT INTO history (user_id, type, amount) VALUES (%s, 'Daily Bonus', 50)", (uid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "message": "৫০ পয়েন্ট পেয়েছেন!"})

@app.route("/admin/all_data")
def admin_data():
    admin_id = request.args.get('admin_id')
    if str(admin_id) != str(ADMIN_ID): return "Denied", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, balance, refs FROM users ORDER BY balance DESC LIMIT 50")
    u_list = cur.fetchall()
    cur.execute("SELECT id, user_id, amount, method, num FROM withdrawals WHERE status = 'Pending'")
    w_list = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"users": [{"id":r[0], "bal":float(r[1]), "ref":r[2]} for r in u_list], "withdrawals": [{"id":r[0], "uid":r[1], "amt":float(r[2]), "method":r[3], "num":r[4]} for r in w_list]})

@app.route("/admin/approve", methods=['POST'])
def approve_payment():
    d = request.json
    if str(d.get('admin_id')) != str(ADMIN_ID): return "Unauthorized", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE withdrawals SET status = 'Success' WHERE id = %s", (d.get('w_id'),))
    conn.commit(); cur.close(); conn.close()
    return "Paid"

@app.route("/history")
def get_history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT type, amount, status FROM (SELECT 'Withdraw' as type, amount, status, id FROM withdrawals WHERE user_id = %s UNION ALL SELECT 'Earning' as type, amount, 'Success' as status, id FROM history WHERE user_id = %s) as combined ORDER BY id DESC LIMIT 15", (uid, uid))
    rows = cur.fetchall(); cur.close(); conn.close()
    return jsonify([{"type": r[0], "amount": float(r[1]), "status": r[2]} for r in rows])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
