import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
import math

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_THICKNESS, ASK_DIAMETER, ASK_HEIGHT, ASK_LABOR = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "برای محاسبه قیمت مخزن:\n"
        "لطفاً ضخامت بدنه را وارد کنید (بر حسب متر):"
    )
    return ASK_THICKNESS

async def get_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        thickness = float(update.message.text)
        context.user_data['thickness'] = thickness
        await update.message.reply_text("حالا قطر مخزن را وارد کنید (بر حسب متر):")
        return ASK_DIAMETER
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return ASK_THICKNESS

async def get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diameter = float(update.message.text)
        context.user_data['diameter'] = diameter
        await update.message.reply_text("حالا ارتفاع مخزن را وارد کنید (بر حسب متر):")
        return ASK_HEIGHT
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return ASK_DIAMETER

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        context.user_data['height'] = height
        await update.message.reply_text("حالا دستمزد ساخت به ازای هر کیلوگرم را وارد کنید (بر حسب ریال):")
        return ASK_LABOR
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return ASK_HEIGHT

async def calculate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        labor_cost = float(update.message.text)
        thickness = context.user_data['thickness']
        diameter = context.user_data['diameter']
        height = context.user_data['height']

        # محاسبه وزن (کیلوگرم)
        weight = math.pi * diameter * height * thickness * 7850

        # محاسبه قیمت (ریال)
        loss_factor = 1.1
        total_price = weight * loss_factor * labor_cost

        await update.message.reply_text(
            f"وزن تقریبی: {weight:,.2f} کیلوگرم\n"
            f"قیمت تقریبی: {total_price:,.0f} ریال\n\n"
            f"(یادآوری: ضخامت، قطر و ارتفاع بر حسب متر وارد شده‌اند)"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return ASK_LABOR

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("محاسبه لغو شد.")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_thickness)],
            ASK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diameter)],
            ASK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            ASK_LABOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
