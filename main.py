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
    # ইউজারের টেলিগ্রাম নাম সংগ্রহ করা
    user_name = update.effective_user.first_name
    
    # ওয়েলকাম মেসেজ
    welcome_text = (
        f"Hello **{user_name}**! 🎓\n\n"
        f"Welcome to the Official **SSC Result Bot**.\n"
        f"Developed by **MD Rasel** (@HANTER_XD_OFFICIAL).\n\n"
        f"Please click the button below to check your SSC result:"
    )
    
    # নিচে রেজাল্ট দেখার বাটন
    keyboard = [
        [InlineKeyboardButton("📊 Check SSC Result", callback_data="open_result")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "open_result":
        await query.edit_message_text(
            text="🔄 Result checking process is starting...\nPlease provide your Board, Roll, and Registration number to proceed."
        )

def main():
    TOKEN = "8813818290:AAHX4pqfg-IkCQ06d9z2YA2jICSvrzWXCJA"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))

    print("Welcome Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
