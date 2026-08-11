import os
import logging
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# লোগিং সেটআপ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

SELECTING_BOARD, SELECTING_YEAR, ENTER_ROLL_REG, ENTER_CAPTCHA = range(4)

BOARDS = [
    ("Dhaka", "dhaka"),
    ("Chattogram", "chattogram"),
    ("Comilla", "comilla"),
    ("Jessore", "jessore"),
    ("Rajshahi", "rajshahi"),
    ("Sylhet", "sylhet"),
    ("Barishal", "barishal"),
    ("Dinajpur", "dinajpur"),
    ("Madrasah", "madrasah"),
    ("Technical", "technical"),
]

BASE_URL = "https://www.educationboardresults.gov.bd/v2/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # নতুন সেশন তৈরি যাতে কুকিজ ঠিক থাকে
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    context.user_data['session'] = session
    
    keyboard = []
    for i in range(0, len(BOARDS), 2):
        row = [InlineKeyboardButton(BOARDS[i][0], callback_data=BOARDS[i][1])]
        if i + 1 < len(BOARDS):
            row.append(InlineKeyboardButton(BOARDS[i+1][0], callback_data=BOARDS[i+1][1]))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎓 **অফিশিয়াল রিয়েল রেজাল্ট বট**\n\nপ্রথমে আপনার **Education Board** সিলেক্ট করুন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_BOARD

async def board_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['board'] = query.data

    years = ["2026", "2025", "2024", "2023", "2022", "2021", "2020"]
    keyboard = []
    for i in range(0, len(years), 3):
        row = [InlineKeyboardButton(years[i], callback_data=years[i])]
        if i + 1 < len(years):
            row.append(InlineKeyboardButton(years[i+1], callback_data=years[i+1]))
        if i + 2 < len(years):
            row.append(InlineKeyboardButton(years[i+2], callback_data=years[i+2]))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"✅ বোর্ড: **{query.data.upper()}**\n\nএবার পাসের **Passing Year** সিলেক্ট করুন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_YEAR

async def year_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['year'] = query.data

    await query.edit_message_text(
        text=f"✅ সাল: **{query.data}**\n\nএখন আপনার **Roll Number** এবং **Registration Number** কমা (,) দিয়ে দিন।\n\n*উদাহরণ:* `123456, 9876543210`",
        parse_mode="Markdown"
    )
    return ENTER_ROLL_REG

async def process_roll_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        roll, reg = [x.strip() for x in text.split(",")]
        context.user_data['roll'] = roll
        context.user_data['reg'] = reg
    except ValueError:
        await update.message.reply_text("❌ ফরম্যাট সঠিক নয়! দয়া করে এভাবে দিন: `123456, 9876543210`", parse_mode="Markdown")
        return ENTER_ROLL_REG

    await update.message.reply_text("🔄 অফিশিয়াল ওয়েবসাইট থেকে রিয়েল ক্যাপচা ডাউনলোড করা হচ্ছে...")

    try:
        session = context.user_data.get('session')
        
        # ১. মেইন পেজ ভিজিট করে কুকি সংগ্রহ
        res = session.get(BASE_URL)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ২. ক্যাপচা ইমেজ লিংক খুঁজে বের করা এবং ডাউনলোড করা
        # (বোর্ড সাইটের ক্যাপচা সাধারণত dynamic src বা captcha endpoint এ থাকে)
        captcha_img_tag = soup.find('img', {'id': 'captcha'}) or soup.find('img', {'class': 'captcha'})
        
        # যদি ডাইরেক্ট ইমেজ পাথ না পাওয়া যায়, স্ট্যান্ডার্ড ক্যাপচা URL ট্রাই করা হবে
        captcha_url = f"{BASE_URL}captcha.php" if not captcha_img_tag else f"{BASE_URL}{captcha_img_tag.get('src')}"
        
        captcha_res = session.get(captcha_url)
        if captcha_res.status_code == 200 and len(captcha_res.content) > 100:
            captcha_bytes = BytesIO(captcha_res.content)
            captcha_bytes.name = "captcha.png"
            
            await update.message.reply_photo(
                photo=InputFile(captcha_bytes),
                caption="🔐 **রিয়েল ক্যাপচা ভেরিফিকেশন:**\n\nউপরে ছবির কোডটি দেখে নিচে লিখে পাঠান:"
            )
        else:
            # ফলব্যাক মেথড যদি ইমেজ ডাইরেক্ট না মিলে
            await update.message.reply_text("⚠️ ক্যাপচা ইমেজ লোড করতে সমস্যা হয়েছে। দয়া করে আবার `/start` দিয়ে চেষ্টা করুন।")
            return ConversationHandler.END

    except Exception as e:
        logging.error(f"Captcha Error: {e}")
        await update.message.reply_text("❌ সার্ভার থেকে ক্যাপচা আনতে ব্যর্থ হয়েছে। আবার `/start` দিন।")
        return ConversationHandler.END

    return ENTER_CAPTCHA

async def verify_captcha_and_get_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_captcha = update.message.text.strip()
    
    board = context.user_data.get('board')
    year = context.user_data.get('year')
    roll = context.user_data.get('roll')
    reg = context.user_data.get('reg')
    session = context.user_data.get('session')

    await update.message.reply_text("🔍 বোর্ড সার্ভারে রিয়েল-টাইম রেজাল্ট যাচাই করা হচ্ছে...")

    try:
        # বোর্ড সাইটের ফর্ম ডাটা সাবমিট করার প্রস্তুতি
        payload = {
            'board': board,
            'year': year,
            'roll': roll,
            'reg': reg,
            'captcha': user_captcha
        }
        
        # অফিশিয়াল সাইটে পোস্ট রিকোয়েস্ট পাঠানো (রিয়েল রেজাল্টের জন্য)
        response = session.post(f"{BASE_URL}result.php", data=payload)
        result_soup = BeautifulSoup(response.text, 'html.parser')
        
        # সাইটের রেসপন্স থেকে টেক্সট বা মার্কশিট এক্সট্রাক্ট করা
        # (বোর্ড সাইটের টেবিলে নাম, রোল এবং সাবজেক্ট মার্কস থাকে)
        name_tag = result_soup.find(text=lambda t: t and "Name" in t)
        
        # যদি সাইট থেকে সঠিক রেজাল্ট বা মার্কশিটের টেবিল ডেটা পাওয়া যায়:
        if response.status_code == 200 and "Invalid" not in response.text and "Error" not in response.text:
            
            # টেবিল থেকে টেক্সট পার্স করে সাজানো
            result_text = (
                f"📄 **অফিশিয়াল রিয়েল-টাইম মার্কশিট**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **Roll:** `{roll}` | **Reg:** `{reg}`\n"
                f"🏛 **Board:** {board.upper()} | 📅 **Year:** {year}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👇 প্রাপ্ত আসল রেজাল্ট ডেটা:\n\n"
                f"{response.text[:1500]}"  # বোর্ড সাইটের রিয়েল রেসপন্স টেক্সট এখানে দেখাবে
            )
        else:
            result_text = "❌ **ভুল ক্যাপচা অথবা ইনফরমেশন!**\n\nক্যাপচা মিলছে না অথবা রোল/রেজিস্ট্রেশন ভুল দিয়েছেন। আবার চেষ্টা করতে `/start` লিখুন।"

        await update.message.reply_text(result_text, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Result Fetch Error: {e}")
        await update.message.reply_text("❌ রেজাল্ট ফেচ করার সময় ত্রুটি ঘটেছে। দয়া করে `/start` দিয়ে আবার চেষ্টা করুন।")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ অপারেশন বাতিল করা হয়েছে। আবার শুরু করতে `/start` লিখুন।")
    return ConversationHandler.END

def main():
    TOKEN = "8813818290:AAHX4pqfg-IkCQ06d9z2YA2jICSvrzWXCJA"
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_BOARD: [CallbackQueryHandler(board_selected)],
            SELECTING_YEAR: [CallbackQueryHandler(year_selected)],
            ENTER_ROLL_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_roll_reg)],
            ENTER_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_captcha_and_get_result)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Real Result Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
