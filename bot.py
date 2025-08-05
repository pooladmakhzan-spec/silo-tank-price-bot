from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# --- حالت‌های محاسبه ---
CHOOSING_MODE, CALC_TANK_THICKNESS, CALC_TANK_DIAMETER, CALC_TANK_HEIGHT, CALC_TANK_CONE_HEIGHT, CALC_TANK_CONE_THICKNESS, CALC_TANK_NUM_LEGS, CALC_TANK_LEG_HEIGHT, CALC_TANK_LEG_DIAMETER, CALC_TANK_LEG_THICKNESS, CALC_TANK_WAGE, CALC_TANK_WASTE, CALC_VOLUME_OPTION, CALC_VOLUME_ORIENTATION, CALC_VOLUME_DIAMETER, CALC_VOLUME_LENGTH, CALC_VOLUME_CONE_HEIGHT = range(16)

user_data_store = {}

# --- شروع ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {}
    await update.message.reply_text(
        "چه کاری می‌خواهید انجام دهید؟\n"
        "1. محاسبه قیمت مخزن و پایه‌ها\n"
        "2. محاسبه حجم، قطر یا طول مخزن"
    )
    return CHOOSING_MODE

# --- انتخاب حالت ---
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = user_data_store[update.effective_user.id]

    if text == "1":
        await update.message.reply_text("ضخامت بدنه مخزن (میلی‌متر):")
        return CALC_TANK_THICKNESS
    elif text == "2":
        await update.message.reply_text("چه چیزی را می‌خواهید محاسبه کنید؟\n1. حجم\n2. قطر\n3. طول")
        return CALC_VOLUME_OPTION
    else:
        await update.message.reply_text("لطفاً 1 یا 2 انتخاب کنید.")
        return CHOOSING_MODE

# --- محاسبه قیمت مخزن و پایه‌ها ---
async def calc_tank_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("قطر مخزن (متر):")
    return CALC_TANK_DIAMETER

async def calc_tank_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع استوانه (متر):")
    return CALC_TANK_HEIGHT

async def calc_tank_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["height"] = float(update.message.text)
    await update.message.reply_text("ارتفاع قیف‌ها (سانتی‌متر):")
    return CALC_TANK_CONE_HEIGHT

async def calc_tank_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["cone_height"] = float(update.message.text) / 100
    await update.message.reply_text("ضخامت قیف‌ها (میلی‌متر):")
    return CALC_TANK_CONE_THICKNESS

async def calc_tank_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["cone_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("تعداد پایه‌ها:")
    return CALC_TANK_NUM_LEGS

async def calc_tank_num_legs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["num_legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر):")
    return CALC_TANK_LEG_HEIGHT

async def calc_tank_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["leg_height"] = float(update.message.text) / 100
    await update.message.reply_text("قطر پایه (اینچ):")
    return CALC_TANK_LEG_DIAMETER

async def calc_tank_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["leg_diameter"] = float(update.message.text) * 0.0254
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return CALC_TANK_LEG_THICKNESS

async def calc_tank_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["leg_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("دستمزد ساخت (تومان به ازای هر کیلوگرم):")
    return CALC_TANK_WAGE

async def calc_tank_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["wage"] = float(update.message.text)
    await update.message.reply_text("درصد پرتی (%):")
    return CALC_TANK_WASTE

async def calc_tank_waste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data_store[update.effective_user.id]
    data["waste_percent"] = float(update.message.text)

    d = data["diameter"]
    h = data["height"]
    t = data["thickness"]
    hc = data["cone_height"]
    tc = data["cone_thickness"]

    # وزن استوانه
    area_cylinder = 3.1416 * d * h
    weight_cylinder = area_cylinder * t * 7850

    # وزن دو قیف (بر اساس مساحت جانبی مخروط)
    if hc > 0:
        slant_height = ((d / 2) ** 2 + hc ** 2) ** 0.5
        cone_area = 3.1416 * (d / 2) * slant_height
        weight_cones = 2 * cone_area * tc * 7850
    else:
        weight_cones = 0

    # وزن پایه‌ها
    num_legs = data["num_legs"]
    leg_height = data["leg_height"]
    leg_diameter = data["leg_diameter"]
    leg_thickness = data["leg_thickness"]

    outer_radius = leg_diameter / 2
    inner_radius = outer_radius - leg_thickness
    leg_area = 3.1416 * (outer_radius**2 - inner_radius**2)
    leg_weight = leg_area * leg_height * 7850
    weight_legs = num_legs * leg_weight

    # وزن کل
    total_weight = weight_cylinder + weight_cones + weight_legs
    total_weight_with_waste = total_weight * (1 + data["waste_percent"] / 100)
    price = total_weight_with_waste * data["wage"]

    await update.message.reply_text(
        f"وزن مخزن بدون پرتی: {round(weight_cylinder + weight_cones)} کیلوگرم\n"
        f"وزن پایه‌ها: {round(weight_legs)} کیلوگرم\n"
        f"وزن کل بدون پرتی: {round(total_weight)} کیلوگرم\n"
        f"وزن کل با پرتی {data['waste_percent']}٪: {round(total_weight_with_waste)} کیلوگرم\n"
        f"قیمت کل: {round(price)} تومان"
    )
    return ConversationHandler.END

# --- محاسبه حجم، قطر یا طول ---
async def calc_volume_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["volume_choice"] = update.message.text
    await update.message.reply_text("مخزن عمودی است یا افقی؟\n1. عمودی\n2. افقی")
    return CALC_VOLUME_ORIENTATION

async def calc_volume_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["orientation"] = update.message.text
    await update.message.reply_text("قطر مخزن (متر):")
    return CALC_VOLUME_DIAMETER

async def calc_volume_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["diameter"] = float(update.message.text)
    await update.message.reply_text("طول استوانه (متر):")
    return CALC_VOLUME_LENGTH

async def calc_volume_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["length"] = float(update.message.text)
    await update.message.reply_text("ارتفاع قیف‌ها (سانتی‌متر):")
    return CALC_VOLUME_CONE_HEIGHT

async def calc_volume_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data_store[update.effective_user.id]
    data["cone_height"] = float(update.message.text) / 100

    r = data["diameter"] / 2
    h = data["length"]
    hc = data["cone_height"]
    orientation = data["orientation"]

    # محاسبه حجم
    if orientation == "1":  # عمودی
        volume_cylinder = 3.1416 * (r**2) * h
        volume_cones = (1/3) * 3.1416 * (r**2) * hc
    else:  # افقی
        volume_cylinder = 3.1416 * (r**2) * h
        volume_cones = 2 * ((1/3) * 3.1416 * (r**2) * hc)

    total_volume = (volume_cylinder + volume_cones) * 1000  # به لیتر

    await update.message.reply_text(f"حجم مخزن: {round(total_volume, 2)} لیتر")
    return ConversationHandler.END

# --- راه‌اندازی ---
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],

            CALC_TANK_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_thickness)],
            CALC_TANK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_diameter)],
            CALC_TANK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_height)],
            CALC_TANK_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_cone_height)],
            CALC_TANK_CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_cone_thickness)],
            CALC_TANK_NUM_LEGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_num_legs)],
            CALC_TANK_LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_leg_height)],
            CALC_TANK_LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_leg_diameter)],
            CALC_TANK_LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_leg_thickness)],
            CALC_TANK_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_wage)],
            CALC_TANK_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_waste)],

            CALC_VOLUME_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_option)],
            CALC_VOLUME_ORIENTATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_orientation)],
            CALC_VOLUME_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_diameter)],
            CALC_VOLUME_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_length)],
            CALC_VOLUME_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_cone_height)],
        },
        fallbacks=[CommandHandler("reset", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
