import math
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ==============================================================================
# ثابت‌های عمومی
# ==============================================================================
STEEL_DENSITY_KG_M3 = 7850      # چگالی فولاد (kg/m^3)
CEMENT_DENSITY_KG_M3 = 1600     # چگالی سیمان فله (kg/m^3)
INCH_TO_M = 0.0254
END = ConversationHandler.END

# --- توکن و URL ربات ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY")
WEBHOOK_URL = f"https://silo-tank-price-bot.onrender.com/{TOKEN}"

# ==============================================================================
# تعریف وضعیت‌های مکالمه (States)
# ==============================================================================

# --- وضعیت‌های سطح بالا ---
SELECTING_COMPONENT, SELECTING_TASK = range(2)

# --- وضعیت‌های مربوط به مخزن (Tank) ---
(
    TANK_CHOOSE_PRICING, TANK_CHOOSE_CALC,
    TANK_PRICING_DIAMETER, TANK_PRICING_HEIGHT, TANK_PRICING_THICKNESS_CYL,
    TANK_PRICING_CONE_BOTTOM_H, TANK_PRICING_CONE_BOTTOM_THICK, TANK_PRICING_CONE_TOP_H,
    TANK_PRICING_CONE_TOP_THICK, TANK_PRICING_SUPPORT_COUNT, TANK_PRICING_SUPPORT_HEIGHT,
    TANK_PRICING_SUPPORT_DIAMETER, TANK_PRICING_SUPPORT_THICKNESS, TANK_PRICING_WASTE,
    TANK_PRICING_WAGE,
    TANK_CALC_ORIENTATION, TANK_CALC_CHOICE, TANK_AWAITING_DIAMETER,
    TANK_AWAITING_LENGTH, TANK_AWAITING_VOLUME, TANK_AWAITING_BOTTOM_H,
    TANK_AWAITING_TOP_H
) = range(2, 24)


# --- وضعیت‌های مربوط به سیلو (Silo) ---
(
    SILO_CHOOSE_PRICING, SILO_CHOOSE_CALC,
    # States for Silo Dimensions Calculation
    SILO_CALC_CHOICE, SILO_AWAITING_DIAMETER, SILO_AWAITING_LENGTH,
    SILO_AWAITING_CAPACITY, SILO_AWAITING_BOTTOM_H, SILO_AWAITING_TOP_H,
    # States for Silo Pricing
    SILO_PRICING_DIAMETER, SILO_PRICING_HEIGHT, SILO_PRICING_THICKNESS_CYL,
    SILO_PRICING_CONE_BOTTOM_H, SILO_PRICING_CONE_BOTTOM_THICK,
    SILO_PRICING_CONE_TOP_H, SILO_PRICING_CONE_TOP_THICK,
    SILO_PRICING_LADDER_NO_CAGE_H, SILO_PRICING_LADDER_CAGE_H,
    SILO_PRICING_SUPPORT_COUNT, SILO_PRICING_SUPPORT_HEIGHT,
    SILO_PRICING_SUPPORT_DIAMETER, SILO_PRICING_SUPPORT_THICKNESS,
    SILO_PRICING_KALLAF_ROWS, SILO_PRICING_KALLAF_DIAMETER, SILO_PRICING_KALLAF_THICKNESS,
    SILO_PRICING_BADBAND_DIAMETER, SILO_PRICING_BADBAND_THICKNESS,
    SILO_PRICING_WASTE, SILO_PRICING_WAGE
) = range(24, 52)


# ==============================================================================
# توابع کمکی
# ==============================================================================

def _calculate_pipe_weight(length_m: float, diameter_inch: float, thickness_mm: float) -> float:
    """وزن یک لوله توخالی را محاسبه می‌کند."""
    if length_m <= 0 or diameter_inch <= 0 or thickness_mm <= 0:
        return 0
    
    outer_r_m = (diameter_inch * INCH_TO_M) / 2
    thickness_m = thickness_mm / 1000
    inner_r_m = outer_r_m - thickness_m
    
    if inner_r_m < 0: inner_r_m = 0 # جلوگیری از شعاع منفی
    
    volume_m3 = math.pi * (outer_r_m**2 - inner_r_m**2) * length_m
    return volume_m3 * STEEL_DENSITY_KG_M3

def _calculate_strap_weight(length_m: float, width_cm: float, thickness_mm: float) -> float:
    """وزن یک تسمه را محاسبه می‌کند."""
    if length_m <= 0 or width_cm <= 0 or thickness_mm <= 0:
        return 0
    
    width_m = width_cm / 100
    thickness_m = thickness_mm / 1000
    area_m2 = width_m * thickness_m
    volume_m3 = area_m2 * length_m
    return volume_m3 * STEEL_DENSITY_KG_M3

# ==============================================================================
# مدیریت جریان اصلی مکالمه
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه و نمایش منوی اصلی برای انتخاب نوع قطعه."""
    keyboard = [
        [InlineKeyboardButton("⚙️ محاسبات مخزن", callback_data="component_tank")],
        [InlineKeyboardButton("🏗️ محاسبات سیلو سیمان", callback_data="component_silo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Clear any previous data
    context.user_data.clear()
    
    if update.message:
        await update.message.reply_text("سلام! لطفاً نوع محاسبات را انتخاب کنید:", reply_markup=reply_markup)
    else: # If coming from a callback query (e.g. back button)
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("سلام! لطفاً نوع محاسبات را انتخاب کنید:", reply_markup=reply_markup)

    return SELECTING_COMPONENT


async def select_component(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب کاربر (مخزن یا سیلو) و نمایش منوی وظایف."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "component_tank":
        context.user_data['component'] = 'tank'
        keyboard = [
            [InlineKeyboardButton("1️⃣ قیمت‌گذاری مخزن", callback_data="task_pricing")],
            [InlineKeyboardButton("2️⃣ محاسبه ابعاد مخزن", callback_data="task_calc")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("محاسبات مخزن انتخاب شد. لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
        return SELECTING_TASK

    elif choice == "component_silo":
        context.user_data['component'] = 'silo'
        keyboard = [
            [InlineKeyboardButton("1️⃣ قیمت‌گذاری سیلو", callback_data="task_pricing")],
            [InlineKeyboardButton("2️⃣ محاسبه ابعاد سیلو", callback_data="task_calc")],
             [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("محاسبات سیلو انتخاب شد. لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
        return SELECTING_TASK
    
    return END


async def select_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب وظیفه (قیمت‌گذاری یا محاسبه) بر اساس نوع قطعه."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_start":
        return await start(update, context)

    task_choice = query.data
    component = context.user_data.get('component')

    if component == 'tank':
        if task_choice == "task_pricing":
            await query.edit_message_text("قیمت‌گذاری مخزن انتخاب شد.\n\nلطفاً قطر بدنه (cm) را وارد کنید:")
            return TANK_PRICING_DIAMETER
        elif task_choice == "task_calc":
            keyboard = [
                [InlineKeyboardButton("عمودی", callback_data="vertical")],
                [InlineKeyboardButton("افقی", callback_data="horizontal")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "محاسبه ابعاد مخزن انتخاب شد.\n\nلطفاً جهت مخزن را انتخاب کنید:", reply_markup=reply_markup
            )
            return TANK_CALC_ORIENTATION

    elif component == 'silo':
        if task_choice == "task_pricing":
            context.user_data['silo_p'] = {} # Initialize pricing data for silo
            await query.edit_message_text("قیمت‌گذاری سیلو انتخاب شد.\n\nلطفاً قطر سیلو (cm) را وارد کنید:")
            return SILO_PRICING_DIAMETER
        elif task_choice == "task_calc":
            context.user_data['silo_c'] = {} # Initialize calc data for silo
            keyboard = [
                [InlineKeyboardButton("ظرفیت (تُن)", callback_data='capacity')],
                [InlineKeyboardButton("ارتفاع استوانه (cm)", callback_data='length')],
                [InlineKeyboardButton("قطر سیلو (cm)", callback_data='diameter')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("محاسبه ابعاد سیلو انتخاب شد.\n\nچه مقداری را می‌خواهید محاسبه کنید؟", reply_markup=reply_markup)
            return SILO_CALC_CHOICE

    return END

# ==============================================================================
# بخش اول: منطق و توابع مربوط به مخزن (TANK)
# ==============================================================================

# --- قیمت‌گذاری مخزن ---
async def tank_pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        if diameter <= 0: raise ValueError
        context.user_data['tank_p'] = {'diameter_cm': diameter}
        await update.message.reply_text("✅ بسیار خب. ارتفاع بدنه (cm) را وارد کنید:")
        return TANK_PRICING_HEIGHT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت یک عدد مثبت (cm) وارد کنید.")
        return TANK_PRICING_DIAMETER

async def tank_pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        if height <= 0: raise ValueError
        context.user_data['tank_p']['height_cm'] = height
        await update.message.reply_text("✅ بسیار خب. ضخامت بدنه (mm) را وارد کنید:")
        return TANK_PRICING_THICKNESS_CYL
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت یک عدد مثبت (cm) وارد کنید.")
        return TANK_PRICING_HEIGHT

async def tank_pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness <= 0: raise ValueError
        context.user_data['tank_p']['thickness_cyl_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
        return TANK_PRICING_CONE_BOTTOM_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت یک عدد مثبت (mm) وارد کنید.")
        return TANK_PRICING_THICKNESS_CYL

async def tank_pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_h = float(update.message.text)
        if cone_h < 0: raise ValueError
        context.user_data['tank_p']['cone_bottom_h_cm'] = cone_h
        await update.message.reply_text("✅ بسیار خب. ضخامت قیف پایین (mm) را وارد کنید:")
        return TANK_PRICING_CONE_BOTTOM_THICK
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return TANK_PRICING_CONE_BOTTOM_H

async def tank_pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['tank_p']['cone_bottom_thick_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف بالا (cm) را وارد کنید (اگر ندارد 0 وارد کنید):")
        return TANK_PRICING_CONE_TOP_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت قیف را به صورت یک عدد (mm) وارد کنید.")
        return TANK_PRICING_CONE_BOTTOM_THICK

async def tank_pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_h = float(update.message.text)
        if cone_h < 0: raise ValueError
        context.user_data['tank_p']['cone_top_h_cm'] = cone_h
        await update.message.reply_text("✅ بسیار خب. ضخامت قیف بالا (mm) را وارد کنید:")
        return TANK_PRICING_CONE_TOP_THICK
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return TANK_PRICING_CONE_TOP_H

async def tank_pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['tank_p']['cone_top_thick_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. تعداد پایه‌ها را وارد کنید:")
        return TANK_PRICING_SUPPORT_COUNT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت قیف را به صورت یک عدد (mm) وارد کنید.")
        return TANK_PRICING_CONE_TOP_THICK

async def tank_pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        if count < 0: raise ValueError
        context.user_data['tank_p']['support_count'] = count
        await update.message.reply_text("✅ بسیار خب. ارتفاع هر پایه (cm) را وارد کنید:")
        return TANK_PRICING_SUPPORT_HEIGHT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً تعداد پایه‌ها را به صورت یک عدد صحیح وارد کنید.")
        return TANK_PRICING_SUPPORT_COUNT

async def tank_pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        if height < 0: raise ValueError
        context.user_data['tank_p']['support_height_cm'] = height
        await update.message.reply_text("✅ بسیار خب. قطر هر پایه (inch) را وارد کنید:")
        return TANK_PRICING_SUPPORT_DIAMETER
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع پایه را به صورت یک عدد (cm) وارد کنید.")
        return TANK_PRICING_SUPPORT_HEIGHT

async def tank_pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        if diameter < 0: raise ValueError
        context.user_data['tank_p']['support_diameter_inch'] = diameter
        await update.message.reply_text("✅ بسیار خب. ضخامت هر پایه (mm) را وارد کنید:")
        return TANK_PRICING_SUPPORT_THICKNESS
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر پایه را به صورت یک عدد (inch) وارد کنید.")
        return TANK_PRICING_SUPPORT_DIAMETER

async def tank_pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['tank_p']['support_thickness_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. درصد پرتی ورق (%) را وارد کنید:")
        return TANK_PRICING_WASTE
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت پایه را به صورت یک عدد (mm) وارد کنید.")
        return TANK_PRICING_SUPPORT_THICKNESS

async def tank_pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        waste = float(update.message.text)
        if waste < 0: raise ValueError
        context.user_data['tank_p']['waste_percent'] = waste
        await update.message.reply_text("✅ بسیار خب. دستمزد ساخت (تومان به ازای هر کیلوگرم) را وارد کنید:")
        return TANK_PRICING_WAGE
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً درصد پرتی را به صورت یک عدد وارد کنید.")
        return TANK_PRICING_WASTE

async def tank_pricing_final_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محاسبه نهایی وزن و قیمت مخزن و ارسال نتیجه."""
    try:
        wage_per_kg = float(update.message.text)
        if wage_per_kg < 0: raise ValueError
        data = context.user_data['tank_p']

        d_m = data['diameter_cm'] / 100
        h_cyl_m = data['height_cm'] / 100
        t_cyl_m = data['thickness_cyl_mm'] / 1000
        h_cb_m = data['cone_bottom_h_cm'] / 100
        t_cb_m = data['cone_bottom_thick_mm'] / 1000
        h_ct_m = data['cone_top_h_cm'] / 100
        t_ct_m = data['cone_top_thick_mm'] / 1000
        
        support_count = data['support_count']
        support_h_m = data['support_height_cm'] / 100
        support_d_inch = data['support_diameter_inch']
        support_t_mm = data['support_thickness_mm']

        radius_m = d_m / 2

        cyl_area = math.pi * d_m * h_cyl_m
        weight_cyl = cyl_area * t_cyl_m * STEEL_DENSITY_KG_M3

        weight_cb = 0
        if h_cb_m > 0:
            slant_cb = math.sqrt(radius_m**2 + h_cb_m**2)
            area_cb = math.pi * radius_m * slant_cb
            weight_cb = area_cb * t_cb_m * STEEL_DENSITY_KG_M3

        weight_ct = 0
        if h_ct_m > 0:
            slant_ct = math.sqrt(radius_m**2 + h_ct_m**2)
            area_ct = math.pi * radius_m * slant_ct
            weight_ct = area_ct * t_ct_m * STEEL_DENSITY_KG_M3

        weight_supports = 0
        if support_count > 0:
            weight_one_support = _calculate_pipe_weight(support_h_m, support_d_inch, support_t_mm)
            weight_supports = weight_one_support * support_count

        total_weight = weight_cyl + weight_cb + weight_ct + weight_supports
        weight_with_waste = total_weight * (1 + data['waste_percent'] / 100)
        total_price = weight_with_waste * wage_per_kg

        response = "📊 **نتایج قیمت‌گذاری مخزن** 📊\n\n"
        response += f"🔹 وزن بدنه استوانه‌ای: `{int(weight_cyl)}` کیلوگرم\n"
        response += f"🔹 وزن قیف پایین: `{int(weight_cb)}` کیلوگرم\n"
        response += f"🔹 وزن قیف بالا: `{int(weight_ct)}` کیلوگرم\n"
        response += f"🔹 وزن پایه‌ها: `{int(weight_supports)}` کیلوگرم\n"
        response += "-----------------------------------\n"
        response += f"🔸 **وزن کلی (بدون پرتی):** `{int(total_weight)}` کیلوگرم\n"
        response += f"🔸 **وزن کلی (با پرتی):** `{int(weight_with_waste)}` کیلوگرم\n\n"
        response += f"💰 **قیمت کل (با دستمزد):** `{int(total_price):,}` تومان"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        context.user_data.clear()
        return END

    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً دستمزد را به صورت یک عدد معتبر وارد کنید.")
        return TANK_PRICING_WAGE
    except Exception as e:
        await update.message.reply_text(f"یک خطای غیرمنتظره در محاسبات رخ داد: {e}")
        context.user_data.clear()
        return END

# --- محاسبه ابعاد مخزن ---

async def tank_calc_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    orient = query.data
    context.user_data['tank_c'] = {'orientation': orient}
    
    keyboard = [
        [InlineKeyboardButton("حجم (لیتر)", callback_data='volume')],
        [InlineKeyboardButton("طول بدنه (cm)", callback_data='length')],
        [InlineKeyboardButton("قطر بدنه (cm)", callback_data='diameter')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"مخزن {'عمودی' if orient == 'vertical' else 'افقی'} انتخاب شد.\n\n"
    text += "چه مقداری را می‌خواهید محاسبه کنید؟"
    await query.edit_message_text(text, reply_markup=reply_markup)
    return TANK_CALC_CHOICE

async def tank_calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    find = query.data
    context.user_data['tank_c']['find'] = find
    
    if find == 'volume':
        await query.edit_message_text("محاسبه حجم انتخاب شد.\n\nلطفاً قطر مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_DIAMETER
    elif find == 'length':
        await query.edit_message_text("محاسبه طول انتخاب شد.\n\nلطفاً قطر مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_DIAMETER
    elif find == 'diameter':
        await query.edit_message_text("محاسبه قطر انتخاب شد.\n\nلطفاً طول بدنه مخزن (cm) را وارد کنید:")
        return TANK_AWAITING_LENGTH
    return END

async def tank_calc_get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['tank_c']['diameter_m'] = val / 100
        find = context.user_data['tank_c']['find']
        if find == 'volume':
            await update.message.reply_text("✅ بسیار خب. طول بدنه مخزن (cm) را وارد کنید:")
            return TANK_AWAITING_LENGTH
        elif find == 'length':
            await update.message.reply_text("✅ بسیار خب. حجم کل مخزن (لیتر) را وارد کنید:")
            return TANK_AWAITING_VOLUME
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت یک عدد مثبت (cm) وارد کنید.")
        return TANK_AWAITING_DIAMETER
    return END

async def tank_calc_get_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['tank_c']['length_m'] = val / 100
        find = context.user_data['tank_c']['find']
        if find == 'volume':
            await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
            return TANK_AWAITING_BOTTOM_H
        elif find == 'diameter':
            await update.message.reply_text("✅ بسیار خب. حجم کل مخزن (لیتر) را وارد کنید:")
            return TANK_AWAITING_VOLUME
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً طول را به صورت یک عدد مثبت (cm) وارد کنید.")
        return TANK_AWAITING_LENGTH
    return END

async def tank_calc_get_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['tank_c']['volume_m3'] = val / 1000
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
        return TANK_AWAITING_BOTTOM_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً حجم را به صورت یک عدد مثبت (لیتر) وارد کنید.")
        return TANK_AWAITING_VOLUME
    return END
    
async def tank_calc_get_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['tank_c']['bottom_h_m'] = val / 100
        
        if context.user_data['tank_c']['orientation'] == 'vertical':
            context.user_data['tank_c']['top_h_m'] = 0
            return await tank_perform_calculation(update, context)
        else:
            await update.message.reply_text("✅ بسیار خب. ارتفاع قیف بالا/عقب (cm) را وارد کنید:")
            return TANK_AWAITING_TOP_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return TANK_AWAITING_BOTTOM_H

async def tank_calc_get_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['tank_c']['top_h_m'] = val / 100
        return await tank_perform_calculation(update, context)
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return TANK_AWAITING_TOP_H

async def tank_perform_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تابع نهایی برای انجام محاسبات ابعاد مخزن."""
    data = context.user_data['tank_c']
    find = data['find']
    
    try:
        if find == 'volume':
            r = data['diameter_m'] / 2
            L = data['length_m']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']
            
            vol_cyl = math.pi * r**2 * L
            vol_cone_b = (1/3) * math.pi * r**2 * h_b
            vol_cone_t = (1/3) * math.pi * r**2 * h_t
            
            total_vol_m3 = vol_cyl + vol_cone_b + vol_cone_t
            total_vol_liters = total_vol_m3 * 1000
            await update.message.reply_text(f"✅ **نتیجه:** حجم کل مخزن `{total_vol_liters:,.2f}` لیتر است.", parse_mode='Markdown')

        elif find == 'length':
            r = data['diameter_m'] / 2
            V = data['volume_m3']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']
            
            vol_cone_b = (1/3) * math.pi * r**2 * h_b
            vol_cone_t = (1/3) * math.pi * r**2 * h_t
            
            vol_cyl_needed = V - vol_cone_b - vol_cone_t
            if vol_cyl_needed < 0 or r == 0:
                await update.message.reply_text("خطا: با این ورودی‌ها، حجم قیف‌ها از حجم کل بیشتر است!")
            else:
                L_calc_m = vol_cyl_needed / (math.pi * r**2)
                await update.message.reply_text(f"✅ **نتیجه:** طول بدنه مخزن `{L_calc_m * 100:.2f}` سانتی‌متر است.", parse_mode='Markdown')

        elif find == 'diameter':
            L = data['length_m']
            V = data['volume_m3']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']

            denominator = math.pi * (L + h_b/3 + h_t/3)
            if denominator <= 0:
                await update.message.reply_text("خطا: با این ورودی‌ها محاسبه قطر ممکن نیست.")
            else:
                r_sq = V / denominator
                if r_sq < 0:
                    await update.message.reply_text("خطا: مقادیر ورودی منجر به قطر نامعتبر می‌شود.")
                else:
                    d_calc_m = 2 * math.sqrt(r_sq)
                    await update.message.reply_text(f"✅ **نتیجه:** قطر بدنه مخزن `{d_calc_m * 100:.2f}` سانتی‌متر است.", parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"یک خطای ناشناخته در محاسبه رخ داد: {e}")
        
    context.user_data.clear()
    return END


# ==============================================================================
# بخش دوم: منطق و توابع مربوط به سیلو (SILO)
# ==============================================================================

# --- محاسبه ابعاد سیلو ---

async def silo_calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    find = query.data
    context.user_data['silo_c']['find'] = find
    
    if find == 'capacity':
        await query.edit_message_text("محاسبه ظرفیت انتخاب شد.\n\nلطفاً قطر سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_DIAMETER
    elif find == 'length':
        await query.edit_message_text("محاسبه ارتفاع استوانه انتخاب شد.\n\nلطفاً قطر سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_DIAMETER
    elif find == 'diameter':
        await query.edit_message_text("محاسبه قطر انتخاب شد.\n\nلطفاً ارتفاع استوانه سیلو (cm) را وارد کنید:")
        return SILO_AWAITING_LENGTH
    return END

async def silo_calc_get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['silo_c']['diameter_m'] = val / 100
        find = context.user_data['silo_c']['find']
        if find == 'capacity':
            await update.message.reply_text("✅ بسیار خب. ارتفاع استوانه سیلو (cm) را وارد کنید:")
            return SILO_AWAITING_LENGTH
        elif find == 'length':
            await update.message.reply_text("✅ بسیار خب. ظرفیت کل سیلو (تُن) را وارد کنید:")
            return SILO_AWAITING_CAPACITY
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت یک عدد مثبت (cm) وارد کنید.")
        return SILO_AWAITING_DIAMETER
    return END

async def silo_calc_get_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['silo_c']['length_m'] = val / 100
        find = context.user_data['silo_c']['find']
        if find == 'capacity':
            await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
            return SILO_AWAITING_BOTTOM_H
        elif find == 'diameter':
            await update.message.reply_text("✅ بسیار خب. ظرفیت کل سیلو (تُن) را وارد کنید:")
            return SILO_AWAITING_CAPACITY
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت یک عدد مثبت (cm) وارد کنید.")
        return SILO_AWAITING_LENGTH
    return END

async def silo_calc_get_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        # Convert tons to kg, then to m^3
        context.user_data['silo_c']['volume_m3'] = (val * 1000) / CEMENT_DENSITY_KG_M3
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
        return SILO_AWAITING_BOTTOM_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ظرفیت را به صورت یک عدد مثبت (تُن) وارد کنید.")
        return SILO_AWAITING_CAPACITY
    return END
    
async def silo_calc_get_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['silo_c']['bottom_h_m'] = val / 100
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف بالا (cm) را وارد کنید:")
        return SILO_AWAITING_TOP_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return SILO_AWAITING_BOTTOM_H

async def silo_calc_get_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['silo_c']['top_h_m'] = val / 100
        return await silo_perform_calculation(update, context)
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return SILO_AWAITING_TOP_H

async def silo_perform_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تابع نهایی برای انجام محاسبات ابعاد سیلو."""
    data = context.user_data['silo_c']
    find = data['find']
    
    try:
        if find == 'capacity':
            r = data['diameter_m'] / 2
            L = data['length_m']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']
            
            vol_cyl = math.pi * r**2 * L
            vol_cone_b = (1/3) * math.pi * r**2 * h_b
            vol_cone_t = (1/3) * math.pi * r**2 * h_t
            
            total_vol_m3 = vol_cyl + vol_cone_b + vol_cone_t
            total_capacity_ton = (total_vol_m3 * CEMENT_DENSITY_KG_M3) / 1000
            await update.message.reply_text(f"✅ **نتیجه:** ظرفیت کل سیلو `{total_capacity_ton:,.2f}` تُن است.", parse_mode='Markdown')

        elif find == 'length':
            r = data['diameter_m'] / 2
            V = data['volume_m3']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']
            
            vol_cone_b = (1/3) * math.pi * r**2 * h_b
            vol_cone_t = (1/3) * math.pi * r**2 * h_t
            
            vol_cyl_needed = V - vol_cone_b - vol_cone_t
            if vol_cyl_needed < 0 or r == 0:
                await update.message.reply_text("خطا: حجم قیف‌ها از ظرفیت کل بیشتر است!")
            else:
                L_calc_m = vol_cyl_needed / (math.pi * r**2)
                await update.message.reply_text(f"✅ **نتیجه:** ارتفاع استوانه سیلو `{L_calc_m * 100:.2f}` سانتی‌متر است.", parse_mode='Markdown')

        elif find == 'diameter':
            L = data['length_m']
            V = data['volume_m3']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']

            denominator = math.pi * (L + h_b/3 + h_t/3)
            if denominator <= 0:
                await update.message.reply_text("خطا: با این ورودی‌ها محاسبه قطر ممکن نیست.")
            else:
                r_sq = V / denominator
                if r_sq < 0:
                    await update.message.reply_text("خطا: مقادیر ورودی منجر به قطر نامعتبر می‌شود.")
                else:
                    d_calc_m = 2 * math.sqrt(r_sq)
                    await update.message.reply_text(f"✅ **نتیجه:** قطر سیلو `{d_calc_m * 100:.2f}` سانتی‌متر است.", parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"یک خطای ناشناخته در محاسبه رخ داد: {e}")
        
    context.user_data.clear()
    return END


# --- قیمت‌گذاری سیلو ---
# This is a long chain of functions. Each one asks for a piece of data.

async def silo_pricing_step(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, prompt: str, next_state: int, current_state: int, is_int: bool = False) -> int:
    """A generic function to handle a pricing step."""
    try:
        value_str = update.message.text
        value = int(value_str) if is_int else float(value_str)
        if value < 0: raise ValueError
        context.user_data['silo_p'][field] = value
        await update.message.reply_text(prompt)
        return next_state
    except (ValueError, TypeError):
        error_msg = f"خطا: لطفاً یک عدد {'صحیح' if is_int else ''} معتبر وارد کنید."
        await update.message.reply_text(error_msg)
        return current_state

# We define a handler for each step to call the generic function
async def silo_pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'diameter_cm', "✅ قطر سیلو. ارتفاع استوانه (cm) را وارد کنید:", SILO_PRICING_HEIGHT, SILO_PRICING_DIAMETER)
async def silo_pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'height_cm', "✅ ارتفاع استوانه. ضخامت استوانه (mm) را وارد کنید:", SILO_PRICING_THICKNESS_CYL, SILO_PRICING_HEIGHT)
async def silo_pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'thickness_cyl_mm', "✅ ضخامت استوانه. ارتفاع قیف پایین (cm) را وارد کنید:", SILO_PRICING_CONE_BOTTOM_H, SILO_PRICING_THICKNESS_CYL)
async def silo_pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'cone_bottom_h_cm', "✅ ارتفاع قیف پایین. ضخامت قیف پایین (mm) را وارد کنید:", SILO_PRICING_CONE_BOTTOM_THICK, SILO_PRICING_CONE_BOTTOM_H)
async def silo_pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'cone_bottom_thick_mm', "✅ ضخامت قیف پایین. ارتفاع قیف بالا (cm) را وارد کنید:", SILO_PRICING_CONE_TOP_H, SILO_PRICING_CONE_BOTTOM_THICK)
async def silo_pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'cone_top_h_cm', "✅ ارتفاع قیف بالا. ضخامت قیف بالا (mm) را وارد کنید:", SILO_PRICING_CONE_TOP_THICK, SILO_PRICING_CONE_TOP_H)
async def silo_pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'cone_top_thick_mm', "✅ ضخامت قیف بالا. ارتفاع نردبان بدون حفاظ (m) را وارد کنید:", SILO_PRICING_LADDER_NO_CAGE_H, SILO_PRICING_CONE_TOP_THICK)
async def silo_pricing_ladder_no_cage_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'ladder_no_cage_h_m', "✅ نردبان بدون حفاظ. ارتفاع نردبان با حفاظ (m) را وارد کنید:", SILO_PRICING_LADDER_CAGE_H, SILO_PRICING_LADDER_NO_CAGE_H)
async def silo_pricing_ladder_cage_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'ladder_cage_h_m', "✅ نردبان با حفاظ. تعداد پایه‌ها را وارد کنید (برای محاسبه دقیق بادبند و کلاف، ۴ فرض می‌شود):", SILO_PRICING_SUPPORT_COUNT, SILO_PRICING_LADDER_CAGE_H)
async def silo_pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'support_count', "✅ تعداد پایه‌ها. ارتفاع هر پایه (cm) را وارد کنید:", SILO_PRICING_SUPPORT_HEIGHT, SILO_PRICING_SUPPORT_COUNT, is_int=True)
async def silo_pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'support_height_cm', "✅ ارتفاع پایه‌ها. قطر هر پایه (inch) را وارد کنید:", SILO_PRICING_SUPPORT_DIAMETER, SILO_PRICING_SUPPORT_HEIGHT)
async def silo_pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'support_diameter_inch', "✅ قطر پایه‌ها. ضخامت هر پایه (mm) را وارد کنید:", SILO_PRICING_SUPPORT_THICKNESS, SILO_PRICING_SUPPORT_DIAMETER)
async def silo_pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'support_thickness_mm', "✅ ضخامت پایه‌ها. تعداد ردیف کلاف‌ها را وارد کنید:", SILO_PRICING_KALLAF_ROWS, SILO_PRICING_SUPPORT_THICKNESS)
async def silo_pricing_kallaf_rows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'kallaf_rows', "✅ تعداد ردیف کلاف. قطر لوله کلاف (inch) را وارد کنید:", SILO_PRICING_KALLAF_DIAMETER, SILO_PRICING_KALLAF_ROWS, is_int=True)
async def silo_pricing_kallaf_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'kallaf_diameter_inch', "✅ قطر کلاف. ضخامت لوله کلاف (mm) را وارد کنید:", SILO_PRICING_KALLAF_THICKNESS, SILO_PRICING_KALLAF_DIAMETER)
async def silo_pricing_kallaf_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'kallaf_thickness_mm', "✅ ضخامت کلاف. قطر لوله بادبند (inch) را وارد کنید:", SILO_PRICING_BADBAND_DIAMETER, SILO_PRICING_KALLAF_THICKNESS)
async def silo_pricing_badband_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'badband_diameter_inch', "✅ قطر بادبند. ضخامت لوله بادبند (mm) را وارد کنید:", SILO_PRICING_BADBAND_THICKNESS, SILO_PRICING_BADBAND_DIAMETER)
async def silo_pricing_badband_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'badband_thickness_mm', "✅ ضخامت بادبند. درصد پرتی ورق (%) را وارد کنید:", SILO_PRICING_WASTE, SILO_PRICING_BADBAND_THICKNESS)
async def silo_pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await silo_pricing_step(update, context, 'waste_percent', "✅ درصد پرتی. دستمزد ساخت (تومان به ازای هر کیلوگرم) را وارد کنید:", SILO_PRICING_WAGE, SILO_PRICING_WASTE)

async def silo_pricing_final_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محاسبه نهایی وزن و قیمت سیلو و ارسال نتیجه."""
    try:
        wage_per_kg = float(update.message.text)
        if wage_per_kg < 0: raise ValueError
        data = context.user_data['silo_p']

        # --- ۱. محاسبه وزن بدنه و قیف‌ها ---
        d_m = data['diameter_cm'] / 100
        radius_m = d_m / 2
        h_cyl_m = data['height_cm'] / 100
        t_cyl_m = data['thickness_cyl_mm'] / 1000
        h_cb_m = data['cone_bottom_h_cm'] / 100
        t_cb_m = data['cone_bottom_thick_mm'] / 1000
        h_ct_m = data['cone_top_h_cm'] / 100
        t_ct_m = data['cone_top_thick_mm'] / 1000

        weight_cyl = (math.pi * d_m * h_cyl_m) * t_cyl_m * STEEL_DENSITY_KG_M3
        
        weight_cb = 0
        if h_cb_m > 0:
            slant_cb = math.sqrt(radius_m**2 + h_cb_m**2)
            area_cb = math.pi * radius_m * slant_cb
            weight_cb = area_cb * t_cb_m * STEEL_DENSITY_KG_M3

        weight_ct = 0
        if h_ct_m > 0:
            slant_ct = math.sqrt(radius_m**2 + h_ct_m**2)
            area_ct = math.pi * radius_m * slant_ct
            weight_ct = area_ct * t_ct_m * STEEL_DENSITY_KG_M3
        
        weight_body = weight_cyl + weight_cb + weight_ct

        # --- ۲. محاسبه وزن نردبان‌ها ---
        # فرض: پله‌ها به عرض ۴۰ سانتی‌متر و با فاصله ۳۰ سانتی‌متر از هم هستند
        # لوله عمودی: قطر ۳ سانت (۱.۱۸ اینچ)، ضخامت ۲ میل. پله: قطر ۲ سانت (۰.۷۸ اینچ)، ضخامت ۲ میل
        weight_ladder_no_cage = 0
        if data['ladder_no_cage_h_m'] > 0:
            h = data['ladder_no_cage_h_m']
            num_rungs = math.ceil(h / 0.30)
            weight_vertical_pipes = _calculate_pipe_weight(h * 2, 1.18, 2)
            weight_rungs = _calculate_pipe_weight(num_rungs * 0.4, 0.78, 2)
            weight_ladder_no_cage = weight_vertical_pipes + weight_rungs

        # فرض: حفاظ از ۳ تسمه عمودی و حلقه‌هایی با قطر ۷۰ سانت در هر ۱.۵ متر تشکیل شده
        # تسمه: عرض ۴ سانت، ضخامت ۳ میل
        weight_ladder_cage = 0
        if data['ladder_cage_h_m'] > 0:
            h = data['ladder_cage_h_m']
            num_rungs = math.ceil(h / 0.30)
            weight_vertical_pipes = _calculate_pipe_weight(h * 2, 1.18, 2)
            weight_rungs = _calculate_pipe_weight(num_rungs * 0.4, 0.78, 2)
            
            num_hoops = math.ceil(h / 1.5)
            hoop_len = math.pi * 0.7 
            weight_cage_straps = _calculate_strap_weight(h * 3, 4, 3) # 3 vertical straps
            weight_cage_hoops = _calculate_strap_weight(num_hoops * hoop_len, 4, 3)
            weight_ladder_cage = weight_vertical_pipes + weight_rungs + weight_cage_straps + weight_cage_hoops

        # --- ۳. محاسبه وزن پایه‌ها ---
        weight_supports = 0
        if data['support_count'] > 0:
            h = data['support_height_cm'] / 100
            d_inch = data['support_diameter_inch']
            t_mm = data['support_thickness_mm']
            weight_one_support = _calculate_pipe_weight(h, d_inch, t_mm)
            weight_supports = weight_one_support * data['support_count']

        # --- ۴. محاسبه وزن کلاف و بادبند ---
        # فرض کلیدی: محاسبات برای ۴ پایه است.
        weight_kallaf = 0
        weight_badband = 0
        if data['kallaf_rows'] > 0:
            # فاصله بین دو پایه مجاور در یک مربع محاط در دایره به قطر d_m
            dist_between_legs = d_m * math.sin(math.pi / 4) * math.sqrt(2) # Simplified to d_m / sqrt(2) * sqrt(2) = d_m
            dist_between_legs = d_m / math.sqrt(2) # Correct calculation for inscribed square side

            # کلاف: ۴ لوله افقی در هر ردیف
            len_kallaf_per_row = 4 * dist_between_legs
            weight_kallaf_per_row = _calculate_pipe_weight(len_kallaf_per_row, data['kallaf_diameter_inch'], data['kallaf_thickness_mm'])
            weight_kallaf = weight_kallaf_per_row * data['kallaf_rows']

            # بادبند: ۸ عدد ضربدری بین هر دو ردیف کلاف
            if data['kallaf_rows'] > 1:
                len_badband = math.sqrt(dist_between_legs**2 + 3**2) # فاصله عمودی کلاف‌ها ۳ متر است
                weight_one_badband = _calculate_pipe_weight(len_badband, data['badband_diameter_inch'], data['badband_thickness_mm'])
                num_badband_sets = data['kallaf_rows'] - 1
                weight_badband = weight_one_badband * 8 * num_badband_sets

        # --- ۵. محاسبه نهایی ---
        total_weight = (weight_body + weight_ladder_no_cage + weight_ladder_cage + 
                        weight_supports + weight_kallaf + weight_badband)
        weight_with_waste = total_weight * (1 + data['waste_percent'] / 100)
        total_price = weight_with_waste * wage_per_kg

        response = "📊 **نتایج قیمت‌گذاری سیلو** 📊\n\n"
        response += f"🔹 وزن بدنه و قیف‌ها: `{int(weight_body)}` کیلوگرم\n"
        response += f"🔹 وزن نردبان بدون حفاظ: `{int(weight_ladder_no_cage)}` کیلوگرم\n"
        response += f"🔹 وزن نردبان با حفاظ: `{int(weight_ladder_cage)}` کیلوگرم\n"
        response += f"🔹 وزن پایه‌ها: `{int(weight_supports)}` کیلوگرم\n"
        response += f"🔹 وزن کلاف‌ها: `{int(weight_kallaf)}` کیلوگرم\n"
        response += f"🔹 وزن بادبندها: `{int(weight_badband)}` کیلوگرم\n"
        response += "-----------------------------------\n"
        response += f"🔸 **وزن کلی (بدون پرتی):** `{int(total_weight)}` کیلوگرم\n"
        response += f"🔸 **وزن کلی (با پرتی):** `{int(weight_with_waste)}` کیلوگرم\n\n"
        response += f"💰 **قیمت کل (با دستمزد):** `{int(total_price):,}` تومان"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        context.user_data.clear()
        return END

    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً دستمزد را به صورت یک عدد معتبر وارد کنید.")
        return SILO_PRICING_WAGE
    except Exception as e:
        await update.message.reply_text(f"یک خطای غیرمنتظره در محاسبات رخ داد: {e}")
        context.user_data.clear()
        return END


# ==============================================================================
# تابع لغو و تنظیمات اصلی برنامه
# ==============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a user-friendly message."""
    print(f"Update '{update}' caused error '{context.error}'")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass your bot's token.
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Define a ConversationHandler for all the logic
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_COMPONENT: [
                CallbackQueryHandler(select_component, pattern="^component_(tank|silo)$")
            ],
            SELECTING_TASK: [
                CallbackQueryHandler(select_task, pattern="^task_(pricing|calc)$|^back_to_start$")
            ],
            # --- Tank Pricing Handlers ---
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

            # --- Tank Calc Handlers ---
            TANK_CALC_ORIENTATION: [CallbackQueryHandler(tank_calc_orientation, pattern="^(vertical|horizontal)$")],
            TANK_CALC_CHOICE: [CallbackQueryHandler(tank_calc_choice, pattern="^(volume|length|diameter)$")],
            TANK_AWAITING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_diameter)],
            TANK_AWAITING_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_length)],
            TANK_AWAITING_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_volume)],
            TANK_AWAITING_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_bottom_h)],
            TANK_AWAITING_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_calc_get_top_h)],
            
            # --- Silo Calc Handlers ---
            SILO_CALC_CHOICE: [CallbackQueryHandler(silo_calc_choice, pattern="^(capacity|length|diameter)$")],
            SILO_AWAITING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_diameter)],
            SILO_AWAITING_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_length)],
            SILO_AWAITING_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_capacity)],
            SILO_AWAITING_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_bottom_h)],
            SILO_AWAITING_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_calc_get_top_h)],
            
            # Add other Silo pricing handlers here once you write them
            SILO_PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ...)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    # Start the bot in webhook mode
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
