from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os, json, psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

# Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
bot = telegram.Bot(token=BOT_TOKEN)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init():
    conn = get_db()
    cur = conn.cursor()
    # ডাটাবেস টেবিল এবং কলাম নিশ্চিত করা (অটো-ফিক্স)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY, 
            balance NUMERIC DEFAULT 0, 
            refs INTEGER DEFAULT 0
        );
        ALTER TABLE users ADD COLUMN IF NOT EXISTS parent_id BIGINT;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_new BOOLEAN DEFAULT TRUE;
        
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY, 
            user_id BIGINT, 
            amount NUMERIC, 
            method TEXT, 
            num TEXT,
            status TEXT DEFAULT 'Pending'
        );
    """)
    conn.commit()
    # টেলিগ্রাম ওয়েব-হুক কানেক্ট করা
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    cur.close()
    conn.close()
    return "Backend is Active & Database Updated!"

@app.route("/data")
def data():
    uid = request.args.get('user_id')
    if not uid:
        return jsonify({"error": "No user_id provided"}), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    # ইউজার ডাটা চেক করা
    cur.execute("SELECT balance, refs, is_new, parent_id FROM users WHERE id = %s", (uid,))
    row = cur.fetchone()
    
    # ইউজার না থাকলে নতুন রো তৈরি করা
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (uid,))
        conn.commit()
        row = (0, 0, True, None)

    # ২-লেভেল রেফারেল কমিশন প্রসেসিং
    if row[2]: # row[2] হলো is_new কলাম
        parent = row[3] # row[3] হলো parent_id কলাম
        if parent:
            # লেভেল ১ কে ২০০ পয়েন্ট দেওয়া
            cur.execute("UPDATE users SET balance = balance + 200, refs = refs + 1 WHERE id = %s", (parent,))
            
            # লেভেল ২ চেক করা (প্যারেন্টের প্যারেন্ট)
            cur.execute("SELECT parent_id FROM users WHERE id = %s", (parent,))
            gp_row = cur.fetchone()
            if gp_row and gp_row[0]:
                # লেভেল ২ কে ৫০ পয়েন্ট দেওয়া
                cur.execute("UPDATE users SET balance = balance + 50 WHERE id = %s", (gp_row[0],))
        
        # ইউজারকে পুরাতন হিসেবে মার্ক করা (যাতে বারবার রেফার বোনাস না যায়)
        cur.execute("UPDATE users SET is_new = False WHERE id = %s", (uid,))
        conn.commit()
    
    # সর্বশেষ ব্যালেন্স রিটার্ন করা
    cur.execute("SELECT balance, refs FROM users WHERE id = %s", (uid,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    
    return jsonify({
        "balance": float(res[0]) if res else 0,
        "refs": res[1] if res else 0
    })

@app.route("/add_point", methods=['POST'])
def add_point():
    d = request.json
    uid = d.get('user_id')
    points = d.get('point', 5)
    
    if not uid:
        return "Missing ID", 400
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (points, uid))
    conn.commit()
    cur.close()
    conn.close()
    return "ok"

@app.route(f"/webhook/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.message:
        uid = update.message.from_user.id
        
        # /start কমান্ড হ্যান্ডলিং
        if update.message.text and "/start" in update.message.text:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
            if not cur.fetchone():
                p_id = None
                args = update.message.text.split()
                if len(args) > 1 and args[1].isdigit():
                    p_id = int(args[1])
                cur.execute("INSERT INTO users (id, parent_id) VALUES (%s, %s)", (uid, p_id))
                conn.commit()
            
            # বটের বাটন
            web_url = "https://ssk079328-spec.github.io/earnquick-frontend/"
            btn = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url=web_url))]]
            update.message.reply_text(
                f"স্বাগতম {update.message.from_user.first_name}!\nEarnQuick Pro থেকে আয় শুরু করতে নিচের বাটনে ক্লিক করুন।",
                reply_markup=telegram.InlineKeyboardMarkup(btn)
            )
            cur.close()
            conn.close()

        # মিনি অ্যাপ থেকে উইথড্র রিকোয়েস্ট গ্রহণ করা
        elif update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            if data.get('action') == 'withdraw':
                amt = float(data['amt'])
                method = data['method']
                num = data['num']
                
                conn = get_db()
                cur = conn.cursor()
                # রিকোয়েস্ট সেভ করা
                cur.execute(
                    "INSERT INTO withdrawals (user_id, amount, method, num) VALUES (%s, %s, %s, %s)",
                    (uid, amt, method, num)
                )
                # ব্যালেন্স কাটা
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amt, uid))
                conn.commit()
                cur.close()
                conn.close()
                
                update.message.reply_text(f"✅ উইথড্র রিকোয়েস্ট সফল হয়েছে!\n\nপদ্ধতি: {method}\nনাম্বার: {num}\nপয়েন্ট: {amt}\nটাকা: {amt/200} TK\n\nখুব শীঘ্রই পেমেন্ট পেয়ে যাবেন।")
                
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
