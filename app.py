import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# এটি আপনার মিনি অ্যাপ থেকে ডাটা আসার অনুমতি দেবে
CORS(app)

# আপনার ডাটাবেস ইউআরএল
DATABASE_URL = "postgresql://earnquick_backend_user:nxsBqFbwGhoq5ryV3AkYssb0QsdkBZXT@dpg-d66lfvumcj7s73dlip5g-a/earnquick_backend"

def get_db_connection():
    # রেন্ডারের জন্য sslmode='require' জরুরি
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    """অটোমেটিক টেবিল তৈরি করার ফাংশন"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            balance FLOAT DEFAULT 0.0,
            refs INTEGER DEFAULT 0,
            username TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Database Initialized!")

# অ্যাপ চালুর সময় টেবিল চেক করা
init_db()

@app.route('/')
def home():
    return "EarnQuick Backend is Running!"

# ইউজার ডাটা লোড করা
@app.route('/data', methods=['GET'])
def get_data():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID missing"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # ইউজার না থাকলে নতুন করে তৈরি করা
    cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
    conn.commit()
    
    cur.execute("SELECT balance, refs FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    return jsonify({
        "balance": row[0] if row else 0.0,
        "refs": row[1] if row else 0
    })

# রিয়েল টাইম ব্যালেন্স আপডেট
@app.route('/update-balance', methods=['POST'])
def update_balance():
    data = request.json
    user_id = data.get('user_id')
    points_to_add = data.get('points', 5.0) # ডিফল্ট ৫ পয়েন্ট

    if not user_id:
        return jsonify({"success": False, "message": "User ID missing"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (points_to_add, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Points Added Successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Render-এর পোর্টের জন্য
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
