import os, telebot, psycopg2, threading
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# এনভায়রনমেন্ট ভেরিয়েবল থেকে তথ্য নেওয়া
TOKEN = os.environ.get("BOT_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = 8145444675 # আপনার আইডি

if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require')

# ডাটাবেজ এবং টেবিল সেটআপ (Fixing name column error)
def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, 
            name TEXT,
            balance FLOAT DEFAULT 0, 
            refs INT DEFAULT 0
        )
    """)
    conn.commit(); cur.close(); conn.close()

@app.route("/")
def home(): return "Backend is Live!"

# অ্যাডমিন প্যানেল রুট (গোপন লিঙ্ক)
@app.route("/admin-panel-secret-8145")
def admin_panel():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except: return "admin.html ফাইলটি পাওয়া যায়নি!"

# ইউজারের ডাটা লোড করা
@app.route("/data")
def get_data():
    uid = request.args.get('user_id')
    name = request.args.get('name', 'User')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance, name FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id, name, balance) VALUES (%s, %s, 0)", (uid, name))
        conn.commit(); res = (0, name)
    cur.close(); conn.close()
    return jsonify({"balance": res[0], "name": res[1]})

# অ্যাড দেখে ইনকাম যোগ করা
@app.route("/postback")
def postback():
    uid = request.args.get('user_id')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = %s", (uid,))
    conn.commit(); cur.close(); conn.close()
    return "Success"

# উইথড্র সিস্টেম (টেলিগ্রাম নোটিফিকেশনসহ)
@app.route("/withdraw", methods=['POST'])
def withdraw():
    data = request.json
    uid, amount, method, phone, name = data['user_id'], int(data['amount']), data['method'], data['phone'], data['name']
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
    res = cur.fetchone()
    
    if res and res[0] >= amount:
        cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, uid))
        conn.commit()
        # অ্যাডমিনকে জানানো
        msg = f"💰 **New Withdraw!**\n👤: {name}\n🆔: {uid}\n💵: {amount} Pts\n📲: {method}\n📞: {phone}"
        bot.send_message(ADMIN_ID, msg)
        cur.close(); conn.close()
        return jsonify({"status": "success", "message": "রিকোয়েস্ট পাঠানো হয়েছে!"})
    
    cur.close(); conn.close()
    return jsonify({"status": "error", "message": "পর্যাপ্ত ব্যালেন্স নেই!"})

if __name__ == "__main__":
    init_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
