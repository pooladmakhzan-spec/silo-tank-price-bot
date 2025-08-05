import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

# فعال‌سازی لاگ برای دیباگ
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

# چگالی فولاد کیلوگرم بر متر مکعب
STEEL_DENSITY = 7850

# تابع محاسبه حجم استوانه
def cylinder_volume(diameter_m, height_m):
    radius = diameter_m / 2
    return 3.1416 * radius**2 * height_m

# تابع محاسبه حجم مخروط
def cone_volume(diameter_m, height_m):
    radius = diameter_m / 2
    return (1/3) * 3.1416 * radius**2 * height_m

# تابع محاسبه وزن لوله (پایه)
def pipe_weight(length_m, outer_diameter_inch, thickness_mm):
    # تبدیل اینچ به متر
    outer_diameter_m = outer_diameter_inch * 0.0254
    thickness_m = thickness_mm / 1000
    inner_diameter_m = outer_diameter_m - 2 * thickness_m
    cross_section_area = 3.1416 * (outer_diameter_m**2 - inner_diameter_m**2) / 4
    volume = cross_section_area * length_m
    weight = volume * STEEL_DENSITY
    return weight

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "سلام! برای محاسبه وزن و قیمت مخزن، ضخامت بدنه را به میلی‌متر وارد کنید:"
    )
    return THICKNESS

async def thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['thickness'] = val
        await update.message.reply_text("قطر مخزن را به متر وارد کنید:")
        return DIAMETER
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['diameter'] = val
        await update.message.reply_text("ارتفاع استوانه مخزن را به متر وارد کنید:")
        return HEIGHT
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['height'] = val
        await update.message.reply_text("ارتفاع قیف کف و سقف مخزن را به سانتی‌متر وارد کنید (مثلاً 20):")
        return FUNNEL_HEIGHT
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def funnel_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val < 0:
            raise ValueError
        context.user_data['funnel_height_cm'] = val
        await update.message.reply_text("ضخامت قیف را به میلی‌متر وارد کنید:")
        return FUNNEL_THICKNESS
    except ValueError:
        await update.message.reply_text("لطفاً عدد غیرمنفی معتبر وارد کنید.")

async def funnel_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['funnel_thickness_mm'] = val
        await update.message.reply_text("تعداد پایه‌ها را وارد کنید (عدد صحیح، حداقل 0):")
        return BASE_COUNT
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def base_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = int(update.message.text)
        if val < 0:
            raise ValueError
        context.user_data['base_count'] = val
        if val == 0:
            # اگر پایه نداریم بریم مرحله بعد
            context.user_data['base_height'] = 0
            context.user_data['base_diameter_inch'] = 0
            context.user_data['base_thickness_mm'] = 0
            await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم را به تومان وارد کنید:")
            return WAGE
        await update.message.reply_text("ارتفاع هر پایه را به سانتی‌متر وارد کنید:")
        return BASE_HEIGHT
    except ValueError:
        await update.message.reply_text("لطفاً عدد صحیح غیرمنفی وارد کنید.")

async def base_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['base_height_cm'] = val
        await update.message.reply_text("قطر هر پایه را به اینچ وارد کنید:")
        return BASE_DIAMETER
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def base_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['base_diameter_inch'] = val
        await update.message.reply_text("ضخامت هر پایه را به میلی‌متر وارد کنید:")
        return BASE_THICKNESS
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def base_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['base_thickness_mm'] = val
        await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم را به تومان وارد کنید:")
        return WAGE
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val <= 0:
            raise ValueError
        context.user_data['wage'] = val
        await update.message.reply_text("درصد ضریب پرتی (مثلاً 10 برای ۱۰٪) را وارد کنید:")
        return WASTE_PERCENT
    except ValueError:
        await update.message.reply_text("لطفاً عدد مثبت معتبر وارد کنید.")

async def waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        if val < 0:
            raise ValueError
        context.user_data['waste_percent'] = val

        # محاسبات
        t = context.user_data['thickness'] / 1000  # میلی‌متر به متر
        d = context.user_data['diameter']
        h = context.user_data['height']

        funnel_h = context.user_data['funnel_height_cm'] / 100  # سانتی‌متر به متر
        funnel_t = context.user_data['funnel_thickness_mm'] / 1000

        base_count = context.user_data['base_count']
        base_h = context.user_data.get('base_height_cm', 0) / 100
        base_d = context.user_data.get('base_diameter_inch', 0)
        base_th = context.user_data.get('base_thickness_mm', 0)

        wage = context.user_data['wage']
        waste = context.user_data['waste_percent']

        # وزن استوانه (بدنه)
        cylinder_vol = cylinder_volume(d, h)
        cylinder_weight = cylinder_vol * STEEL_DENSITY * t

        # وزن قیف کف و سقف (دو مخروط)
        cone_vol = cone_volume(d, funnel_h)
        funnel_weight = cone_vol * STEEL_DENSITY * funnel_t * 2  # دو قیف (کف و سقف)

        # وزن کل مخزن بدون پایه
        total_tank_weight = cylinder_weight + funnel_weight

        # وزن پایه‌ها
        base_weight = 0
        if base_count > 0:
            base_weight_single = pipe_weight(base_h, base_d, base_th)
            base_weight = base_weight_single * base_count

        # وزن کل شامل پایه
        total_weight = total_tank_weight + base_weight

        # اعمال ضریب پرتی
        total_weight_with_waste = total_weight * (
