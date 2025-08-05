from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
import math
import os

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل مکالمه
(
    CHOOSING_ORIENTATION,
    CYLINDER_DIAMETER,
    CYLINDER_HEIGHT,
    CYLINDER_THICKNESS,
    CONE_HEIGHT,
    CONE_THICKNESS,
    NUM_LEGS,
    LEG_HEIGHT,
    LEG_DIAMETER,
    LEG_THICKNESS,
    WASTE_PERCENT,
    LABOR_COST
) = range(12)

# چگالی فولاد
STEEL_DENSITY = 7850  # kg/m³

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("عمودی", callback_data="vertical")],
        [InlineKeyboardButton("افقی", callback_data="horizontal")]
    ]
    await update.message.reply_text(
        "لطفاً نوع مخزن را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_ORIENTATION

async def choose_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["orientation"] = query.data
    await query.edit_message_text("قطر بدنه استوانه (متر) را وارد کنید:")
    return CYLINDER_DIAMETER

async def get_cylinder_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cylinder_diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع بدنه استوانه (متر) را وارد کنید:")
    return CYLINDER_HEIGHT

async def get_cylinder_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cylinder_height"] = float(update.message.text)
    await update.message.reply_text("ضخامت بدنه استوانه (میلی‌متر) را وارد کنید:")
    return CYLINDER_THICKNESS

async def get_cylinder_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cylinder_thickness"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتی‌متر) را وارد کنید:")
    return CONE_HEIGHT

async def get_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_height"] = float(update.message.text)
    await update.message.reply_text("ضخامت قیف‌ها (میلی‌متر) را وارد کنید:")
    return CONE_THICKNESS

async def get_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_thickness"] = float(update.message.text)
    await update.message.reply_text("تعداد پایه‌ها را وارد کنید:")
    return NUM_LEGS

async def get_num_legs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["num_legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر) را وارد کنید:")
    return LEG_HEIGHT

async def get_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_height"] = float(update.message.text)
    await update.message.reply_text("قطر هر پایه (اینچ) را وارد کنید:")
    return LEG_DIAMETER

async def get_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_diameter"] = float(update.message.text)
    await update.message.reply_text("ضخامت هر پایه (میلی‌متر) را وارد کنید:")
    return LEG_THICKNESS

async def get_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_thickness"] = float(update.message.text)
    await update.message.reply_text("درصد پرتی را وارد کنید:")
    return WASTE_PERCENT

async def get_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waste_percent"] = float(update.message.text)
    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کنید:")
    return LABOR_COST

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    labor_cost = float(update.message.text)
    data = context.user_data

    # داده‌های ورودی
    d = data["cylinder_diameter"]
    h = data["cylinder_height"]
    t_cyl = data["cylinder_thickness"] / 1000
    h_cone = data["cone_height"] / 100
    t_cone = data["cone_thickness"] / 1000
    orientation = data["orientation"]

    # محاسبه سطح جانبی استوانه
    cylinder_area = math.pi * d * h
    cylinder_weight = cylinder_area * t_cyl * STEEL_DENSITY

    # محاسبه سطح هر قیف
    r_base = d / 2
    slant_height = math.sqrt(r_base**2 + h_cone**2)
    cone_area = math.pi * r_base * slant_height
    cone_weight = cone_area * t_cone * STEEL_DENSITY

    # وزن مخزن بر اساس حالت
    if orientation == "vertical":
        tank_weight = cylinder_weight + cone_weight  # فقط قیف پایین
    else:
        tank_weight = cylinder_weight + (2 * cone_weight)  # هر دو قیف

    # محاسبه وزن پایه‌ها
    num_legs = data["num_legs"]
    leg_h = data["leg_height"] / 100
    leg_d = data["leg_diameter"] * 0.0254
    leg_t = data["leg_thickness"] / 1000
    leg_circumference = math.pi * leg_d
    leg_weight = leg_circumference * leg_t * leg_h * STEEL_DENSITY * num_legs

    # وزن کل
    total_weight = tank_weight + leg_weight
    total_with_waste = total_weight * (1 + data["waste_percent"] / 100)
    total_price = total_with_waste * labor_cost

    result = (
        f"وزن مخزن (بدون پایه): {int(tank_weight)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(leg_weight)} کیلوگرم\n"
        f"وزن کل (بدون پرتی): {int(total_weight)} کیلوگرم\n"
        f"وزن کل با پرتی: {int(total_with_waste)} کیلوگرم\n"
        f"قیمت کل: {int(total_price)} تومان"
    )

    await update.message.reply_text(result)
    return ConversationHandler.END

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("داده‌ها ریست شد. /start")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ORIENTATION: [CallbackQueryHandler(choose_orientation)],
            CYLINDER_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cylinder_diameter)],
            CYLINDER_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cylinder_height)],
            CYLINDER_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cylinder_thickness)],
            CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_height)],
            CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_thickness)],
            NUM_LEGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num_legs)],
            LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_height)],
            LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_diameter)],
            LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_thickness)],
            WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_waste_percent)],
            LABOR_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate)],
        },
        fallbacks=[CommandHandler("reset", reset)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
