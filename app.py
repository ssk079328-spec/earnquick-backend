import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_URL = "postgresql://earnquick_backend_user:nxsBqFbwGhoq5ryV3AkYssb0QsdkBZXT@dpg-d66lfvumcj7s73dlip5g-a/earnquick_backend"
ADMIN_ID = 8145444675

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

# ডাটাবেস টেবিল সঠিক করা (প্রয়োজন হলে একবার চলবে)
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, balance FLOAT DEFAULT 0.0, refs INTEGER DEFAULT 0);")
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/data')
def data():
    uid = request.args.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (uid,))
    conn.commit()
    cur.execute("SELECT balance, refs FROM users WHERE user_id = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"balance": row[0], "refs": row[1]})

@app.route('/update-balance', methods=['POST'])
def update():
    data = request.json
    uid = data.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

# অ্যাডমিন রুট - সব ইউজার দেখা
@app.route('/admin/users')
def admin_users():
    admin_id = request.args.get('admin_id')
    if str(admin_id) != str(ADMIN_ID):
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, balance FROM users ORDER BY balance DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    users = [{"user_id": r[0], "balance": r[1]} for r in rows]
    return jsonify({"users": users})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
