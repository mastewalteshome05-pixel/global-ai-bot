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
    return "Advanced Multi-Lingual AI Bot with Image Generation is Running Globally!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# 2. ያቀረብካቸው የቦት መለያዎች (API Keys)
TELEGRAM_TOKEN = '8645911917:AAHty0mzRmgnAxxyy3HMI5GzNwacGUn6CkQ'
GEMINI_API_KEY = 'AQ.Ab8RN6IUk09HCemdQmdNVJMIZgUGrUA30EZn0CgEemuPPguZqg'
ADMIN_ID = 7585327665  # ያንተ የቴሌግራም ID

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-pro')

# 3. ጊዜያዊ መዝገቦች
user_usage = {}
premium_users = {ADMIN_ID}
user_languages = {}

# የ 12 ቋንቋዎች መልዕክቶች መዝገብ (ቦቱን ዓለም አቀፍ ለማድረግ)
STRINGS = {
    "am": {"welcome": "እንኳን ወደ AI ረዳት ቦት በደህና መጡ! 👋\n\n🧠 ማናቸውንም ጥያቄ መጠየቅ፣ ጽሑፍ ማስተርጎም ወይም የፈለጉትን ምስል ማመንጨት ይችላሉ።\n\n🖼 **ምስል ለማመንጨት**፦ `/image [የምስሉ መግለጫ]` ብለው ይጻፉ።\n🗣 **በድምፅ ለማንበብ**፦ `/voice [ጽሑፍ]` ይበሉ።", "limit": "⚠️ የዛሬው ነፃ ገደብዎ አልቋል! ወደ ፕሪሚየም ለማሳደግ አድሚኑን ያነጋግሩ።", "premium_alert": "🎉 እንኳን ደስ አለዎት! የፕሪሚየም አገልግሎት ተከፍቶልዎታል።", "generating": "🎨 ምስል በመስራት ላይ ነኝ... እባክዎ በትዕግስት ይጠብቁ..."},
    "en": {"welcome": "Welcome to AI Assistant Bot! 👋\n\n🧠 Ask any question, translate text, or generate high-quality images.\n\n🖼 **To generate image**: Type `/image [description]`.\n🗣 **Text-to-Speech**: Type `/voice [text]`.", "limit": "⚠️ Your free limit is over! Contact admin to upgrade to Premium.", "premium_alert": "🎉 Congratulations! Premium access activated.", "generating": "🎨 Generating image... Please wait a moment..."},
    "om": {"welcome": "Baga gara AI Assistant Bot nagaan dhuftan! 👋\n🧠 Gaaffii kamiyyuu gaafachuu, hiikuu fi fakkii uumuu ni dandeessu.\n\n🖼 **/image [ibsa bakkichaa]** fayyadamaa.", "limit": "⚠️ Daangaan keessan dhumeera! Admin qunnamaa.", "premium_alert": "🎉 Gara Premium tti ol guddifamtaniittu.", "generating": "🎨 Fakkii uumaa jira... Maaloo yeroo muraasa eegaa..."},
    "ti": {"welcome": "እንቋዕ ናብ AI ረዳት ቦት ብደሓን መጻእኹም! 👋\n🧠 ዝኾነ ሕቶ ክትሓቱ ወይ ምስሊ ከተመንጭዉ ትኽእሉ ኢኹም።", "limit": "⚠️ ነጻ ገደብኩም ተወዲኡ እዩ! ናብ ፕሪሚየም ንምዕባይ ንኣድሚን አዘራርቡ።", "premium_alert": "🎉 ናብ ፕሪሚየም ተቐይርኩም ኣለኹም።", "generating": "🎨 ምስሊ ኣብ ምስራሕ ይርከብ... በጃኹም ተጸበዩ..."},
    "so": {"welcome": "Ku soo dhawaada AI Assistant Bot! 👋\n🧠 Weydii su'aal kasta, tarjum qoraal ama sawir samee.", "limit": "⚠️ Xadkaagii bilaashka ahaa waa dhammaaday! La xiriir admin.", "premium_alert": "🎉 Helitaanka Premium waa laguu furay.", "generating": "🎨 Sawirka waa la diyaarinayaa... Fadlan sug..."},
    "ar": {"welcome": "مرحبًا بك في بوت الذكاء الاصطناعي! 👋\n🧠 اسأل أي سؤال، ترجم النصوص، أو قم بتوليد صور عالية الجودة.", "limit": "⚠️ لقد انتهى حدك المجاني! تواصل مع المسؤول للترقية.", "premium_alert": "🎉 تم تفعيل الحساب المميز بنجاح.", "generating": "🎨 جاري توليد الصورة... يرجى الانتظار..."},
    "fr": {"welcome": "Bienvenue sur le Bot Assistant IA ! 👋\n🧠 Posez vos questions, traduisez ou générez des images.", "limit": "⚠️ Limite gratuite atteinte ! Contactez l'administrateur.", "premium_alert": "🎉 Accès Premium activé.", "generating": "🎨 Génération de l'image... Veuillez patienter..."},
    "es": {"welcome": "¡Bienvenido al Bot de Asistente de IA! 👋\n🧠 Haz preguntas, traduce o genera imágenes de alta calidad.", "limit": "⚠️ ¡Límite gratuito agotado! Contacta al administrador.", "premium_alert": "🎉 Acceso Premium activado.", "generating": "🎨 Generando imagen... Por favor espera..."},
    "de": {"welcome": "Willkommen beim KI-Assistenten-Bot! 👋\n🧠 Stellen Sie Fragen, übersetzen Sie oder generieren Sie Bilder.", "limit": "⚠️ Kostenloses Limit erreicht! Kontaktieren Sie den Admin.", "premium_alert": "🎉 Premium-Zugang aktiviert.", "generating": "🎨 Bild wird generiert... Bitte warten..."},
    "it": {"welcome": "Benvenuto nel Bot Assistente IA! 👋\n🧠 Fai domande, traduci o genera immagini di alta qualità.", "limit": "⚠️ Limite gratuito superato! Contatta l'amministratore.", "premium_alert": "🎉 Accesso Premium activato.", "generating": "🎨 Generazione dell'immagine in corso... Attendere..."},
    "ru": {"welcome": "Добро пожаловать в ИИ Ассистент Бот! 👋\n🧠 Задавайте вопросы, переводите тексты или создавайте изображения.", "limit": "⚠️ Лимит бесплатных запросов исчерпан! Свяжитесь с админом.", "premium_alert": "🎉 Премиум доступ активирован.", "generating": "🎨 Создание изображения... Пожалуйста, подождите..."},
    "zh": {"welcome": "欢迎使用人工智能 assistant 机器人！ 👋\n🧠 您可以提问、翻译文本或生成高质量图片。", "limit": "⚠️ 您的免费额度已用完！请聯繫管理员升级。", "premium_alert": "🎉 尊贵的高级会员已激活。", "generating": "🎨 正在生成图片... 请稍候..."}
}

# 4. የቋንቋ መምረጫ Button ማሳየት
@bot.message_handler(commands=['start'])
def choose_language(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="ailang_am"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="ailang_en"),
        types.InlineKeyboardButton("Afaan Oromoo 🇪🇹", callback_data="ailang_om"),
        types.InlineKeyboardButton("ትግርኛ 🇪🇹", callback_data="ailang_ti"),
        types.InlineKeyboardButton("Soomaali 🇸🇴", callback_data="ailang_so"),
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="ailang_ar"),
        types.InlineKeyboardButton("Français 🇫🇷", callback_data="ailang_fr"),
        types.InlineKeyboardButton("Español 🇪🇸", callback_data="ailang_es"),
        types.InlineKeyboardButton("Deutsch 🇩🇪", callback_data="ailang_de"),
        types.InlineKeyboardButton("Italiano 🇮🇹", callback_data="ailang_it"),
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="ailang_ru"),
        types.InlineKeyboardButton("中文 🇨🇳", callback_data="ailang_zh")
    )
    bot.send_message(message.chat.id, "🌐 Please select your language / ቋንቋ ይምረጡ፦", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ailang_"))
def set_language(call):
    chat_id = call.message.chat.id
    lang_code = call.data.split("_")[1]
    user_languages[chat_id] = lang_code
    bot.delete_message(chat_id, call.message.message_id)
    
    ln = STRINGS[lang_code]
    bot.send_message(chat_id, ln["welcome"], parse_mode="Markdown")

# 5. የነፃ አጠቃቀም ገደብ ማረጋገጫ (በቀን 5 ጊዜ ብቻ)
def check_limit(chat_id, lang):
    if chat_id in premium_users:
        return True
    current_count = user_usage.get(chat_id, 0)
    if current_count >= 5:
        bot.send_message(chat_id, STRINGS[lang]["limit"], parse_mode="Markdown")
        return False
    user_usage[chat_id] = current_count + 1
    return True

# 6. የኢሜጅ ማመንጫ (High-Quality Image Generator)
@bot.message_handler(commands=['image'])
def generate_image(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "am")
    
    if not check_limit(chat_id, lang):
        return

    try:
        prompt = message.text.split(None, 1)[1]
    except IndexError:
        bot.reply_to(message, "❌ እባክዎ ከትዕዛዙ ጎን የሚፈልጉትን ምስል መግለጫ ይጻፉ።\nምሳሌ፦ `/image a beautiful software developer, realistic, 4k` ", parse_mode="Markdown")
        return

    bot.send_message(chat_id, STRINGS[lang]["generating"])
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=1024&height=1024&nologo=true"
        bot.send_photo(chat_id, image_url, caption=f"🎨 **የተፈጠረ ምስል፦** `{prompt}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ ይቅርታ፣ ምስሉን ማመንጨት አልተቻለም።")

# 7. የድምፅ ማነበቢያ (Text-to-Speech)
@bot.message_handler(commands=['voice'])
def text_to_speech(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "am")
    
    if not check_limit(chat_id, lang):
        return

    try:
        text = message.text.split(None, 1)[1]
    except IndexError:
        bot.reply_to(message, "❌ እባክዎ የሚነበበውን ጽሑፍ ያስገቡ። ምሳሌ፦ `/voice Hello how are you` ")
        return

    bot.send_chat_action(chat_id, 'record_audio')
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={requests.utils.quote(text)}"
    try:
        bot.send_voice(chat_id, tts_url)
    except:
        bot.reply_to(message, "❌ ድምፅ መፍጠር አልተቻለም።")

# 8. የአድሚን ትዕዛዞች (/vip እና /stats)
@bot.message_handler(commands=['vip'])
def activate_premium(message):
    if message.chat.id == ADMIN_ID:
        try:
            target_id = int(message.text.split()[1])
            premium_users.add(target_id)
            bot.reply_to(message, f"👑 ` {target_id} ` በተሳካ ሁኔታ ፕሪሚየም ሆኗል!")
            bot.send_message(target_id, "🎉 Congratulations! Your Premium Service is now active!")
        except:
            bot.reply_to(message, "ትክክለኛ ቅርጸት፦ `/vip [USER_ID]`")

@bot.message_handler(commands=['stats'])
def view_stats(message):
    if message.chat.id == ADMIN_ID:
        total_users = len(user_usage)
        total_vip = len(premium_users) - 1
        stats_text = f"📊 **የቦቱ አጠቃላይ መረጃ**\n\n👥 ጠቅላላ ተጠቃሚዎች፦ {total_users}\n👑 ፕሪሚየም ተጠቃሚዎች፦ {total_vip}"
        bot.send_message(ADMIN_ID, stats_text, parse_mode="Markdown")

# 9. ጠቅላላ የ AI ጥያቄዎች መልስ
@bot.message_handler(func=lambda message: True)
def handle_ai(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "am")
    
    if not check_limit(chat_id, lang):
        return

    bot.send_chat_action(chat_id, 'typing')
    try:
        ai_instruction = "You are a world-class multi-lingual AI. Answer user queries accurately and professionally in the language they use."
        response = ai_model.generate_content(f"{ai_instruction} {message.text}")
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "❌ ስህተት አጋጥሟል። እባክዎ ድጋሚ ይሞክሩ።")

print("Globally Advanced AI Bot V2 is running...")
bot.infinity_polling()
