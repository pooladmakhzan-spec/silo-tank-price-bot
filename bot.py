from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import math

# --- مراحل مکالمه ---
(
    CHOOSING,
    # حالت وزن و قیمت
    WEIGHT_THICKNESS, WEIGHT_DIAMETER, WEIGHT_HEIGHT, WEIGHT_CONE_THICKNESS, WEIGHT_CONE_HEIGHT,
    WEIGHT_NUM_LEGS, WEIGHT_LEG_HEIGHT, WEIGHT_LEG_DIAMETER, WEIGHT_LEG_THICKNESS,
    WEIGHT_WASTE, WEIGHT_COST,
    # حالت حجم/قطر/طول
    CALC_OPTION, VOLUME_DIAMETER, VOLUME_HEIGHT, VOLUME_CONE_HEIGHT, VOLUME_ORIENTATION,
    TARGET_VOLUME, TARGET_DIAMETER, TARGET_LENGTH
) = range(20)

# --- شروع ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["1. محاسبه وزن و قیمت مخزن", "2. محاسبه حجم/طول/قطر مخزن"]]
    await update.message.reply_text(
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING

# --- انتخاب حالت ---
async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice.startswith("1"):
        await update.message.reply_text("ضخامت بدنه (میلی‌متر):")
        return WEIGHT_THICKNESS
    elif choice.startswith("2"):
        reply_keyboard = [["1. حجم", "2. قطر", "3. طول"]]
        await update.message.reply_text(
            "چه چیزی را می‌خواهید محاسبه کنید؟",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CALC_OPTION
    else:
        await update.message.reply_text("لطفاً یک گزینه معتبر انتخاب کنید.")
        return CHOOSING

# --- حالت محاسبه وزن و قیمت ---
async def weight_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["thickness"] = float(update.message.text)
    await update.message.reply_text("قطر مخزن (متر):")
    return WEIGHT_DIAMETER

async def weight_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع مخزن (متر):")
    return WEIGHT_HEIGHT

async def weight_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = float(update.message.text)
    await update.message.reply_text("ضخامت قیف‌ها (میلی‌متر):")
    return WEIGHT_CONE_THICKNESS

async def weight_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_thickness"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتی‌متر):")
    return WEIGHT_CONE_HEIGHT

async def weight_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_height"] = float(update.message.text)
    await update.message.reply_text("تعداد پایه‌ها:")
    return WEIGHT_NUM_LEGS

async def weight_num_legs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["num_legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر):")
    return WEIGHT_LEG_HEIGHT

async def weight_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_height"] = float(update.message.text)
    await update.message.reply_text("قطر پایه (اینچ):")
    return WEIGHT_LEG_DIAMETER

async def weight_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_diameter"] = float(update.message.text)
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return WEIGHT_LEG_THICKNESS

async def weight_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["leg_thickness"] = float(update.message.text)
    await update.message.reply_text("درصد پرتی:")
    return WEIGHT_WASTE

async def weight_waste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waste_percent"] = float(update.message.text)
    await update.message.reply_text("دستمزد ساخت (تومان بر کیلوگرم):")
    return WEIGHT_COST

async def weight_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = context.user_data
    t["cost_per_kg"] = float(update.message.text)

    # محاسبات وزن
    steel_density = 7850
    r = t["diameter"] / 2
    h = t["height"]
    t_body = t["thickness"] / 1000
    t_cone = t["cone_thickness"] / 1000
    h_cone = t["cone_height"] / 100

    # وزن استوانه
    area_cylinder = 2 * math.pi * r * h
    weight_cylinder = area_cylinder * t_body * steel_density

    # وزن قیف‌ها
    slant_height = math.sqrt(r**2 + h_cone**2)
    area_cone = math.pi * r * slant_height
    weight_cones = 2 * area_cone * t_cone * steel_density if h_cone > 0 else 0

    # وزن پایه‌ها
    leg_r_outer = (t["leg_diameter"] * 0.0254) / 2
    leg_thickness = t["leg_thickness"] / 1000
    leg_r_inner = leg_r_outer - leg_thickness
    leg_height = t["leg_height"] / 100
    volume_leg = math.pi * (leg_r_outer**2 - leg_r_inner**2) * leg_height
    weight_legs = t["num_legs"] * volume_leg * steel_density

    total_weight = weight_cylinder + weight_cones + weight_legs
    total_weight_with_waste = total_weight * (1 + t["waste_percent"] / 100)
    price = total_weight_with_waste * t["cost_per_kg"]

    await update.message.reply_text(
        f"وزن مخزن بدون پرتی: {round(weight_cylinder + weight_cones)} کیلوگرم\n"
        f"وزن پایه‌ها: {round(weight_legs)} کیلوگرم\n"
        f"وزن کل بدون پرتی: {round(total_weight)} کیلوگرم\n"
        f"وزن کل با پرتی ({t['waste_percent']}٪): {round(total_weight_with_waste)} کیلوگرم\n"
        f"قیمت کل: {round(price)} تومان"
    )
    return ConversationHandler.END

# --- حالت محاسبه حجم/قطر/طول ---
async def calc_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["calc_choice"] = choice
    if choice.startswith("1"):
        await update.message.reply_text("قطر مخزن (متر):")
        return VOLUME_DIAMETER
    elif choice.startswith("2"):
        await update.message.reply_text("حجم مخزن (لیتر):")
        return TARGET_VOLUME
    elif choice.startswith("3"):
        await update.message.reply_text("حجم مخزن (لیتر):")
        return TARGET_VOLUME
    else:
        await update.message.reply_text("گزینه نامعتبر است. دوباره انتخاب کنید.")
        return CALC_OPTION

async def volume_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع استوانه (متر):")
    return VOLUME_HEIGHT

async def volume_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتی‌متر):")
    return VOLUME_CONE_HEIGHT

async def volume_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cone_height"] = float(update.message.text)
    await update.message.reply_text("مخزن عمودی است یا افقی؟ (عمودی/افقی):")
    return VOLUME_ORIENTATION

async def volume_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orientation = update.message.text
    t = context.user_data

    # بررسی اینکه مقادیر لازم وجود دارند
    if "diameter" not in t or "height" not in t or "cone_height" not in t:
        await update.message.reply_text("اطلاعات کافی وارد نشده است. دوباره از ابتدا وارد کنید /start")
        return ConversationHandler.END

    r = t["diameter"] / 2
    h = t["height"]
    h_cone = t["cone_height"] / 100

    if orientation == "عمودی":
        vol_cylinder = math.pi * r**2 * h
        vol_cone = (1/3) * math.pi * r**2 * h_cone
        total_vol = vol_cylinder + vol_cone
    elif orientation == "افقی":
        vol_cylinder = math.pi * r**2 * h
        vol_cone = 2 * ((1/3) * math.pi * r**2 * h_cone)
        total_vol = vol_cylinder + vol_cone
    else:
        await update.message.reply_text("لطفاً فقط 'عمودی' یا 'افقی' وارد کنید.")
        return VOLUME_ORIENTATION

    await update.message.reply_text(f"حجم کل: {round(total_vol * 1000, 2)} لیتر")
    return ConversationHandler.END

async def target_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["volume"] = float(update.message.text) / 1000
    choice = context.user_data["calc_choice"]
    if choice.startswith("2"):
        await update.message.reply_text("طول استوانه (متر):")
        return TARGET_LENGTH
    elif choice.startswith("3"):
        await update.message.reply_text("قطر مخزن (متر):")
        return TARGET_DIAMETER

async def target_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["length"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتی‌متر):")
    return VOLUME_CONE_HEIGHT

async def target_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع هر قیف (سانتی‌متر):")
    return VOLUME_CONE_HEIGHT

# --- ریست ---
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("بازنشانی شد. برای شروع دوباره /start را بزنید.")
    return ConversationHandler.END

# --- اجرای برنامه ---
def main():
    app = Application.builder().token("8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY").build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing)],
            WEIGHT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_thickness)],
            WEIGHT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_diameter)],
            WEIGHT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_height)],
            WEIGHT_CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cone_thickness)],
            WEIGHT_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cone_height)],
            WEIGHT_NUM_LEGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_num_legs)],
            WEIGHT_LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_leg_height)],
            WEIGHT_LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_leg_diameter)],
            WEIGHT_LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_leg_thickness)],
            WEIGHT_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_waste)],
            WEIGHT_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cost)],
            CALC_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_option)],
            VOLUME_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_diameter)],
            VOLUME_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_height)],
            VOLUME_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_cone_height)],
            VOLUME_ORIENTATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_orientation)],
            TARGET_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_volume)],
            TARGET_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_length)],
            TARGET_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_diameter)],
        },
        fallbacks=[CommandHandler("reset", reset)],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
