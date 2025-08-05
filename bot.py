from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import math

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل مکالمه
CHOOSING, CYL_THICKNESS, CYL_DIAMETER, CYL_HEIGHT, CONE_HEIGHT, CONE_THICKNESS, NUM_LEGS, LEG_HEIGHT, LEG_DIAMETER, LEG_THICKNESS, WASTE_PERCENT, LABOR_COST, VOLUME_CHOICE, VOLUME_PARAMS = range(14)

# ذخیره داده‌های کاربران
user_data = {}

DENSITY = 7850  # kg/m³
INCH_TO_M = 0.0254

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً یک گزینه انتخاب کنید:\n"
        "1. محاسبه وزن و قیمت مخزن و پایه‌ها\n"
        "2. محاسبه حجم، طول یا قطر مخزن بر اساس پارامترهای دیگر"
    )
    return CHOOSING

async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == "1":
        await update.message.reply_text("ضخامت بدنه را به میلی‌متر وارد کنید:")
        return CYL_THICKNESS
    elif choice == "2":
        await update.message.reply_text(
            "چه چیزی را می‌خواهید محاسبه کنید؟\n"
            "1. حجم (لیتر)\n"
            "2. قطر (متر)\n"
            "3. طول (متر)"
        )
        return VOLUME_CHOICE
    else:
        await update.message.reply_text("لطفاً فقط 1 یا 2 را انتخاب کنید.")
        return CHOOSING

# --- محاسبات وزن و قیمت ---
async def get_cyl_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"cyl_thickness": float(update.message.text) / 1000}
    await update.message.reply_text("قطر بدنه را به متر وارد کنید:")
    return CYL_DIAMETER

async def get_cyl_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["cyl_diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع بدنه را به متر وارد کنید:")
    return CYL_HEIGHT

async def get_cyl_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["cyl_height"] = float(update.message.text)
    await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر یعنی صاف):")
    return CONE_HEIGHT

async def get_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["cone_height"] = float(update.message.text) / 100
    await update.message.reply_text("ضخامت قیف‌ها را به میلی‌متر وارد کنید:")
    return CONE_THICKNESS

async def get_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["cone_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("تعداد پایه‌ها را وارد کنید:")
    return NUM_LEGS

async def get_num_legs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["num_legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه را به سانتی‌متر وارد کنید:")
    return LEG_HEIGHT

async def get_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["leg_height"] = float(update.message.text) / 100
    await update.message.reply_text("قطر پایه را به اینچ وارد کنید:")
    return LEG_DIAMETER

async def get_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["leg_diameter"] = float(update.message.text) * INCH_TO_M
    await update.message.reply_text("ضخامت پایه را به میلی‌متر وارد کنید:")
    return LEG_THICKNESS

async def get_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["leg_thickness"] = float(update.message.text) / 1000
    await update.message.reply_text("درصد پرتی را وارد کنید:")
    return WASTE_PERCENT

async def get_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["waste_percent"] = float(update.message.text)
    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کنید:")
    return LABOR_COST

async def get_labor_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[update.effective_user.id]
    data["labor_cost"] = float(update.message.text)

    r = data["cyl_diameter"] / 2
    h = data["cyl_height"]
    cone_h = data["cone_height"]

    # مساحت استوانه
    cyl_area = 2 * math.pi * r * h
    cyl_weight = cyl_area * data["cyl_thickness"] * DENSITY

    # مساحت قیف (شعاع کوچک صفر)
    cone_slant = math.sqrt(r**2 + cone_h**2)
    cone_area = math.pi * r * cone_slant
    cone_weight = 2 * cone_area * data["cone_thickness"] * DENSITY if cone_h > 0 else 0

    # وزن پایه‌ها
    leg_r_ext = data["leg_diameter"] / 2
    leg_r_int = leg_r_ext - data["leg_thickness"]
    leg_vol = math.pi * (leg_r_ext**2 - leg_r_int**2) * data["leg_height"]
    leg_weight = leg_vol * DENSITY * data["num_legs"]

    total_weight = cyl_weight + cone_weight + leg_weight
    total_weight_with_waste = total_weight * (1 + data["waste_percent"] / 100)
    total_price = total_weight_with_waste * data["labor_cost"]

    await update.message.reply_text(
        f"وزن مخزن: {int(cyl_weight + cone_weight)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(leg_weight)} کیلوگرم\n"
        f"وزن کل بدون پرتی: {int(total_weight)} کیلوگرم\n"
        f"وزن کل با پرتی {data['waste_percent']}٪: {int(total_weight_with_waste)} کیلوگرم\n"
        f"قیمت کل: {int(total_price)} تومان"
    )
    return ConversationHandler.END

# --- محاسبات حجم/طول/قطر ---
async def volume_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"calc_type": update.message.text.strip()}
    if update.message.text.strip() == "1":
        await update.message.reply_text("قطر را به متر وارد کنید:")
    elif update.message.text.strip() == "2":
        await update.message.reply_text("حجم را به لیتر وارد کنید:")
    elif update.message.text.strip() == "3":
        await update.message.reply_text("حجم را به لیتر وارد کنید:")
    return VOLUME_PARAMS

async def volume_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[update.effective_user.id]
    calc_type = data["calc_type"]

    if calc_type == "1":  # محاسبه حجم
        if "diameter" not in data:
            data["diameter"] = float(update.message.text)
            await update.message.reply_text("طول استوانه را به متر وارد کنید:")
            return VOLUME_PARAMS
        elif "length" not in data:
            data["length"] = float(update.message.text)
            await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر یعنی صاف):")
            return VOLUME_PARAMS
        else:
            cone_h = float(update.message.text) / 100
            r = data["diameter"] / 2
            cyl_vol = math.pi * r**2 * data["length"]
            cone_vol = (1/3) * math.pi * r**2 * cone_h * 2 if cone_h > 0 else 0
            total_vol_l = (cyl_vol + cone_vol) * 1000
            await update.message.reply_text(f"حجم مخزن: {round(total_vol_l, 2)} لیتر")
            return ConversationHandler.END

    elif calc_type == "2":  # محاسبه قطر
        if "volume" not in data:
            data["volume"] = float(update.message.text) / 1000
            await update.message.reply_text("طول استوانه را به متر وارد کنید:")
            return VOLUME_PARAMS
        elif "length" not in data:
            data["length"] = float(update.message.text)
            await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر یعنی صاف):")
            return VOLUME_PARAMS
        else:
            cone_h = float(update.message.text) / 100
            V = data["volume"]
            a = data["length"] + (2/3)*cone_h
            d = math.sqrt((4 * V) / (math.pi * a))
            await update.message.reply_text(f"قطر مخزن: {round(d, 2)} متر")
            return ConversationHandler.END

    elif calc_type == "3":  # محاسبه طول
        if "volume" not in data:
            data["volume"] = float(update.message.text) / 1000
            await update.message.reply_text("قطر را به متر وارد کنید:")
            return VOLUME_PARAMS
        elif "diameter" not in data:
            data["diameter"] = float(update.message.text)
            await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر یعنی صاف):")
            return VOLUME_PARAMS
        else:
            cone_h = float(update.message.text) / 100
            r = data["diameter"] / 2
            cyl_length = (data["volume"] - (2/3)*math.pi*r**2*cone_h) / (math.pi*r**2)
            total_length = cyl_length + 2*cone_h
            await update.message.reply_text(
                f"طول استوانه: {round(cyl_length, 2)} متر\n"
                f"طول کل (با قیف‌ها): {round(total_length, 2)} متر"
            )
            return ConversationHandler.END

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data.pop(update.effective_user.id, None)
    await update.message.reply_text("اطلاعات شما ریست شد. /start را بزنید.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_option)],
            CYL_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cyl_thickness)],
            CYL_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cyl_diameter)],
            CYL_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cyl_height)],
            CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_height)],
            CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cone_thickness)],
            NUM_LEGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num_legs)],
            LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_height)],
            LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_diameter)],
            LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leg_thickness)],
            WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_waste_percent)],
            LABOR_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_labor_cost)],
            VOLUME_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_choice)],
            VOLUME_PARAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume_params)],
        },
        fallbacks=[CommandHandler("reset", reset)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
