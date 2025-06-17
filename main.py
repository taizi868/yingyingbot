import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import openai

# 初始化日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 环境变量读取
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "0"))
GPT4_DAILY_LIMIT = int(os.environ.get("GPT4_DAILY_LIMIT", "30"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_MODEL = os.environ.get("OPENAI_API_MODEL", "gpt-4o")

openai.api_key = OPENAI_API_KEY

# 简单用户请求记录
user_usage = {}

# 指令：状态
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        return
    await update.message.reply_text("盈盈运行中 ✅\n当前模型：" + OPENAI_API_MODEL)

# 指令：增加管理员（仅演示，无实际存储）
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("功能占位：管理员权限尚未持久化实现")

# 私聊限制
async def private_chat_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    await chat_handler(update, context)

# 主逻辑
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id not in user_usage:
        user_usage[user_id] = 0

    if user_usage[user_id] >= GPT4_DAILY_LIMIT:
        model = "gpt-3.5-turbo"
        notice = "\n⚠️ 您的 GPT-4 使用额度已用尽，已切换为 GPT-3.5。"
    else:
        model = OPENAI_API_MODEL
        notice = ""

    user_usage[user_id] += 1

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": message}]
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = "出错了：" + str(e)

    await update.message.reply_text(answer + notice)

# FAQ 示例
faq_data = {
    "VIP返水怎么算": "VIP返水根据不同等级发放比例，VIP1 为 0.5%，VIP5 为 1.5%。详情请咨询客服。",
}

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for keyword, reply in faq_data.items():
        if keyword in text:
            await update.message.reply_text(reply)
            return
    await chat_handler(update, context)

# 启动 bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("状态", status))
    app.add_handler(CommandHandler("增加管理员", add_admin))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, private_chat_block))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, faq_handler))

    print("YingYing bot 正在运行...")
    app.run_polling()

if __name__ == "__main__":
    main()
