import math
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes, 
    ConversationHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
)

STEEL_DENSITY = 7850  # کیلوگرم بر متر مکعب

# مراحل گفتگو
(
    ASK_THICKNESS_BODY,
    ASK_DIAMETER_BODY,
    ASK_HEIGHT_BODY,
    ASK_THICKNESS_CONE,
    ASK_HEIGHT_CONE,
    ASK_BASE_COUNT,
    ASK_BASE_HEIGHT,
    ASK_BASE_DIAMETER,
    ASK_BASE_THICKNESS,
    ASK_WASTE_PERCENT,
    ASK_WAGE,
) = range(11)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! برای شروع، ضخامت ورق بدنه مخزن (میلیمتر) را وارد کنید:"
    )
    context.user_data.clear()
    return ASK_THICKNESS_BODY


async def ask_diameter_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['thickness_body'] = val / 1000  # تبدیل میلیمتر به متر
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ضخامت ورق وارد کنید:")
        return ASK_THICKNESS_BODY

    await update.message.reply_text("📏 قطر بدنه مخزن (متر) را وارد کنید:")
    return ASK_DIAMETER_BODY


async def ask_height_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['diameter_body'] = val
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای قطر وارد کنید:")
        return ASK_DIAMETER_BODY

    await update.message.reply_text("📐 ارتفاع بدنه مخزن (متر) را وارد کنید:")
    return ASK_HEIGHT_BODY


async def ask_thickness_cone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['height_body'] = val
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ارتفاع وارد کنید:")
        return ASK_HEIGHT_BODY

    await update.message.reply_text("🔧 ضخامت ورق قیف‌ها (میلیمتر) را وارد کنید:")
    return ASK_THICKNESS_CONE


async def ask_height_cone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['thickness_cone'] = val / 1000
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ضخامت قیف وارد کنید:")
        return ASK_THICKNESS_CONE

    await update.message.reply_text("🔻 ارتفاع قیف (سانتی‌متر) را وارد کنید:")
    return ASK_HEIGHT_CONE


async def ask_base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['height_cone'] = val / 100  # تبدیل سانتی‌متر به متر
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ارتفاع قیف وارد کنید:")
        return ASK_HEIGHT_CONE

    await update.message.reply_text("🦵 تعداد پایه‌ها را وارد کنید:")
    return ASK_BASE_COUNT


async def ask_base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = int(text)
        if val <= 0:
            raise ValueError()
        context.user_data['base_count'] = val
    except:
        await update.message.reply_text("⚠️ لطفا عدد صحیح مثبت برای تعداد پایه‌ها وارد کنید:")
        return ASK_BASE_COUNT

    await update.message.reply_text("📏 ارتفاع هر پایه (سانتی‌متر) را وارد کنید:")
    return ASK_BASE_HEIGHT


async def ask_base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['base_height'] = val / 100  # تبدیل به متر
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ارتفاع پایه وارد کنید:")
        return ASK_BASE_HEIGHT

    await update.message.reply_text("🔵 قطر پایه (اینچ) را وارد کنید:")
    return ASK_BASE_DIAMETER


async def ask_base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError()
        context.user_data['base_diameter_inch'] = val
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای قطر پایه وارد کنید:")
        return ASK_BASE_DIAMETER

    await update.message.reply_text("⚙️ ضخامت پایه (میلیمتر) را وارد کنید:")
    return ASK_BASE_THICKNESS


async def ask_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError()
        context.user_data['base_thickness'] = val / 1000  # میلیمتر به متر
    except:
        await update.message.reply_text("⚠️ لطفا عدد مثبت معتبر برای ضخامت پایه وارد کنید:")
        return ASK_BASE_THICKNESS

    await update.message.reply_text("♻️ درصد پرتی مواد را وارد کنید (مثلا 5 برای ۵٪):")
    return ASK_WASTE_PERCENT


async def ask_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError()
        context.user_data['waste_percent'] = val
    except:
        await update.message.reply_text("⚠️ لطفا درصد پرتی را به عدد مثبت یا صفر وارد کنید:")
        return ASK_WASTE_PERCENT

    await update.message.reply_text("💰 دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کنید:")
    return ASK_WAGE


async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        wage_per_kg = float(text)
        if wage_per_kg < 0:
            raise ValueError()
        context.user_data['wage'] = wage_per_kg
    except:
        await update.message.reply_text("⚠️ لطفا دستمزد را عددی مثبت یا صفر وارد کنید:")
        return ASK_WAGE

    data = context.user_data
    wage = data['wage']

    r_body = data['diameter_body'] / 2
    t_body = data['thickness_body']
    h_body = data['height_body']

    t_cone = data['thickness_cone']
    h_cone = data['height_cone']

    base_count = data['base_count']
    base_height = data['base_height']
    base_diameter_inch = data['base_diameter_inch']
    base_thickness = data['base_thickness']
    waste_percent = data['waste_percent']

    # وزن بدنه استوانه
    surface_cylinder = 2 * math.pi * r_body * h_body
    volume_body = surface_cylinder * t_body
    weight_body = volume_body * STEEL_DENSITY

    # وزن دو قیف (مخروط)
    circumference_cone = 2 * math.pi * r_body
    volume_one_cone = circumference_cone * t_cone * h_cone
    weight_cones = 2 * volume_one_cone * STEEL_DENSITY

    # محاسبه وزن پایه‌ها (لوله‌ای)
    base_diameter_m = base_diameter_inch * 0.0254
    outer_radius = base_diameter_m / 2
    inner_radius = outer_radius - base_thickness
    height_base = base_height

    volume_base = base_count * (math.pi * (outer_radius ** 2) * height_base - math.pi * (inner_radius ** 2) * height_base)
    weight_base = volume_base * STEEL_DENSITY

    weight_total = weight_body + weight_cones + weight_base
    weight_total_with_waste = weight_total * (1 + waste_percent / 100)

    price = weight_total_with_waste * wage

    weight_body_int = int(round(weight_body))
    weight_cones_int = int(round(weight_cones))
    weight_base_int = int(round(weight_base))
    weight_total_int = int(round(weight_total))
    weight_total_waste_int = int(round(weight_total_with_waste))
    price_int = int(round(price))

    result_text = (
        f"🏭 وزن بدنه مخزن: {weight_body_int} کیلوگرم\n"
        f"🔻 وزن دو قیف: {weight_cones_int} کیلوگرم\n"
        f"🦵 وزن پایه‌ها: {weight_base_int} کیلوگرم\n"
        f"⚖️ وزن کل (بدون پرتی): {weight_total_int} کیلوگرم\n"
        f"📦 وزن کل با پرتی ({waste_percent}%): {weight_total_waste_int} کیلوگرم\n"
        f"💵 قیمت کل ساخت: {price_int} تومان\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 شروع دوباره", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(result_text, reply_markup=reply_markup)
    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'restart':
        await query.message.delete()
        await start(update, context)
        return ASK_THICKNESS_BODY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد. برای شروع دوباره /start را بزنید.")
    return ConversationHandler.END


def main():
    import os
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_THICKNESS_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_diameter_body)],
            ASK_DIAMETER_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_height_body)],
            ASK_HEIGHT_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_thickness_cone)],
            ASK_THICKNESS_CONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_height_cone)],
            ASK_HEIGHT_CONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_base_count)],
            ASK_BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_base_height)],
            ASK_BASE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_base_diameter)],
            ASK_BASE_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_base_thickness)],
            ASK_BASE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_waste_percent)],
            ASK_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_wage)],
            ASK_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_result)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="calc_tank_bot",
        persistent=False,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 ربات آماده به کار است...")
    app.run_polling()


if __name__ == '__main__':
    main()
