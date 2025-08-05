import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

# فعال‌سازی لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل گفتگو
(
    THICKNESS, DIAMETER, HEIGHT,
    FUNNEL_HEIGHT, FUNNEL_THICKNESS,
    BASE_COUNT, BASE_HEIGHT,
    BASE_DIAMETER, BASE_THICKNESS,
    WAGE, WASTE_PERCENT
) = range(11)

STEEL_DENSITY = 7850  # چگالی فولاد

def cylinder_volume(diameter_m, height_m):
    r = diameter_m / 2
    return 3.1416 * r**2 * height_m

def cone_surface_area(diameter_m, height_m):
    r = diameter_m / 2
    l = (r**2 + height_m**2) ** 0.5
    return 3.1416 * r * l

def pipe_weight(length_m, outer_diameter_inch, thickness_mm):
    outer_diameter_m = outer_diameter_inch * 0.0254
    thickness_m = thickness_mm / 1000
    inner_diameter_m = outer_diameter_m - 2 * thickness_m
    area = 3.1416 * (outer_diameter_m**2 - inner_diameter_m**2) / 4
    volume = area * length_m
    return volume * STEEL_DENSITY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("سلام! ضخامت بدنه مخزن را به میلی‌متر وارد کنید:")
    return THICKNESS

async def thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['thickness'] = val
        await update.message.reply_text("قطر مخزن را به متر وارد کنید:")
        return DIAMETER
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید:")

async def diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['diameter'] = val
        await update.message.reply_text("ارتفاع استوانه مخزن را به متر وارد کنید:")
        return HEIGHT
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['height'] = val
        await update.message.reply_text("ارتفاع قیف‌ها (کف و سقف) را به سانتی‌متر وارد کنید:")
        return FUNNEL_HEIGHT
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def funnel_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['funnel_height_cm'] = val
        await update.message.reply_text("ضخامت قیف‌ها را به میلی‌متر وارد کنید:")
        return FUNNEL_THICKNESS
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def funnel_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['funnel_thickness_mm'] = val
        await update.message.reply_text("تعداد پایه‌ها را وارد کنید (عدد صحیح، می‌تواند صفر باشد):")
        return BASE_COUNT
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = int(update.message.text)
        if val < 0: raise ValueError
        context.user_data['base_count'] = val
        if val == 0:
            context.user_data['base_height_cm'] = 0
            context.user_data['base_diameter_inch'] = 0
            context.user_data['base_thickness_mm'] = 0
            await update.message.reply_text("دستمزد به ازای هر کیلوگرم (تومان):")
            return WAGE
        else:
            await update.message.reply_text("ارتفاع هر پایه را به سانتی‌متر وارد کنید:")
            return BASE_HEIGHT
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['base_height_cm'] = val
        await update.message.reply_text("قطر هر پایه (اینچ):")
        return BASE_DIAMETER
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['base_diameter_inch'] = val
        await update.message.reply_text("ضخامت هر پایه (میلی‌متر):")
        return BASE_THICKNESS
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['base_thickness_mm'] = val
        await update.message.reply_text("دستمزد به ازای هر کیلوگرم (تومان):")
        return WAGE
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['wage'] = val
        await update.message.reply_text("درصد پرتی (مثلاً 10 برای ۱۰٪):")
        return WASTE_PERCENT
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

async def waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        waste = float(update.message.text)
        if waste < 0: raise ValueError
        context.user_data['waste_percent'] = waste

        # تبدیل واحدها
        t = context.user_data['thickness'] / 1000
        d = context.user_data['diameter']
        h = context.user_data['height']
        funnel_h = context.user_data['funnel_height_cm'] / 100
        funnel_t = context.user_data['funnel_thickness_mm'] / 1000
        base_count = context.user_data['base_count']
        base_h = context.user_data['base_height_cm'] / 100
        base_d = context.user_data['base_diameter_inch']
        base_th = context.user_data['base_thickness_mm']
        wage = context.user_data['wage']

        # وزن استوانه
        cyl_area = 3.1416 * d * h
        cyl_weight = cyl_area * t * STEEL_DENSITY

        # وزن قیف‌ها
        cone_area = cone_surface_area(d, funnel_h)
        funnel_weight = cone_area * funnel_t * STEEL_DENSITY * 2

        # وزن پایه‌ها
        base_weight = 0
        if base_count > 0:
            base_weight = pipe_weight(base_h, base_d, base_th) * base_count

        # وزن کل
        total_weight = cyl_weight + funnel_weight + base_weight
        total_with_waste = total_weight * (1 + waste / 100)
        price = total_with_waste * wage

        # پیام خروجی
        result = (
            f"وزن بدنه و قیف‌ها: {round(cyl_weight + funnel_weight)} کیلوگرم\n"
            f"وزن پایه‌ها: {round(base_weight)} کیلوگرم\n"
            f"وزن کل بدون پرتی: {round(total_weight)} کیلوگرم\n"
            f"وزن کل با پرتی {waste}٪: {round(total_with_waste)} کیلوگرم\n"
            f"قیمت کل: {round(price)} تومان"
        )
        await update.message.reply_text(result)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("عدد معتبر وارد کنید:")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, thickness)],
            DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, diameter)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            FUNNEL_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, funnel_height)],
            FUNNEL_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, funnel_thickness)],
            BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_count)],
            BASE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_height)],
            BASE_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_diameter)],
            BASE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_thickness)],
            WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wage)],
            WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, waste_percent)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
