from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

import math

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

(
    CHOOSING,
    WEIGHT_THICKNESS,
    WEIGHT_DIAMETER,
    WEIGHT_HEIGHT,
    WEIGHT_CONE_THICKNESS,
    WEIGHT_CONE_HEIGHT_BOTTOM,
    WEIGHT_CONE_HEIGHT_TOP,
    WEIGHT_BASE_COUNT,
    WEIGHT_BASE_HEIGHT,
    WEIGHT_BASE_DIAMETER,
    WEIGHT_BASE_THICKNESS,
    WEIGHT_WASTE_PERCENT,
    WEIGHT_WAGE,
    CALC_CHOICE,
    CALC_DIAMETER_INPUT,
    CALC_LENGTH_INPUT,
    CALC_CONE_HEIGHT,
    CALC_TANK_TYPE,
    CALC_VOLUME_INPUT,
    CALC_TANK_TYPE_2,
) = range(20)

user_data_temp = {}

reply_keyboard = [
    ["محاسبه وزن و قیمت مخزن", "محاسبه طول، قطر یا حجم مخزن"],
]

calc_options = ["حجم", "قطر", "طول"]

tank_types = ["عمودی", "افقی"]


def volume_cylinder(diameter_m, height_m):
    r = diameter_m / 2
    return math.pi * r**2 * height_m  # متر مکعب


def volume_cone(height_m, diameter_m):
    r = diameter_m / 2
    return (1/3) * math.pi * r**2 * height_m  # متر مکعب


def weight_cylinder(thickness_mm, diameter_m, height_m):
    # وزن بدنه استوانه‌ای (ضخامت بر حسب متر)
    thickness_m = thickness_mm / 1000
    outer_r = diameter_m / 2
    inner_r = outer_r - thickness_m
    # حجم ورق = مساحت جانبی ورق * ضخامت
    area_side = 2 * math.pi * outer_r * height_m
    volume = area_side * thickness_m  # متر مکعب فولاد
    return volume * 7850  # کیلوگرم


def weight_cone(thickness_mm, diameter_m, height_m):
    thickness_m = thickness_mm / 1000
    r = diameter_m / 2
    # مساحت سطح مخروطی تقریبی ورق = محیط پایه * طول شیب
    slant_height = math.sqrt(r**2 + height_m**2)
    perimeter = 2 * math.pi * r
    area_sheet = perimeter * slant_height
    volume = area_sheet * thickness_m
    return volume * 7850  # کیلوگرم


def weight_pipe(count, height_cm, diameter_inch, thickness_mm):
    # فرمول وزن لوله: محیط * ضخامت * ارتفاع * چگالی
    # تبدیل به متر و میلی متر
    height_m = height_cm / 100
    thickness_m = thickness_mm / 1000
    diameter_m = diameter_inch * 0.0254
    outer_circumference = math.pi * diameter_m
    volume = outer_circumference * thickness_m * height_m * count
    return volume * 7850  # کیلوگرم


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp[update.effective_user.id] = {}
    await update.message.reply_text(
        "سلام! چه کاری می‌خواهید انجام دهید؟\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING


async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    user_data_temp[update.effective_user.id] = {"choice": choice}

    if choice == "محاسبه وزن و قیمت مخزن":
        await update.message.reply_text(
            "لطفاً ضخامت بدنه مخزن را به میلی‌متر وارد کنید:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return WEIGHT_THICKNESS

    elif choice == "محاسبه طول، قطر یا حجم مخزن":
        await update.message.reply_text(
            "چه موردی را می‌خواهید محاسبه کنید؟\n"
            "عدد مورد نظر را ارسال کنید:\n"
            "1. حجم\n"
            "2. قطر\n"
            "3. طول",
            reply_markup=ReplyKeyboardRemove(),
        )
        return CALC_CHOICE

    else:
        await update.message.reply_text(
            "گزینه نامعتبر است، لطفاً دوباره /start بزنید."
        )
        return ConversationHandler.END


# بخش محاسبه وزن و قیمت مخزن
async def weight_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["thickness"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای ضخامت وارد کنید:")
        return WEIGHT_THICKNESS

    await update.message.reply_text("قطر مخزن را به متر وارد کنید (مثلاً 1.5):")
    return WEIGHT_DIAMETER


async def weight_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["diameter"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای قطر وارد کنید:")
        return WEIGHT_DIAMETER

    await update.message.reply_text("ارتفاع استوانه (بدنه اصلی) را به متر وارد کنید:")
    return WEIGHT_HEIGHT


async def weight_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["height"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای ارتفاع وارد کنید:")
        return WEIGHT_HEIGHT

    await update.message.reply_text("ضخامت قیف‌ها را به میلی‌متر وارد کنید:")
    return WEIGHT_CONE_THICKNESS


async def weight_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["cone_thickness"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای ضخامت قیف وارد کنید (0 اگر قیف ندارید):")
        return WEIGHT_CONE_THICKNESS

    await update.message.reply_text("ارتفاع قیف کف مخزن را به سانتی‌متر وارد کنید (0 اگر قیف ندارید):")
    return WEIGHT_CONE_HEIGHT_BOTTOM


async def weight_cone_height_bottom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["cone_height_bottom"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای ارتفاع قیف کف وارد کنید:")
        return WEIGHT_CONE_HEIGHT_BOTTOM

    await update.message.reply_text("ارتفاع قیف سقف مخزن را به سانتی‌متر وارد کنید (0 اگر قیف ندارید):")
    return WEIGHT_CONE_HEIGHT_TOP


async def weight_cone_height_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["cone_height_top"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای ارتفاع قیف سقف وارد کنید:")
        return WEIGHT_CONE_HEIGHT_TOP

    await update.message.reply_text("تعداد پایه‌ها را وارد کنید (مثلاً 4):")
    return WEIGHT_BASE_COUNT


async def weight_base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = int(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["base_count"] = val
    except:
        await update.message.reply_text("لطفاً عدد صحیح غیرمنفی برای تعداد پایه‌ها وارد کنید:")
        return WEIGHT_BASE_COUNT

    if val == 0:
        # بدون پایه به مرحله بعد پرتی میریم
        await update.message.reply_text("درصد پرتی کار را وارد کنید (مثلاً 5):")
        return WEIGHT_WASTE_PERCENT
    else:
        await update.message.reply_text("ارتفاع هر پایه را به سانتی‌متر وارد کنید:")
        return WEIGHT_BASE_HEIGHT


async def weight_base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["base_height"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای ارتفاع پایه وارد کنید:")
        return WEIGHT_BASE_HEIGHT

    await update.message.reply_text("قطر هر پایه را به اینچ وارد کنید:")
    return WEIGHT_BASE_DIAMETER


async def weight_base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["base_diameter"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای قطر پایه وارد کنید:")
        return WEIGHT_BASE_DIAMETER

    await update.message.reply_text("ضخامت پایه‌ها را به میلی‌متر وارد کنید:")
    return WEIGHT_BASE_THICKNESS


async def weight_base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["base_thickness"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای ضخامت پایه وارد کنید:")
        return WEIGHT_BASE_THICKNESS

    await update.message.reply_text("درصد پرتی کار را وارد کنید (مثلاً 5):")
    return WEIGHT_WASTE_PERCENT


async def weight_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["waste_percent"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای درصد پرتی وارد کنید:")
        return WEIGHT_WASTE_PERCENT

    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم را به تومان وارد کنید:")
    return WEIGHT_WAGE


async def weight_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["wage"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای دستمزد وارد کنید:")
        return WEIGHT_WAGE

    data = user_data_temp[update.effective_user.id]

    # محاسبه وزن استوانه اصلی
    weight_body = weight_cylinder(data["thickness"], data["diameter"], data["height"])

    # محاسبه وزن قیف کف اگر وجود داشته باشد
    weight_cone_bottom = 0
    if data["cone_thickness"] > 0 and data["cone_height_bottom"] > 0:
        cone_height_m = data["cone_height_bottom"] / 100
        weight_cone_bottom = weight_cone(data["cone_thickness"], data["diameter"], cone_height_m)

    # محاسبه وزن قیف سقف اگر وجود داشته باشد
    weight_cone_top = 0
    if data["cone_thickness"] > 0 and data["cone_height_top"] > 0:
        cone_height_m = data["cone_height_top"] / 100
        weight_cone_top = weight_cone(data["cone_thickness"], data["diameter"], cone_height_m)

    # مجموع وزن قیف‌ها
    total_cone_weight = weight_cone_bottom + weight_cone_top

    # وزن پایه‌ها
    base_weight = 0
    if data.get("base_count", 0) > 0:
        base_weight = weight_pipe(
            data["base_count"],
            data.get("base_height", 0),
            data.get("base_diameter", 0),
            data.get("base_thickness", 0),
        )

    total_weight = weight_body + total_cone_weight + base_weight
    total_weight_with_waste = total_weight * (1 + data["waste_percent"] / 100)
    price = total_weight_with_waste * data["wage"]

    text = (
        f"وزن بدنه مخزن: {weight_body:.0f} کیلوگرم\n"
        f"وزن قیف‌ها: {total_cone_weight:.0f} کیلوگرم\n"
        f"وزن پایه‌ها: {base_weight:.0f} کیلوگرم\n"
        f"وزن کل بدون پرتی: {total_weight:.0f} کیلوگرم\n"
        f"وزن کل با پرتی ({data['waste_percent']}%): {total_weight_with_waste:.0f} کیلوگرم\n"
        f"قیمت کل (تومان): {price:.0f}"
    )

    await update.message.reply_text(text)
    await update.message.reply_text("برای شروع مجدد /start بزنید.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# بخش دوم: محاسبه طول، قطر یا حجم مخزن با قیف و مخزن افقی یا عمودی

async def calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data_temp[update.effective_user.id]["calc_choice"] = text

    if text == "1" or text == "حجم":
        await update.message.reply_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER_INPUT
    elif text == "2" or text == "قطر":
        await update.message.reply_text("طول مخزن (متر) را وارد کنید:")
        return CALC_LENGTH_INPUT
    elif text == "3" or text == "طول":
        await update.message.reply_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER_INPUT
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های 1، 2 یا 3 را ارسال کنید:")
        return CALC_CHOICE


async def calc_diameter_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["calc_diameter"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای قطر وارد کنید:")
        return CALC_DIAMETER_INPUT

    choice = user_data_temp[update.effective_user.id]["calc_choice"]
    if choice == "1" or choice == "حجم":
        await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر اگر قیف ندارید):")
        return CALC_CONE_HEIGHT
    elif choice == "3" or choice == "طول":
        await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر اگر قیف ندارید):")
        return CALC_CONE_HEIGHT
    else:
        # قطر که نمیخوایم طول رو وارد کنیم در این حالت بعد از قطر میپرسیم حجم
        await update.message.reply_text("حجم مخزن را به لیتر وارد کنید:")
        return CALC_VOLUME_INPUT


async def calc_length_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val <= 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["calc_length"] = val
    except:
        await update.message.reply_text("لطفاً عدد مثبت برای طول وارد کنید:")
        return CALC_LENGTH_INPUT

    await update.message.reply_text("ارتفاع قیف‌ها را به سانتی‌متر وارد کنید (صفر اگر قیف ندارید):")
    return CALC_CONE_HEIGHT


async def calc_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = float(text)
        if val < 0:
            raise ValueError
        user_data_temp[update.effective_user.id]["calc_cone_height_cm"] = val
    except:
        await update.message.reply_text("لطفاً عدد غیرمنفی برای ارتفاع قیف‌ها وارد کنید:")
        return CALC_CONE_HEIGHT

    await update.message.reply_text(
        "نوع مخزن را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([tank_types], one_time_keyboard=True, resize_keyboard=True),
    )
    return CALC_TANK_TYPE


async def calc_tank_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in tank_types:
        await update.message.reply_text("لطفاً یکی از گزینه‌های 'عمودی' یا 'افقی' را انتخاب کنید:")
        return CALC_TANK_TYPE

    user_data_temp[update.effective_user.id]["calc_tank_type"] = text

    # حالا محاسبه بر اساس نوع و داده‌ها
    d = user_data_temp[update.effective_user.id].get("calc_diameter", 0)
    l = user_data_temp[update.effective_user.id].get("calc_length", 0)
    h_cone_cm = user_data_temp[update.effective_user.id].get("calc_cone_height_cm", 0)

    if text == "عمودی":
        # حجم = حجم استوانه + حجم قیف بالا + حجم قیف پایین
        # حجم استوانه = π * (d/2)^2 * l
        # قیف ها مخروطی با ارتفاع h_cone_cm سانتی متر و شعاع قاعده d/2 متر (یعنی باید تبدیل کنیم)
        h_cone_m = h_cone_cm / 100
        cylinder_volume = 3.14159 * (d / 2) ** 2 * l  # متر مکعب
        cone_volume = 3.14159 * (d / 2) ** 2 * h_cone_m / 3
        total_volume = cylinder_volume + 2 * cone_volume  # متر مکعب
        total_volume_liters = total_volume * 1000  # لیتر

        await update.message.reply_text(
            f"حجم کل مخزن (استوانه + دو قیف): {total_volume_liters:.2f} لیتر"
        )
    elif text == "افقی":
        # محاسبه حجم استوانه افقی با قطر d و طول l
        # حجم استوانه = سطح مقطع * طول
        # سطح مقطع دایره = π * r^2
        r = d / 2
        cylinder_area = 3.14159 * r ** 2
        cylinder_volume = cylinder_area * l  # متر مکعب

        # قیف ها مخروطی با ارتفاع h_cone_cm سانتی متر و شعاع قاعده r متر
        h_cone_m = h_cone_cm / 100
        cone_volume = 3.14159 * r ** 2 * h_cone_m / 3

        total_volume = cylinder_volume + 2 * cone_volume
        total_volume_liters = total_volume * 1000

        await update.message.reply_text(
            f"حجم کل مخزن افقی (استوانه + دو قیف): {total_volume_liters:.2f} لیتر"
        )
    else:
        await update.message.reply_text("نوع مخزن نامعتبر است.")
        return CALC_TANK_TYPE

    await update.message.reply_text("برای شروع مجدد /start بزنید.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    application = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("reset", reset)],
        states={
            THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, thickness)],
            DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, diameter)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            CONE_HEIGHT_BOTTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, cone_height_bottom)],
            CONE_HEIGHT_TOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, cone_height_top)],
            BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_count)],
            WEIGHT_BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_count)],
            WEIGHT_BASE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_height)],
            WEIGHT_BASE_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_diameter)],
            WEIGHT_BASE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_thickness)],
            WEIGHT_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_waste_percent)],
            WEIGHT_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_wage)],
            CALC_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_choice)],
            CALC_DIAMETER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_diameter_input)],
            CALC_LENGTH_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_length_input)],
            CALC_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_cone_height)],
            CALC_TANK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_type)],
        },
        fallbacks=[CommandHandler("reset", reset)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()


در این کد کامل ربات تلگرامی برای محاسبه وزن و قیمت مخزن و پایه‌ها بر اساس ورودی کاربر هست که شامل مراحل پرسش ضخامت، قطر، ارتفاع مخزن، ارتفاع قیف‌ها، تعداد و ابعاد پایه‌ها، درصد پرتی و دستمزد به ازای هر کیلوگرم می‌باشد. در انتها وزن‌های محاسبه شده و قیمت نهایی به کاربر نمایش داده می‌شود.

اگر بخواهید من این کد را برایتان در یک فایل پایتون کامل و آماده اجرا بسازم، بگوید یا اگر بخواهید فقط بخشی از آن یا توضیح عملکرد بخش خاصی را بدهم، خوشحال می‌شوم کمک کنم.

همچنین اگر بخواهید راهنمایی برای دیپلوی روی Render یا اضافه کردن امکانات دیگر بدهم، بفرمایید.
