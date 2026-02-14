import os, telebot, psycopg2, threading, random
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 # আপনার টেলিগ্রাম আইডি

if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

# ডাটাবেজ এবং টেবিল অটো-ক্রিয়েশন ও আপডেট লজিক
def init_db():
    conn = get_db()
    cur = conn.cursor()
    # মূল টেবিল তৈরি (যদি না থাকে)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, 
            balance FLOAT DEFAULT 0, 
            refs INT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            method TEXT,
            status TEXT DEFAULT 'Pending',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # আপনার এরর সমাধানের জন্য 'name' কলামটি অটো-ফিক্স
    try:
        cur.execute("ALTER TABLE users ADD COLUMN name TEXT DEFAULT 'User';")
        print("Column 'name' added successfully.")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback() # কলামটি ইতিমধ্যে থাকলে এরর এড়িয়ে যাবে
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
        
    conn.commit()
    cur.close()
    conn.close()

# --- টেলিগ্রাম বট লজিক ---
@bot.message_handler(commands=['start'])
def start(message):
    uid, name = message.from_user.id, message.from_user.first_name
    args = message.text.split()
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (uid,))
    if not cur.fetchone():
        ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        cur.execute("INSERT INTO users (user_id, name, referred_by) VALUES (%s, %s, %s)", (uid, name, ref_id))
        if ref_id:
            cur.execute("UPDATE users SET balance = balance + 50, refs = refs + 1 WHERE user_id = %s", (ref_id,))
            bot.send_message(ref_id, "🎉 কেউ আপনার লিঙ্কে জয়েন করেছে! আপনি ৫০ পয়েন্ট বোনাস পেয়েছেন।")
        conn.commit()
    cur.close(); conn.close()
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App 🚀", url="https://t.me/EarnQuick_Official_bot/app"))
    bot.reply_to(message, f"স্বাগতম {name}!\nরেফার করে ও অ্যাড দেখে ইনকাম শুরু করুন।", reply_markup=markup)

# --- এপিআই রুটস ---
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    if not uid:
        return jsonify({"error": "User ID missing"}), 400
        
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT balance, name, refs FROM users WHERE user_id = %s", (uid,))
        res = cur.fetchone()
        if res:
            return jsonify({
                "balance": res[0], 
                "name": res[1], 
                "refs": res[2], 
                "ref_link": f"https://t.me/EarnQuick_Official_bot?start={uid}"
            })
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close(); conn.close()

@app.route("/postback")
def add_points():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "OK"

@app.route("/spin", methods=['POST'])
def spin_game():
    uid = request.json.get('user_id')
    win = random.choice([0, 1, 2, 5, 10, 3])
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (win, uid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"win": win})

@app.route("/withdraw", methods=['POST'])
def handle_withdraw():
    d = request.json
    uid, amt, mthd, phn = d['user_id'], int(d['amount']), d['method'], d['phone']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, name FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] >= amt:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amt, uid))
        cur.execute("INSERT INTO withdrawals (user_id, amount, method) VALUES (%s, %s, %s)", (uid, amt, mthd))
        conn.commit()
        bot.send_message(ADMIN_ID, f"💰 **Withdraw Alert!**\nUser: {res[1]}\nAmount: {amt}\nVia: {mthd}\nPhone: {phn}")
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route("/history")
def get_history():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT amount, method, status FROM withdrawals WHERE user_id = %s ORDER BY id DESC", (uid,))
    data = [{"amount": r[0], "method": r[1], "status": r[2]} for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(data)

@app.route("/")
def home():
    return "Backend is running smoothly!"

if __name__ == "__main__":
    init_db() # অ্যাপ চালু হওয়ার সময় ডাটাবেস চেক করবে
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
