import os, telebot, psycopg2, threading, random
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

TOKEN = os.environ.get("BOT_TOKEN")
# সরাসরি Neon URL টি এখানে ভেরিয়েবল হিসেবে দিয়ে দিচ্ছি যাতে এরর না হয়
RAW_DB_URL = "postgresql://neondb_owner:npg_mY1anzgdSXs8@ep-aged-king-a1jzmmxq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    # কানেকশন স্ট্রিংটি পরিষ্কার করে নেওয়া হচ্ছে
    db_url = RAW_DB_URL.strip()
    return psycopg2.connect(db_url)

# ডাটাবেজ মাস্টার ফিক্স
def master_db_fix():
    print("Connecting to Neon and checking schema...")
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # টেবিল তৈরি
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY, 
                name TEXT DEFAULT 'User',
                balance FLOAT DEFAULT 0, 
                refs INT DEFAULT 0,
                referred_by BIGINT DEFAULT NULL
            );
        """)
        
        # নিশ্চিত করা যে 'name' কলাম আছে
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='name';")
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN name TEXT DEFAULT 'User';")
            
        conn.commit()
        cur.close()
        print("Neon Database is ready!")
    except Exception as e:
        print(f"Database Initialization Error: {e}")
    finally:
        if conn: conn.close()

# --- এপিআই রুটস ---
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    if not uid: return jsonify({"error": "No ID"})
    
    conn = None
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT balance, name, refs FROM users WHERE user_id = %s", (uid,))
        res = cur.fetchone()
        if res:
            return jsonify({
                "balance": res[0], "name": res[1], "refs": res[2],
                "ref_link": f"https://t.me/EarnQuick_Official_bot?start={uid}"
            })
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: cur.close(); conn.close()

# অন্যান্য রুট (postback, spin, withdraw, history) আগের মতোই থাকবে...

@app.route("/")
def home():
    return "Backend connected to Neon Successfully!"

if __name__ == "__main__":
    master_db_fix()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
