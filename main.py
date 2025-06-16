
import os
import logging
import json
from datetime import datetime, timedelta

from telegram import Update, MessageEntity
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
import openai

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_GPT4 = "gpt-4"
OPENAI_MODEL_GPT35 = "gpt-3.5-turbo"
MODEL_LIMIT_PER_USER = int(os.getenv("GPT4_DAILY_LIMIT", 30))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

# 用户数据存储
user_model_usage = {}
admin_list = set([ADMIN_USER_ID])
FAQ_DATA = {}

# 载入FAQ
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except:
            FAQ_DATA = {}

# 工具函数
def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

def is_admin(user_id):
    return user_id in admin_list

def get_model_for_user(user_id):
    now = datetime.utcnow().date()
    usage = user_model_usage.get(user_id, {})
    if usage.get("date") != now:
        usage = {"date": now, "count": 0}
    if usage["count"] < MODEL_LIMIT_PER_USER:
        usage["count"] += 1
        user_model_usage[user_id] = usage
        return OPENAI_MODEL_GPT4, f"（GPT-4 剩余 {MODEL_LIMIT_PER_USER - usage['count']} 次）"
    else:
        return OPENAI_MODEL_GPT35, "（GPT-4 今日已用尽，切换为 GPT-3.5）"

# 消息处理主逻辑
async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id
    text = message.text.strip()

    if update.message.chat.type != "private":
        if not is_authorized(chat_id):
            return
        if not (message.entities and any(e.type == MessageEntity.MENTION for e in message.entities)):
            return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    model, note = get_model_for_user(user_id)
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion["choices"][0]["message"]["content"]
        await message.reply_text(reply + f"

{note}")
    except Exception as e:
        logger.exception(e)
        await message.reply_text("出错了，请稍后再试或联系管理员。")

# /状态 指令
async def status_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("无权限。")
        return
    stats = "
".join([f"{uid}: {d['count']}次" for uid, d in user_model_usage.items()])
    await update.message.reply_text(f"📊 当前使用情况：
{stats or '暂无数据'}")

# 管理员添加/移除指令
async def add_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("仅超级管理员可操作。")
        return
    try:
        target_id = int(context.args[0])
        admin_list.add(target_id)
        await update.message.reply_text(f"✅ 已添加管理员 {target_id}")
    except:
        await update.message.reply_text("格式错误，用法：/添加管理员 <用户ID>")

async def remove_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("仅超级管理员可操作。")
        return
    try:
        target_id = int(context.args[0])
        if target_id in admin_list:
            admin_list.remove(target_id)
            await update.message.reply_text(f"✅ 已移除管理员 {target_id}")
        else:
            await update.message.reply_text("该用户不是管理员。")
    except:
        await update.message.reply_text("格式错误，用法：/移除管理员 <用户ID>")

# 主程序入口
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("状态", status_command))
    app.add_handler(CommandHandler("添加管理员", add_admin))
    app.add_handler(CommandHandler("移除管理员", remove_admin))
    app.run_polling()

if __name__ == "__main__":
    main()
