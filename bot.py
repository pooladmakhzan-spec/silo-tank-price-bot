import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import math

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل گفتگو
(
    CHOOSE_PRODUCT,
    MIKONAM_MOKHTALAF,  # placeholder if needed
    # مخزن و سیلو
    # ... (برای حفظ کوتاهی فقط اسکرو رو کامل می نویسم)
    SCREW_LENGTH,
    SCREW_OUTER_DIAMETER,
    SCREW_OUTER_THICKNESS,
    SCREW_SHAFT_DIAMETER,
    SCREW_SHAFT_THICKNESS,
    SCREW_PITCH,
    SCREW_BLADE_THICKNESS,
    MOTOR_GEARBOX_PRICE,
    TURNER_PRICE,
    TRANS_SHAFT_DIAMETER,
    TRANS_SHAFT_LENGTH,
    TRANS_SHAFT_PRICE_PER_KG,
    WAGE_PER_KG,
    FINAL_RESULT,
    RESTART,
) = range(17)

# چگالی فولاد کیلوگرم بر متر مکعب
STEEL_DENSITY = 7850

def format_number(num):
    return f"{int(math.ceil(num)):,}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("مخزن"), KeyboardButton("سیلو")],
        [KeyboardButton("اسکرو کانوایر")]
    ]
    await update.message.reply_text(
        "سلام! 👋\nلطفا محصول مورد نظر برای محاسبه را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSE_PRODUCT

# برای حفظ کد مخزن و سیلو همانطور که بود، اینجا فقط بخش اسکرو را می‌نویسم

async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "اسکرو کانوایر":
        await update.message.reply_text(
            "🚜 طول اسکرو کانوایر را به سانتی‌متر وارد کنید:",
            reply_markup=None,
        )
        return SCREW_LENGTH
    elif text == "مخزن" or text == "سیلو":
        # اینجا کد قبلی بخش مخزن و سیلو قرار می‌گیرد که شما قبلا نوشته بودید
        # برای کوتاهی الان فقط پیام می‌دهم
        await update.message.reply_text("⚠️ بخش مخزن و سیلو (فعلا به صورت پیش‌فرض فقط پیام تست)")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفا یکی از گزینه‌ها را انتخاب کنید.")
        return CHOOSE_PRODUCT

async def screw_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        length = float(update.message.text)
        if length <= 0:
            raise ValueError
        context.user_data['screw_length_cm'] = length
        await update.message.reply_text("📏 قطر خارجی لوله بدنه اسکرو را به اینچ وارد کنید:")
        return SCREW_OUTER_DIAMETER
    except:
        await update.message.reply_text("عدد معتبر به سانتی‌متر وارد کنید لطفا.")
        return SCREW_LENGTH

async def screw_outer_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diameter = float(update.message.text)
        if diameter <= 0:
            raise ValueError
        context.user_data['screw_outer_diameter_inch'] = diameter
        await update.message.reply_text("🛠️ ضخامت لوله بدنه اسکرو را به میلی‌متر وارد کنید:")
        return SCREW_OUTER_THICKNESS
    except:
        await update.message.reply_text("عدد معتبر به اینچ وارد کنید لطفا.")
        return SCREW_OUTER_DIAMETER

async def screw_outer_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        thickness = float(update.message.text)
        if thickness <= 0:
            raise ValueError
        context.user_data['screw_outer_thickness_mm'] = thickness
        await update.message.reply_text("📏 قطر لوله شفت وسط اسکرو را به اینچ وارد کنید:")
        return SCREW_SHAFT_DIAMETER
    except:
        await update.message.reply_text("عدد معتبر به میلی‌متر وارد کنید لطفا.")
        return SCREW_OUTER_THICKNESS

async def screw_shaft_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diameter = float(update.message.text)
        if diameter <= 0:
            raise ValueError
        context.user_data['screw_shaft_diameter_inch'] = diameter
        await update.message.reply_text("🛠️ ضخامت لوله شفت وسط اسکرو را به میلی‌متر وارد کنید:")
        return SCREW_SHAFT_THICKNESS
    except:
        await update.message.reply_text("عدد معتبر به اینچ وارد کنید لطفا.")
        return SCREW_SHAFT_DIAMETER

async def screw_shaft_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        thickness = float(update.message.text)
        if thickness <= 0:
            raise ValueError
        context.user_data['screw_shaft_thickness_mm'] = thickness
        await update.message.reply_text("🔄 گام (پیتچ) ماردون اسکرو را به میلی‌متر وارد کنید:")
        return SCREW_PITCH
    except:
        await update.message.reply_text("عدد معتبر به میلی‌متر وارد کنید لطفا.")
        return SCREW_SHAFT_THICKNESS

async def screw_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pitch = float(update.message.text)
        if pitch <= 0:
            raise ValueError
        context.user_data['screw_pitch_mm'] = pitch
        await update.message.reply_text("🪛 ضخامت تیغه ماردون را به میلی‌متر وارد کنید:")
        return SCREW_BLADE_THICKNESS
    except:
        await update.message.reply_text("عدد معتبر به میلی‌متر وارد کنید لطفا.")
        return SCREW_PITCH

async def screw_blade_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        blade_thickness = float(update.message.text)
        if blade_thickness <= 0:
            raise ValueError
        context.user_data['screw_blade_thickness_mm'] = blade_thickness
        await update.message.reply_text("💰 قیمت موتور و گیربکس را به تومان وارد کنید:")
        return MOTOR_GEARBOX_PRICE
    except:
        await update.message.reply_text("عدد معتبر به میلی‌متر وارد کنید لطفا.")
        return SCREW_BLADE_THICKNESS

async def motor_gearbox_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(",", ""))
        if price < 0:
            raise ValueError
        context.user_data['motor_gearbox_price'] = price
        await update.message.reply_text("🔧 اجرت تراشکار را به تومان وارد کنید:")
        return TURNER_PRICE
    except:
        await update.message.reply_text("عدد معتبر به تومان وارد کنید لطفا.")
        return MOTOR_GEARBOX_PRICE

async def turner_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(",", ""))
        if price < 0:
            raise ValueError
        context.user_data['turner_price'] = price

        # محاسبه قطر پیشنهادی شفت انتقال قدرت:
        # قطر داخلی لوله شفت = قطر اسمی - 2* ضخامت (همه به اینچ ولی ما قطر شفت میخوایم سانتی متر)
        # پس قطر داخلی لوله شفت به اینچ:
        shaft_diameter_inch = context.user_data['screw_shaft_diameter_inch']
        shaft_thickness_mm = context.user_data['screw_shaft_thickness_mm']
        # تبدیل ضخامت میلیمتر به اینچ: 1 اینچ = 25.4 میلیمتر
        shaft_thickness_inch = shaft_thickness_mm / 25.4
        shaft_inner_diameter_inch = shaft_diameter_inch - 2 * shaft_thickness_inch
        # تبدیل به سانتی متر:
        shaft_inner_diameter_cm = shaft_inner_diameter_inch * 2.54

        await update.message.reply_text(
            f"📐 قطر شفت انتقال قدرت را به سانتی‌متر وارد کنید:\n(قطر پیشنهادی: {shaft_inner_diameter_cm:.2f} سانتی‌متر)",
        )
        context.user_data['shaft_inner_diameter_cm'] = shaft_inner_diameter_cm
        return TRANS_SHAFT_DIAMETER
    except:
        await update.message.reply_text("عدد معتبر به تومان وارد کنید لطفا.")
        return TURNER_PRICE

async def trans_shaft_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diameter_cm = float(update.message.text)
        if diameter_cm <= 0:
            raise ValueError
        context.user_data['trans_shaft_diameter_cm'] = diameter_cm
        await update.message.reply_text("📏 طول شفت انتقال قدرت را به سانتی‌متر وارد کنید:")
        return TRANS_SHAFT_LENGTH
    except:
        await update.message.reply_text("عدد معتبر به سانتی‌متر وارد کنید لطفا.")
        return TRANS_SHAFT_DIAMETER

async def trans_shaft_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        length_cm = float(update.message.text)
        if length_cm <= 0:
            raise ValueError
        context.user_data['trans_shaft_length_cm'] = length_cm
        await update.message.reply_text("💰 قیمت هر کیلوگرم شفت انتقال قدرت را به تومان وارد کنید:")
        return TRANS_SHAFT_PRICE_PER_KG
    except:
        await update.message.reply_text("عدد معتبر به تومان وارد کنید لطفا.")
        return TRANS_SHAFT_LENGTH

async def trans_shaft_price_per_kg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(",", ""))
        if price < 0:
            raise ValueError
        context.user_data['trans_shaft_price_per_kg'] = price
        await update.message.reply_text("💸 دستمزد ساخت هر کیلوگرم را به تومان وارد کنید:")
        return WAGE_PER_KG
    except:
        await update.message.reply_text("عدد معتبر به تومان وارد کنید لطفا.")
        return TRANS_SHAFT_PRICE_PER_KG

def calc_cylinder_volume(radius_cm, height_cm):
    return math.pi * (radius_cm ** 2) * height_cm  # حجم بر حسب سانتی‌متر مکعب

def calc_cylinder_weight(volume_cm3, density_kg_per_m3):
    # چگالی به کیلوگرم بر متر مکعب، حجم به سانتی متر مکعب
    # تبدیل حجم به متر مکعب: 1m³ = 1,000,000 cm³
    volume_m3 = volume_cm3 / 1_000_000
    return volume_m3 * density_kg_per_m3

async def final_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # دریافت داده‌ها
    length_cm = context.user_data['screw_length_cm']
    outer_diameter_inch = context.user_data['screw_outer_diameter_inch']
    outer_thickness_mm = context.user_data['screw_outer_thickness_mm']
    shaft_diameter_inch = context.user_data['screw_shaft_diameter_inch']
    shaft_thickness_mm = context.user_data['screw_shaft_thickness_mm']
    pitch_mm = context.user_data['screw_pitch_mm']
    blade_thickness_mm = context.user_data['screw_blade_thickness_mm']
    motor_gearbox_price = context.user_data['motor_gearbox_price']
    turner_price = context.user_data['turner_price']
    trans_shaft_diameter_cm = context.user_data['trans_shaft_diameter_cm']
    trans_shaft_length_cm = context.user_data['trans_shaft_length_cm']
    trans_shaft_price_per_kg = context.user_data['trans_shaft_price_per_kg']
    wage_per_kg = context.user_data['wage_per_kg']

    # تبدیل ها:
    length_m = length_cm / 100
    outer_diameter_cm = outer_diameter_inch * 2.54
    shaft_diameter_cm = shaft_diameter_inch * 2.54

    # شعاع های لوله بدنه اسکرو:
    outer_radius_cm = outer_diameter_cm / 2
    inner_radius_cm = outer_radius_cm - (outer_thickness_mm / 10)  # ضخامت میلیمتر به سانتی متر

    # وزن لوله بدنه اسکرو (پوسته لوله استوانه ای):
    # حجم = π * h * (R_outer^2 - R_inner^2)
    volume_outer_pipe_cm3 = math.pi * length_cm * (outer_radius_cm ** 2 - inner_radius_cm ** 2)
    weight_outer_pipe_kg = calc_cylinder_weight(volume_outer_pipe_cm3, STEEL_DENSITY)

    # شعاع داخلی لوله شفت:
    shaft_outer_radius_cm = shaft_diameter_cm / 2
    shaft_inner_radius_cm = shaft_outer_radius_cm - (shaft_thickness_mm / 10)  # ضخامت به سانتی متر

    # وزن لوله شفت (پوسته لوله):
    volume_shaft_pipe_cm3 = math.pi * length_cm * (shaft_outer_radius_cm ** 2 - shaft_inner_radius_cm ** 2)
    weight_shaft_pipe_kg = calc_cylinder_weight(volume_shaft_pipe_cm3, STEEL_DENSITY)

    # شعاع تیغه ماردون = شعاع داخلی لوله بدنه - شعاع بیرونی لوله شفت
    # شعاع بیرونی لوله شفت = شعاع خارجی لوله شفت (چون ضخامت لوله شفت داخل هست)
    blade_radius_cm = inner_radius_cm - shaft_outer_radius_cm

    # وزن تیغه ماردون:
    # حجم تیغه = طول * مساحت تیغه
    # مساحت تیغه تقریبی: طول * ضخامت * محیط دایره = ضخامت تیغه * محیط دایره * طول (محیط دایره= 2πr)
    blade_area_cm2 = 2 * math.pi * blade_radius_cm * blade_thickness_mm / 10  # ضخامت به سانتی متر
    volume_blade_cm3 = blade_area_cm2 * length_cm
    weight_blade_kg = calc_cylinder_weight(volume_blade_cm3, STEEL_DENSITY)

    # وزن کل لوله ها و تیغه
    total_weight_kg = weight_outer_pipe_kg + weight_shaft_pipe_kg + weight_blade_kg

    # وزن شفت انتقال قدرت (استوانه توپر فلزی)
    trans_shaft_radius_cm = trans_shaft_diameter_cm / 2
    trans_shaft_length_cm = trans_shaft_length_cm
    volume_trans_shaft_cm3 = math.pi * (trans_shaft_radius_cm ** 2) * trans_shaft_length_cm
    weight_trans_shaft_kg = calc_cylinder_weight(volume_trans_shaft_cm3, STEEL_DENSITY)

    # هزینه شفت انتقال قدرت
    trans_shaft_price = weight_trans_shaft_kg * trans_shaft_price_per_kg

    # هزینه کل:
    total_price = motor_gearbox_price + turner_price + trans_shaft_price + total_weight_kg * wage_per_kg

    text_result = (
        f"📊 نتایج محاسبه اسکرو کانوایر:\n\n"
        f"⚙️ وزن لوله بدنه اسکرو: {format_number(weight_outer_pipe_kg)} کیلوگرم\n"
        f"⚙️ وزن لوله شفت وسط: {format_number(weight_shaft_pipe_kg)} کیلوگرم\n"
        f"⚙️ وزن تیغه ماردون: {format_number(weight_blade_kg)} کیلوگرم\n"
        f"⚙️ وزن کل اسکرو (لوله ها و تیغه): {format_number(total_weight_kg)} کیلوگرم\n\n"
        f"🛠️ وزن شفت انتقال قدرت (میلگرد): {format_number(weight_trans_shaft_kg)} کیلوگرم\n"
        f"💰 هزینه شفت انتقال قدرت: {format_number(trans_shaft_price)} تومان\n\n"
        f"💰 هزینه موتور و گیربکس: {format_number(motor_gearbox_price)} تومان\n"
        f"💰 اجرت تراشکار: {format_number(turner_price)} تومان\n"
        f"💸 دستمزد ساخت هر کیلوگرم: {format_number(wage_per_kg)} تومان\n\n"
        f"💵 مجموع کل هزینه: {format_number(total_price)} تومان\n\n"
        f"برای شروع مجدد /reset را بزنید."
    )
    await update.message.reply_text(text_result)
    return ConversationHandler.END

async def wage_per_kg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = int(update.message.text.replace(",", ""))
        if wage < 0:
            raise ValueError
        context.user_data['wage_per_kg'] = wage
        return await final_result(update, context)
    except:
        await update.message.reply_text("عدد معتبر به تومان وارد کنید لطفا.")
        return WAGE_PER_KG

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات ریست شد. لطفا /start را بزنید.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    # جایگزین توکن تلگرام خودت کن
    TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_product)],

            SCREW_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_length)],
            SCREW_OUTER_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_diameter)],
            SCREW_OUTER_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_thickness)],
            SCREW_SHAFT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_diameter)],
            SCREW_SHAFT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_thickness)],
            SCREW_PITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_pitch)],
            SCREW_BLADE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_blade_thickness)],

            MOTOR_GEARBOX_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, motor_gearbox_price)],
            TURNER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, turner_price)],

            TRANS_SHAFT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_diameter)],
            TRANS_SHAFT_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_length)],
            TRANS_SHAFT_PRICE_PER_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_price_per_kg)],
            WAGE_PER_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, wage_per_kg)],
        },
        fallbacks=[CommandHandler('reset', reset)],
    )

    app.add_handler(conv_handler)

    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
