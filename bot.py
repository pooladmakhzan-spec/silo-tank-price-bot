import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

ASKING_TYPE, ASKING_DIMENSIONS = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام!\n"
        "برای محاسبه قیمت:\n"
        "1️⃣ برای سیلو یا مخزن عدد 1 را بفرست\n"
        "2️⃣ برای اسکرو کانوایر عدد 2 را بفرست"
    )
    return ASKING_TYPE

async def ask_dimensions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == '1':
        context.user_data['type'] = 'silo'
        await update.message.reply_text("ابعاد سیلو/مخزن را به فرمت: قطر,ارتفاع,ضخامت (مثال: 3,7,0.5) بفرست")
        return ASKING_DIMENSIONS
    elif text == '2':
        context.user_data['type'] = 'screw'
        await update.message.reply_text("ابعاد اسکرو را به فرمت: قطر شفت,ضخامت تیغه,گام تیغه (مثال: 0.1,0.05,0.2) بفرست")
        return ASKING_DIMENSIONS
    else:
        await update.message.reply_text("لطفاً فقط عدد 1 یا 2 را ارسال کن.")
        return ASKING_TYPE

async def calculate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text.strip()
    try:
        if context.user_data['type'] == 'silo':
            diameter, height, thickness = map(float, data.split(','))
            weight = 3.14 * diameter * height * thickness * 7.85
            price_per_kg = 50
            loss_factor = 1.1
            labor_cost_per_kg = 20
            total_price = weight * loss_factor * labor_cost_per_kg
            await update.message.reply_text(f"قیمت تقریبی سیلو: {total_price:,.0f} ریال")
        elif context.user_data['type'] == 'screw':
            shaft_diameter, blade_thickness, blade_pitch = map(float, data.split(','))
            base_price = 1000000
            labor_shaper = 500000
            labor_builder = 300000
            total_price = base_price + labor_shaper + labor_builder + (shaft_diameter + blade_thickness + blade_pitch) * 1000000
            await update.message.reply_text(f"قیمت تقریبی اسکرو: {total_price:,.0f} ریال")
        else:
            await update.message.reply_text("نوع محصول مشخص نشده است.")
    except Exception as e:
        await update.message.reply_text("فرمت داده‌ها اشتباه است. لطفاً دوباره تلاش کنید.")
        logger.error(f"Error calculating price: {e}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرایند محاسبه لغو شد.")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_dimensions)],
            ASKING_DIMENSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()