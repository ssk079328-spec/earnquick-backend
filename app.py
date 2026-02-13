import os
import telebot
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 

# Postgresql (P বড় হাতের) ফিক্স
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, name TEXT, balance FLOAT DEFAULT 0, refs INT DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS withdraws (id SERIAL PRIMARY KEY, user_id BIGINT, name TEXT, method TEXT, phone TEXT, amount INT, status TEXT DEFAULT 'Pending')")
    conn.commit(); cur.close(); conn.close()

@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "refs": res[1]}) if res else jsonify({"balance":0,"refs":0})

@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid, amount = data['user_id'], int(data['amount'])
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = %s", (uid,))
    balance = cur.fetchone()[0]
    
    if balance >= amount and amount >= 1000:
        cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, uid))
        cur.execute("INSERT INTO withdraws (user_id, name, method, phone, amount) VALUES (%s, %s, %s, %s, %s)", 
                    (uid, data['name'], data['method'], data['phone'], amount))
        conn.commit()
        # এডমিন নোটিফিকেশন
        bot.send_message(ADMIN_ID, f"💰 **নতুন উইথড্র!**\n\n👤 নাম: {data['name']}\n📞 নাম্বার: {data['phone']}\n💰 পরিমাণ: {amount}\n💳 মেথড: {data['method']}")
        msg = "রিকোয়েস্ট সফল হয়েছে!"
    else:
        msg = "পর্যাপ্ত ব্যালেন্স নেই (মিনিমাম ১০০০)"
    
    cur.close(); conn.close()
    return jsonify({"message": msg})

@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "OK"

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
