import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# استیت‌ها
MAIN_MENU, PRICING_DIAMETER, PRICING_HEIGHT, PRICING_THICKNESS, PRICING_CONE_HEIGHT, \
PRICING_CONE_TOP_THICK, PRICING_CONE_BOTTOM_THICK, PRICING_LEG_COUNT, PRICING_LEG_HEIGHT, \
PRICING_LEG_DIAMETER, PRICING_LEG_THICKNESS, PRICING_WASTE, PRICING_WAGE, \
MODE_SELECTION, CALC_CHOICE, CALC_DIAMETER, CALC_HEIGHT, CALC_VOLUME = range(18)

user_data = {}

# ⬅️ شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 قیمت‌گذاری مخزن", callback_data="pricing")],
        [InlineKeyboardButton("📐 محاسبه طول، قطر یا حجم", callback_data="calc")]
    ]
    await update.message.reply_text("یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

# ⬅️ منوی اصلی
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "pricing":
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return PRICING_DIAMETER
    elif choice == "calc":
        keyboard = [
            [InlineKeyboardButton("عمودی", callback_data="vertical"),
             InlineKeyboardButton("افقی", callback_data="horizontal")]
        ]
        await query.edit_message_text("مخزن افقی است یا عمودی؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return MODE_SELECTION

# ⬅️ انتخاب حالت عمودی یا افقی
async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id] = {"orientation": query.data}
    keyboard = [
        [InlineKeyboardButton("محاسبه طول", callback_data="length"),
         InlineKeyboardButton("محاسبه قطر", callback_data="diameter")],
        [InlineKeyboardButton("محاسبه حجم", callback_data="volume")]
    ]
    await query.edit_message_text("چه چیزی را می‌خواهید محاسبه کنید؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return CALC_CHOICE

# ⬅️ انتخاب نوع محاسبه
async def calc_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_data[query.from_user.id]["action"] = action
    if action == "length":
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER
    elif action == "diameter":
        await query.edit_message_text("طول مخزن (متر) را وارد کنید:")
        return CALC_HEIGHT
    elif action == "volume":
        await query.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER

# ⬅️ دریافت ورودی محاسبه اول
async def get_calc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    action = user_data[user_id]["action"]

    if action == "length":
        user_data[user_id]["diameter"] = float(update.message.text)
        await update.message.reply_text("حجم مورد نظر (لیتر) را وارد کنید:")
        return CALC_VOLUME
    elif action == "diameter":
        user_data[user_id]["length"] = float(update.message.text)
        await update.message.reply_text("حجم مورد نظر (لیتر) را وارد کنید:")
        return CALC_VOLUME
    elif action == "volume":
        user_data[user_id]["diameter"] = float(update.message.text)
        await update.message.reply_text("طول مخزن (متر) را وارد کنید:")
        return CALC_HEIGHT

# ⬅️ دریافت ورودی دوم برای محاسبه
async def get_calc_second_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    action = user_data[user_id]["action"]
    orientation = user_data[user_id]["orientation"]

    if action == "length":
        volume_liter = float(update.message.text)
        volume_m3 = volume_liter / 1000
        d = user_data[user_id]["diameter"]
        r = d / 2
        cone_h = 0.5
        cone_vol = (math.pi * r ** 2 * cone_h) / 3
        usable_volume = volume_m3 - (cone_vol if orientation == "vertical" else 2 * cone_vol)
        length = usable_volume / (math.pi * r ** 2)
        await update.message.reply_text(f"طول مخزن ≈ {length:.2f} متر")
        return ConversationHandler.END

    elif action == "diameter":
        await update.message.reply_text("این بخش در حال توسعه است.")
        return ConversationHandler.END

    elif action == "volume":
        length = float(update.message.text)
        d = user_data[user_id]["diameter"]
        r = d / 2
        cone_h = 0.5
        cone_vol = (math.pi * r ** 2 * cone_h) / 3
        total_vol = (math.pi * r ** 2 * length) + (cone_vol if orientation == "vertical" else 2 * cone_vol)
        await update.message.reply_text(f"حجم مخزن ≈ {total_vol * 1000:.0f} لیتر")
        return ConversationHandler.END

# 🧮 قیمت‌گذاری: مرحله به مرحله
async def pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id] = {"diameter": float(update.message.text)}
    await update.message.reply_text("ارتفاع بدنه (متر) را وارد کنید:")
    return PRICING_HEIGHT

async def pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["height"] = float(update.message.text)
    await update.message.reply_text("ضخامت ورق بدنه (میلی‌متر) را وارد کنید:")
    return PRICING_THICKNESS

async def pricing_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["thickness"] = float(update.message.text)
    await update.message.reply_text("ارتفاع قیف‌ها (سانتی‌متر) را وارد کنید:")
    return PRICING_CONE_HEIGHT

async def pricing_cone_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["cone_height"] = float(update.message.text)
    await update.message.reply_text("ضخامت قیف بالا (میلی‌متر) را وارد کنید:")
    return PRICING_CONE_TOP_THICK

async def pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["cone_top_thickness"] = float(update.message.text)
    await update.message.reply_text("ضخامت قیف پایین (میلی‌متر) را وارد کنید:")
    return PRICING_CONE_BOTTOM_THICK

async def pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تعداد پایه‌ها را وارد کنید:")
    user_data[update.message.from_user.id]["cone_bottom_thickness"] = float(update.message.text)
    return PRICING_LEG_COUNT

async def pricing_leg_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع هر پایه (سانتی‌متر) را وارد کنید:")
    return PRICING_LEG_HEIGHT

async def pricing_leg_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_height"] = float(update.message.text)
    await update.message.reply_text("قطر پایه (اینچ) را وارد کنید:")
    return PRICING_LEG_DIAMETER

async def pricing_leg_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_diameter"] = float(update.message.text)
    await update.message.reply_text("ضخامت پایه (میلی‌متر) را وارد کنید:")
    return PRICING_LEG_THICKNESS

async def pricing_leg_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["leg_thickness"] = float(update.message.text)
    await update.message.reply_text("درصد پرتی را وارد کنید:")
    return PRICING_WASTE

async def pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.from_user.id]["waste"] = float(update.message.text)
    await update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کنید:")
    return PRICING_WAGE

async def pricing_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_data[uid]["wage"] = float(update.message.text)

    d = user_data[uid]["diameter"]
    h = user_data[uid]["height"]
    t_body = user_data[uid]["thickness"] / 1000
    ch = user_data[uid]["cone_height"] / 100
    t_cone_top = user_data[uid]["cone_top_thickness"] / 1000
    t_cone_bot = user_data[uid]["cone_bottom_thickness"] / 1000
    legs = user_data[uid]["legs"]
    leg_h = user_data[uid]["leg_height"] / 100
    leg_d = (user_data[uid]["leg_diameter"] * 2.54) / 100
    leg_t = user_data[uid]["leg_thickness"] / 1000
    waste = user_data[uid]["waste"]
    wage = user_data[uid]["wage"]

    density = 7850
    r = d / 2

    # وزن بدنه
    body_area = 2 * math.pi * r * h
    body_weight = body_area * t_body * density

    # وزن قیف‌ها
    slant = math.sqrt(r**2 + ch**2)
    cone_area = math.pi * r * slant
    cone_weight = cone_area * density * (t_cone_top + t_cone_bot)

    # وزن پایه‌ها
    leg_weight = legs * (2 * math.pi * (leg_d / 2) * leg_h * leg_t * density)

    total_weight = body_weight + cone_weight + leg_weight
    total_with_waste = total_weight * (1 + waste / 100)
    price = total_with_waste * wage

    msg = (
        f"✅ وزن بدنه: {int(body_weight)} کیلوگرم\n"
        f"✅ وزن قیف‌ها: {int(cone_weight)} کیلوگرم\n"
        f"✅ وزن پایه‌ها: {int(leg_weight)} کیلوگرم\n"
        f"✅ وزن کل: {int(total_weight)} کیلوگرم\n"
        f"✅ وزن با پرتی: {int(total_with_waste)} کیلوگرم\n"
        f"✅ قیمت کل: {int(price):,} تومان"
    )
    await update.message.reply_text(msg)
    return ConversationHandler.END

# 🎯 اجرای برنامه
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            MODE_SELECTION: [CallbackQueryHandler(mode_selection)],
            CALC_CHOICE: [CallbackQueryHandler(calc_choice)],
            CALC_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_input)],
            CALC_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_input)],
            CALC_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_calc_second_input)],

            PRICING_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_diameter)],
            PRICING_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_height)],
            PRICING_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_thickness)],
            PRICING_CONE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_height)],
            PRICING_CONE_TOP_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_top_thick)],
            PRICING_CONE_BOTTOM_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_bottom_thick)],
            PRICING_LEG_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_count)],
            PRICING_LEG_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_height)],
            PRICING_LEG_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_diameter)],
            PRICING_LEG_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_thickness)],
            PRICING_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_waste)],
            PRICING_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_wage)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
