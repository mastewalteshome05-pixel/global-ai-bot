import os
import threading
import telebot
from telebot import types
import google.generativeai as genai
import requests
from flask import Flask

# 1. የፍላስክ ሰርቨር ማዋቀር (Render እንዳይዘጋ)
app = Flask('')

@app.route('/')
def home():
    return "Global AI Customer Service Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# 2. የአንተ እውነተኛ መለያዎች (የተተኩ)
TELEGRAM_TOKEN = '8645911917:AAHty0mzRmgnAxxyy3HMI5GzNwacGUn6CkQ'
ADMIN_ID = 7585327665
GEMINI_API_KEY = 'AQ.Ab8RN6IUk09HCemdQmdNVJMIZgUGrUA30EZn0CgEemuPPguZqg'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# 3. የምርት ካታሎግ (Product Catalog Data)
PRODUCTS = {
    "p1": {"name": "የወንድ ጫማ (Nike)", "price": 3500, "stock": 10, "desc": "👟 ጥራት ያለው የኪነቲክ ስኒከር፣ መጠን፡ 40-44"},
    "p2": {"name": "የሴት ቲሸርት (Zara)", "price": 1200, "stock": 5, "desc": "👕 ጥጥ የተሰራ ውብ ቲሸርት፣ መጠን፡ S, M, L"},
    "p3": {"name": "ስማርት ሰዓት (Series 9)", "price": 4500, "stock": 0, "desc": "⌚ ሙሉ ታች ስክሪን፣ የጤና መከታተያ ያለው"}
}

# 12 ቋንቋዎችን ያካተተ የተጠቃሚ መዋቅር
STRINGS = {
    "am": {"welcome": "እንኳን ወደ AI የሽያጭ ረዳት ቦት በደህና መጡ! 👋", "shop": "🛍️ ምርቶችን እይ", "cart": "🛒 የእኔ ጋሪ", "track": "📦 ትዕዛዝ መከታተያ", "faq": "❓ መረጃ (FAQ)", "empty": "🛒 ጋሪዎ ባዶ ነው።"},
    "en": {"welcome": "Welcome to AI Customer Service Bot! 👋", "shop": "🛍️ Shop Products", "cart": "🛒 My Cart", "track": "📦 Track Order", "faq": "❓ FAQ Info", "empty": "🛒 Your cart is empty."},
    "om": {"welcome": "Baga Gara AI Assistant Bot nagaan dhuftan! 👋", "shop": "🛍️ Oomishaalee", "cart": "🛒 Kaartii Koo", "track": "📦 Hordoffii", "faq": "❓ FAQ", "empty": "🛒 Kaartiin keessan duudaadha."},
    "ti": {"welcome": "እንቋዕ ናብ AI ረዳት ቦት ብደሓን መጻእኹም! 👋", "shop": "🛍️ ፍርያት ርአ", "cart": "🛒 ዓንደ ጋሪ", "track": "📦 ምክትታል", "faq": "❓ ሕቶታት", "empty": "🛒 ጋሪኹም ባዶ እዩ።"},
    "so": {"welcome": "Ku soo dhawaada AI Assistant Bot! 👋", "shop": "🛍️ Eeg Alaabta", "cart": "🛒 Kooratada", "track": "📦 La soco", "faq": "❓ FAQ", "empty": "🛒 Kooratadaadu waa maran tahay."},
    "ar": {"welcome": "مرحبًا بك في بوت خدمة العملاء الذكي! 👋", "shop": "🛍️ عرض المنتجات", "cart": "🛒 عربة التسوق", "track": "📦 تتبع الطلب", "faq": "❓ الأسئلة الشائعة", "empty": "🛒 عربة التسوق فارغة."},
    "fr": {"welcome": "Bienvenue sur le Bot Boutique IA ! 👋", "shop": "🛍️ Voir Produits", "cart": "🛒 Mon Panier", "track": "📦 Suivre Commande", "faq": "❓ FAQ", "empty": "🛒 Votre panier est vide."},
    "es": {"welcome": "¡Bienvenido al Bot de Tienda IA! 👋", "shop": "🛍️ Ver Productos", "cart": "🛒 Mi Carrito", "track": "📦 Rastrear Pedido", "faq": "❓ FAQ", "empty": "🛒 Tu carrito está vacío."},
    "de": {"welcome": "Willkommen beim KI-Shop-Bot! 👋", "shop": "🛍️ Produkte ansehen", "cart": "🛒 Mein Warenkorb", "track": "📦 Bestellung verfolgen", "faq": "❓ FAQ", "empty": "🛒 Ihr Warenkorb ist leer."},
    "it": {"welcome": "Benvenuto nel Bot Negozio IA! 👋", "shop": "🛍️ Vedi Prodotti", "cart": "🛒 Il Mio Carrello", "track": "📦 Traccia Ordine", "faq": "❓ FAQ", "empty": "🛒 Il tuo carrello è vuoto."},
    "ru": {"welcome": "Добро пожаловать в ИИ Магазиን Бот! 👋", "shop": "🛍️ Смотреть товары", "cart": "🛒 Корзина", "track": "📦 Отследить заказ", "faq": "❓ FAQ", "empty": "🛒 Ваша корзина пуста."},
    "zh": {"welcome": "欢迎使用人工智能商城机器人！ 👋", "shop": "🛍️ 浏览商品", "cart": "🛒 我的购物车", "track": "📦 追踪订单", "faq": "❓ 常见问题", "empty": "🛒 您的购物车是空的。"}
}

user_carts = {}
user_orders = {}
user_languages = {}
order_counter = 1000

# ቋንቋ ተኮር የዋና ማውጫ ቁልፍ
def get_main_menu(lang):
    ln = STRINGS.get(lang, STRINGS["en"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(ln["shop"]),
        types.KeyboardButton(ln["cart"]),
        types.KeyboardButton(ln["track"]),
        types.KeyboardButton(ln["faq"])
    )
    return markup

@bot.message_handler(commands=['start'])
def choose_language(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="shoplang_am"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="shoplang_en"),
        types.InlineKeyboardButton("Afaan Oromoo 🇪🇹", callback_data="shoplang_om"),
        types.InlineKeyboardButton("ትግርኛ 🇪🇹", callback_data="shoplang_ti"),
        types.InlineKeyboardButton("Soomaali 🇸🇴", callback_data="shoplang_so"),
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="shoplang_ar"),
        types.InlineKeyboardButton("Français 🇫🇷", callback_data="shoplang_fr"),
        types.InlineKeyboardButton("Español 🇪🇸", callback_data="shoplang_es"),
        types.InlineKeyboardButton("Deutsch 🇩🇪", callback_data="shoplang_de"),
        types.InlineKeyboardButton("Italiano 🇮🇹", callback_data="shoplang_it"),
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="shoplang_ru"),
        types.InlineKeyboardButton("中文 🇨🇳", callback_data="shoplang_zh")
    )
    bot.send_message(message.chat.id, "🌐 Please select your shop language / ቋንቋ ይምረጡ፦", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shoplang_"))
def set_language(call):
    chat_id = call.message.chat.id
    lang_code = call.data.split("_")[1]
    user_languages[chat_id] = lang_code
    bot.delete_message(chat_id, call.message.message_id)
    
    ln = STRINGS[lang_code]
    bot.send_message(chat_id, ln["welcome"], reply_markup=get_main_menu(lang_code))

# ምርቶችን በሙሉ ማሳያ
@bot.message_handler(func=lambda m: any(m.text == STRINGS[k]["shop"] for k in STRINGS if m.chat.id in user_languages))
def list_products(message):
    chat_id = message.chat.id
    for p_id, info in PRODUCTS.items():
        status = f"✅ In Stock ({info['stock']})" if info['stock'] > 0 else "❌ Out of Stock"
        text = f"📦 **{info['name']}**\n💰 Price: {info['price']} ETB\n📌 Status: {status}\n📝 Details: {info['desc']}"
        markup = types.InlineKeyboardMarkup()
        if info['stock'] > 0:
            markup.add(types.InlineKeyboardButton("🛒 Add to Cart", callback_data=f"shopadd_{p_id}"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("shopadd_"))
def add_to_cart(call):
    chat_id = call.message.chat.id
    p_id = call.data.split("_")[1]
    if chat_id not in user_carts: user_carts[chat_id] = {}
    user_carts[chat_id][p_id] = user_carts[chat_id].get(p_id, 0) + 1
    bot.answer_callback_query(call.id, f"Added to cart! 🛒")

# ጋሪ እይታ
@bot.message_handler(func=lambda m: any(m.text == STRINGS[k]["cart"] for k in STRINGS if m.chat.id in user_languages))
def show_cart(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "en")
    cart = user_carts.get(chat_id, {})
    
    if not cart:
        bot.send_message(chat_id, STRINGS[lang]["empty"])
        return
        
    total = 0
    text = "🛒 **Your Cart / የእርስዎ ጋሪ፦**\n\n"
    for p_id, qty in cart.items():
        subtotal = PRODUCTS[p_id]['price'] * qty
        total += subtotal
        text += f"▪️ {PRODUCTS[p_id]['name']} x {qty} = {subtotal} ETB\n"
    text += f"\n💵 **Total: {total} ETB**"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💳 Checkout (Pay via Chapa/Telebirr)", callback_data="shop_checkout"),
        types.InlineKeyboardButton("🗑️ Clear Cart", callback_data="shop_clear")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["shop_checkout", "shop_clear"])
def cart_actions(call):
    chat_id = call.message.chat.id
    global order_counter
    if call.data == "shop_clear":
        user_carts[chat_id] = {}
        bot.edit_message_text("🛒 Cart cleared!", chat_id, call.message.message_id)
    elif call.data == "shop_checkout":
        cart = user_carts.get(chat_id, {})
        if not cart: return
        order_id = order_counter
        user_orders[order_id] = {"chat_id": chat_id, "status": "Pending / በመጠባበቅ ላይ"}
        order_counter += 1
        user_carts[chat_id] = {}
        
        pay_text = (
            f"🎉 **Order Registered! / ትዕዛዝዎ ተመዝግቧል!**\n🆔 Order ID: `{order_id}`\n\n"
            f"💳 **Payment Options / የክፍያ አማራጮች፦**\n"
            f"▪️ Telebirr / CBE Birr: `0911223344`\n"
            f"▪️ Chapa Gateway: [Click here to pay](https://chapa.co)\n\n"
            f"የከፈሉበትን ደረሰኝ በውስጥ መስመር ይላኩ።"
        )
        bot.edit_message_text(pay_text, chat_id, call.message.message_id, parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"🔔 **New Order {order_id}!** Approve using `/approve {order_id}`")

# ትዕዛዝ መከታተያ ቁልፍ
@bot.message_handler(func=lambda m: any(m.text == STRINGS[k]["track"] for k in STRINGS if m.chat.id in user_languages))
def track_order(message):
    msg = bot.reply_to(message, "🔢 Enter your Order ID / የትዕዛዝ ቁጥርዎን ያስገቡ፦")
    bot.register_next_step_handler(msg, process_track)

def process_track(message):
    try:
        order_id = int(message.text)
        if order_id in user_orders:
            bot.reply_to(message, f"📦 **Status for {order_id}:** {user_orders[order_id]['status']}")
        else:
            bot.reply_to(message, "❌ Order ID not found / አልተገኘም።")
    except:
        bot.reply_to(message, "❌ Invalid ID.")

# አድሚን ማጽደቂያ
@bot.message_handler(commands=['approve'])
def approve(message):
    if message.chat.id == ADMIN_ID:
        try:
            order_id = int(message.text.split()[1])
            if order_id in user_orders:
                user_orders[order_id]["status"] = "✅ Paid & Shipping / ተከፍሏል"
                bot.send_message(user_orders[order_id]["chat_id"], f"🎉 Your order `{order_id}` has been approved and is shipping! 🛵")
                bot.reply_to(message, "Order approved!")
        except:
            bot.reply_to(message, "Use: `/approve ID`")

# ጠቅላላ የአለም አቀፍ የ AI ደንበኞች አገልግሎት ጥያቄ (FAQ & AI Help)
@bot.message_handler(func=lambda message: True)
def handle_global_ai(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    try:
        system_instruction = (
            "You are an AI Customer Service agent for a global online store in Ethiopia. "
            "Help the user in their language. Delivery takes 2 hours in city, 1 day for region. "
            "Returns allowed in 48 hours. Answer this politely:"
        )
        response = ai_model.generate_content(f"{system_instruction} {message.text}")
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "❌ System busy, please try again.")

print("Global AI Shop Bot is running live...")
bot.infinity_polling()
