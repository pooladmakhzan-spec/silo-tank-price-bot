import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# States
MAIN_MENU, PRICING_DIAMETER, PRICING_HEIGHT, PRICING_BODY_THICKNESS, \
PRICING_CONE_BOTTOM_THICKNESS, PRICING_CONE_TOP_THICKNESS, PRICING_CONE_HEIGHT, \
PRICING_LEG_COUNT, PRICING_LEG_HEIGHT, PRICING_LEG_DIAMETER, PRICING_LEG_THICKNESS, \
PRICING_WASTE, PRICING_WAGE, \
MODE_SELECTION, CALC_CHOICE, CALC_DIAMETER, CALC_HEIGHT, CALC_VOLUME = range(16)

user_data = {}
STEEL_DENSITY = 7850  # kg/m³

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 قیمت‌گذاری مخزن", callback_data="pricing")],
        [InlineKeyboardButton("📐 محاسبه طول/قطر/حجم", callback_data="calc")]
    ]
    await update.message.reply_text(
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id] = {}
    if query.data == "pricing":
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return PRICING_DIAMETER
    else:
        keyboard = [
            [InlineKeyboardButton("عمودی", callback_data="vertical"),
             InlineKeyboardButton("افقی", callback_data="horizontal")]
        ]
        await query.edit_message_text(
            "مخزن افقی است یا عمودی؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MODE_SELECTION

# --- Pricing flow ---

async def pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع بدنه مخزن (متر) را وارد کنید:")
    return PRICING_HEIGHT

async def pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["height"] = float(update.message.text)
    await update.message.reply_text("ضخامت ورق بدنه (میلی‌متر) را وارد کنید:")
    return PRICING_BODY_THICKNESS

async def pricing_body_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["body_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("ضخامت قیف پایین (میلی‌متر) را وارد کنید:")
    return PRICING_CONE_BOTTOM_THICKNESS

async def pricing_cone_bottom_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["cone_bottom_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("ضخامت قیف بالا (میلی‌متر) را وارد کنید:")
    return PRICING_CONE_TOP_THICKNESS

async def pricing_cone_top_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["cone_top_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("ارتفاع قیف‌ها (سانتی‌متر) را وارد کنید:")
    return PRICING_CONE_HEIGHT

async def pricing_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["cone_height"] = float(update.message.text) / 100
    await update.message.reply_text("تعداد پایه‌ها را وارد کنید:")
    return PRICING_LEG_COUNT

async def pricing_leg_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر) را وارد کنید:")
    return PRICING_LEG_HEIGHT

async def pricing_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_height"] = float(update.message.text) / 100
    await update.message.reply_text("قطر پایه (اینچ) را وارد کنید:")
    return PRICING_LEG_DIAMETER

async def pricing_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_diameter"] = float(update.message.text) * 0.0254
    await update.message.reply_text("ضخامت پایه (میلی‌متر) را وارد کنید:")
    return PRICING_LEG_THICKNESS

async def pricing_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("درصد پرتی را وارد کنید (مثلاً 10):")
    return PRICING_WASTE

async def pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["waste"] = float(update.message.text) / 100
    await update.message.reply_text("دستمزد ساخت (تومان به ازای هر کیلوگرم) را وارد کنید:")
    return PRICING_WAGE

async def pricing_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    wage = float(update.message.text)
    data = user_data[uid]

    d = data["diameter"]
    h = data["height"]
    t_body = data["body_thickness"]
    t_cb = data["cone_bottom_thickness"]
    t_ct = data["cone_top_thickness"]
    ch = data["cone_height"]
    legs = data["legs"]
    lh = data["leg_height"]
    ld = data["leg_diameter"]
    lt = data["leg_thickness"]
    waste = data["waste"]

    # بدنه
    r = d / 2
    body_area = 2 * math.pi * r * h
    body_weight = body_area * t_body * STEEL_DENSITY

    # قیف پایین
    sl_b = math.sqrt(r**2 + ch**2)
    area_cb = math.pi * r * sl_b
    weight_cb = area_cb * t_cb * STEEL_DENSITY

    # قیف بالا
    sl_t = sl_b
    area_ct = math.pi * r * sl_t
    weight_ct = area_ct * t_ct * STEEL_DENSITY

    # پایه‌ها
    base_weight = legs * (2 * math.pi * ld/2 * lh * lt * STEEL_DENSITY)

    tank_weight = body_weight + weight_cb + weight_ct
    total_weight = tank_weight + base_weight
    total_with_waste = total_weight * (1 + waste)
    price = total_with_waste * wage

    await update.message.reply_text(
        f"وزن مخزن (بدنه + قیف‌ها): {int(tank_weight)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(base_weight)} کیلوگرم\n"
        f"وزن کل بدون پرتی: {int(total_weight)} کیلوگرم\n"
        f"وزن کل با پرتی ({int(waste*100)}%): {int(total_with_waste)} کیلوگرم\n"
        f"قیمت کل: {int(price):,} تومان"
    )
    return ConversationHandler.END

# --- Dimensions flow ---

async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id] = {"orientation": query.data}
    keyboard = [
        [InlineKeyboardButton("محاسبه طول", callback_data="length"),
         InlineKeyboardButton("محاسبه قطر", callback_data="diameter")],
        [InlineKeyboardButton("محاسبه حجم", callback_data="volume")]
    ]
    await query.edit_message_text("چه چیزی را می‌خواهید محاسبه کنید؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return CALC_CHOICE

async def calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]["action"] = query.data
    if query.data == "length":
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER
    elif query.data == "diameter":
        await query.edit_message_text("طول مخزن (متر) را وارد کنید:")
        return CALC_HEIGHT
    else:
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER

async def get_calc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    action = user_data[uid]["action"]
    if action == "length":
        user_data[uid]["diameter"] = float(update.message.text)
        await update.message.reply_text("حجم مخزن (لیتر) را وارد کنید:")
        return CALC_VOLUME
    elif action == "diameter":
        user_data[uid]["length"] = float(update.message.text)
        await update.message.reply_text("حجم مخزن (لیتر) را وارد کنید:")
        return CALC_VOLUME
    else:
        user_data[uid]["diameter"] = float(update.message.text)
        await update.message.reply_text("طول مخزن (متر) را وارد کنید:")
        return CALC_HEIGHT

async def get_calc_second_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    data = user_data[uid]
    orientation = data["orientation"]
    action = data["action"]

    if action == "length":
        volume_l = float(update.message.text)
        volume_m3 = volume_l / 1000
        r = data["diameter"] / 2
        ch = data.get("cone_height", 0.5)  # default if not set
        cone_vol = (math.pi * r**2 * ch) / 3
        usable = volume_m3 - (2*cone_vol if orientation=="horizontal" else cone_vol)
        length = usable / (math.pi * r**2)
        await update.message.reply_text(f"طول مخزن ≈ {length:.2f} متر")

    elif action == "diameter":
        volume_l = float(update.message.text)
        volume_m3 = volume_l / 1000
        length = data["length"]
        ch = data.get("cone_height", 0.5)
        cone_vol = (math.pi * (data["diameter"]/2)**2 * ch) / 3
        usable = volume_m3 - (2*cone_vol if orientation=="horizontal" else cone_vol)
        diameter = math.sqrt(usable / (math.pi * length)) * 2
        await update.message.reply_text(f"قطر مخزن ≈ {diameter:.2f} متر")

    else:  # volume
        length = data["length"]
        diameter = data["diameter"]
        r = diameter / 2
        ch = data.get("cone_height", 0.5)
        cyl_vol = math.pi * r**2 * length
        cone_vol = (math.pi * r**2 * ch) / 3
        total = cyl_vol + (2*cone_vol if orientation=="horizontal" else cone_vol)
        await update.message.reply_text(f"حجم مخزن ≈ {total*1000:.0f} لیتر")

    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_diameter)],
            PRICING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_height)],
            PRICING_BODY_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_body_thickness)],
            PRICING_CONE_BOTTOM_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_bottom_thickness)],
            PRICING_CONE_TOP_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_top_thickness)],
            PRICING_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_height)],
            PRICING_LEG_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_count)],
            PRICING_LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_height)],
            PRICING_LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_diameter)],
            PRICING_LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_thickness)],
            PRICING_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_waste)],
            PRICING_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_wage)],

            MODE_SELECTION: [CallbackQueryHandler(mode_selection)],
            CALC_CHOICE: [CallbackQueryHandler(calc_choice)],
            CALC_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_input)],
            CALC_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_input)],
            CALC_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_second_input)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
