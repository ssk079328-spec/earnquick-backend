from flask import Flask, request, jsonify
from flask_cors import CORS
import telegram
import os
import json
import psycopg2
from datetime import date

app = Flask(__name__)
CORS(app)

# --- কনফিগারেশন (Render Environment Variables থেকে আসবে) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# আপনার GitHub Pages লিঙ্ক (যেখানে index.html আছে)
WEB_APP_URL = "https://ssk079328-spec.github.io/earnquick-frontend/"

bot = telegram.Bot(token=BOT_TOKEN)

# --- পয়েন্ট সিস্টেম সেটিংস ---
AD_REWARD = 5        # প্রতি বিজ্ঞাপনে ৫ পয়েন্ট
REFER_REWARD = 200   # প্রতি রেফারে ২০০ পয়েন্ট
CONVERSION_RATE = 200 # ১ টাকা = ২০০ পয়েন্ট (কারণ ৪০০০ পয়েন্ট = ২০ টাকা)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def init_system():
    conn = get_db_connection()
    cur = conn.cursor()
    # ইউজার এবং উইথড্র টেবিল তৈরি
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            balance NUMERIC(10, 2) DEFAULT 0.00,
            ads_today INTEGER DEFAULT 0,
            refs INTEGER DEFAULT 0,
            last_ad_date DATE,
            referrer_id BIGINT
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount_points NUMERIC(10, 2),
            method TEXT,
            account_number TEXT,
            status TEXT DEFAULT 'Pending',
            request_date DATE DEFAULT CURRENT_DATE
        );
    """)
    conn.commit()
    # ওয়েব হুক সেট করা
    bot.set_webhook(url=RENDER_URL + WEBHOOK_PATH)
    cur.close()
    conn.close()
    return "EarnQuick Backend is Live & Database Ready!"

@app.route("/data", methods=['GET'])
def get_user_data():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance, ads_today, refs, last_ad_date FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    
    if row:
        balance, ads, refs, last_date = row
        # তারিখ পরিবর্তন হলে ডেইলি অ্যাড কাউন্ট রিসেট
        if last_date != date.today():
            ads = 0
        data = {"balance": float(balance), "ads": ads, "refs": refs}
    else:
        data = {"balance": 0.00, "ads": 0, "refs": 0}
    
    cur.close()
    conn.close()
    return jsonify(data)

@app.route(WEBHOOK_PATH, methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
        conn = get_db_connection()
        cur = conn.cursor()
        
        # নতুন ইউজার রেজিস্ট্রেশন
        cur.execute("INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING", (user_id,))
        conn.commit()

        if update.message.text and "/start" in update.message.text:
            # রেফারেল হ্যান্ডলিং
            args = update.message.text.split()
            if len(args) > 1 and args[1].isdigit():
                ref_id = int(args[1])
                # নিজের লিঙ্কে নিজে ক্লিক করলে বোনাস পাবে না
                if ref_id != user_id:
                    # চেক করা হচ্ছে ইউজারটি আগে থেকেই রেফারড কি না
                    cur.execute("SELECT referrer_id FROM users WHERE id = %s", (user_id,))
                    if cur.fetchone()[0] is None:
                        cur.execute("UPDATE users SET balance = balance + %s, refs = refs + 1 WHERE id = %s", (REFER_REWARD, ref_id))
                        cur.execute("UPDATE users SET referrer_id = %s WHERE id = %s", (ref_id, user_id))
                        conn.commit()

            # ওয়েলকাম মেসেজ ও বাটন
            keyboard = [[telegram.InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=telegram.WebAppInfo(url=WEB_APP_URL))]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(f"হ্যালো {user_name}! 👋\nEarnQuick Pro-তে আপনাকে স্বাগতম। আয় শুরু করতে নিচের বাটনে ক্লিক করুন।", reply_markup=reply_markup)

        # মিনি অ্যাপ থেকে পাঠানো ডেটা হ্যান্ডেল
        elif update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            
            if data['action'] == 'ad':
                # প্রতি অ্যাডে ৫ পয়েন্ট যোগ
                cur.execute("UPDATE users SET balance = balance + %s, ads_today = ads_today + 1, last_ad_date = %s WHERE id = %s", (AD_REWARD, date.today(), user_id))
                conn.commit()
                update.message.reply_text(f"✅ অভিনন্দন! আপনি {AD_REWARD} পয়েন্ট পেয়েছেন।")
                
            elif data['action'] == 'withdraw':
                # উইথড্র রিকোয়েস্ট জমা দেওয়া
                cur.execute("INSERT INTO withdrawals (user_id, amount_points, method, account_number) VALUES (%s, %s, %s, %s)", 
                            (user_id, data['amt'], data['method'], data['num']))
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (data['amt'], user_id))
                conn.commit()
                update.message.reply_text(f"💰 আপনার উইথড্র রিকোয়েস্ট সফল হয়েছে! খুব শীঘ্রই পেমেন্ট পাবেন।")

        cur.close()
        conn.close()
        
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
