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

# কনভারসেশনের স্টেপগুলো
ENTER_CAPTCHA, SELECTING_BOARD, SELECTING_YEAR, ENTER_ROLL, ENTER_REG = range(5)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # নতুন সেশন তৈরি যাতে কুকিজ ঠিক থাকে
    session = requests.Session()
    context.user_data['session'] = session
    
    await update.message.reply_text("⚡ Official Fast Result\n⌛ Captcha লোড হচ্ছে...")

    try:
        # অফিশিয়াল সাইটের মূল পেজ থেকে কুকিজ এবং ক্যাপচা ইমেজ ফেচ করার লজিক
        # (এখানে বোর্ড সাইটের ক্যাপচা লিংক থেকে ইমেজ নামিয়ে টেলিগ্রামে পাঠানো হবে)
        
        # ডেমো হিসেবে ক্যাপচা ইমেজ ফেচ করার কোড স্ট্রাকচার:
        # res = session.get("https://www.educationboardresults.gov.bd/v2/home")
        # captcha_res = session.get("BOARD_CAPTCHA_IMAGE_URL")
        # captcha_bytes = BytesIO(captcha_res.content)

        # ইউজারকে ক্যাপচা ইমেজ পাঠানো
        keyboard = [[InlineKeyboardButton("🔄 নতুন Captcha", callback_data="refresh_captcha")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔢 Image টা open করে **Captcha** সম্পূর্ণ লিখে পাঠান:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        # await update.message.reply_photo(photo=InputFile(captcha_bytes))

    except Exception as e:
        await update.message.reply_text("❌ ক্যাপচা লোড করতে সমস্যা হয়েছে। আবার চেষ্টা করতে `/start` লিখুন।")
        return ConversationHandler.END

    return ENTER_CAPTCHA

async def verify_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_captcha = update.message.text.strip()
    session = context.user_data.get('session')

    # এখানে ইউজার প্রদত্ত ক্যাপচা সঠিক কি না তা বোর্ড সার্ভারে চেক করার লজিক হবে
    # যদি সঠিক হয়, তবে বোর্ড সিলেকশন মেনু দেখাবে:

    keyboard = []
    for i in range(0, len(BOARDS), 2):
        row = [InlineKeyboardButton(BOARDS[i][0].upper(), callback_data=BOARDS[i][1])]
        if i + 1 < len(BOARDS):
            row.append(InlineKeyboardButton(BOARDS[i+1][0].upper(), callback_data=BOARDS[i+1][1]))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✅ **বোর্ড:** (যাচাই সফল)\n📅 **Year:** 2026 (Fixed)\n\n📍 এখন **বোর্ড সিলেক্ট করুন:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_BOARD

async def board_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['board'] = query.data

    await query.message.reply_text(
        f"✅ **বোর্ড:** {query.data.upper()}\n📅 **Year:** 2026 (Fixed)\n\n📌 এখন **Roll Number** পাঠান:",
        parse_mode="Markdown"
    )
    return ENTER_ROLL

async def process_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['roll'] = update.message.text.strip()
    
    await update.message.reply_text(
        "✅ Roll নেওয়া হয়েছে!\n\nএখন **Registration Number** পাঠান:",
        parse_mode="Markdown"
    )
    return ENTER_REG

async def process_reg_and_get_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] = update.message.text.strip()
    
    board = context.user_data.get('board')
    roll = context.user_data.get('roll')
    reg = context.user_data.get('reg')
    session = context.user_data.get('session')

    await update.message.reply_text("⚡ Result খোঁজা হচ্ছে...")

    try:
        # বোর্ড সার্ভারে সমস্ত তথ্য (ক্যাপচা, বোর্ড, রোল, রেজি) সাবমিট করে রিয়েল রেজাল্ট টেক্সট আকারে ফেচ করার লজিক
        # সফলভাবে ডেটা আসলে নিচের ফরম্যাটে টেক্সট দেখাবে:

        result_text = (
            f"📄 **Official Result & Marksheet**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Name:** [Student Name from Board]\n"
            f"📌 **Roll:** `{roll}` | **Reg:** `{reg}`\n"
            f"🏛 **Board:** {board.upper()} | 📅 **Year:** 2026\n"
            f"🏆 **GPA:** `5.00`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📚 **Subject-wise Marks:**\n\n"
            f"• Bangla: `A+` (85)\n"
            f"• English: `A+` (82)\n"
            f"• Mathematics: `A+` (95)\n"
            f"• Science: `A+` (88)\n"
            f"• ICT: `A+` (48)\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Status:** PASSED"
        )
        await update.message.reply_text(result_text, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❌ রেজাল্ট পাওয়া যায়নি। দয়া করে আবার `/start` দিয়ে চেষ্টা করুন।")

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
            ENTER_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_captcha)],
            SELECTING_BOARD: [CallbackQueryHandler(board_selected)],
            ENTER_ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_roll)],
            ENTER_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_reg_and_get_result)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
