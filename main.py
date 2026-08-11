import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# লোগিং সেটআপ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # প্রফেশনাল ওয়েলকাম মেসেজ
    welcome_text = (
        f"✨ **Welcome, {user_name}!**\n\n"
        f"🎓 **Official SSC Result Bot 2026**\n"
        f"Get your board results, marks, and grades instantly and securely.\n\n"
        f"👨‍💻 *Developed by:* [MD Rasel](https://t.me/HANTER_XD_OFFICIAL)\n\n"
        f"👇 *Click the buttons below to proceed:*"
    )
    
    # ইউনিক এবং প্রফেশনাল বাটন ডিজাইন
    keyboard = [
        [
            InlineKeyboardButton("📊 Check Result", callback_data="open_result"),
            InlineKeyboardButton("📌 Instructions", callback_data="instructions")
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer Support", url="https://t.me/HANTER_XD_OFFICIAL")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "open_result":
        await query.edit_message_text(
            text="🔄 **Result Portal is loading...**\n\nPlease select your Education Board and provide your details.",
            parse_mode="Markdown"
        )
    elif query.data == "instructions":
        await query.edit_message_text(
            text="📌 **How to check result:**\n\n1. Select your Education Board.\n2. Choose passing year.\n3. Enter Roll & Registration number.\n4. Solve the captcha and get your markSheet!",
            parse_mode="Markdown"
        )

def main():
    TOKEN = "8813818290:AAHX4pqfg-IkCQ06d9z2YA2jICSvrzWXCJA"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))

    print("Professional Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
