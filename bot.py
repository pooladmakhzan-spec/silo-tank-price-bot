import math
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

(
    THICKNESS_BODY,
    THICKNESS_CONE,
    DIAMETER,
    HEIGHT_BODY,
    HEIGHT_CONE_BOTTOM,
    HEIGHT_CONE_TOP,
    WAGE,
) = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("سلام! ضخامت بدنه (میلی‌متر) را وارد کنید:")
    return THICKNESS_BODY

async def thickness_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness_body = float(update.message.text)
        context.user_data['thickness_body'] = thickness_body
        await update.message.reply_text("ضخامت قیف‌ها (میلی‌متر) را وارد کنید:")
        return THICKNESS_CONE
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return THICKNESS_BODY

async def thickness_cone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness_cone = float(update.message.text)
        context.user_data['thickness_cone'] = thickness_cone
        await update.message.reply_text("قطر مخزن (متر) را وارد کنید:")
        return DIAMETER
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return THICKNESS_CONE

async def diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        context.user_data['diameter'] = diameter
        await update.message.reply_text("ارتفاع بدنه استوانه‌ای مخزن (متر) را وارد کنید:")
        return HEIGHT_BODY
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return DIAMETER

async def height_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height_body = float(update.message.text)
        context.user_data['height_body'] = height_body
        await update.message.reply_text("ارتفاع قیف کف (سانتی‌متر) را وارد کنید:")
        return HEIGHT_CONE_BOTTOM
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return HEIGHT_BODY

async def height_cone_bottom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height_cone_bottom = float(update.message.text)
        context.user_data['height_cone_bottom'] = height_cone_bottom
        await update.message.reply_text("ارتفاع قیف سقف (سانتی‌متر) را وارد کنید:")
        return HEIGHT_CONE_TOP
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return HEIGHT_CONE_BOTTOM

async def height_cone_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height_cone_top = float(update.message.text)
        context.user_data['height_cone_top'] = height_cone_top
        await update.message.reply_text("دستمزد به ازای هر کیلوگرم (تومان) را وارد کنید:")
        return WAGE
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return HEIGHT_CONE_TOP

async def wage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        wage = float(update.message.text)
        context.user_data['wage'] = wage

        # محاسبات
        thickness_body_m = context.user_data['thickness_body'] / 1000
        thickness_cone_m = context.user_data['thickness_cone'] / 1000
        diameter_m = context.user_data['diameter']
        height_body_m = context.user_data['height_body']
        height_cone_bottom_m = context.user_data['height_cone_bottom'] / 100
        height_cone_top_m = context.user_data['height_cone_top'] / 100
        radius_m = diameter_m / 2
        density = 7850  # kg/m^3

        lateral_area_cylinder = math.pi * diameter_m * height_body_m
        weight_cylinder = lateral_area_cylinder * thickness_body_m * density

        l_bottom = math.sqrt(radius_m**2 + height_cone_bottom_m**2)
        lateral_area_cone_bottom = math.pi * radius_m * l_bottom
        weight_cone_bottom = lateral_area_cone_bottom * thickness_cone_m * density

        l_top = math.sqrt(radius_m**2 + height_cone_top_m**2)
        lateral_area_cone_top = math.pi * radius_m * l_top
        weight_cone_top = lateral_area_cone_top * thickness_cone_m * density

        total_weight_no_scrap = weight_cylinder + weight_cone_bottom + weight_cone_top
        total_weight_with_scrap = total_weight_no_scrap * 1.1
        final_price = total_weight_with_scrap * wage

        await update.message.reply_text(
            f"وزن مخزن بدون پرتی: {total_weight_no_scrap:.2f} کیلوگرم\n"
            f"وزن مخزن با احتساب ۱۰٪ ضریب پرتی: {total_weight_with_scrap:.2f} کیلوگرم\n"
            f"قیمت نهایی مخزن: {final_price:,.0f} تومان"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً عدد معتبر وارد کنید.")
        return WAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("محاسبه لغو شد.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            THICKNESS_BODY: [MessageHandler(filters.TEXT & (~filters.COMMAND), thickness_body)],
            THICKNESS_CONE: [MessageHandler(filters.TEXT & (~filters.COMMAND), thickness_cone)],
            DIAMETER: [MessageHandler(filters.TEXT & (~filters.COMMAND), diameter)],
            HEIGHT_BODY: [MessageHandler(filters.TEXT & (~filters.COMMAND), height_body)],
            HEIGHT_CONE_BOTTOM: [MessageHandler(filters.TEXT & (~filters.COMMAND), height_cone_bottom)],
            HEIGHT_CONE_TOP: [MessageHandler(filters.TEXT & (~filters.COMMAND), height_cone_top)],
            WAGE: [MessageHandler(filters.TEXT & (~filters.COMMAND), wage)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    print("ربات در حال اجراست...")
    application.run_polling()

if __name__ == '__main__':
    main()
