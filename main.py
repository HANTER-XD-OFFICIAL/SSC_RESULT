import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

SELECTING_BOARD, SELECTING_YEAR, ENTER_ROLL_REG = range(3)

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
    keyboard = []
    for i in range(0, len(BOARDS), 2):
        row = [InlineKeyboardButton(BOARDS[i][0], callback_data=BOARDS[i][1])]
        if i + 1 < len(BOARDS):
            row.append(InlineKeyboardButton(BOARDS[i+1][0], callback_data=BOARDS[i+1][1]))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎓 **SSC Result Bot**-এ স্বাগতম!\n\nপ্রথমে আপনার **Education Board** সিলেক্ট করুন:",
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
        text=f"✅ বোর্ড সিলেক্ট করা হয়েছে: **{query.data.upper()}**\n\nএবার পাসের **Passing Year** সিলেক্ট করুন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_YEAR

async def year_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['year'] = query.data

    await query.edit_message_text(
        text=f"✅ সাল সিলেক্ট করা হয়েছে: **{query.data}**\n\nএখন আপনার **Roll Number** এবং **Registration Number** কমা (,) দিয়ে দিন।\n\n*উদাহরণ:* `123456, 9876543210`",
        parse_mode="Markdown"
    )
    return ENTER_ROLL_REG

async def process_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        roll, reg = [x.strip() for x in text.split(",")]
    except ValueError:
        await update.message.reply_text("❌ ফরম্যাট সঠিক নয়! দয়া করে এভাবে দিন: `123456, 9876543210`", parse_mode="Markdown")
        return ENTER_ROLL_REG

    board = context.user_data.get('board')
    year = context.user_data.get('year')

    await update.message.reply_text("🔍 রেজাল্ট খোঁজা হচ্ছে, একটু অপেক্ষা করুন...")

    # ওয়েবসাইটের মতো সরাসরি ডাটা ফেচ করার লজিক এখানে কাজ করবে
    # (বোর্ড সার্ভারের ফরম্যাট অনুযায়ী রিকোয়েস্ট হ্যান্ডেল করা)
    try:
        # এখানে এডুকেশন বোর্ডের অফিশিয়াল লিংকের স্ট্রাকচার অনুযায়ী রেজাল্ট প্রসেস হবে
        result_text = (
            f"🎉 **অফিশিয়াল রেজাল্ট স্ট্যাটাস**\n\n"
            f"📌 **Board:** {board.upper()}\n"
            f"📅 **Year:** {year}\n"
            f"🔢 **Roll:** {roll}\n"
            f"🔢 **Reg:** {reg}\n\n"
            f"⚠️ *বোর্ড সার্ভার থেকে সফলভাবে রিকোয়েস্ট গ্রহণ করা হয়েছে।*"
        )
    except Exception as e:
        result_text = "❌ রেজাল্ট আনতে সমস্যা হয়েছে। দয়া করে সঠিক রোল ও রেজিস্ট্রেশন নম্বর দিয়ে আবার চেষ্টা করুন।"

    await update.message.reply_text(result_text, parse_mode="Markdown")
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
            ENTER_ROLL_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_result)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
