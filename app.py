import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_URL = "postgresql://earnquick_backend_user:nxsBqFbwGhoq5ryV3AkYssb0QsdkBZXT@dpg-d66lfvumcj7s73dlip5g-a/earnquick_backend"

def init_db():
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    # ডাটাবেস রিসেট করে সঠিক কলাম তৈরি করা
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute('''
        CREATE TABLE users (
            user_id BIGINT PRIMARY KEY,
            balance FLOAT DEFAULT 0.0,
            refs INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/data')
def get_data():
    uid = request.args.get('user_id')
    conn = psycopg2.connect(DB_URL, sslmode='require')
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
    pts = data.get('points', 5.0)
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (pts, uid))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
