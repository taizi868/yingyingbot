
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("你没有权限查看状态。")
        return
    await update.message.reply_text("盈盈AI 当前运行正常 ✅")

def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("status", status))  # 使用英文命令
    app.run_polling()

if __name__ == "__main__":
    main()
