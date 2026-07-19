import os
import threading
import hashlib
import secrets
import time
import telebot
from telebot import types
import google.generativeai as genai
from flask import Flask
import psycopg2
from psycopg2 import pool

app = Flask('')

@app.route('/')
def home():
    return "Production Multi-Tenant AI Shop Engine with Persistent PostgreSQL is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ Error: DATABASE_URL environment variable is missing!")

# Connection Pool Initialization
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("✅ PostgreSQL Connection Pool initialized.")
except Exception as e:
    print(f"❌ Failed to connect to PostgreSQL: {e}")
    raise e

# Safe connection retrieval helper (Handles Render auto-reconnects)
def get_safe_connection():
    try:
        conn = db_pool.getconn()
        # ግንኙነቱ በህይወት መኖሩን ቼክ ማድረግ
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        print("🔄 Re-initializing connection pool due to disconnect...")
        global db_pool
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
        return db_pool.getconn()

def init_db():
    conn = get_safe_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS stores (
                                token TEXT PRIMARY KEY,
                                store_name TEXT,
                                admin_id BIGINT,
                                password_hash TEXT,
                                password_salt TEXT,
                                telebirr TEXT,
                                is_active INTEGER DEFAULT 1)''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                                id SERIAL PRIMARY KEY,
                                token TEXT,
                                name_am TEXT,
                                name_en TEXT,
                                price REAL,
                                stock INTEGER,
                                desc_am TEXT,
                                desc_en TEXT,
                                image_url TEXT)''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                                id SERIAL PRIMARY KEY,
                                token TEXT,
                                customer_id BIGINT,
                                status_am TEXT,
                                status_en TEXT,
                                total_price REAL)''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_langs (
                                chat_id BIGINT PRIMARY KEY,
                                lang TEXT)''')
            conn.commit()
    finally:
        db_pool.putconn(conn)

init_db()

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt

STRINGS = {
    "am": {
        "welcome": "እንኳን ወደ AI የሽያጭ ረዳት ቦት በደህና መጡ! 👋",
        "shop": "🛍️ ምርቶችን እይ", "cart": "🛒 የእኔ ጋሪ", "track": "📦 ትዕዛዝ መከታተያ", "faq": "❓ መረጃ (FAQ)",
        "empty": "🛒 ጋሪዎ በአሁኑ ሰዓት ባዶ ነው።", "added": "ወደ ጋሪ ተጨምሯል! 🛒", "total": "አጠቃላይ ድምር",
        "price_label": "ዋጋ", "checkout_btn": "💳 ሂሳብ ማጠቃለያ", "clear_btn": "🗑️ ጋሪ አጽዳ",
        "enter_id": "🔢 እባክዎ የትዕዛዝ ቁጥርዎን (Order ID) ያስገቡ፦", 
        "not_found": "❌ የትዕዛዝ ቁጥሩ አልተገኘም ወይም የዚህ ሱቅ አይደለም።", "invalid_id": "❌ የተሳሳተ ቁጥር ገብቷል።",
        "approved_msg": "🎉 ደስ የሚል ዜና! የትዕዛዝ ቁጥርዎ ክፍያ ተረጋግጦ ዕቃው እየመጣላችሁ ነው። 🛵",
        "receipt_prompt": "እባክዎ የከፈሉበትን የቴሌብር ደረሰኝ (Screenshot ፎቶ) እዚህ ላይ ይላኩ። 📸",
        "faq_text": "ℹ️ **ስለ ሱቃችን መረጃ**\n\n📍 አድራሻችን፦ አዲስ አበባ፣ ኢትዮጵያ\n📞 ስልክ፦ 0911223344\n⏱️ የስራ ሰዓት፦ ከሰኞ - ቅዳሜ (2:00 ሰዓት - 12:00 ሰዓት)\n\nማንኛውንም ጥያቄ እዚህ በመጻፍ AI ረዳታችንን መጠየቅ ይችላሉ!"
    },
    "en": {
        "welcome": "Welcome to AI Customer Service Bot! 👋",
        "shop": "🛍️ Shop Products", "cart": "🛒 My Cart", "track": "📦 Track Order", "faq": "❓ FAQ Info",
        "empty": "🛒 Your cart is currently empty.", "added": "Added to cart! 🛒", "total": "Total",
        "price_label": "Price", "checkout_btn": "💳 Checkout", "clear_btn": "🗑️ Clear Cart",
        "enter_id": "🔢 Please enter your Order ID:", 
        "not_found": "❌ Order ID not found or invalid for this store.", "invalid_id": "❌ Invalid ID entered.",
        "approved_msg": "🎉 Great news! Your payment has been approved and your item is on the way! 🛵",
        "receipt_prompt": "Please send the Telebirr payment confirmation screenshot here. 📸",
        "faq_text": "ℹ️ **About Our Store**\n\n📍 Location: Addis Ababa, Ethiopia\n📞 Phone: +251911223344\n⏱️ Hours: Mon - Sat (8:00 AM - 6:00 PM)\n\nYou can ask our AI anything else by just typing your question!"
    }
}

user_carts = {}
active_sessions = {}  
admin_states = {}     
login_attempts = {}   

def get_main_menu(lang):
    ln = STRINGS[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(ln["shop"]), types.KeyboardButton(ln["cart"]),
               types.KeyboardButton(ln["track"]), types.KeyboardButton(ln["faq"]))
    return markup

def setup_bot_handlers(token):
    bot = telebot.TeleBot(token)

    def get_store_info():
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT store_name, admin_id, telebirr, is_active, password_hash, password_salt FROM stores WHERE token=%s", (token,))
                row = cursor.fetchone()
        finally:
            db_pool.putconn(conn)
        if row:
            return {"store_name": row[0], "admin_id": row[1], "telebirr": row[2], "is_active": row[3], "pass_hash": row[4], "salt": row[5]}
        return None

    def check_active_middleware(chat_id):
        store = get_store_info()
        if not store:
            bot.send_message(chat_id, "🏪 ይህ ሱቅ ገና አልተመዘገበም።")
            return False
        if not store["is_active"]:
            bot.send_message(chat_id, "❌ ይህ ሱቅ ንቁ አይደለም።")
            return False
        return True

    def get_user_lang(chat_id):
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT lang FROM user_langs WHERE chat_id=%s", (chat_id,))
                row = cursor.fetchone()
        finally:
            db_pool.putconn(conn)
        return row[0] if row else "am"

    def is_verified_admin(chat_id):
        store = get_store_info()
        session_key = (token, chat_id)
        if store and store["admin_id"] == chat_id:
            if session_key in active_sessions and time.time() < active_sessions[session_key]:
                return True
        return False

    @bot.message_handler(commands=['start'])
    def choose_language(message):
        if not check_active_middleware(message.chat.id): return
        store = get_store_info()
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="shoplang_am"),
                   types.InlineKeyboardButton("English 🇬🇧", callback_data="shoplang_en"))
        bot.send_message(message.chat.id, f"🌐 Welcome to {store['store_name']}!\n\nቋንቋ ይምረጡ / Select Language:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("shoplang_"))
    def set_language(call):
        chat_id = call.message.chat.id
        if not check_active_middleware(chat_id): return
        lang_code = call.data.split("_")[1]
        
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''INSERT INTO user_langs (chat_id, lang) VALUES (%s, %s)
                                  ON CONFLICT (chat_id) DO UPDATE SET lang = EXCLUDED.lang''', (chat_id, lang_code))
                conn.commit()
        finally:
            db_pool.putconn(conn)
            
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, STRINGS[lang_code]["welcome"], reply_markup=get_main_menu(lang_code))

    @bot.message_handler(commands=['register'])
    def register_store(message):
        store = get_store_info()
        if store:
            bot.reply_to(message, "❌ ይህ ቦት ቀድሞውኑ ተመዝግቧል!")
            return
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            bot.reply_to(message, "⚠️ አጠቃቀም፦ `/register [የይለፍ_ቃል] [ሙሉ የሱቅ ስም]`")
            return
        password = args[1]
        store_name = args[2]
        h_pass, salt = hash_password(password)
        
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''INSERT INTO stores (token, store_name, admin_id, password_hash, password_salt, telebirr) 
                                  VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING''',
                               (token, store_name, message.chat.id, h_pass, salt, "0900000000"))
                conn.commit()
                affected = cursor.rowcount
        finally:
            db_pool.putconn(conn)
            
        if affected > 0:
            bot.reply_to(message, f"✅ ሱቅዎ '{store_name}' ተመዝግቧል! ለመግባት፦ `/login {password}`")
        else:
            bot.reply_to(message, "❌ ምዝገባው አልተሳካም።")

    @bot.message_handler(commands=['login'])
    def login_store(message):
        chat_id = message.chat.id
        store = get_store_info()
        if not store: return
            
        attempt_key = (token, chat_id)
        if attempt_key not in login_attempts:
            login_attempts[attempt_key] = {"count": 0, "lockout_until": 0}
            
        if time.time() < login_attempts[attempt_key]["lockout_until"]:
            bot.reply_to(message, "🔒 እገዳ ላይ ነዎት!")
            return

        args = message.text.split()
        if len(args) < 2: return
            
        input_pass = args[1]
        test_hash, _ = hash_password(input_pass, store["salt"])
        
        if test_hash == store["pass_hash"]:
            conn = get_safe_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE stores SET admin_id=%s WHERE token=%s", (chat_id, token))
                    conn.commit()
            finally:
                db_pool.putconn(conn)
            active_sessions[(token, chat_id)] = time.time() + 7200 
            bot.reply_to(message, "🔓 በስኬት ገብተዋል።")
        else:
            login_attempts[attempt_key]["count"] += 1
            if login_attempts[attempt_key]["count"] >= 5:
                login_attempts[attempt_key]["lockout_until"] = time.time() + 900
            bot.reply_to(message, "❌ የተሳሳተ የይለፍ ቃል!")

    @bot.message_handler(commands=['addproduct'])
    def start_add_product(message):
        if not is_verified_admin(message.chat.id): return
        bot.reply_to(message, "📝 እባክዎ የምርቱን መረጃ በዚህ ፎርማት ይጻፉ፦\n`[የአማርኛ ስም],[የእንግሊዝኛ ስም],[ዋጋ],[ብዛት],[አማርኛ መግለጫ],[እንግሊዝኛ መግለጫ]`")
        admin_states[(token, message.chat.id)] = {"state": "WAITING_PRODUCT_DETAILS", "data": {}}

    @bot.message_handler(func=lambda m: any(m.text == STRINGS[k]["shop"] for k in STRINGS if get_user_lang(m.chat.id) == k))
    def list_products(message):
        chat_id = message.chat.id
        if not check_active_middleware(chat_id): return
        lang = get_user_lang(chat_id)
        
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name_am, name_en, price, stock, desc_am, desc_en, image_url FROM products WHERE token=%s", (token,))
                rows = cursor.fetchall()
        finally:
            db_pool.putconn(conn)
            
        if not rows:
            bot.send_message(chat_id, "🛍️ ምንም ምርት የለም።" if lang == "am" else "🛍️ No products available.")
            return

        for row in rows:
            p_id, name_am, name_en, price, stock, desc_am, desc_en, image_url = row
            name = name_am if lang == "am" else name_en
            desc = desc_am if lang == "am" else desc_en
            status = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
            text = f"📦 **{name}**\n💰 {STRINGS[lang]['price_label']}: {price} ETB\n📌 Status: {status}\n📝 {desc}"
            
            markup = types.InlineKeyboardMarkup()
            if stock > 0:
                btn_text = "🛒 ወደ ጋሪ ጨምር" if lang == "am" else "🛒 Add to Cart"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"shopadd_{p_id}"))
            
            # 🟢 🟢 🟢 የፎቶ ስህተት ጥበቃ (Photo Fallback Layer) 🟢 🟢 🟢
            if image_url:
                try:
                    bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup, parse_mode="Markdown")
                    continue
                except telebot.api_helper.ApiTelegramException:
                    # ፎቶው ካልሰራ ወይም ከተሰረዘ በጽሑፍ ብቻ በሰላም ያልፋል
                    text += "\n\n⚠️ *(Image could not be loaded)*"
            
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("shopadd_"))
    def add_to_cart(call):
        chat_id = call.message.chat.id
        if not check_active_middleware(chat_id): return
        lang = get_user_lang(chat_id)
        p_id = int(call.data.split("_")[1])
        
        # Cross-Store Validation: ምርቱ የዚህ ሱቅ መሆኑን ማረጋገጥ
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM products WHERE id=%s AND token=%s", (p_id, token))
                exists = cursor.fetchone()
        finally:
            db_pool.putconn(conn)
            
        if not exists:
            bot.answer_callback_query(call.id, "❌ Error: Product mismatch.")
            return

        cart_key = (token, chat_id)
        if cart_key not in user_carts: user_carts[cart_key] = {}
        user_carts[cart_key][p_id] = user_carts[cart_key].get(p_id, 0) + 1
        bot.answer_callback_query(call.id, STRINGS[lang]["added"])

    @bot.message_handler(func=lambda m: any(m.text == STRINGS[k]["cart"] for k in STRINGS if get_user_lang(m.chat.id) == k))
    def show_cart(message):
        chat_id = message.chat.id
        if not check_active_middleware(chat_id): return
        lang = get_user_lang(chat_id)
        cart = user_carts.get((token, chat_id), {})
        if not cart:
            bot.send_message(chat_id, STRINGS[lang]["empty"])
            return
            
        total = 0
        text = "🛒 **Your Cart / የእርስዎ ጋሪ፦**\n\n"
        
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                for p_id, qty in list(cart.items()):
                    # 🟠 🟠 🟠 Token filter toegevoegd: Token leakage መከላከያ 🟠 🟠 🟠
                    cursor.execute("SELECT name_am, name_en, price FROM products WHERE id=%s AND token=%s", (p_id, token))
                    row = cursor.fetchone()
                    if row:
                        name = row[0] if lang == "am" else row[1]
                        price = row[2]
                        subtotal = price * qty
                        total += subtotal
                        text += f"▪️ {name} x {qty} = {subtotal} ETB\n"
                    else:
                        # የሌላ ሱቅ ምርት ከሆነ ከጋሪው በራስ ሰር ሰርዝ
                        del cart[p_id]
        finally:
            db_pool.putconn(conn)
            
        text += f"\n💵 **{STRINGS[lang]['total']}: {total} ETB**"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(STRINGS[lang]["checkout_btn"], callback_data="shop_checkout"),
                   types.InlineKeyboardButton(STRINGS[lang]["clear_btn"], callback_data="shop_clear"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data in ["shop_checkout", "shop_clear"])
    def cart_actions(call):
        chat_id = call.message.chat.id
        if not check_active_middleware(chat_id): return
        lang = get_user_lang(chat_id)
        cart_key = (token, chat_id)
        store = get_store_info()
        
        if call.data == "shop_clear":
            user_carts[cart_key] = {}
            bot.edit_message_text("🛒 Cart cleared / ጋሪው ጸድቷል!", chat_id, call.message.message_id)
        elif call.data == "shop_checkout":
            cart = user_carts.get(cart_key, {})
            if not cart: return
            
            total_price = 0
            conn = get_safe_connection()
            try:
                with conn.cursor() as cursor:
                    for p_id, qty in list(cart.items()):
                        # 🟠 Token Filter ለ cross-store leak መከላከያ
                        cursor.execute("SELECT price FROM products WHERE id=%s AND token=%s", (p_id, token))
                        p_row = cursor.fetchone()
                        if p_row: 
                            total_price += p_row[0] * qty
                        else:
                            del cart[p_id]
                    
                    cursor.execute('''INSERT INTO orders (token, customer_id, status_am, status_en, total_price) 
                                      VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                                   (token, chat_id, "በመጠባበቅ ላይ (ፎቶ ይጠበቃል)", "Pending (Awaiting Screenshot)", total_price))
                    order_id = cursor.fetchone()[0]
                    conn.commit()
            finally:
                db_pool.putconn(conn)
            
            user_carts[cart_key] = {}
            pay_text = f"🆔 **Order ID / የትዕዛዝ ቁጥር፦** `{order_id}`\n\n📱 **Telebirr / ቴሌብር፦** `{store['telebirr']}`\n\n{STRINGS[lang]['receipt_prompt']}"
            bot.edit_message_text(pay_text, chat_id, call.message.message_id, parse_mode="Markdown")
            admin_states[(token, chat_id)] = {"state": f"AWAITING_RECEIPT_{order_id}", "data": {}}

    @bot.message_handler(content_types=['photo'])
    def handle_incoming_photos(message):
        chat_id = message.chat.id
        if not check_active_middleware(chat_id): return
        
        session_key = (token, chat_id)
        state_dict = admin_states.get(session_key, {"state": "", "data": {}})
        state = state_dict["state"]
        store = get_store_info()
        
        if state.startswith("AWAITING_RECEIPT_"):
            order_id = int(state.split("_")[2])
            admin_id = store["admin_id"] if store else chat_id
            
            bot.send_message(admin_id, f"🔔 **አዲስ የክፍያ ደረሰኝ ለትዕዛዝ ቁጥር #{order_id}!**\nለማፅደቅ፡ `/approve {order_id}`")
            bot.forward_message(admin_id, chat_id, message.message_id)
            
            conn = get_safe_connection()
            try:
                with conn.cursor() as cursor:
                    # 🟠 Token Check: ትዕዛዙ የዚህ ሱቅ መሆኑን ማረጋገጥ
                    cursor.execute("UPDATE orders SET status_am=%s, status_en=%s WHERE id=%s AND token=%s", 
                                   ("ክፍያ ተልኳል (በማረጋገጥ ላይ)", "Payment sent (Verifying)", order_id, token))
                    conn.commit()
            finally:
                db_pool.putconn(conn)
                
            bot.reply_to(message, "✅ የክፍያ ማረጋገጫ ፎቶዎ ተልኳል።")
            admin_states[session_key] = {"state": "", "data": {}}
            
        elif state == "WAITING_PRODUCT_PHOTO":
            if not is_verified_admin(chat_id): return
            photo_id = message.photo[-1].file_id
            p_data = state_dict["data"]
            
            conn = get_safe_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute('''INSERT INTO products (token, name_am, name_en, price, stock, desc_am, desc_en, image_url) 
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                                   (token, p_data["name_am"], p_data["name_en"], p_data["price"], p_data["stock"], p_data["desc_am"], p_data["desc_en"], photo_id))
                    conn.commit()
            finally:
                db_pool.putconn(conn)
            bot.reply_to(message, f"🎉 ምርቱ '{p_data['name_am']}' በስኬት ተጨምሯል!")
            admin_states[session_key] = {"state": "", "data": {}}

    @bot.message_handler(func=lambda m: admin_states.get((token, m.chat.id), {}).get("state") == "WAITING_PRODUCT_DETAILS")
    def process_add_product_fields(message):
        session_key = (token, message.chat.id)
        try:
            parts = message.text.split(",")
            product_data = {
                "name_am": parts[0].strip(),
                "name_en": parts[1].strip(),
                "price": float(parts[2].strip()),
                "stock": int(parts[3].strip()),
                "desc_am": parts[4].strip(),
                "desc_en": parts[5].strip()
            }
            bot.reply_to(message, "📸 አሁን ደግሞ የምርቱን ፎቶ ይላኩ። ፎቶ ከሌለ 'none' ይበሉ፦")
            admin_states[session_key] = {"state": "WAITING_PRODUCT_PHOTO", "data": product_data}
        except:
            bot.reply_to(message, "❌ ፎርማት ስህተት አለው። በኮማ (,) በመለየት ይሞክሩ።")

    @bot.message_handler(func=lambda m: admin_states.get((token, m.chat.id), {}).get("state") == "WAITING_PRODUCT_PHOTO" and m.text and m.text.lower() == 'none')
    def process_product_no_photo(message):
        session_key = (token, message.chat.id)
        if not is_verified_admin(message.chat.id): return
        p_data = admin_states[session_key]["data"]
        
        conn = get_safe_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''INSERT INTO products (token, name_am, name_en, price, stock, desc_am, desc_en, image_url) 
                                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                               (token, p_data["name_am"], p_data["name_en"], p_data["price"], p_data["stock"], p_data["desc_am"], p_data["desc_en"], ""))
                conn.commit()
        finally:
            db_pool.putconn(conn)
        bot.reply_to(message, f"🎉 ምርቱ '{p_data['name_am']}' ያለ ፎቶ ተጨምሯል!")
        admin_states[session_key] = {"state": "", "data": {}}

    @bot.message_handler(commands=['approve'])
    def approve(message):
        if not is_verified_admin(message.chat.id): return
        try:
            order_id = int(message.text.split()[1])
            conn = get_safe_connection()
            try:
                with conn.cursor() as cursor:
                    # 🟠 Token Check: የሌላ ሱቅ ትዕዛዝ እንዳይፈቀድ ማጣሪያ
                    cursor.execute("SELECT customer_id FROM orders WHERE id=%s AND token=%s", (order_id, token))
                    row = cursor.fetchone()
                    if row:
                        cust_id = row[0]
                        cursor.execute("UPDATE orders SET status_am=%s, status_en=%s WHERE id=%s", ("✅ ተከፍሏል", "✅ Paid", order_id))
                        conn.commit()
                        cust_lang = get_user_lang(cust_id)
                        bot.send_message(cust_id, STRINGS[cust_lang]["approved_msg"])
                        bot.reply_to(message, f"✅ Order #{order_id} approved!")
                    else:
                        bot.reply_to(message, "❌ Order not found in your store.")
            finally:
                db_pool.putconn(conn)
        except:
            bot.reply_to(message, "Use: `/approve ID`")

    @bot.message_handler(func=lambda message: True)
    def handle_global_ai(message):
        if not check_active_middleware(message.chat.id): return
        bot.send_chat_action(message.chat.id, 'typing')
        lang = get_user_lang(message.chat.id)
        store = get_store_info()
        store_name = store["store_name"] if store else "Our Shop"
        try:
            system_instruction = f"You are an AI assistant for '{store_name}'. Respond in {lang}. Keep it short."
            response = ai_model.generate_content(f"{system_instruction} {message.text}")
            bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, "❌ System busy.")

    threading.Thread(target=bot.infinity_polling, name=f"Bot_{token}", daemon=True).start()

RAW_TOKENS = os.environ.get("BOT_TOKENS", "")
if RAW_TOKENS:
    LIVE_TOKENS = [t.strip() for t in RAW_TOKENS.split(",") if t.strip()]
    for t in LIVE_TOKENS:
        setup_bot_handlers(t)

while True:
    time.sleep(3600)
