#!/usr/bin/env python3
# coding: utf-8

import os
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# -------------------------
# ثابت‌ها و مراحل گفتگو
# -------------------------
STEEL_DENSITY = 7850.0  # kg/m^3 (چگالی آهن سیاه / فولاد)

# مراحل اصلی
CHOOSING_PRODUCT = 0

# مخزن (بدون تغییر در منطق)
TANK_THICKNESS, TANK_DIAMETER, TANK_HEIGHT, TANK_CONE_TOP_CM, TANK_CONE_BOTTOM_CM, TANK_WASTE_PERCENT, TANK_WAGE = range(10, 17)

# سیلو (بدون تغییر در منطق)
SILO_DIAMETER_M, SILO_HEIGHT_M, SILO_CAPACITY_TON, SILO_FRAMES, SILO_BRACES, SILO_WASTE_PERCENT, SILO_WAGE = range(20, 27)

# اسکرو کانوایر (واحدها: اینچ/میلیمتر/سانتی‌متر)
(
    SCREW_LENGTH_CM,
    SCREW_OUTER_DIAMETER_INCH,
    SCREW_OUTER_THICKNESS_MM,
    SCREW_SHAFT_OUTER_DIAMETER_INCH,
    SCREW_SHAFT_THICKNESS_MM,
    SCREW_PITCH_CM,
    SCREW_BLADE_THICKNESS_MM,
    TRANS_SHAFT_DIAMETER_INCH,      # کاربر وارد می‌کند (در پیام سؤال، پیشنهاد نشان داده می‌شود)
    TRANS_SHAFT_LENGTH_CM,
    TRANS_SHAFT_PRICE_PER_KG,       # اکنون قیمت به ازای هر کیلو (تومان/kg)
    SCREW_MOTOR_PRICE,
    SCREW_LATHE_WAGE,
    SCREW_LABOR_PER_KG,
) = range(30, 43)

CALLBACK_RESTART = "restart"

# -------------------------
# توابع کمکی تبدیل واحد
# -------------------------
def inch_to_meter(inch: float) -> float:
    return inch * 0.0254

def mm_to_meter(mm: float) -> float:
    return mm / 1000.0

def cm_to_meter(cm: float) -> float:
    return cm / 100.0

def fmt(n) -> str:
    """قالب‌بندی عدد با جداکننده هزارگان (برای int و float)."""
    try:
        if isinstance(n, int):
            return f"{n:,}"
        else:
            # اگر تقریباً عدد صحیح بود، بدون اعشار نمایش می‌دهیم
            if abs(n - round(n)) < 1e-6:
                return f"{int(round(n)):,}"
            return f"{n:,.2f}"
    except:
        return str(n)

# وزن پوسته استوانه‌ای (حجم پوسته × چگالی)، outer_d_m قطر خارجی و thickness_m ضخامت ورق
def cylindrical_shell_weight(outer_d_m: float, thickness_m: float, length_m: float) -> float:
    r_out = outer_d_m / 2.0
    r_in = max(r_out - thickness_m, 0.0)
    volume = math.pi * (r_out**2 - r_in**2) * length_m
    return volume * STEEL_DENSITY  # kg

# وزن استوانه توپر (برای شفت ترانس)
def solid_cylinder_weight(diameter_m: float, length_m: float) -> float:
    r = diameter_m / 2.0
    volume = math.pi * r**2 * length_m
    return volume * STEEL_DENSITY  # kg

# وزن تیغه ماردون (تقریبی: ضخامت × محیط(2πr_blade) × طول)
def screw_blade_weight(blade_thickness_m: float, blade_radius_m: float, length_m: float) -> float:
    if blade_thickness_m <= 0 or blade_radius_m <= 0 or length_m <= 0:
        return 0.0
    circumference = 2.0 * math.pi * blade_radius_m
    volume = blade_thickness_m * circumference * length_m
    return volume * STEEL_DENSITY

# -------------------------
# هندلرها
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """صفحهٔ اصلی: انتخاب محصول"""
    keyboard = [
        [InlineKeyboardButton("🛢️ مخزن", callback_data="tank")],
        [InlineKeyboardButton("🌾 سیلو", callback_data="silo")],
        [InlineKeyboardButton("⚙️ اسکرو کانوایر", callback_data="screw")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("👋 سلام! کدام محاسبه را می‌خواهی انجام دهی؟", reply_markup=reply_markup)
    else:
        # اگر از callback (مثلاً restart) آمده
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("👋 سلام! کدام محاسبه را می‌خواهی انجام دهی؟", reply_markup=reply_markup)
    return CHOOSING_PRODUCT

async def choose_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data.clear()
    context.user_data['product'] = choice

    if choice == "tank":
        await query.message.reply_text("🛠️ وارد بخش **مخزن** شدی.\nلطفاً ضخامت بدنه مخزن را به **میلیمتر** وارد کن:")
        return TANK_THICKNESS
    elif choice == "silo":
        await query.message.reply_text("🛠️ وارد بخش **سیلو** شدی.\nلطفاً قطر سیلو را به **متر** وارد کن:")
        return SILO_DIAMETER_M
    elif choice == "screw":
        await query.message.reply_text("⚙️ وارد بخش **اسکرو کانوایر** شدی.\nلطفاً طول اسکرو را به **سانتی‌متر** وارد کن:")
        return SCREW_LENGTH_CM
    else:
        await query.message.reply_text("❌ انتخاب نامعتبر. لطفاً /start را بزن.")
        return ConversationHandler.END

# -------------------------
# ----- مخزن (بدون تغییر) -----
# -------------------------
async def tank_thickness_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0:
            raise ValueError
        context.user_data['tank_thickness_mm'] = v
        await update.message.reply_text("📏 قطر بدنه مخزن را به **متر** وارد کن:")
        return TANK_DIAMETER
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — لطفاً ضخامت را به میلی‌متر (عدد مثبت) وارد کن:")
        return TANK_THICKNESS

async def tank_diameter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['tank_diameter_m'] = v
        await update.message.reply_text("📐 ارتفاع بدنه مخزن را به **متر** وارد کن:")
        return TANK_HEIGHT
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قطر را به متر وارد کن:")
        return TANK_DIAMETER

async def tank_height_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['tank_height_m'] = v
        await update.message.reply_text("🔻 ارتفاع قیف بالای مخزن را به **سانتی‌متر** وارد کن (اگر ندارد 0):")
        return TANK_CONE_TOP_CM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ارتفاع را به متر وارد کن:")
        return TANK_HEIGHT

async def tank_cone_top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['tank_cone_top_cm'] = v
        await update.message.reply_text("🔺 ارتفاع قیف پایین مخزن را به **سانتی‌متر** وارد کن (اگر ندارد 0):")
        return TANK_CONE_BOTTOM_CM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ارتفاع قیف را به سانتی‌متر وارد کن:")
        return TANK_CONE_TOP_CM

async def tank_cone_bottom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['tank_cone_bottom_cm'] = v
        await update.message.reply_text("📦 درصد پرتی فولاد را وارد کن (مثلاً 5 برای ۵٪):")
        return TANK_WASTE_PERCENT
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ارتفاع قیف را به سانتی‌متر وارد کن:")
        return TANK_CONE_BOTTOM_CM

async def tank_waste_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['tank_waste_percent'] = v
        await update.message.reply_text("💰 دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کن:")
        return TANK_WAGE
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — درصد پرتی را وارد کن:")
        return TANK_WASTE_PERCENT

async def tank_wage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = float(update.message.text.strip())
        if wage < 0: raise ValueError

        d_m = context.user_data['tank_diameter_m']
        thickness_m = mm_to_meter(context.user_data['tank_thickness_mm'])
        height_m = context.user_data['tank_height_m']
        cone_top_m = cm_to_meter(context.user_data.get('tank_cone_top_cm', 0.0))
        cone_bottom_m = cm_to_meter(context.user_data.get('tank_cone_bottom_cm', 0.0))
        waste = context.user_data['tank_waste_percent']

        # محاسبات
        weight_body = cylindrical_shell_weight(d_m, thickness_m, height_m)
        r = d_m / 2.0
        vol_cone_top = (math.pi * r**2 * cone_top_m) / 3.0
        vol_cone_bottom = (math.pi * r**2 * cone_bottom_m) / 3.0
        weight_cone_top = vol_cone_top * thickness_m * STEEL_DENSITY
        weight_cone_bottom = vol_cone_bottom * thickness_m * STEEL_DENSITY

        total_weight = weight_body + weight_cone_top + weight_cone_bottom
        total_weight_with_waste = total_weight * (1.0 + waste / 100.0)
        price = int(total_weight_with_waste * wage)

        text = (
            f"✅ نتایج محاسبه مخزن:\n\n"
            f"🏷️ وزن (بدون پرتی): {fmt(total_weight)} kg\n"
            f"📦 وزن (با پرتی {fmt(waste)}%): {fmt(total_weight_with_waste)} kg\n"
            f"💵 قیمت ساخت: {fmt(price)} تومان\n"
        )
        keyboard = [[InlineKeyboardButton("🔄 شروع دوباره", callback_data=CALLBACK_RESTART)]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — لطفاً عدد معتبر برای دستمزد وارد کن:")
        return TANK_WAGE

# -------------------------
# ----- سیلو (بدون تغییر منطق اصلی) -----
# -------------------------
async def silo_diameter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['silo_diameter_m'] = v
        await update.message.reply_text("📐 ارتفاع سیلو را به **متر** وارد کن:")
        return SILO_HEIGHT_M
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قطر را به متر وارد کن:")
        return SILO_DIAMETER_M

async def silo_height_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['silo_height_m'] = v
        await update.message.reply_text("⚖️ ظرفیت سیلو را به **تن** وارد کن:")
        return SILO_CAPACITY_TON
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ارتفاع را به متر وارد کن:")
        return SILO_HEIGHT_M

async def silo_capacity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        context.user_data['silo_capacity_ton'] = v
        await update.message.reply_text("🔧 تعداد کلاف‌ها (عدد) را وارد کن:")
        return SILO_FRAMES
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ظرفیت را به تن وارد کن:")
        return SILO_CAPACITY_TON

async def silo_frames_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = int(update.message.text.strip())
        context.user_data['silo_frames'] = v
        await update.message.reply_text("🔧 تعداد بادبندها (عدد) را وارد کن:")
        return SILO_BRACES
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — تعداد کلاف را عدد صحیح وارد کن:")
        return SILO_FRAMES

async def silo_braces_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = int(update.message.text.strip())
        context.user_data['silo_braces'] = v
        await update.message.reply_text("📦 درصد پرتی فولاد (%) را وارد کن:")
        return SILO_WASTE_PERCENT
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — تعداد بادبند را عدد صحیح وارد کن:")
        return SILO_BRACES

async def silo_waste_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['silo_waste_percent'] = v
        await update.message.reply_text("💰 دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کن:")
        return SILO_WAGE
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — درصد پرتی را وارد کن:")
        return SILO_WASTE_PERCENT

async def silo_wage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = float(update.message.text.strip())
        # محاسبات ساده مشابه نسخهٔ قبلی (منطق دست‌نخورده)
        d = context.user_data['silo_diameter_m']
        h = context.user_data['silo_height_m']
        frames = context.user_data.get('silo_frames', 0)
        braces = context.user_data.get('silo_braces', 0)
        waste = context.user_data['silo_waste_percent']

        thickness_m = 0.005  # فرضی (نگه‌داشته شده از منطق قبلی)
        body_weight = cylindrical_shell_weight(d, thickness_m, h)
        frame_weight_each = 100.0
        brace_weight_each = 50.0
        total_weight = body_weight + frames * frame_weight_each + braces * brace_weight_each
        total_weight_with_waste = total_weight * (1.0 + waste / 100.0)
        price = int(total_weight_with_waste * wage)

        text = (
            f"✅ نتایج محاسبه سیلو:\n\n"
            f"⚖️ وزن بدون پرتی: {fmt(total_weight)} kg\n"
            f"📦 وزن با پرتی ({fmt(waste)}%): {fmt(total_weight_with_waste)} kg\n"
            f"💵 قیمت ساخت: {fmt(price)} تومان\n"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 شروع دوباره", callback_data=CALLBACK_RESTART)]]))
        return ConversationHandler.END
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — لطفاً عدد معتبر وارد کن:")
        return SILO_WAGE

# -------------------------
# ----- اسکرو کانوایر (جدید و دقیق) -----
# -------------------------
async def screw_length_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['screw_length_cm'] = v
        await update.message.reply_text("📏 قطر بدنه اسکرو (بیرونی) را به **اینچ** وارد کن (مثلاً 8):")
        return SCREW_OUTER_DIAMETER_INCH
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — طول را به سانتی‌متر وارد کن:")
        return SCREW_LENGTH_CM

async def screw_outer_diameter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['screw_outer_d_inch'] = v
        await update.message.reply_text("🔩 ضخامت بدنه اسکرو را به **میلیمتر** وارد کن (مثلاً 6):")
        return SCREW_OUTER_THICKNESS_MM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قطر را به اینچ وارد کن:")
        return SCREW_OUTER_DIAMETER_INCH

async def screw_outer_thickness_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['screw_outer_thickness_mm'] = v
        await update.message.reply_text("🔩 قطر شفت وسط (outer diameter) را به **اینچ** وارد کن (مثلاً 3):")
        return SCREW_SHAFT_OUTER_DIAMETER_INCH
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ضخامت بدنه را میلی‌متر وارد کن:")
        return SCREW_OUTER_THICKNESS_MM

async def screw_shaft_outer_d_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['screw_shaft_outer_d_inch'] = v
        await update.message.reply_text("🔩 ضخامت دیواره شفت وسط را به **میلیمتر** وارد کن (برای شفت لوله‌ای):")
        return SCREW_SHAFT_THICKNESS_MM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قطر شفت را به اینچ وارد کن:")
        return SCREW_SHAFT_OUTER_DIAMETER_INCH

async def screw_shaft_thickness_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['screw_shaft_thickness_mm'] = v
        await update.message.reply_text("📐 گام (Pitch) ماردون را به **سانتی‌متر** وارد کن (فاصله بین دورها):")
        return SCREW_PITCH_CM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ضخامت شفت را میلی‌متر وارد کن:")
        return SCREW_SHAFT_THICKNESS_MM

async def screw_pitch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['screw_pitch_cm'] = v
        await update.message.reply_text("🔧 ضخامت تیغه ماردون را به **میلیمتر** وارد کن:")
        return SCREW_BLADE_THICKNESS_MM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — گام را به سانتی‌متر وارد کن:")
        return SCREW_PITCH_CM

async def screw_blade_thickness_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['screw_blade_thickness_mm'] = v

        # محاسبه شعاع‌های داخلی و پیشنهاد قطر شفت ترانس
        outer_pipe_d_m = inch_to_meter(context.user_data['screw_outer_d_inch'])
        pipe_thickness_m = mm_to_meter(context.user_data['screw_outer_thickness_mm'])
        pipe_inner_radius_m = outer_pipe_d_m / 2.0 - pipe_thickness_m

        shaft_outer_d_m = inch_to_meter(context.user_data['screw_shaft_outer_d_inch'])
        shaft_outer_radius_m = shaft_outer_d_m / 2.0
        shaft_thickness_m = mm_to_meter(context.user_data['screw_shaft_thickness_mm'])
        shaft_inner_radius_m = max(shaft_outer_radius_m - shaft_thickness_m, 0.0)

        # پیشنهاد قطر شفت ترانس = قطر داخلی لوله شفت (به اینچ برای نمایش به کاربر)
        suggested_trans_shaft_d_m = shaft_inner_radius_m * 2.0
        suggested_trans_shaft_d_inch = suggested_trans_shaft_d_m / 0.0254 if suggested_trans_shaft_d_m > 0 else 0.0

        # پیام: هنگام پرسیدن قطر شفت ترانس، پیشنهاد را نشان می‌دهیم
        msg = (
            f"📐 پیشنهاد قطر شفت ترانس (برابر قطر داخلی لوله شفت): {fmt(round(suggested_trans_shaft_d_inch, 3))} inch\n\n"
            f"📏 حالا قطر شفت ترانس را به **اینچ** وارد کن (اگر می‌خواهی پیشنهاد را بپذیری، همان مقدار را وارد کن):"
        )
        await update.message.reply_text(msg)
        return TRANS_SHAFT_DIAMETER_INCH
    except Exception:
        await update.message.reply_text("⚠️ مقدار نامعتبر — ضخامت تیغه را میلی‌متر وارد کن:")
        return SCREW_BLADE_THICKNESS_MM

async def trans_shaft_diameter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['trans_shaft_d_inch'] = v
        await update.message.reply_text("📏 طول شفت ترانس را به **سانتی‌متر** وارد کن:")
        return TRANS_SHAFT_LENGTH_CM
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قطر شفت ترانس را به اینچ وارد کن:")
        return TRANS_SHAFT_DIAMETER_INCH

async def trans_shaft_length_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v <= 0: raise ValueError
        context.user_data['trans_shaft_length_cm'] = v
        await update.message.reply_text("💰 قیمت شفت ترانس را به **تومان به ازای هر کیلوگرم** وارد کن (مثلاً 12000):")
        return TRANS_SHAFT_PRICE_PER_KG
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — طول را به سانتی‌متر وارد کن:")
        return TRANS_SHAFT_LENGTH_CM

async def trans_shaft_price_per_kg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['trans_shaft_price_per_kg'] = v
        await update.message.reply_text("💰 قیمت موتور/گیربکس را به **تومان** وارد کن:")
        return SCREW_MOTOR_PRICE
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قیمت شفت ترانس را به تومان/کیلو وارد کن:")
        return TRANS_SHAFT_PRICE_PER_KG

async def screw_motor_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['screw_motor_price'] = v
        await update.message.reply_text("💰 اجرت تراشکار را به **تومان** وارد کن:")
        return SCREW_LATHE_WAGE
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — قیمت موتور را به تومان وارد کن:")
        return SCREW_MOTOR_PRICE

async def screw_lathe_wage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.strip())
        if v < 0: raise ValueError
        context.user_data['screw_lathe_wage'] = v
        await update.message.reply_text("💸 دستمزد ساخت را به ازای هر کیلوگرم (تومان/kg) وارد کن:")
        return SCREW_LABOR_PER_KG
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر — اجرت تراشکار را به تومان وارد کن:")
        return SCREW_LATHE_WAGE

async def screw_labor_per_kg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        labor = float(update.message.text.strip())
        if labor < 0: raise ValueError
        context.user_data['screw_labor_per_kg'] = labor

        # ---------- محاسبات ----------
        length_m = cm_to_meter(context.user_data['screw_length_cm'])
        outer_d_m = inch_to_meter(context.user_data['screw_outer_d_inch'])
        outer_thickness_m = mm_to_meter(context.user_data['screw_outer_thickness_mm'])
        shaft_outer_d_m = inch_to_meter(context.user_data['screw_shaft_outer_d_inch'])
        shaft_thickness_m = mm_to_meter(context.user_data['screw_shaft_thickness_mm'])
        pitch_m = cm_to_meter(context.user_data['screw_pitch_cm'])
        blade_thickness_m = mm_to_meter(context.user_data['screw_blade_thickness_mm'])

        # محاسبه شعاع‌ها
        pipe_outer_radius = outer_d_m / 2.0
        pipe_inner_radius = max(pipe_outer_radius - outer_thickness_m, 0.0)

        shaft_outer_radius = shaft_outer_d_m / 2.0
        shaft_inner_radius = max(shaft_outer_radius - shaft_thickness_m, 0.0)

        # شعاع تیغه = شعاع داخلی لوله بدنه − شعاع بیرونی شفت
        blade_radius_m = pipe_inner_radius - shaft_outer_radius

        if blade_radius_m <= 0:
            await update.message.reply_text(
                "❌ فضای بین شفت و لوله بدنه کافی نیست (شعاع تیغه ≤ 0). لطفاً ورودی‌ها را بازبینی کن."
            )
            return ConversationHandler.END

        # وزن‌ها
        pipe_shell_weight = cylindrical_shell_weight(outer_d_m, outer_thickness_m, length_m)  # kg
        shaft_weight = cylindrical_shell_weight(shaft_outer_d_m, shaft_thickness_m, length_m)   # kg
        blade_weight = screw_blade_weight(blade_thickness_m, blade_radius_m, length_m)         # kg

        total_weight_kg = pipe_shell_weight + shaft_weight + blade_weight

        # وزن و هزینه شفت ترانس (استوانه توپر)
        trans_d_inch = context.user_data.get('trans_shaft_d_inch')
        trans_length_m = cm_to_meter(context.user_data.get('trans_shaft_length_cm', 0.0))
        trans_price_per_kg = context.user_data.get('trans_shaft_price_per_kg', 0.0)

        # اگر کاربر قطر شفت ترانس را وارد نکرده به 0 پیش‌فرض می‌شود (نباید، چون قبلاً پرسیده شده)
        if trans_d_inch is None:
            trans_weight_kg = 0.0
            trans_total_price = 0.0
        else:
            trans_d_m = inch_to_meter(trans_d_inch)
            trans_weight_kg = solid_cylinder_weight(trans_d_m, trans_length_m)
            trans_total_price = trans_weight_kg * trans_price_per_kg

        motor_price = context.user_data.get('screw_motor_price', 0.0)
        lathe_wage = context.user_data.get('screw_lathe_wage', 0.0)
        labor_per_kg = context.user_data['screw_labor_per_kg']

        total_price = int(total_weight_kg * labor_per_kg + motor_price + lathe_wage + trans_total_price)

        # نمایش نتایج — شعاع تیغه به سانتی‌متر
        blade_radius_cm = blade_radius_m * 100.0

        text = (
            f"✅ نتایج محاسبه اسکرو کانوایر:\n\n"
            f"📏 طول اسکرو: {fmt(context.user_data['screw_length_cm'])} cm\n"
            f"🔘 قطر بدنه (بیرونی): {fmt(context.user_data['screw_outer_d_inch'])} inch\n"
            f"🔩 ضخامت بدنه: {fmt(context.user_data['screw_outer_thickness_mm'])} mm\n"
            f"🔧 قطر شفت (بیرونی): {fmt(context.user_data['screw_shaft_outer_d_inch'])} inch\n"
            f"⚙️ ضخامت شفت: {fmt(context.user_data['screw_shaft_thickness_mm'])} mm\n"
            f"🌀 گام ماردون: {fmt(context.user_data['screw_pitch_cm'])} cm\n"
            f"🗜️ ضخامت تیغه: {fmt(context.user_data['screw_blade_thickness_mm'])} mm\n\n"
            f"📐 شعاع تیغه محاسبه‌شده: {fmt(blade_radius_cm)} cm\n"
            f"🔄 تعداد دور تقریباً: {fmt(int(length_m / pitch_m) if pitch_m>0 else 0)} دور\n\n"
            f"⚖️ وزن لوله بدنه: {fmt(pipe_shell_weight)} kg\n"
            f"⚖️ وزن شفت: {fmt(shaft_weight)} kg\n"
            f"⚖️ وزن تیغه (ماردون): {fmt(blade_weight)} kg\n"
            f"🔢 وزن کل (لوله+شفت+تیغه): {fmt(total_weight_kg)} kg\n\n"
            f"⚖️ وزن شفت ترانس (استوانه توپر): {fmt(trans_weight_kg)} kg\n"
            f"💰 هزینه شفت ترانس (تومان): {fmt(int(trans_total_price))}\n\n"
            f"💰 قیمت موتور/گیربکس: {fmt(int(motor_price))} تومان\n"
            f"🔧 اجرت تراشکار: {fmt(int(lathe_wage))} تومان\n"
            f"💸 دستمزد ساخت (تومان/kg): {fmt(labor_per_kg)}\n\n"
            f"💵 مجموع قیمت نهایی: {fmt(total_price)} تومان\n"
        )

        keyboard = [[InlineKeyboardButton("🔄 شروع دوباره", callback_data=CALLBACK_RESTART)]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا یا ورودی نامعتبر: {e}\nلطفاً دوباره تلاش کن.")
        return SCREW_LABOR_PER_KG

# -------------------------
# callback برای restart
# -------------------------
async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    try:
        await query.message.delete()
    except:
        pass
    return await start(update, context)

# -------------------------
# cancel
# -------------------------
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد. برای شروع دوباره /start را بزن.")
    return ConversationHandler.END

# -------------------------
# ساخت اپ و ConversationHandler
# -------------------------
def build_app(token: str):
    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_PRODUCT: [CallbackQueryHandler(choose_product_cb)],

            # مخزن
            TANK_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_thickness_handler)],
            TANK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_diameter_handler)],
            TANK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_height_handler)],
            TANK_CONE_TOP_CM: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_top_handler)],
            TANK_CONE_BOTTOM_CM: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_bottom_handler)],
            TANK_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_waste_handler)],
            TANK_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_wage_handler)],

            # سیلو
            SILO_DIAMETER_M: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_diameter_handler)],
            SILO_HEIGHT_M: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_height_handler)],
            SILO_CAPACITY_TON: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_capacity_handler)],
            SILO_FRAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_frames_handler)],
            SILO_BRACES: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_braces_handler)],
            SILO_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_waste_handler)],
            SILO_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_wage_handler)],

            # اسکرو
            SCREW_LENGTH_CM: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_length_handler)],
            SCREW_OUTER_DIAMETER_INCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_diameter_handler)],
            SCREW_OUTER_THICKNESS_MM: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_thickness_handler)],
            SCREW_SHAFT_OUTER_DIAMETER_INCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_outer_d_handler)],
            SCREW_SHAFT_THICKNESS_MM: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_thickness_handler)],
            SCREW_PITCH_CM: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_pitch_handler)],
            SCREW_BLADE_THICKNESS_MM: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_blade_thickness_handler)],
            TRANS_SHAFT_DIAMETER_INCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_diameter_handler)],
            TRANS_SHAFT_LENGTH_CM: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_length_handler)],
            TRANS_SHAFT_PRICE_PER_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_price_per_kg_handler)],
            SCREW_MOTOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_motor_price_handler)],
            SCREW_LATHE_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_lathe_wage_handler)],
            SCREW_LABOR_PER_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_labor_per_kg_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(restart_callback, pattern=f"^{CALLBACK_RESTART}$"))

    return app

# -------------------------
# اجرا
# -------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY") or "YOUR_BOT_TOKEN"
    app = build_app(TOKEN)
    print("🤖 ربات آماده است. از /start استفاده کن.")
    app.run_polling()
