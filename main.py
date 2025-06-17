import os
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
ALLOWED_CHAT_IDS = list(map(int, os.getenv("ALLOWED_CHAT_IDS").split(",")))
GPT4_DAILY_LIMIT = int(os.getenv("GPT4_DAILY_LIMIT", "20"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USE_REPLY_ONLY = os.getenv("USE_REPLY_ONLY", "true").lower() == "true"

user_usage = {}
faq_data = {}

def load_faq_data():
    global faq_data
    try:
        with open("faq_data.json", "r", encoding="utf-8") as f:
            faq_data = json.load(f)
    except Exception as e:
        faq_data = {}

def get_faq_answer(message):
    for keyword, answer in faq_data.items():
        if keyword in message:
            return answer
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if USE_REPLY_ONLY and update.message and not update.message.text.startswith("@"):
        return

    if chat_id not in ALLOWED_CHAT_IDS:
        return

    text = update.message.text.strip()
    if user_id not in user_usage:
        user_usage[user_id] = {"gpt4_count": 0}

    if "/状态" in text and user_id == ADMIN_USER_ID:
        usage = user_usage.get(user_id, {})
        await update.message.reply_text(f"已用GPT-4：{usage.get('gpt4_count', 0)}次/每日上限{GPT4_DAILY_LIMIT}")
        return

    if "/增加管理员" in text and user_id == ADMIN_USER_ID:
        try:
            new_admin_id = int(text.split()[-1])
            if new_admin_id:
                await update.message.reply_text(f"管理员 {new_admin_id} 已添加（模拟）")
        except:
            await update.message.reply_text("格式错误，应为：/增加管理员 123456789")
        return

    answer = get_faq_answer(text)
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text("抱歉，我不太明白您的意思。")

if __name__ == "__main__":
    load_faq_data()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()