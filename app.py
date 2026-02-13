import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 

if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_db():
    conn = get_db(); cur = conn.cursor()
    # লগের এরর ফিক্স করতে কলামগুলো নিশ্চিত করা হচ্ছে
    try:
        cur.execute("SELECT name FROM users LIMIT 1;")
    except:
        conn.rollback()
        # টেবিলটি নতুন করে সঠিক কলামসহ তৈরি করা হচ্ছে
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("""
            CREATE TABLE users (
                user_id BIGINT PRIMARY KEY, 
                name TEXT,
                balance FLOAT DEFAULT 0, 
                refs INT DEFAULT 0
            )
        """)
    conn.commit(); cur.close(); conn.close()

@app.route("/")
def home(): return "Backend Active"

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    name = request.args.get('name', 'User')
    if not uid: return jsonify({"error": "No ID"}), 400
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    
    if not res:
        # এখানে 'name' কলামে ডাটা ইনসার্ট করা হচ্ছে যা আগে এরর দিচ্ছিল
        cur.execute("INSERT INTO users (user_id, name, balance, refs) VALUES (%s, %s, 0, 0)", (uid, name))
        conn.commit()
        res = (0, 0)
    
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]})

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    if not uid: return "Error", 400
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "Success"

@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid, amount = data['user_id'], int(data['amount'])
    method, phone = data['method'], data['phone']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if res and res[0] >= amount:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, uid))
        conn.commit()
        bot.send_message(ADMIN_ID, f"💰 **Withdraw!**\nUser: {data['name']}\nAmt: {amount}\nPh: {phone}\nVia: {method}")
        return jsonify({"status": "success", "message": "Request Sent!"})
    return jsonify({"status": "error", "message": "Low Balance!"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
