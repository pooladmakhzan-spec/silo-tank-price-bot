import math
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

# تعریف ثابت‌ها برای خوانایی بهتر
STEEL_DENSITY_KG_M3 = 7850  # چگالی فولاد (kg/m^3)
INCH_TO_M = 0.0254

# ==============================================================================
# تعریف وضعیت‌های مکالمه (States)
# ==============================================================================
MAIN_MENU, CHOOSE_PRICING, CHOOSE_CALC = range(3)

# وضعیت‌های مربوط به قیمت‌گذاری
(
    PRICING_DIAMETER,
    PRICING_HEIGHT,
    PRICING_THICKNESS_CYL,
    PRICING_CONE_BOTTOM_H,
    PRICING_CONE_BOTTOM_THICK,
    PRICING_CONE_TOP_H,
    PRICING_CONE_TOP_THICK,
    PRICING_SUPPORT_COUNT,
    PRICING_SUPPORT_HEIGHT,
    PRICING_SUPPORT_DIAMETER,
    PRICING_SUPPORT_THICKNESS,
    PRICING_WASTE,
    PRICING_WAGE,
) = range(3, 16)

# وضعیت‌های مربوط به محاسبه (طول، حجم، قطر)
(
    CALC_ORIENTATION,
    CALC_CHOICE,
    AWAITING_DIAMETER,
    AWAITING_LENGTH,
    AWAITING_VOLUME,
    AWAITING_BOTTOM_H,
    AWAITING_TOP_H,
) = range(16, 23)

# ==============================================================================
# توابع اصلی و شروع مکالمه
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه و نمایش منوی اصلی."""
    keyboard = [
        [InlineKeyboardButton("1️⃣ قیمت‌گذاری مخزن", callback_data="pricing")],
        [InlineKeyboardButton("2️⃣ محاسبه طول، حجم یا قطر", callback_data="calc")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    return MAIN_MENU

async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش انتخاب کاربر از منوی اصلی."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "pricing":
        await query.edit_message_text("قیمت‌گذاری مخزن انتخاب شد.\n\nلطفاً قطر بدنه (cm) را وارد کنید:")
        return PRICING_DIAMETER
    elif choice == "calc":
        keyboard = [
            [InlineKeyboardButton("عمودی", callback_data="vertical")],
            [InlineKeyboardButton("افقی", callback_data="horizontal")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "محاسبه انتخاب شد.\n\nلطفاً جهت مخزن را انتخاب کنید:", reply_markup=reply_markup
        )
        return CALC_ORIENTATION
    return ConversationHandler.END


# ==============================================================================
# بخش اول: منطق و توابع مربوط به قیمت‌گذاری
# ==============================================================================

async def get_positive_float(update: Update, text: str, next_state: int, error_state: int) -> int:
    """یک تابع کمکی برای دریافت عدد مثبت و انتقال به مرحله بعد."""
    try:
        value = float(update.message.text)
        if value <= 0:
            raise ValueError("مقدار باید مثبت باشد.")
        # مقدار معتبر است، در context ذخیره شده و به مرحله بعد می‌رود
        # این تابع فقط برای اعتبارسنجی است، ذخیره‌سازی در تابع اصلی انجام می‌شود
        await update.message.reply_text(text)
        return next_state
    except (ValueError, TypeError):
        await update.message.reply_text("ورودی نامعتبر است. لطفاً یک عدد مثبت وارد کنید.")
        return error_state

async def pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        if diameter <= 0: raise ValueError
        context.user_data['p'] = {'diameter_cm': diameter}
        await update.message.reply_text("✅ بسیار خب. ارتفاع بدنه (cm) را وارد کنید:")
        return PRICING_HEIGHT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت یک عدد مثبت (cm) وارد کنید.")
        return PRICING_DIAMETER

async def pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        if height <= 0: raise ValueError
        context.user_data['p']['height_cm'] = height
        await update.message.reply_text("✅ بسیار خب. ضخامت بدنه (mm) را وارد کنید:")
        return PRICING_THICKNESS_CYL
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع را به صورت یک عدد مثبت (cm) وارد کنید.")
        return PRICING_HEIGHT

async def pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness <= 0: raise ValueError
        context.user_data['p']['thickness_cyl_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
        return PRICING_CONE_BOTTOM_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت را به صورت یک عدد مثبت (mm) وارد کنید.")
        return PRICING_THICKNESS_CYL

async def pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_h = float(update.message.text)
        if cone_h < 0: raise ValueError # ارتفاع قیف می‌تواند صفر باشد
        context.user_data['p']['cone_bottom_h_cm'] = cone_h
        await update.message.reply_text("✅ بسیار خب. ضخامت قیف پایین (mm) را وارد کنید:")
        return PRICING_CONE_BOTTOM_THICK
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return PRICING_CONE_BOTTOM_H

async def pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['p']['cone_bottom_thick_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف بالا (cm) را وارد کنید (اگر ندارد 0 وارد کنید):")
        return PRICING_CONE_TOP_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت قیف را به صورت یک عدد (mm) وارد کنید.")
        return PRICING_CONE_BOTTOM_THICK

async def pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_h = float(update.message.text)
        if cone_h < 0: raise ValueError
        context.user_data['p']['cone_top_h_cm'] = cone_h
        await update.message.reply_text("✅ بسیار خب. ضخامت قیف بالا (mm) را وارد کنید:")
        return PRICING_CONE_TOP_THICK
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return PRICING_CONE_TOP_H

async def pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['p']['cone_top_thick_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. تعداد پایه‌ها را وارد کنید:")
        return PRICING_SUPPORT_COUNT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت قیف را به صورت یک عدد (mm) وارد کنید.")
        return PRICING_CONE_TOP_THICK

async def pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        if count < 0: raise ValueError
        context.user_data['p']['support_count'] = count
        await update.message.reply_text("✅ بسیار خب. ارتفاع هر پایه (cm) را وارد کنید:")
        return PRICING_SUPPORT_HEIGHT
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً تعداد پایه‌ها را به صورت یک عدد صحیح وارد کنید.")
        return PRICING_SUPPORT_COUNT

async def pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        if height < 0: raise ValueError
        context.user_data['p']['support_height_cm'] = height
        await update.message.reply_text("✅ بسیار خب. قطر هر پایه (inch) را وارد کنید:")
        return PRICING_SUPPORT_DIAMETER
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع پایه را به صورت یک عدد (cm) وارد کنید.")
        return PRICING_SUPPORT_HEIGHT

async def pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        if diameter < 0: raise ValueError
        context.user_data['p']['support_diameter_inch'] = diameter
        await update.message.reply_text("✅ بسیار خب. ضخامت هر پایه (mm) را وارد کنید:")
        return PRICING_SUPPORT_THICKNESS
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر پایه را به صورت یک عدد (inch) وارد کنید.")
        return PRICING_SUPPORT_DIAMETER

async def pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        if thickness < 0: raise ValueError
        context.user_data['p']['support_thickness_mm'] = thickness
        await update.message.reply_text("✅ بسیار خب. درصد پرتی ورق (%) را وارد کنید:")
        return PRICING_WASTE
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ضخامت پایه را به صورت یک عدد (mm) وارد کنید.")
        return PRICING_SUPPORT_THICKNESS

async def pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        waste = float(update.message.text)
        if waste < 0: raise ValueError
        context.user_data['p']['waste_percent'] = waste
        await update.message.reply_text("✅ بسیار خب. دستمزد ساخت (تومان به ازای هر کیلوگرم) را وارد کنید:")
        return PRICING_WAGE
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً درصد پرتی را به صورت یک عدد وارد کنید.")
        return PRICING_WASTE

async def pricing_final_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محاسبه نهایی وزن و قیمت و ارسال نتیجه."""
    try:
        wage_per_kg = float(update.message.text)
        if wage_per_kg < 0: raise ValueError
        data = context.user_data['p']

        # --- تبدیل تمام واحدها به متر برای محاسبات ---
        d_m = data['diameter_cm'] / 100
        h_cyl_m = data['height_cm'] / 100
        t_cyl_m = data['thickness_cyl_mm'] / 1000
        h_cb_m = data['cone_bottom_h_cm'] / 100
        t_cb_m = data['cone_bottom_thick_mm'] / 1000
        h_ct_m = data['cone_top_h_cm'] / 100
        t_ct_m = data['cone_top_thick_mm'] / 1000
        
        support_count = data['support_count']
        support_h_m = data['support_height_cm'] / 100
        support_d_m = data['support_diameter_inch'] * INCH_TO_M
        support_t_m = data['support_thickness_mm'] / 1000

        radius_m = d_m / 2

        # محاسبه وزن بدنه استوانه‌ای
        cyl_area = math.pi * d_m * h_cyl_m
        weight_cyl = cyl_area * t_cyl_m * STEEL_DENSITY_KG_M3

        # محاسبه وزن قیف پایین
        if h_cb_m > 0:
            slant_cb = math.sqrt(radius_m**2 + h_cb_m**2)
            area_cb = math.pi * radius_m * slant_cb
            weight_cb = area_cb * t_cb_m * STEEL_DENSITY_KG_M3
        else:
            weight_cb = 0

        # محاسبه وزن قیف بالا
        if h_ct_m > 0:
            slant_ct = math.sqrt(radius_m**2 + h_ct_m**2)
            area_ct = math.pi * radius_m * slant_ct
            weight_ct = area_ct * t_ct_m * STEEL_DENSITY_KG_M3
        else:
            weight_ct = 0

        # محاسبه وزن پایه‌ها
        if support_count > 0:
            support_r_m = support_d_m / 2
            inner_r_m = support_r_m - support_t_m
            if inner_r_m < 0: inner_r_m = 0 # جلوگیری از شعاع داخلی منفی
            
            # حجم یک پایه (لوله توخالی)
            support_volume_one = math.pi * (support_r_m**2 - inner_r_m**2) * support_h_m
            weight_supports = support_volume_one * STEEL_DENSITY_KG_M3 * support_count
        else:
            weight_supports = 0

        # محاسبه وزن کل و قیمت
        total_weight = weight_cyl + weight_cb + weight_ct + weight_supports
        weight_with_waste = total_weight * (1 + data['waste_percent'] / 100)
        total_price = weight_with_waste * wage_per_kg

        # ایجاد پیام نتیجه
        response = "📊 **نتایج محاسبه قیمت‌گذاری** 📊\n\n"
        response += f"🔹 وزن بدنه استوانه‌ای: `{int(weight_cyl)}` کیلوگرم\n"
        response += f"🔹 وزن قیف پایین: `{int(weight_cb)}` کیلوگرم\n"
        response += f"🔹 وزن قیف بالا: `{int(weight_ct)}` کیلوگرم\n"
        response += f"🔹 وزن پایه‌ها: `{int(weight_supports)}` کیلوگرم\n"
        response += "-----------------------------------\n"
        response += f"🔸 **وزن کلی (بدون پرتی):** `{int(total_weight)}` کیلوگرم\n"
        response += f"🔸 **وزن کلی (با پرتی):** `{int(weight_with_waste)}` کیلوگرم\n\n"
        response += f"💰 **قیمت کل (با دستمزد):** `{int(total_price):,}` تومان"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        return ConversationHandler.END

    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً دستمزد را به صورت یک عدد معتبر وارد کنید.")
        return PRICING_WAGE
    except Exception as e:
        await update.message.reply_text(f"یک خطای غیرمنتظره در محاسبات رخ داد: {e}")
        return ConversationHandler.END


# ==============================================================================
# بخش دوم: منطق و توابع مربوط به محاسبه (طول، حجم، قطر)
# ==============================================================================

async def calc_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    orient = query.data
    context.user_data['c'] = {'orientation': orient}
    
    keyboard = [
        [InlineKeyboardButton("حجم (لیتر)", callback_data='volume')],
        [InlineKeyboardButton("طول بدنه (cm)", callback_data='length')],
        [InlineKeyboardButton("قطر بدنه (cm)", callback_data='diameter')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"مخزن {'عمودی' if orient == 'vertical' else 'افقی'} انتخاب شد.\n\n"
    text += "چه مقداری را می‌خواهید محاسبه کنید؟"
    await query.edit_message_text(text, reply_markup=reply_markup)
    return CALC_CHOICE

async def calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    find = query.data
    context.user_data['c']['find'] = find
    
    if find == 'volume':
        await query.edit_message_text("محاسبه حجم انتخاب شد.\n\nلطفاً قطر مخزن (cm) را وارد کنید:")
        return AWAITING_DIAMETER
    elif find == 'length':
        await query.edit_message_text("محاسبه طول انتخاب شد.\n\nلطفاً قطر مخزن (cm) را وارد کنید:")
        return AWAITING_DIAMETER
    elif find == 'diameter':
        await query.edit_message_text("محاسبه قطر انتخاب شد.\n\nلطفاً طول بدنه مخزن (cm) را وارد کنید:")
        return AWAITING_LENGTH
    return ConversationHandler.END

async def calc_get_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['c']['diameter_m'] = val / 100 # Convert cm to m
        find = context.user_data['c']['find']
        if find == 'volume':
            await update.message.reply_text("✅ بسیار خب. طول بدنه مخزن (cm) را وارد کنید:")
            return AWAITING_LENGTH
        elif find == 'length':
            await update.message.reply_text("✅ بسیار خب. حجم کل مخزن (لیتر) را وارد کنید:")
            return AWAITING_VOLUME
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً قطر را به صورت یک عدد مثبت (cm) وارد کنید.")
        return AWAITING_DIAMETER
    return ConversationHandler.END

async def calc_get_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['c']['length_m'] = val / 100 # Convert cm to m
        find = context.user_data['c']['find']
        if find == 'volume':
            await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
            return AWAITING_BOTTOM_H
        elif find == 'diameter':
            await update.message.reply_text("✅ بسیار خب. حجم کل مخزن (لیتر) را وارد کنید:")
            return AWAITING_VOLUME
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً طول را به صورت یک عدد مثبت (cm) وارد کنید.")
        return AWAITING_LENGTH
    return ConversationHandler.END

async def calc_get_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val <= 0: raise ValueError
        context.user_data['c']['volume_m3'] = val / 1000 # Convert Liters to m^3
        await update.message.reply_text("✅ بسیار خب. ارتفاع قیف پایین (cm) را وارد کنید:")
        return AWAITING_BOTTOM_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً حجم را به صورت یک عدد مثبت (لیتر) وارد کنید.")
        return AWAITING_VOLUME
    return ConversationHandler.END
    
async def calc_get_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['c']['bottom_h_m'] = val / 100 # Convert cm to m
        
        # اگر مخزن عمودی است، مرحله قیف بالا را رد کن
        if context.user_data['c']['orientation'] == 'vertical':
            context.user_data['c']['top_h_m'] = 0
            return await perform_calculation(update, context)
        else:
            await update.message.reply_text("✅ بسیار خب. ارتفاع قیف بالا/عقب (cm) را وارد کنید:")
            return AWAITING_TOP_H
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return AWAITING_BOTTOM_H

async def calc_get_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text)
        if val < 0: raise ValueError
        context.user_data['c']['top_h_m'] = val / 100 # Convert cm to m
        return await perform_calculation(update, context)
    except (ValueError, TypeError):
        await update.message.reply_text("خطا: لطفاً ارتفاع قیف را به صورت یک عدد (cm) وارد کنید.")
        return AWAITING_TOP_H

async def perform_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تابع نهایی برای انجام محاسبات طول، حجم یا قطر."""
    data = context.user_data['c']
    find = data['find']
    orient = data['orientation']
    
    try:
        if find == 'volume':
            r = data['diameter_m'] / 2
            L = data['length_m']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m'] # برای عمودی این 0 است
            
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
                await update.message.reply_text("خطا: با این ورودی‌ها، حجم قیف‌ها از حجم کل بیشتر است! لطفاً مقادیر را بررسی کنید.")
            else:
                L_calc_m = vol_cyl_needed / (math.pi * r**2)
                await update.message.reply_text(f"✅ **نتیجه:** طول بدنه مخزن `{L_calc_m * 100:.2f}` سانتی‌متر است.", parse_mode='Markdown')

        elif find == 'diameter':
            L = data['length_m']
            V = data['volume_m3']
            h_b = data['bottom_h_m']
            h_t = data['top_h_m']

            # V = (pi*r^2 * L) + (1/3*pi*r^2*h_b) + (1/3*pi*r^2*h_t)
            # V = pi * r^2 * (L + h_b/3 + h_t/3)
            denominator = math.pi * (L + h_b/3 + h_t/3)
            if denominator <= 0:
                await update.message.reply_text("خطا: با این ورودی‌ها محاسبه قطر ممکن نیست (مخرج صفر یا منفی).")
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
    return ConversationHandler.END


# ==============================================================================
# تابع لغو و تنظیمات اصلی برنامه
# ==============================================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو عملیات و پایان مکالمه."""
    await update.message.reply_text("عملیات لغو شد.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    """اجرای اصلی بات تلگرام."""
    # توکن ربات خود را در اینجا قرار دهید
    application = ApplicationBuilder().token("8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_choice, pattern='^(pricing|calc)$')],
            
            # States for Pricing
            PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_diameter)],
            PRICING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_height)],
            PRICING_THICKNESS_CYL: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_thickness_cyl)],
            PRICING_CONE_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_bottom_h)],
            PRICING_CONE_BOTTOM_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_bottom_thick)],
            PRICING_CONE_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_top_h)],
            PRICING_CONE_TOP_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_top_thick)],
            PRICING_SUPPORT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_support_count)],
            PRICING_SUPPORT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_support_height)],
            PRICING_SUPPORT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_support_diameter)],
            PRICING_SUPPORT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_support_thickness)],
            PRICING_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_waste)],
            PRICING_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_final_calculate)],
            
            # States for Calculation
            CALC_ORIENTATION: [CallbackQueryHandler(calc_orientation, pattern='^(vertical|horizontal)$')],
            CALC_CHOICE: [CallbackQueryHandler(calc_choice, pattern='^(length|volume|diameter)$')],
            AWAITING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_get_diameter)],
            AWAITING_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_get_length)],
            AWAITING_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_get_volume)],
            AWAITING_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_get_bottom_h)],
            AWAITING_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_get_top_h)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
