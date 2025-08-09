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

# ثابت‌ها
STEEL_DENSITY_KG_M3 = 7850
INCH_TO_M = 0.0254

# مراحل کلی
(
    CHOOSE_TYPE,
    # مخزن
    TANK_DIAMETER,
    TANK_HEIGHT,
    TANK_THICKNESS,
    TANK_CONE_BOTTOM_HEIGHT,
    TANK_CONE_BOTTOM_THICKNESS,
    TANK_CONE_TOP_HEIGHT,
    TANK_CONE_TOP_THICKNESS,
    TANK_SUPPORT_COUNT,
    TANK_SUPPORT_HEIGHT,
    TANK_SUPPORT_DIAMETER,
    TANK_SUPPORT_THICKNESS,
    TANK_WASTE_PERCENT,
    TANK_WAGE,
    # سیلو
    SILO_DIAMETER,
    SILO_HEIGHT,
    SILO_THICKNESS,
    SILO_CONE_HEIGHT,
    SILO_CONE_THICKNESS,
    SILO_SUPPORT_COUNT,
    SILO_SUPPORT_HEIGHT,
    SILO_SUPPORT_DIAMETER,
    SILO_SUPPORT_THICKNESS,
    SILO_WASTE_PERCENT,
    SILO_WAGE,
) = range(25)

END = ConversationHandler.END


def is_positive_number(text: str) -> bool:
    try:
        val = float(text)
        return val >= 0
    except ValueError:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    reply_keyboard = [["مخزن", "سیلو"]]
    await update.message.reply_text(
        "سلام! لطفاً نوع سازه را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSE_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text not in ["مخزن", "سیلو"]:
        await update.message.reply_text("لطفاً فقط 'مخزن' یا 'سیلو' را انتخاب کنید:")
        return CHOOSE_TYPE
    context.user_data['type'] = text
    if text == "مخزن":
        await update.message.reply_text(
            "قطر مخزن (سانتی‌متر):", reply_markup=ReplyKeyboardRemove()
        )
        return TANK_DIAMETER
    else:
        await update.message.reply_text(
            "قطر سیلو (سانتی‌متر):", reply_markup=ReplyKeyboardRemove()
        )
        return SILO_DIAMETER


# --- مخزن ---
async def tank_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً قطر مخزن را عدد مثبت و غیر صفر وارد کنید:")
        return TANK_DIAMETER
    context.user_data['tank_diameter_cm'] = float(text)
    await update.message.reply_text("ارتفاع بدنه استوانه‌ای مخزن (سانتی‌متر):")
    return TANK_HEIGHT


async def tank_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع بدنه را به عدد معتبر وارد کنید:")
        return TANK_HEIGHT
    context.user_data['tank_height_cm'] = float(text)
    await update.message.reply_text("ضخامت ورق بدنه استوانه‌ای (میلی‌متر):")
    return TANK_THICKNESS


async def tank_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً ضخامت بدنه را عدد مثبت و غیر صفر وارد کنید:")
        return TANK_THICKNESS
    context.user_data['tank_thickness_mm'] = float(text)
    await update.message.reply_text("ارتفاع قیف کف مخزن (سانتی‌متر):")
    return TANK_CONE_BOTTOM_HEIGHT


async def tank_cone_bottom_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع قیف کف را عدد معتبر وارد کنید:")
        return TANK_CONE_BOTTOM_HEIGHT
    context.user_data['tank_cone_bottom_h_cm'] = float(text)
    await update.message.reply_text("ضخامت ورق قیف کف (میلی‌متر):")
    return TANK_CONE_BOTTOM_THICKNESS


async def tank_cone_bottom_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ضخامت قیف کف را عدد معتبر وارد کنید:")
        return TANK_CONE_BOTTOM_THICKNESS
    context.user_data['tank_cone_bottom_thick_mm'] = float(text)
    await update.message.reply_text("ارتفاع قیف بالای مخزن (سانتی‌متر):")
    return TANK_CONE_TOP_HEIGHT


async def tank_cone_top_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع قیف بالا را عدد معتبر وارد کنید:")
        return TANK_CONE_TOP_HEIGHT
    context.user_data['tank_cone_top_h_cm'] = float(text)
    await update.message.reply_text("ضخامت ورق قیف بالا (میلی‌متر):")
    return TANK_CONE_TOP_THICKNESS


async def tank_cone_top_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ضخامت قیف بالا را عدد معتبر وارد کنید:")
        return TANK_CONE_TOP_THICKNESS
    context.user_data['tank_cone_top_thick_mm'] = float(text)
    await update.message.reply_text("تعداد پایه‌ها (عدد صحیح):")
    return TANK_SUPPORT_COUNT


async def tank_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not text.isdigit() or int(text) == 0:
        await update.message.reply_text("لطفاً تعداد پایه‌ها را عدد صحیح مثبت وارد کنید:")
        return TANK_SUPPORT_COUNT
    context.user_data['tank_support_count'] = int(text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر):")
    return TANK_SUPPORT_HEIGHT


async def tank_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع پایه را عدد معتبر وارد کنید:")
        return TANK_SUPPORT_HEIGHT
    context.user_data['tank_support_height_cm'] = float(text)
    await update.message.reply_text("قطر پایه (اینچ):")
    return TANK_SUPPORT_DIAMETER


async def tank_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً قطر پایه را عدد مثبت وارد کنید:")
        return TANK_SUPPORT_DIAMETER
    context.user_data['tank_support_diameter_inch'] = float(text)
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return TANK_SUPPORT_THICKNESS


async def tank_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً ضخامت پایه را عدد مثبت وارد کنید:")
        return TANK_SUPPORT_THICKNESS
    context.user_data['tank_support_thickness_mm'] = float(text)
    await update.message.reply_text("درصد پرتی (%):")
    return TANK_WASTE_PERCENT


async def tank_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً درصد پرتی را عدد معتبر وارد کنید:")
        return TANK_WASTE_PERCENT
    context.user_data['tank_waste_percent'] = float(text)
    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان):")
    return TANK_WAGE


async def tank_wage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً دستمزد را عدد مثبت وارد کنید:")
        return TANK_WAGE

    data = context.user_data

    try:
        d_m = data['tank_diameter_cm'] / 100
        h_cyl_m = data['tank_height_cm'] / 100
        t_cyl_m = data['tank_thickness_mm'] / 1000

        h_cb_m = data['tank_cone_bottom_h_cm'] / 100
        t_cb_m = data['tank_cone_bottom_thick_mm'] / 1000

        h_ct_m = data['tank_cone_top_h_cm'] / 100
        t_ct_m = data['tank_cone_top_thick_mm'] / 1000

        support_count = data['tank_support_count']
        support_height_m = data['tank_support_height_cm'] / 100
        support_diameter_inch = data['tank_support_diameter_inch']
        support_thickness_m = data['tank_support_thickness_mm'] / 1000

        waste_percent = data['tank_waste_percent']
        wage_per_kg = float(text)

        # وزن بدنه استوانه‌ای (لایه ورق فولادی)
        outer_radius = d_m / 2
        inner_radius = outer_radius - t_cyl_m
        # مساحت جانبی استوانه: محیط × ارتفاع
        lateral_area_cyl = 2 * math.pi * outer_radius * h_cyl_m
        volume_cyl = lateral_area_cyl * t_cyl_m  # حجم ورق
        weight_cyl = volume_cyl * STEEL_DENSITY_KG_M3

        # قیف کف (مخروط ناقص) فرض شعاع کوچک = 0
        # حجم مخروط = (1/3) * π * r^2 * h
        volume_cone_bottom = (1/3) * math.pi * (outer_radius ** 2) * h_cb_m
        weight_cone_bottom = volume_cone_bottom * t_cb_m * STEEL_DENSITY_KG_M3

        # قیف بالا
        volume_cone_top = (1/3) * math.pi * (outer_radius ** 2) * h_ct_m
        weight_cone_top = volume_cone_top * t_ct_m * STEEL_DENSITY_KG_M3

        # وزن پایه‌ها (لوله توخالی)
        # محیط لوله = π * قطر بیرونی
        # سطح جانبی = محیط × ارتفاع
        # حجم لوله = سطح جانبی × ضخامت
        support_diameter_m = support_diameter_inch * INCH_TO_M
        circumference = math.pi * support_diameter_m
        volume_per_support = circumference * support_height_m * support_thickness_m
        weight_per_support = volume_per_support * STEEL_DENSITY_KG_M3
        total_support_weight = weight_per_support * support_count

        total_weight = weight_cyl + weight_cone_bottom + weight_cone_top + total_support_weight
        total_weight_with_waste = total_weight * (1 + waste_percent / 100)
        price = total_weight_with_waste * wage_per_kg

        # خروجی
        msg = (
            f"وزن بدنه استوانه‌ای مخزن: {int(weight_cyl)} کیلوگرم\n"
            f"وزن قیف کف: {int(weight_cone_bottom)} کیلوگرم\n"
            f"وزن قیف بالا: {int(weight_cone_top)} کیلوگرم\n"
            f"وزن کل پایه‌ها: {int(total_support_weight)} کیلوگرم\n"
            f"وزن کل بدون پرتی: {int(total_weight)} کیلوگرم\n"
            f"وزن کل با پرتی ({waste_percent}%): {int(total_weight_with_waste)} کیلوگرم\n"
            f"قیمت کل (با احتساب دستمزد): {int(price)} تومان"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"خطا در محاسبه: {e}")

    return END


# --- سیلو ---
async def silo_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً قطر سیلو را عدد مثبت و غیر صفر وارد کنید:")
        return SILO_DIAMETER
    context.user_data['silo_diameter_cm'] = float(text)
    await update.message.reply_text("ارتفاع سیلو (سانتی‌متر):")
    return SILO_HEIGHT


async def silo_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع سیلو را عدد معتبر وارد کنید:")
        return SILO_HEIGHT
    context.user_data['silo_height_cm'] = float(text)
    await update.message.reply_text("ضخامت ورق سیلو (میلی‌متر):")
    return SILO_THICKNESS


async def silo_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً ضخامت ورق سیلو را عدد مثبت وارد کنید:")
        return SILO_THICKNESS
    context.user_data['silo_thickness_mm'] = float(text)
    await update.message.reply_text("ارتفاع قیف سیلو (سانتی‌متر):")
    return SILO_CONE_HEIGHT


async def silo_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع قیف را عدد معتبر وارد کنید:")
        return SILO_CONE_HEIGHT
    context.user_data['silo_cone_h_cm'] = float(text)
    await update.message.reply_text("ضخامت ورق قیف سیلو (میلی‌متر):")
    return SILO_CONE_THICKNESS


async def silo_cone_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً ضخامت ورق قیف را عدد مثبت وارد کنید:")
        return SILO_CONE_THICKNESS
    context.user_data['silo_cone_thick_mm'] = float(text)
    await update.message.reply_text("تعداد پایه‌ها (عدد صحیح):")
    return SILO_SUPPORT_COUNT


async def silo_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not text.isdigit() or int(text) == 0:
        await update.message.reply_text("لطفاً تعداد پایه‌ها را عدد صحیح مثبت وارد کنید:")
        return SILO_SUPPORT_COUNT
    context.user_data['silo_support_count'] = int(text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر):")
    return SILO_SUPPORT_HEIGHT


async def silo_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً ارتفاع پایه را عدد معتبر وارد کنید:")
        return SILO_SUPPORT_HEIGHT
    context.user_data['silo_support_height_cm'] = float(text)
    await update.message.reply_text("قطر پایه (اینچ):")
    return SILO_SUPPORT_DIAMETER


async def silo_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً قطر پایه را عدد مثبت وارد کنید:")
        return SILO_SUPPORT_DIAMETER
    context.user_data['silo_support_diameter_inch'] = float(text)
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return SILO_SUPPORT_THICKNESS


async def silo_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً ضخامت پایه را عدد مثبت وارد کنید:")
        return SILO_SUPPORT_THICKNESS
    context.user_data['silo_support_thickness_mm'] = float(text)
    await update.message.reply_text("درصد پرتی (%):")
    return SILO_WASTE_PERCENT


async def silo_waste_percent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text):
        await update.message.reply_text("لطفاً درصد پرتی را عدد معتبر وارد کنید:")
        return SILO_WASTE_PERCENT
    context.user_data['silo_waste_percent'] = float(text)
    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان):")
    return SILO_WAGE


async def silo_wage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not is_positive_number(text) or float(text) == 0:
        await update.message.reply_text("لطفاً دستمزد را عدد مثبت وارد کنید:")
        return SILO_WAGE

    data = context.user_data

    try:
        d_m = data['silo_diameter_cm'] / 100
        h_m = data['silo_height_cm'] / 100
        t_m = data['silo_thickness_mm'] / 1000

        h_cone_m = data['silo_cone_h_cm'] / 100
        t_cone_m = data['silo_cone_thick_mm'] / 1000

        support_count = data['silo_support_count']
        support_height_m = data['silo_support_height_cm'] / 100
        support_diameter_inch = data['silo_support_diameter_inch']
        support_thickness_m = data['silo_support_thickness_mm'] / 1000

        waste_percent = data['silo_waste_percent']
        wage_per_kg = float(text)

        # وزن بدنه استوانه‌ای سیلو
        outer_radius = d_m / 2
        lateral_area_cyl = 2 * math.pi * outer_radius * h_m
        volume_cyl = lateral_area_cyl * t_m
        weight_cyl = volume_cyl * STEEL_DENSITY_KG_M3

        # قیف سیلو (مخروط ناقص)
        volume_cone = (1/3) * math.pi * (outer_radius ** 2) * h_cone_m
        weight_cone = volume_cone * t_cone_m * STEEL_DENSITY_KG_M3

        # وزن پایه‌ها
        support_diameter_m = support_diameter_inch * INCH_TO_M
        circumference = math.pi * support_diameter_m
        volume_per_support = circumference * support_height_m * support_thickness_m
        weight_per_support = volume_per_support * STEEL_DENSITY_KG_M3
        total_support_weight = weight_per_support * support_count

        total_weight = weight_cyl + weight_cone + total_support_weight
        total_weight_with_waste = total_weight * (1 + waste_percent / 100)
        price = total_weight_with_waste * wage_per_kg

        msg = (
            f"وزن بدنه استوانه‌ای سیلو: {int(weight_cyl)} کیلوگرم\n"
            f"وزن قیف سیلو: {int(weight_cone)} کیلوگرم\n"
            f"وزن کل پایه‌ها: {int(total_support_weight)} کیلوگرم\n"
            f"وزن کل بدون پرتی: {int(total_weight)} کیلوگرم\n"
            f"وزن کل با پرتی ({waste_percent}%): {int(total_weight_with_waste)} کیلوگرم\n"
            f"قیمت کل (با احتساب دستمزد): {int(price)} تومان"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"خطا در محاسبه: {e}")

    return END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return END


def main() -> None:
    app = ApplicationBuilder().token("8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_type)],

            # مخزن
            TANK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_diameter)],
            TANK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_height)],
            TANK_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_thickness)],
            TANK_CONE_BOTTOM_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_bottom_height)],
            TANK_CONE_BOTTOM_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_bottom_thickness)],
            TANK_CONE_TOP_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_top_height)],
            TANK_CONE_TOP_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_top_thickness)],
            TANK_SUPPORT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_support_count)],
            TANK_SUPPORT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_support_height)],
            TANK_SUPPORT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_support_diameter)],
            TANK_SUPPORT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_support_thickness)],
            TANK_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_waste_percent)],
            TANK_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_wage)],

            # سیلو
            SILO_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_diameter)],
            SILO_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_height)],
            SILO_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_thickness)],
            SILO_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_cone_height)],
            SILO_CONE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_cone_thickness)],
            SILO_SUPPORT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_support_count)],
            SILO_SUPPORT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_support_height)],
            SILO_SUPPORT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_support_diameter)],
            SILO_SUPPORT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_support_thickness)],
            SILO_WASTE_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_waste_percent)],
            SILO_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_wage)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
