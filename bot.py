import math
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# Enable logging to see errors and bot activity
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# ثابت‌های عمومی
# ==============================================================================
TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"  # <-- توکن ربات خود را اینجا وارد کنید
STEEL_DENSITY_KG_M3 = 7850      # چگالی فولاد (kg/m^3)
CEMENT_DENSITY_KG_M3 = 1600     # چگالی سیمان فله (kg/m^3)
INCH_TO_M = 0.0254
END = ConversationHandler.END

# ==============================================================================
# تعریف وضعیت‌های مکالمه (States)
# ==============================================================================

# --- وضعیت‌های سطح بالا ---
SELECTING_COMPONENT, SELECTING_TASK = range(2)

# --- وضعیت‌های مربوط به مخزن (Tank) ---
(
    TANK_PRICING_DIAMETER, TANK_PRICING_HEIGHT, TANK_PRICING_THICKNESS_CYL,
    TANK_PRICING_CONE_BOTTOM_H, TANK_PRICING_CONE_BOTTOM_THICK, TANK_PRICING_CONE_TOP_H,
    TANK_PRICING_CONE_TOP_THICK, TANK_PRICING_SUPPORT_COUNT, TANK_PRICING_SUPPORT_HEIGHT,
    TANK_PRICING_SUPPORT_DIAMETER, TANK_PRICING_SUPPORT_THICKNESS, TANK_PRICING_WASTE,
    TANK_PRICING_WAGE,
    TANK_CALC_ORIENTATION, TANK_CALC_CHOICE, TANK_AWAITING_DIAMETER,
    TANK_AWAITING_LENGTH, TANK_AWAITING_VOLUME, TANK_AWAITING_BOTTOM_H,
    TANK_AWAITING_TOP_H
) = range(2, 22)


# --- وضعیت‌های مربوط به سیلو (Silo) ---
(
    SILO_CALC_CHOICE, SILO_AWAITING_DIAMETER, SILO_AWAITING_LENGTH,
    SILO_AWAITING_CAPACITY, SILO_AWAITING_BOTTOM_H, SILO_AWAITING_TOP_H,
    SILO_PRICING_DIAMETER, SILO_PRICING_HEIGHT, SILO_PRICING_THICKNESS_CYL,
    SILO_PRICING_CONE_BOTTOM_H, SILO_PRICING_CONE_BOTTOM_THICK,
    SILO_PRICING_CONE_TOP_H, SILO_PRICING_CONE_TOP_THICK,
    SILO_PRICING_SUPPORT_COUNT, SILO_PRICING_SUPPORT_HEIGHT,
    SILO_PRICING_SUPPORT_DIAMETER, SILO_PRICING_SUPPORT_THICKNESS,
    SILO_PRICING_LADDER_H,
    SILO_PRICING_KALLAF_ROWS, SILO_PRICING_KALLAF_DIAMETER, SILO_PRICING_KALLAF_THICKNESS,
    SILO_PRICING_BADBAND_WIDTH, SILO_PRICING_BADBAND_THICKNESS,
    SILO_PRICING_WASTE, SILO_PRICING_WAGE
) = range(22, 47)


# ==============================================================================
# توابع کمکی
# ==============================================================================

def _calculate_pipe_weight(length_m: float, diameter_inch: float, thickness_mm: float) -> float:
    """وزن یک لوله توخالی را محاسبه می‌کند."""
    if not all(x > 0 for x in [length_m, diameter_inch, thickness_mm]):
        return 0
    outer_r_m = (diameter_inch * INCH_TO_M) / 2
    thickness_m = thickness_mm / 1000
    inner_r_m = outer_r_m - thickness_m
    if inner_r_m < 0: inner_r_m = 0
    volume_m3 = math.pi * (outer_r_m**2 - inner_r_m**2) * length_m
    return volume_m3 * STEEL_DENSITY_KG_M3

def _calculate_strap_weight(length_m: float, width_cm: float, thickness_mm: float) -> float:
    """وزن یک تسمه را محاسبه می‌کند."""
    if not all(x > 0 for x in [length_m, width_cm, thickness_mm]):
        return 0
    width_m = width_cm / 100
    thickness_m = thickness_mm / 1000
    volume_m3 = length_m * width_m * thickness_m
    return volume_m3 * STEEL_DENSITY_KG_M3

# ==============================================================================
# مدیریت جریان اصلی مکالمه
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع یا راه‌اندازی مجدد مکالمه."""
    keyboard = [
        [InlineKeyboardButton("⚙️ محاسبات مخزن", callback_data="component_tank")],
        [InlineKeyboardButton("🏗️ محاسبات سیلو سیمان", callback_data="component_silo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data.clear()
    text = "سلام! لطفاً نوع محاسبات را انتخاب کنید:\n/cancel برای لغو عملیات"
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)
    return SELECTING_COMPONENT

async def select_component(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب کاربر (مخزن یا سیلو) و نمایش منوی وظایف."""
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['component'] = choice.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ قیمت‌گذاری", callback_data="task_pricing")],
        [InlineKeyboardButton("2️⃣ محاسبه ابعاد", callback_data="task_calc")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    component_name = "مخزن" if context.user_data['component'] == 'tank' else "سیلو"
    await query.edit_message_text(f"محاسبات {component_name} انتخاب شد. لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    return SELECTING_TASK

async def select_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب وظیفه (قیمت‌گذاری یا محاسبه)."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_start":
        return await start(update, context)

    task_choice = query.data.split('_')[1]
    component = context.user_data.get('component')

    if component == 'tank':
        if task_choice == "pricing":
            context.user_data['data'] = {}
            await query.edit_message_text("قیمت‌گذاری مخزن: لطفاً قطر بدنه (cm) را وارد کنید:")
            return TANK_PRICING_DIAMETER
        elif task_choice == "calc":
            context.user_data['data'] = {}
            keyboard = [[InlineKeyboardButton("عمودی", callback_data="vertical"), InlineKeyboardButton("افقی", callback_data="horizontal")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("محاسبه ابعاد مخزن: لطفاً جهت مخزن را انتخاب کنید:", reply_markup=reply_markup)
            return TANK_CALC_ORIENTATION
    elif component == 'silo':
        if task_choice == "pricing":
            context.user_data['data'] = {}
            await query.edit_message_text("قیمت‌گذاری سیلو: لطفاً قطر سیلو (cm) را وارد کنید:")
            return SILO_PRICING_DIAMETER
        elif task_choice == "calc":
            context.user_data['data'] = {}
            keyboard = [[InlineKeyboardButton("ظرفیت (تُن)", callback_data='capacity')], [InlineKeyboardButton("ارتفاع استوانه (cm)", callback_data='length')], [InlineKeyboardButton("قطر سیلو (cm)", callback_data='diameter')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("محاسبه ابعاد سیلو: چه مقداری را می‌خواهید محاسبه کنید؟", reply_markup=reply_markup)
            return SILO_CALC_CHOICE
    return END

# ==============================================================================
# بخش اول: منطق و توابع مربوط به مخزن (TANK)
# ==============================================================================

# --- قیمت‌گذاری مخزن ---
async def tank_pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['diameter_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع بدنه (cm):")
        return TANK_PRICING_HEIGHT
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return TANK_PRICING_DIAMETER

async def tank_pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['height_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت بدنه (mm):")
        return TANK_PRICING_THICKNESS_CYL
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_PRICING_HEIGHT

async def tank_pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['thickness_cyl_mm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع قیف پایین (cm) (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_CONE_BOTTOM_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return TANK_PRICING_THICKNESS_CYL

async def tank_pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_bottom_h_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت قیف پایین (mm) (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_CONE_BOTTOM_THICK
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_PRICING_CONE_BOTTOM_H

async def tank_pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_bottom_thick_mm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع قیف بالا (cm) (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_CONE_TOP_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return TANK_PRICING_CONE_BOTTOM_THICK

async def tank_pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_top_h_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت قیف بالا (mm) (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_CONE_TOP_THICK
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_PRICING_CONE_TOP_H

async def tank_pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_top_thick_mm'] = float(update.message.text)
        await update.message.reply_text("✅ تعداد پایه‌ها (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_SUPPORT_COUNT
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return TANK_PRICING_CONE_TOP_THICK

async def tank_pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        context.user_data['data']['support_count'] = count
        if count > 0:
            await update.message.reply_text("✅ ارتفاع هر پایه (cm):")
            return TANK_PRICING_SUPPORT_HEIGHT
        else:
            await update.message.reply_text("✅ درصد پرتی ورق (%):")
            return TANK_PRICING_WASTE
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً تعداد را به صورت عدد صحیح وارد کنید.")
        return TANK_PRICING_SUPPORT_COUNT

async def tank_pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_height_cm'] = float(update.message.text)
        await update.message.reply_text("✅ قطر هر پایه (inch):")
        return TANK_PRICING_SUPPORT_DIAMETER
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_PRICING_SUPPORT_HEIGHT

async def tank_pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_diameter_inch'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت هر پایه (mm):")
        return TANK_PRICING_SUPPORT_THICKNESS
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return TANK_PRICING_SUPPORT_DIAMETER

async def tank_pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_thickness_mm'] = float(update.message.text)
        await update.message.reply_text("✅ درصد پرتی ورق (%):")
        return TANK_PRICING_WASTE
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return TANK_PRICING_SUPPORT_THICKNESS

async def tank_pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['waste_percent'] = float(update.message.text)
        await update.message.reply_text("✅ دستمزد ساخت (تومان به ازای هر کیلوگرم):")
        return TANK_PRICING_WAGE
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً درصد را به صورت عدد وارد کنید.")
        return TANK_PRICING_WASTE

async def tank_pricing_final_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        wage_per_kg = float(update.message.text)
        data = context.user_data['data']
        d_m = data.get('diameter_cm', 0) / 100
        radius_m = d_m / 2
        
        # Cylinder
        weight_cyl = _calculate_strap_weight(math.pi * d_m, data.get('height_cm', 0), data.get('thickness_cyl_mm', 0))
        
        # Cones
        weight_cb = 0
        if data.get('cone_bottom_h_cm', 0) > 0:
            slant_cb = math.sqrt(radius_m**2 + (data['cone_bottom_h_cm']/100)**2)
            area_cb = math.pi * radius_m * slant_cb
            weight_cb = area_cb * (data.get('cone_bottom_thick_mm', 0) / 1000) * STEEL_DENSITY_KG_M3

        weight_ct = 0
        if data.get('cone_top_h_cm', 0) > 0:
            slant_ct = math.sqrt(radius_m**2 + (data['cone_top_h_cm']/100)**2)
            area_ct = math.pi * radius_m * slant_ct
            weight_ct = area_ct * (data.get('cone_top_thick_mm', 0) / 1000) * STEEL_DENSITY_KG_M3
            
        # Supports
        weight_supports = data.get('support_count', 0) * _calculate_pipe_weight(
            data.get('support_height_cm', 0) / 100,
            data.get('support_diameter_inch', 0),
            data.get('support_thickness_mm', 0)
        )

        total_weight = weight_cyl + weight_cb + weight_ct + weight_supports
        weight_with_waste = total_weight * (1 + data.get('waste_percent', 0) / 100)
        total_price = weight_with_waste * wage_per_kg

        response = "📊 **نتایج قیمت‌گذاری مخزن** 📊\n\n"
        response += f"🔹 وزن بدنه: `{int(weight_cyl)}` کیلوگرم\n"
        response += f"🔹 وزن قیف پایین: `{int(weight_cb)}` کیلوگرم\n"
        response += f"🔹 وزن قیف بالا: `{int(weight_ct)}` کیلوگرم\n"
        response += f"🔹 وزن پایه‌ها: `{int(weight_supports)}` کیلوگرم\n"
        response += "-----------------------------------\n"
        response += f"🔸 **وزن کلی (با پرتی):** `{int(weight_with_waste)}` کیلوگرم\n"
        response += f"💰 **قیمت کل:** `{int(total_price):,}` تومان"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        await update.message.reply_text("برای شروع مجدد /start را بزنید.")
        context.user_data.clear()
        return END
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً دستمزد را به صورت عدد معتبر وارد کنید.")
        return TANK_PRICING_WAGE
    except Exception as e:
        logger.error(f"Error in tank_pricing_final_calculate: {e}")
        await update.message.reply_text(f"یک خطای غیرمنتظره رخ داد. لطفاً با /start دوباره تلاش کنید.")
        context.user_data.clear()
        return END

# --- محاسبه ابعاد مخزن ---
async def tank_calc_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['data']['orientation'] = query.data
    keyboard = [[InlineKeyboardButton("حجم (لیتر)", callback_data='volume')], [InlineKeyboardButton("طول بدنه (cm)", callback_data='length')], [InlineKeyboardButton("قطر بدنه (cm)", callback_data='diameter')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("چه مقداری را می‌خواهید محاسبه کنید؟", reply_markup=reply_markup)
    return TANK_CALC_CHOICE

async def tank_calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['data']['find'] = query.data
    if query.data == 'volume':
        await query.edit_message_text("لطفاً قطر مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_DIAMETER
    elif query.data == 'length':
        await query.edit_message_text("لطفاً قطر مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_DIAMETER
    elif query.data == 'diameter':
        await query.edit_message_text("لطفاً طول بدنه مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_LENGTH
    return END

async def tank_calc_get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['diameter_m'] = float(update.message.text) / 100
        find = context.user_data['data']['find']
        if find == 'volume':
            await update.message.reply_text("✅ طول بدنه مخزن (cm):")
            return TANK_AWAITING_LENGTH
        elif find == 'length':
            await update.message.reply_text("✅ حجم کل مخزن (لیتر):")
            return TANK_AWAITING_VOLUME
    except ValueError:
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return TANK_AWAITING_DIAMETER
    return END

async def tank_calc_get_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['length_m'] = float(update.message.text) / 100
        find = context.user_data['data']['find']
        if find == 'volume':
            await update.message.reply_text("✅ ارتفاع قیف/عدسی اول (cm) (اگر ندارد 0 وارد کنید):")
            return TANK_AWAITING_BOTTOM_H
        elif find == 'diameter':
            await update.message.reply_text("✅ حجم کل مخزن (لیتر):")
            return TANK_AWAITING_VOLUME
    except ValueError:
        await update.message.reply_text("خطا: لطفاً طول را به صورت عدد وارد کنید.")
        return TANK_AWAITING_LENGTH
    return END

async def tank_calc_get_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['volume_m3'] = float(update.message.text) / 1000
        await update.message.reply_text("✅ ارتفاع قیف/عدسی اول (cm) (اگر ندارد 0 وارد کنید):")
        return TANK_AWAITING_BOTTOM_H
    except ValueError:
        await update.message.reply_text("خطا: لطفاً حجم را به صورت عدد وارد کنید.")
        return TANK_AWAITING_VOLUME

async def tank_calc_get_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['bottom_h_m'] = float(update.message.text) / 100
        await update.message.reply_text("✅ ارتفاع قیف/عدسی دوم (cm) (اگر ندارد 0 وارد کنید):")
        return TANK_AWAITING_TOP_H
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_AWAITING_BOTTOM_H

async def tank_calc_get_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['top_h_m'] = float(update.message.text) / 100
        return await perform_volume_calculation(update, context, 1000, "لیتر")
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return TANK_AWAITING_TOP_H

# ==============================================================================
# بخش دوم: منطق و توابع مربوط به سیلو (SILO)
# ==============================================================================

# --- قیمت‌گذاری سیلو ---
async def silo_pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['diameter_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع بدنه (cm):")
        return SILO_PRICING_HEIGHT
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return SILO_PRICING_DIAMETER

async def silo_pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['height_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت بدنه (mm):")
        return SILO_PRICING_THICKNESS_CYL
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_PRICING_HEIGHT

async def silo_pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['thickness_cyl_mm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع قیف پایین (cm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_CONE_BOTTOM_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_THICKNESS_CYL

async def silo_pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_bottom_h_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت قیف پایین (mm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_CONE_BOTTOM_THICK
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_PRICING_CONE_BOTTOM_H

async def silo_pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_bottom_thick_mm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع قیف بالا (cm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_CONE_TOP_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_CONE_BOTTOM_THICK

async def silo_pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_top_h_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت قیف بالا (mm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_CONE_TOP_THICK
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_PRICING_CONE_TOP_H

async def silo_pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['cone_top_thick_mm'] = float(update.message.text)
        await update.message.reply_text("✅ تعداد پایه‌ها (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_SUPPORT_COUNT
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_CONE_TOP_THICK

async def silo_pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        context.user_data['data']['support_count'] = count
        if count > 0:
            await update.message.reply_text("✅ ارتفاع هر پایه (cm):")
            return SILO_PRICING_SUPPORT_HEIGHT
        else:
            await update.message.reply_text("✅ ارتفاع نردبان (m) (اگر ندارد 0 وارد کنید):")
            return SILO_PRICING_LADDER_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً تعداد را به صورت عدد صحیح وارد کنید.")
        return SILO_PRICING_SUPPORT_COUNT

async def silo_pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_height_cm'] = float(update.message.text)
        await update.message.reply_text("✅ قطر هر پایه (inch):")
        return SILO_PRICING_SUPPORT_DIAMETER
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_PRICING_SUPPORT_HEIGHT

async def silo_pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_diameter_inch'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت هر پایه (mm):")
        return SILO_PRICING_SUPPORT_THICKNESS
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return SILO_PRICING_SUPPORT_DIAMETER

async def silo_pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['support_thickness_mm'] = float(update.message.text)
        await update.message.reply_text("✅ ارتفاع نردبان (m) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_LADDER_H
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_SUPPORT_THICKNESS

async def silo_pricing_ladder_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['ladder_h_m'] = float(update.message.text)
        await update.message.reply_text("✅ تعداد ردیف کلاف‌ها (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_KALLAF_ROWS
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ارتفاع نردبان را به صورت عدد وارد کنید.")
        return SILO_PRICING_LADDER_H

async def silo_pricing_kallaf_rows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        rows = int(update.message.text)
        context.user_data['data']['kallaf_rows'] = rows
        if rows > 0:
            await update.message.reply_text("✅ قطر لوله کلاف (inch):")
            return SILO_PRICING_KALLAF_DIAMETER
        else:
            await update.message.reply_text("✅ عرض بادبند (cm) (اگر ندارد 0 وارد کنید):")
            return SILO_PRICING_BADBAND_WIDTH
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً تعداد ردیف را به صورت عدد صحیح وارد کنید.")
        return SILO_PRICING_KALLAF_ROWS

async def silo_pricing_kallaf_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['kallaf_diameter_inch'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت لوله کلاف (mm):")
        return SILO_PRICING_KALLAF_THICKNESS
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return SILO_PRICING_KALLAF_DIAMETER

async def silo_pricing_kallaf_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['kallaf_thickness_mm'] = float(update.message.text)
        await update.message.reply_text("✅ عرض بادبند (cm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_BADBAND_WIDTH
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_KALLAF_THICKNESS

async def silo_pricing_badband_width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['badband_width_cm'] = float(update.message.text)
        await update.message.reply_text("✅ ضخامت بادبند (mm) (اگر ندارد 0 وارد کنید):")
        return SILO_PRICING_BADBAND_THICKNESS
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً عرض را به صورت عدد وارد کنید.")
        return SILO_PRICING_BADBAND_WIDTH

async def silo_pricing_badband_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['badband_thickness_mm'] = float(update.message.text)
        await update.message.reply_text("✅ درصد پرتی ورق (%):")
        return SILO_PRICING_WASTE
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت عدد وارد کنید.")
        return SILO_PRICING_BADBAND_THICKNESS

async def silo_pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['waste_percent'] = float(update.message.text)
        await update.message.reply_text("✅ دستمزد ساخت (تومان به ازای هر کیلوگرم):")
        return SILO_PRICING_WAGE
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً درصد را به صورت عدد وارد کنید.")
        return SILO_PRICING_WASTE

async def silo_pricing_final_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        wage_per_kg = float(update.message.text)
        data = context.user_data['data']
        d_m = data.get('diameter_cm', 0) / 100
        radius_m = d_m / 2
        circumference = math.pi * d_m

        # Cylinder & Cones
        weight_cyl = _calculate_strap_weight(circumference, data.get('height_cm', 0), data.get('thickness_cyl_mm', 0))
        weight_cb, weight_ct = 0, 0
        if data.get('cone_bottom_h_cm', 0) > 0:
            slant_cb = math.sqrt(radius_m**2 + (data['cone_bottom_h_cm']/100)**2)
            area_cb = math.pi * radius_m * slant_cb
            weight_cb = area_cb * (data.get('cone_bottom_thick_mm', 0) / 1000) * STEEL_DENSITY_KG_M3
        if data.get('cone_top_h_cm', 0) > 0:
            slant_ct = math.sqrt(radius_m**2 + (data['cone_top_h_cm']/100)**2)
            area_ct = math.pi * radius_m * slant_ct
            weight_ct = area_ct * (data.get('cone_top_thick_mm', 0) / 1000) * STEEL_DENSITY_KG_M3
            
        # Supports, Ladder, Kallaf, Badband
        weight_supports = data.get('support_count', 0) * _calculate_pipe_weight(data.get('support_height_cm', 0)/100, data.get('support_diameter_inch', 0), data.get('support_thickness_mm', 0))
        weight_ladder = data.get('ladder_h_m', 0) * 15 # Approximation: 15 kg per meter of ladder
        weight_kallaf = data.get('kallaf_rows', 0) * _calculate_pipe_weight(circumference, data.get('kallaf_diameter_inch', 0), data.get('kallaf_thickness_mm', 0))
        weight_badband = _calculate_strap_weight(circumference, data.get('badband_width_cm', 0), data.get('badband_thickness_mm', 0))

        total_weight = weight_cyl + weight_cb + weight_ct + weight_supports + weight_ladder + weight_kallaf + weight_badband
        weight_with_waste = total_weight * (1 + data.get('waste_percent', 0) / 100)
        total_price = weight_with_waste * wage_per_kg

        response = "📊 **نتایج قیمت‌گذاری سیلو** 📊\n\n"
        response += f"🔹 وزن بدنه و قیف‌ها: `{int(weight_cyl + weight_cb + weight_ct)}` کیلوگرم\n"
        response += f"🔹 وزن پایه‌ها: `{int(weight_supports)}` کیلوگرم\n"
        response += f"🔹 وزن نردبان: `{int(weight_ladder)}` کیلوگرم\n"
        response += f"🔹 وزن کلاف‌ها: `{int(weight_kallaf)}` کیلوگرم\n"
        response += f"🔹 وزن بادبند: `{int(weight_badband)}` کیلوگرم\n"
        response += "-----------------------------------\n"
        response += f"🔸 **وزن کلی (با پرتی):** `{int(weight_with_waste)}` کیلوگرم\n"
        response += f"💰 **قیمت کل:** `{int(total_price):,}` تومان"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        await update.message.reply_text("برای شروع مجدد /start را بزنید.")
        context.user_data.clear()
        return END
    except (ValueError):
        await update.message.reply_text("خطا: لطفاً دستمزد را به صورت عدد معتبر وارد کنید.")
        return SILO_PRICING_WAGE
    except Exception as e:
        logger.error(f"Error in silo_pricing_final_calculate: {e}")
        await update.message.reply_text(f"یک خطای غیرمنتظره رخ داد. لطفاً با /start دوباره تلاش کنید.")
        context.user_data.clear()
        return END

# --- محاسبه ابعاد سیلو ---
async def silo_calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['data']['find'] = query.data
    if query.data == 'capacity':
        await query.edit_message_text("لطفاً قطر سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_DIAMETER
    elif query.data == 'length':
        await query.edit_message_text("لطفاً قطر سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_DIAMETER
    elif query.data == 'diameter':
        await query.edit_message_text("لطفاً ارتفاع استوانه سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_LENGTH
    return END

async def silo_calc_get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['diameter_m'] = float(update.message.text) / 100
        find = context.user_data['data']['find']
        if find == 'capacity':
            await update.message.reply_text("✅ ارتفاع استوانه سیلو (cm):")
            return SILO_AWAITING_LENGTH
        elif find == 'length':
            await update.message.reply_text("✅ ظرفیت کل سیلو (تُن):")
            return SILO_AWAITING_CAPACITY
    except ValueError:
        await update.message.reply_text("خطا: لطفاً قطر را به صورت عدد وارد کنید.")
        return SILO_AWAITING_DIAMETER
    return END

async def silo_calc_get_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['length_m'] = float(update.message.text) / 100
        find = context.user_data['data']['find']
        if find == 'capacity':
            await update.message.reply_text("✅ ارتفاع قیف پایین (cm):")
            return SILO_AWAITING_BOTTOM_H
        elif find == 'diameter':
            await update.message.reply_text("✅ ظرفیت کل سیلو (تُن):")
            return SILO_AWAITING_CAPACITY
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_AWAITING_LENGTH
    return END

async def silo_calc_get_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        context.user_data['data']['volume_m3'] = (val * 1000) / CEMENT_DENSITY_KG_M3
        await update.message.reply_text("✅ ارتفاع قیف پایین (cm):")
        return SILO_AWAITING_BOTTOM_H
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ظرفیت را به صورت عدد وارد کنید.")
        return SILO_AWAITING_CAPACITY

async def silo_calc_get_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['bottom_h_m'] = float(update.message.text) / 100
        await update.message.reply_text("✅ ارتفاع قیف بالا (cm):")
        return SILO_AWAITING_TOP_H
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_AWAITING_BOTTOM_H

async def silo_calc_get_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['data']['top_h_m'] = float(update.message.text) / 100
        return await perform_volume_calculation(update, context, CEMENT_DENSITY_KG_M3 / 1000, "تُن")
    except ValueError:
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت عدد وارد کنید.")
        return SILO_AWAITING_TOP_H

# ==============================================================================
# توابع عمومی و اجرای ربات
# ==============================================================================
async def perform_volume_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE, multiplier: float, unit: str) -> int:
    """یک تابع عمومی برای انجام محاسبات ابعاد (حجم، طول، قطر)."""
    data = context.user_data['data']
    find = data['find']
    result_text = ""
    try:
        if find == 'volume' or find == 'capacity':
            r = data['diameter_m'] / 2
            vol_cyl = math.pi * r**2 * data['length_m']
            vol_cone_b = (1/3) * math.pi * r**2 * data['bottom_h_m']
            vol_cone_t = (1/3) * math.pi * r**2 * data['top_h_m']
            total_vol_m3 = vol_cyl + vol_cone_b + vol_cone_t
            result = total_vol_m3 * multiplier
            result_text = f"✅ **نتیجه:** ظرفیت کل `{result:,.2f}` {unit} است."
        elif find == 'length':
            r = data['diameter_m'] / 2
            vol_cone_b = (1/3) * math.pi * r**2 * data['bottom_h_m']
            vol_cone_t = (1/3) * math.pi * r**2 * data['top_h_m']
            vol_cyl_needed = data['volume_m3'] - vol_cone_b - vol_cone_t
            if vol_cyl_needed < 0 or r == 0:
                result_text = "خطا: حجم قیف‌ها از حجم کل بیشتر است!"
            else:
                L_calc_m = vol_cyl_needed / (math.pi * r**2)
                result_text = f"✅ **نتیجه:** طول/ارتفاع بدنه `{L_calc_m * 100:.2f}` سانتی‌متر است."
        elif find == 'diameter':
            denominator = math.pi * (data['length_m'] + data['bottom_h_m']/3 + data['top_h_m']/3)
            if denominator <= 0:
                result_text = "خطا: با این ورودی‌ها محاسبه قطر ممکن نیست."
            else:
                r_sq = data['volume_m3'] / denominator
                if r_sq < 0:
                    result_text = "خطا: مقادیر ورودی منجر به قطر نامعتبر می‌شود."
                else:
                    d_calc_m = 2 * math.sqrt(r_sq)
                    result_text = f"✅ **نتیجه:** قطر بدنه `{d_calc_m * 100:.2f}` سانتی‌متر است."
    except Exception as e:
        logger.error(f"Error in perform_volume_calculation: {e}")
        result_text = f"یک خطای ناشناخته در محاسبه رخ داد."
        
    await update.message.reply_text(result_text, parse_mode='Markdown')
    await update.message.reply_text("برای شروع مجدد /start را بزنید.")
    context.user_data.clear()
    return END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو مکالمه و پاک کردن داده‌های کاربر."""
    await update.message.reply_text("عملیات لغو شد. برای شروع مجدد /start را بزنید.")
    context.user_data.clear()
    return END

def main() -> None:
    """اجرای ربات."""
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_COMPONENT: [CallbackQueryHandler(select_component, pattern="^component_")],
            SELECTING_TASK: [CallbackQueryHandler(select_task, pattern="^task_|^back_to_start$")],
            
            # Tank Pricing States
            TANK_PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_diameter)],
            TANK_PRICING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_height)],
            TANK_PRICING_THICKNESS_CYL: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_thickness_cyl)],
            TANK_PRICING_CONE_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_cone_bottom_h)],
            TANK_PRICING_CONE_BOTTOM_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_cone_bottom_thick)],
            TANK_PRICING_CONE_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_cone_top_h)],
            TANK_PRICING_CONE_TOP_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_cone_top_thick)],
            TANK_PRICING_SUPPORT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_support_count)],
            TANK_PRICING_SUPPORT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_support_height)],
            TANK_PRICING_SUPPORT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_support_diameter)],
            TANK_PRICING_SUPPORT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_support_thickness)],
            TANK_PRICING_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_waste)],
            TANK_PRICING_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_pricing_final_calculate)],
            
            # Tank Calculation States
            TANK_CALC_ORIENTATION: [CallbackQueryHandler(tank_calc_orientation, pattern="^vertical$|^horizontal$")],
            TANK_CALC_CHOICE: [CallbackQueryHandler(tank_calc_choice, pattern="^volume$|^length$|^diameter$")],
            TANK_AWAITING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_diameter)],
            TANK_AWAITING_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_length)],
            TANK_AWAITING_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_volume)],
            TANK_AWAITING_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_bottom_h)],
            TANK_AWAITING_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_top_h)],
            
            # Silo Pricing States
            SILO_PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_diameter)],
            SILO_PRICING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_height)],
            SILO_PRICING_THICKNESS_CYL: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_thickness_cyl)],
            SILO_PRICING_CONE_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_cone_bottom_h)],
            SILO_PRICING_CONE_BOTTOM_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_cone_bottom_thick)],
            SILO_PRICING_CONE_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_cone_top_h)],
            SILO_PRICING_CONE_TOP_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_cone_top_thick)],
            SILO_PRICING_SUPPORT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_support_count)],
            SILO_PRICING_SUPPORT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_support_height)],
            SILO_PRICING_SUPPORT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_support_diameter)],
            SILO_PRICING_SUPPORT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_support_thickness)],
            SILO_PRICING_LADDER_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_ladder_h)],
            SILO_PRICING_KALLAF_ROWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_kallaf_rows)],
            SILO_PRICING_KALLAF_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_kallaf_diameter)],
            SILO_PRICING_KALLAF_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_kallaf_thickness)],
            SILO_PRICING_BADBAND_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_badband_width)],
            SILO_PRICING_BADBAND_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_badband_thickness)],
            SILO_PRICING_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_waste)],
            SILO_PRICING_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_pricing_final_calculate)],
            
            # Silo Calculation States
            SILO_CALC_CHOICE: [CallbackQueryHandler(silo_calc_choice, pattern="^capacity$|^length$|^diameter$")],
            SILO_AWAITING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_diameter)],
            SILO_AWAITING_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_length)],
            SILO_AWAITING_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_capacity)],
            SILO_AWAITING_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_bottom_h)],
            SILO_AWAITING_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_top_h)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        persistent=False,
        name="main_conversation",
    )

    application.add_handler(conv_handler)
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
