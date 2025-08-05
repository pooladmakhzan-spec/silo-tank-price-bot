from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import math

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل کلی
CHOOSING, WEIGHT_THICKNESS, WEIGHT_DIAMETER, WEIGHT_HEIGHT, WEIGHT_CONE_THICKNESS, WEIGHT_CONE_HEIGHT, \
WEIGHT_BASE_COUNT, WEIGHT_BASE_HEIGHT, WEIGHT_BASE_DIAMETER, WEIGHT_BASE_THICKNESS, WEIGHT_WASTE_PERCENT, WEIGHT_WAGE, \
CALC_CHOICE, CALC_VOLUME, CALC_DIAMETER, CALC_LENGTH, CALC_CONE_HEIGHT, CALC_TANK_TYPE, CALC_VOLUME_INPUT, CALC_DIAMETER_INPUT, CALC_LENGTH_INPUT = range(22)

user_data_template = {}

# ثابت‌ها
STEEL_DENSITY = 7850  # kg/m3
INCH_TO_METER = 0.0254

# کیبوردها
main_keyboard = [['محاسبه وزن و قیمت مخزن'], ['محاسبه حجم/قطر/طول مخزن']]
main_markup = ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)

calc_choice_keyboard = [['حجم'], ['قطر'], ['طول']]
calc_choice_markup = ReplyKeyboardMarkup(calc_choice_keyboard, one_time_keyboard=True, resize_keyboard=True)

tank_type_keyboard = [['عمودی'], ['افقی']]
tank_type_markup = ReplyKeyboardMarkup(tank_type_keyboard, one_time_keyboard=True, resize_keyboard=True)


# --- بخش محاسبه وزن و قیمت مخزن و پایه ها ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام!\n"
        "لطفا یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=main_markup
    )
    context.user_data.clear()
    return CHOOSING

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "داده‌ها پاک شد. برای شروع دوباره /start بزنید.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'محاسبه وزن و قیمت مخزن':
        await update.message.reply_text("لطفا ضخامت بدنه مخزن (میلی‌متر) را وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return WEIGHT_THICKNESS
    elif text == 'محاسبه حجم/قطر/طول مخزن':
        await update.message.reply_text("می‌خواهید چه چیزی را محاسبه کنید؟\n(حجم / قطر / طول)", reply_markup=calc_choice_markup)
        return CALC_CHOICE
    else:
        await update.message.reply_text("لطفا یکی از گزینه‌های موجود را انتخاب کنید.")
        return CHOOSING

# --- مراحل پرسش برای محاسبه وزن و قیمت ---

async def weight_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        thickness = float(update.message.text)
        if thickness <= 0:
            raise ValueError
        context.user_data['weight_thickness'] = thickness
        await update.message.reply_text("قطر مخزن را به متر وارد کنید:")
        return WEIGHT_DIAMETER
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر برای ضخامت وارد کنید:")
        return WEIGHT_THICKNESS

async def weight_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        diameter = float(update.message.text)
        if diameter <= 0:
            raise ValueError
        context.user_data['weight_diameter'] = diameter
        await update.message.reply_text("ارتفاع مخزن را به متر وارد کنید:")
        return WEIGHT_HEIGHT
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر برای قطر وارد کنید:")
        return WEIGHT_DIAMETER

async def weight_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        if height <= 0:
            raise ValueError
        context.user_data['weight_height'] = height
        await update.message.reply_text("ضخامت قیف (کف و سقف) را به میلی‌متر وارد کنید (اگر قیف ندارید عدد 0 وارد کنید):")
        return WEIGHT_CONE_THICKNESS
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر برای ارتفاع وارد کنید:")
        return WEIGHT_HEIGHT

async def weight_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cone_thickness = float(update.message.text)
        if cone_thickness < 0:
            raise ValueError
        context.user_data['weight_cone_thickness'] = cone_thickness
        await update.message.reply_text("ارتفاع قیف (کف) را به سانتی‌متر وارد کنید (اگر قیف ندارید عدد 0 وارد کنید):")
        return WEIGHT_CONE_HEIGHT
    except:
        await update.message.reply_text("لطفا عدد معتبر برای ضخامت قیف وارد کنید:")
        return WEIGHT_CONE_THICKNESS

async def weight_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cone_height_bottom = float(update.message.text)
        if cone_height_bottom < 0:
            raise ValueError
        context.user_data['weight_cone_height_bottom'] = cone_height_bottom
        await update.message.reply_text("ارتفاع قیف (سقف) را به سانتی‌متر وارد کنید (اگر قیف ندارید عدد 0 وارد کنید):")
        return WEIGHT_BASE_COUNT
    except:
        await update.message.reply_text("لطفا عدد معتبر برای ارتفاع قیف کف وارد کنید:")
        return WEIGHT_CONE_HEIGHT

async def weight_base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        base_count = int(update.message.text)
        if base_count < 0:
            raise ValueError
        context.user_data['weight_base_count'] = base_count
        if base_count == 0:
            # اگر پایه نداریم، بریم سوال بعدی
            await update.message.reply_text("درصد پرتی را به درصد وارد کنید (مثلاً 10):")
            return WEIGHT_WASTE_PERCENT
        else:
            await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر) را وارد کنید:")
            return WEIGHT_BASE_HEIGHT
    except:
        await update.message.reply_text("لطفا عدد صحیح معتبر برای تعداد پایه وارد کنید:")
        return WEIGHT_BASE_COUNT

async def weight_base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        base_height = float(update.message.text)
        if base_height <= 0:
            raise ValueError
        context.user_data['weight_base_height'] = base_height
        await update.message.reply_text("قطر هر پایه (اینچ) را وارد کنید:")
        return WEIGHT_BASE_DIAMETER
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر برای ارتفاع پایه وارد کنید:")
        return WEIGHT_BASE_HEIGHT

async def weight_base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        base_diameter = float(update.message.text)
        if base_diameter <= 0:
            raise ValueError
        context.user_data['weight_base_diameter'] = base_diameter
        await update.message.reply_text("ضخامت هر پایه (میلی‌متر) را وارد کنید:")
        return WEIGHT_BASE_THICKNESS
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر برای قطر پایه وارد کنید:")
        return WEIGHT_BASE_DIAMETER

async def weight_base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        base_thickness = float(update.message.text)
        if base_thickness < 0:
            raise ValueError
        context.user_data['weight_base_thickness'] = base_thickness
        await update.message.reply_text("درصد پرتی را به درصد وارد کنید (مثلاً 10):")
        return WEIGHT_WASTE_PERCENT
    except:
        await update.message.reply_text("لطفا عدد معتبر برای ضخامت پایه وارد کنید:")
        return WEIGHT_BASE_THICKNESS

async def weight_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        waste_percent = float(update.message.text)
        if waste_percent < 0:
            raise ValueError
        context.user_data['weight_waste_percent'] = waste_percent
        await update.message.reply_text("دستمزد هر کیلوگرم (تومان) را وارد کنید:")
        return WEIGHT_WAGE
    except:
        await update.message.reply_text("لطفا عدد معتبر برای درصد پرتی وارد کنید:")
        return WEIGHT_WASTE_PERCENT

async def weight_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = float(update.message.text)
        if wage < 0:
            raise ValueError
        context.user_data['weight_wage'] = wage
        # انجام محاسبات و نمایش خروجی
        text = calculate_weight_price(context.user_data)
        await update.message.reply_text(text, reply_markup=main_markup)
        return CHOOSING
    except:
        await update.message.reply_text("لطفا عدد معتبر برای دستمزد وارد کنید:")
        return WEIGHT_WAGE

# --- توابع محاسبات وزن و قیمت ---

def calculate_weight_price(data):
    # تبدیل واحدها
    thickness_m = data['weight_thickness'] / 1000  # میلی متر به متر
    diameter = data['weight_diameter']
    height = data['weight_height']
    cone_thickness_m = data['weight_cone_thickness'] / 1000
    cone_height_bottom_m = data['weight_cone_height_bottom'] / 100
    cone_height_top_m = data.get('weight_cone_height_top', 0) / 100  # اگر نبود 0 در نظر بگیر
    base_count = data['weight_base_count']
    base_height_m = data.get('weight_base_height', 0) / 100
    base_diameter_m = data.get('weight_base_diameter', 0) * INCH_TO_METER
    base_thickness_m = data.get('weight_base_thickness', 0) / 1000
    waste_percent = data['weight_waste_percent']
    wage = data['weight_wage']

    radius = diameter / 2

    # وزن بدنه استوانه
    body_area = 2 * math.pi * radius * height
    body_volume = body_area * thickness_m
    body_weight = body_volume * STEEL_DENSITY

    # قیف کف (مخروط)
    cone_bottom_volume = 0
    if cone_height_bottom_m > 0 and cone_thickness_m > 0:
        outer_volume = (1/3) * math.pi * (radius ** 2) * cone_height_bottom_m
        inner_radius = radius - cone_thickness_m
        inner_volume = (1/3) * math.pi * (inner_radius ** 2) * max(cone_height_bottom_m - cone_thickness_m, 0)
        cone_bottom_volume = outer_volume - inner_volume

    # قیف سقف (مخروط)
    cone_top_volume = 0
    if cone_height_top_m > 0 and cone_thickness_m > 0:
        outer_volume = (1/3) * math.pi * (radius ** 2) * cone_height_top_m
        inner_radius = radius - cone_thickness_m
        inner_volume = (1/3) * math.pi * (inner_radius ** 2) * max(cone_height_top_m - cone_thickness_m, 0)
        cone_top_volume = outer_volume - inner_volume

    cone_weight = (cone_bottom_volume + cone_top_volume) * STEEL_DENSITY

    # وزن پایه ها
    base_weight = 0
    if base_count > 0:
        outer_circumference = 2 * math.pi * base_diameter_m / 2
        # وزن هر پایه (لوله استوانه ای): محیط × ضخامت × ارتفاع × چگالی
        single_base_volume = outer_circumference * base_thickness_m * base_height_m
        base_weight = single_base_volume * STEEL_DENSITY * base_count

    total_weight = body_weight + cone_weight + base_weight
    total_weight_rounded = round(total_weight)

    total_weight_with_waste = total_weight * (1 + waste_percent / 100)
    total_weight_with_waste_rounded = round(total_weight_with_waste)

    total_price = total_weight_with_waste * wage
    total_price_rounded = round(total_price)

    text = (
        f"وزن مخزن بدون پرتی: {round(body_weight + cone_weight)} کیلوگرم\n"
        f"وزن پایه‌ها: {round(base_weight)} کیلوگرم\n"
        f"وزن کل: {total_weight_rounded} کیلوگرم\n"
        f"وزن کل با پرتی {waste_percent}%: {total_weight_with_waste_rounded} کیلوگرم\n"
        f"قیمت کل: {total_price_rounded} تومان"
    )
    return text


# --- بخش محاسبه حجم، قطر، طول ---

async def calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'حجم':
        context.user_data['calc_choice'] = 'volume'
        await update.message.reply_text("لطفا قطر مخزن را به متر وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return CALC_DIAMETER_INPUT
    elif text == 'قطر':
        context.user_data['calc_choice'] = 'diameter'
        await update.message.reply_text("لطفا طول مخزن را به متر وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return CALC_LENGTH_INPUT
    elif text == 'طول':
        context.user_data['calc_choice'] = 'length'
        await update.message.reply_text("لطفا قطر مخزن را به متر وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return CALC_DIAMETER_INPUT
    else:
        await update.message.reply_text("لطفا یکی از گزینه‌های موجود را انتخاب کنید:")
        return CALC_CHOICE

async def calc_diameter_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['calc_diameter'] = val
        await update.message.reply_text("لطفا طول مخزن را به متر وارد کنید:")
        return CALC_LENGTH_INPUT
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر وارد کنید:")
        return CALC_DIAMETER_INPUT

async def calc_length_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['calc_length'] = val
        await update.message.reply_text("ارتفاع قیف (کف و سقف) را به سانتی‌متر وارد کنید (اگر قیف ندارید عدد 0 وارد کنید):")
        return CALC_CONE_HEIGHT
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر وارد کنید:")
        return CALC_LENGTH_INPUT

async def calc_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val < 0:
            raise ValueError
        context.user_data['calc_cone_height'] = val
        await update.message.reply_text("نوع مخزن را انتخاب کنید (عمودی یا افقی):", reply_markup=tank_type_markup)
        return CALC_TANK_TYPE
    except:
        await update.message.reply_text("لطفا عدد معتبر وارد کنید:")
        return CALC_CONE_HEIGHT

async def calc_tank_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ['عمودی', 'افقی']:
        await update.message.reply_text("لطفا 'عمودی' یا 'افقی' را انتخاب کنید:", reply_markup=tank_type_markup)
        return CALC_TANK_TYPE
    context.user_data['calc_tank_type'] = text

    choice = context.user_data.get('calc_choice')

    if choice == 'volume':
        # برای حجم، بعد از قطر و طول و قیف و نوع مخزن، محاسبه حجم
        diameter = context.user_data['calc_diameter']
        length = context.user_data['calc_length']
        cone_height_cm = context.user_data['calc_cone_height']
        tank_type = context.user_data['calc_tank_type']
        volume_liter = calculate_volume(diameter, length, cone_height_cm, tank_type)
        await update.message.reply_text(f"حجم مخزن برابر است با: {volume_liter:.2f} لیتر", reply_markup=main_markup)
        return CHOOSING

    elif choice == 'diameter':
        # قطر رو با توجه به طول و حجم محاسبه کن
        # باید حجم رو هم بپرسیم:
        await update.message.reply_text("لطفا حجم مخزن را به لیتر وارد کنید:")
        return CALC_VOLUME_INPUT

    elif choice == 'length':
        # طول رو با توجه به قطر و حجم محاسبه کن
        await update.message.reply_text("لطفا حجم مخزن را به لیتر وارد کنید:")
        return CALC_VOLUME_INPUT

async def calc_volume_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['calc_volume'] = val
        choice = context.user_data.get('calc_choice')
        if choice == 'diameter':
            # قطر = تابعی از طول و حجم و قیف و نوع مخزن
            diameter = calculate_diameter(context.user_data)
            await update.message.reply_text(f"قطر مخزن برابر است با: {diameter:.2f} متر", reply_markup=main_markup)
            return CHOOSING
        elif choice == 'length':
            length = calculate_length(context.user_data)
            await update.message.reply_text(f"طول مخزن برابر است با: {length:.2f} متر", reply_markup=main_markup)
            return CHOOSING
        else:
            await update.message.reply_text("خطا در انتخاب عملیات محاسبه.")
            return CHOOSING
    except:
        await update.message.reply_text("لطفا عدد مثبت معتبر وارد کنید:")
        return CALC_VOLUME_INPUT

# --- توابع کمکی برای محاسبه حجم، قطر، طول ---

def calculate_volume(diameter, length, cone_height_cm, tank_type):
    # حجم کل = حجم استوانه + حجم قیف‌ها (اگر قیف‌ها وجود داشته باشند)
    radius = diameter / 2
    height_m = length
    cone_height_m = cone_height_cm / 100

    # حجم استوانه
    if tank_type == 'عمودی':
        cylinder_volume = math.pi * (radius ** 2) * height_m  # متر مکعب
    else:  # افقی
        # حجم افقی همان حجم استوانه طولی است (طول در حجم)
        cylinder_volume = math.pi * (radius ** 2) * height_m

    # حجم قیف‌ها (دو قیف بالا و پایین)
    cone_volume = 0
    if cone_height_m > 0:
        cone_volume = 2 * (1/3) * math.pi * (radius ** 2) * cone_height_m

    total_volume_m3 = cylinder_volume + cone_volume
    total_volume_liter = total_volume_m3 * 1000  # تبدیل مترمکعب به لیتر

    return total_volume_liter

def calculate_diameter(data):
    volume_liter = data['calc_volume']
    volume_m3 = volume_liter / 1000
    length = data['calc_length']
    cone_height_m = data['calc_cone_height'] / 100
    tank_type = data['calc_tank_type']
    radius = 0

    # حجم قیف‌ها را کم کن از حجم کل
    cone_volume = 0
    if cone_height_m > 0:
        cone_volume = 2 * (1/3) * math.pi * (radius ** 2) * cone_height_m

    # با توجه به نوع مخزن محاسبه شعاع
    if tank_type == 'عمودی':
        # حجم استوانه = حجم کل - حجم قیف
        cylinder_volume = volume_m3 - cone_volume
        # حجم استوانه = π * r² * h
        radius = math.sqrt(cylinder_volume / length / math.pi)
    else:
        # افقی هم مشابه است چون استوانه است
        cylinder_volume = volume_m3 - cone_volume
        radius = math.sqrt(cylinder_volume / length / math.pi)

    diameter = radius * 2
    return diameter

def calculate_length(data):
    volume_liter = data['calc_volume']
    volume_m3 = volume_liter / 1000
    diameter = data['calc_diameter']
    cone_height_m = data['calc_cone_height'] / 100
    tank_type = data['calc_tank_type']

    radius = diameter / 2

    cone_volume = 0
    if cone_height_m > 0:
        cone_volume = 2 * (1/3) * math.pi * (radius ** 2) * cone_height_m

    cylinder_volume = volume_m3 - cone_volume

    length = cylinder_volume / (math.pi * radius ** 2)
    return length


# --- دستورات اصلی ربات ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! برای محاسبه وزن و قیمت مخزن از منوی زیر استفاده کنید.",
        reply_markup=main_markup
    )
    return CHOOSING

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "داده‌ها پاک شد. از اول شروع کنید.",
        reply_markup=main_markup
    )
    return CHOOSING

# --- تعریف Markup ها ---

main_markup = ReplyKeyboardMarkup([['محاسبه وزن و قیمت', 'محاسبه حجم، قطر، طول']], resize_keyboard=True)
tank_type_markup = ReplyKeyboardMarkup([['عمودی', 'افقی']], resize_keyboard=True)
calc_choice_markup = ReplyKeyboardMarkup([['حجم', 'قطر', 'طول']], resize_keyboard=True)

# --- تعریف وضعیت‌ها ---

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
) = range(19)

# --- اضافه کردن handler ها ---

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex('^محاسبه وزن و قیمت$'), weight_thickness),
                MessageHandler(filters.Regex('^محاسبه حجم، قطر، طول$'), calc_choice),
            ],
            WEIGHT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_diameter)],
            WEIGHT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_height)],
            WEIGHT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cone_thickness)],
            WEIGHT_CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cone_height_bottom)],
            WEIGHT_CONE_HEIGHT_BOTTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_cone_height_top)],
            WEIGHT_CONE_HEIGHT_TOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_count)],
            WEIGHT_BASE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_height)],
            WEIGHT_BASE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_diameter)],
            WEIGHT_BASE_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_base_thickness)],
            WEIGHT_BASE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_waste_percent)],
            WEIGHT_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_wage)],
            WEIGHT_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_wage)],
            CALC_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_choice)],
            CALC_DIAMETER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_diameter_input)],
            CALC_LENGTH_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_length_input)],
            CALC_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_cone_height)],
            CALC_TANK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_tank_type)],
            CALC_VOLUME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_volume_input)],
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
