from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, ContextTypes
import math

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# States
CHOOSE_MODE, CHOOSE_CALC, GET_DIAMETER, GET_HEIGHT, GET_VOLUME, CHOOSE_ORIENTATION, \
GET_TANK_DIAMETER, GET_TANK_HEIGHT, GET_CONE_HEIGHT, GET_BODY_THICKNESS, GET_CONE_THICKNESS, \
GET_BASE_COUNT, GET_BASE_HEIGHT, GET_BASE_DIAMETER, GET_BASE_THICKNESS, GET_SCRAP, GET_COST = range(16)

STEEL_DENSITY = 7850  # kg/m³

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("محاسبه طول/قطر/حجم", callback_data="calc")],
        [InlineKeyboardButton("محاسبه وزن و قیمت", callback_data="price")]
    ]
    await update.message.reply_text("یکی از حالت‌ها را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_MODE

# Choose mode
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "calc":
        keyboard = [
            [InlineKeyboardButton("محاسبه طول", callback_data="length")],
            [InlineKeyboardButton("محاسبه قطر", callback_data="diameter")],
            [InlineKeyboardButton("محاسبه حجم", callback_data="volume")]
        ]
        await query.edit_message_text("چه چیزی را می‌خواهید محاسبه کنید؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSE_CALC
    else:
        await query.edit_message_text("قطر مخزن (متر):")
        return GET_TANK_DIAMETER

# Choose calculation type
async def choose_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["calc_type"] = query.data
    if query.data == "length":
        await query.edit_message_text("قطر مخزن (متر):")
        return GET_DIAMETER
    elif query.data == "diameter":
        await query.edit_message_text("طول مخزن (متر):")
        return GET_HEIGHT
    elif query.data == "volume":
        await query.edit_message_text("قطر مخزن (متر):")
        return GET_VOLUME

# For calc: get inputs
async def get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("حجم مورد نظر (متر مکعب):")
    return CHOOSE_ORIENTATION

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["length"] = float(update.message.text)
    await update.message.reply_text("حجم مورد نظر (متر مکعب):")
    return CHOOSE_ORIENTATION

async def get_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("طول مخزن (متر):")
    return CHOOSE_ORIENTATION

# Orientation selection
async def choose_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # برای طول و قطر، ورودی حجم را اینجا می‌گیریم
    calc_type = context.user_data["calc_type"]
    if calc_type in ["length", "diameter"]:
        context.user_data["volume"] = float(update.message.text)
    elif calc_type == "volume":
        context.user_data["length"] = float(update.message.text)

    keyboard = [
        [InlineKeyboardButton("عمودی", callback_data="vertical")],
        [InlineKeyboardButton("افقی", callback_data="horizontal")]
    ]
    await update.message.reply_text("مخزن افقی است یا عمودی؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return None

# Orientation callback and calculation
async def orientation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orientation = query.data
    calc_type = context.user_data.get("calc_type")

    d = context.user_data.get("diameter")
    v = context.user_data.get("volume")
    l = context.user_data.get("length")

    r = d / 2 if d else None
    cone_vol = (1/3) * math.pi * r**2 * r if r else 0  # حجم قیف‌ها

    if calc_type == "length":
        if orientation == "vertical":
            v -= cone_vol
        else:
            v -= 2 * cone_vol
        length = v / (math.pi * r**2)
        await query.edit_message_text(f"طول مورد نیاز: {length:.2f} متر")

    elif calc_type == "diameter":
        if orientation == "vertical":
            v -= cone_vol
        else:
            v -= 2 * cone_vol
        diameter = math.sqrt((4 * v) / (math.pi * l))
        await query.edit_message_text(f"قطر مورد نیاز: {diameter:.2f} متر")

    elif calc_type == "volume":
        cyl_vol = math.pi * r**2 * l
        if orientation == "vertical":
            total_vol = cyl_vol + cone_vol
        else:
            total_vol = cyl_vol + 2 * cone_vol
        await query.edit_message_text(f"حجم مخزن: {total_vol:.2f} متر مکعب")

    return ConversationHandler.END

# Weight and price inputs
async def get_tank_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع بدنه (متر):")
    return GET_TANK_HEIGHT

async def get_tank_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتیمتر):")
    return GET_CONE_HEIGHT

async def get_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_height"] = float(update.message.text) / 100
    await update.message.reply_text("ضخامت بدنه (میلی‌متر):")
    return GET_BODY_THICKNESS

async def get_body_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["body_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("ضخامت قیف‌ها (میلی‌متر):")
    return GET_CONE_THICKNESS

async def get_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("تعداد پایه:")
    return GET_BASE_COUNT

async def get_base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["base_count"] = int(update.message.text)
    await update.message.reply_text("ارتفاع پایه‌ها (سانتیمتر):")
    return GET_BASE_HEIGHT

async def get_base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["base_height"] = float(update.message.text) / 100
    await update.message.reply_text("قطر پایه (اینچ):")
    return GET_BASE_DIAMETER

async def get_base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["base_diameter"] = float(update.message.text) * 0.0254
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return GET_BASE_THICKNESS

async def get_base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["base_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("درصد پرتی (%):")
    return GET_SCRAP

async def get_scrap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["scrap"] = float(update.message.text) / 100
    await update.message.reply_text("دستمزد ساخت (تومان/کیلوگرم):")
    return GET_COST

async def get_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cost_per_kg"] = float(update.message.text)

    # محاسبات وزن
    d = context.user_data["diameter"]
    h = context.user_data["height"]
    hc = context.user_data["cone_height"]
    t_body = context.user_data["body_thickness"]
    t_cone = context.user_data["cone_thickness"]

    # وزن بدنه
    body_area = math.pi * d * h
    body_vol = body_area * t_body
    body_weight = body_vol * STEEL_DENSITY

    # وزن قیف‌ها
    r = d / 2
    cone_area = math.pi * r * math.sqrt(r**2 + hc**2)
    cone_vol = cone_area * t_cone
    cones_weight = 2 * cone_vol * STEEL_DENSITY

    # وزن پایه‌ها
    n = context.user_data["base_count"]
    hb = context.user_data["base_height"]
    db = context.user_data["base_diameter"]
    tb = context.user_data["base_thickness"]
    base_weight = n * (math.pi * db * tb * hb * STEEL_DENSITY)

    # وزن کلی
    total_weight = body_weight + cones_weight + base_weight
    total_weight_scrap = total_weight * (1 + context.user_data["scrap"])
    total_price = total_weight_scrap * context.user_data["cost_per_kg"]

    await update.message.reply_text(
        f"وزن مخزن: {int(body_weight + cones_weight)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(base_weight)} کیلوگرم\n"
        f"وزن کلی با پرتی: {int(total_weight_scrap)} کیلوگرم\n"
        f"قیمت کل: {int(total_price)} تومان"
    )

    return ConversationHandler.END

# Reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("بات ریست شد. /start را بزنید.")
    return ConversationHandler.END

# Main
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [CallbackQueryHandler(choose_mode)],
            CHOOSE_CALC: [CallbackQueryHandler(choose_calc)],
            GET_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diameter)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            GET_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_volume)],
            CHOOSE_ORIENTATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_orientation)],

            GET_TANK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tank_diameter)],
            GET_TANK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tank_height)],
            GET_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_height)],
            GET_BODY_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_body_thickness)],
            GET_CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_thickness)],
            GET_BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_base_count)],
            GET_BASE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_base_height)],
            GET_BASE_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_base_diameter)],
            GET_BASE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_base_thickness)],
            GET_SCRAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_scrap)],
            GET_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cost)],
        },
        fallbacks=[CommandHandler("reset", reset)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(orientation_callback, pattern="^(vertical|horizontal)$"))
    app.run_polling()

if __name__ == "__main__":
    main()
