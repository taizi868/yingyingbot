
import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
import openai

logging.basicConfig(level=logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

USER_USAGE = {}

def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

def is_admin(user_id):
    return str(user_id) in ADMIN_USER_IDS

async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id
    text = message.text.strip()

    if message.chat.type != "private" and not message.text.startswith("@") and not message.text.startswith("/"):
        return

    if not is_authorized(chat_id) and message.chat.type != "private":
        return

    if message.chat.type == "private" and not is_admin(user_id):
        await message.reply_text("⚠️ 仅限管理员可使用盈盈私聊功能")
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    usage = USER_USAGE.get(user_id, {"gpt4": 0})
    model = "gpt-3.5-turbo"
    if usage["gpt4"] < 30:
        model = "gpt-4"
        usage["gpt4"] += 1
        USER_USAGE[user_id] = usage
    else:
        await message.reply_text("⚠️ 今日 GPT-4 使用已达 30 次，已自动切换为 GPT-3.5")

    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion["choices"][0]["message"]["content"]
        await message.reply_text(reply)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

async def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    await update.message.reply_text("✅ 盈盈运行中，OpenAI模型：{}".format(OPENAI_MODEL))

async def add_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    if context.args:
        ADMIN_USER_IDS.append(context.args[0])
        await update.message.reply_text(f"✅ 添加管理员成功：{context.args[0]}")

async def remove_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    if context.args:
        ADMIN_USER_IDS.remove(context.args[0])
        await update.message.reply_text(f"✅ 移除管理员成功：{context.args[0]}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.run_polling()

if __name__ == "__main__":
    main()
