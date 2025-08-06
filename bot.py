from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل مکالمه
MAIN_MENU, PRICING, DIMENSIONS, ORIENTATION, TARGET_CHOICE, ASK_PARAMS, ASK_CYLINDER, ASK_CONES, ASK_BASES, ASK_WASTE, ASK_LABOR = range(11)

# متغیرهای کمکی
user_data = {}

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("محاسبه قیمت مخزن", callback_data="pricing")],
        [InlineKeyboardButton("محاسبه طول/قطر/حجم مخزن", callback_data="dimensions")]
    ]
    update.message.reply_text("یک گزینه انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

def main_menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    choice = query.data
    user_data[query.from_user.id] = {}
    if choice == "pricing":
        query.edit_message_text("مشخصات بدنه مخزن:\nضخامت (میلی‌متر)، قطر (متر)، ارتفاع (متر) را وارد کنید.\nمثال: 8,2.5,6")
        return ASK_CYLINDER
    elif choice == "dimensions":
        keyboard = [
            [InlineKeyboardButton("عمودی", callback_data="vertical")],
            [InlineKeyboardButton("افقی", callback_data="horizontal")]
        ]
        query.edit_message_text("نوع مخزن را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ORIENTATION

def orientation_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    user_data[user_id]["orientation"] = query.data
    keyboard = [
        [InlineKeyboardButton("حجم", callback_data="volume")],
        [InlineKeyboardButton("طول", callback_data="length")],
        [InlineKeyboardButton("قطر", callback_data="diameter")]
    ]
    query.edit_message_text("چه چیزی را می‌خواهید محاسبه کنید؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return TARGET_CHOICE

def target_choice_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    user_data[user_id]["target"] = query.data
    query.edit_message_text("ورودی‌های لازم را به‌صورت عددی وارد کنید (بر حسب متر یا لیتر، بسته به مجهول).")
    return ASK_PARAMS

def ask_params(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    orientation = user_data[user_id]["orientation"]
    target = user_data[user_id]["target"]
    inputs = list(map(float, update.message.text.split(",")))
    if target == "volume":
        d, h, cone_h = inputs
        cyl_vol = 3.1416 * (d/2)**2 * h
        cone_vol = (1/3) * 3.1416 * (d/2)**2 * cone_h
        total = cyl_vol + (2 * cone_vol if orientation == "horizontal" else cone_vol)
        update.message.reply_text(f"حجم مخزن ≈ {round(total, 2)} متر مکعب")
    elif target == "length":
        # محاسبه طول بر اساس حجم داده شده
        v, d, cone_h = inputs
        cone_vol = (1/3) * 3.1416 * (d/2)**2 * cone_h
        effective_v = v - (2 * cone_vol if orientation == "horizontal" else cone_vol)
        length = effective_v / (3.1416 * (d/2)**2)
        update.message.reply_text(f"طول مخزن ≈ {round(length, 2)} متر")
    elif target == "diameter":
        v, h, cone_h = inputs
        # محاسبه قطر با روش ساده‌سازی (نیوتن-رافسون حذف شده برای اختصار)
        update.message.reply_text("محاسبه قطر نیاز به روش عددی دارد که باید جدا پیاده‌سازی شود.")
    return ConversationHandler.END

def ask_cylinder(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    thickness, diameter, height = map(float, update.message.text.split(","))
    user_data[user_id]["cylinder"] = (thickness/1000, diameter, height)
    update.message.reply_text("مشخصات قیف‌ها:\nضخامت (میلی‌متر)، ارتفاع قیف (سانتی‌متر) را وارد کنید.\nمثال: 8,60")
    return ASK_CONES

def ask_cones(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    thickness, cone_h = map(float, update.message.text.split(","))
    user_data[user_id]["cones"] = (thickness/1000, cone_h/100)
    update.message.reply_text("مشخصات پایه‌ها:\nتعداد، ارتفاع (سانتی‌متر)، قطر (اینچ)، ضخامت (میلی‌متر) را وارد کنید.\nمثال: 4,250,6,8")
    return ASK_BASES

def ask_bases(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    count, height, dia_inch, thickness = map(float, update.message.text.split(","))
    user_data[user_id]["bases"] = (count, height/100, dia_inch*0.0254, thickness/1000)
    update.message.reply_text("درصد پرتی را وارد کنید (مثلاً 10):")
    return ASK_WASTE

def ask_waste(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["waste"] = float(update.message.text)/100
    update.message.reply_text("دستمزد ساخت (تومان به ازای هر کیلوگرم) را وارد کنید:")
    return ASK_LABOR

def ask_labor(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    labor = float(update.message.text)
    # محاسبات وزن
    t, d, h = user_data[user_id]["cylinder"]
    cyl_weight = (3.1416 * d * h * t) * 7850
    tc, hc = user_data[user_id]["cones"]
    cone_area = 3.1416 * (d/2) * (((d/2)**2 + hc**2)**0.5)
    cone_weight = cone_area * tc * 7850
    total_cones = 2 * cone_weight
    c, hb, db, tb = user_data[user_id]["bases"]
    base_weight = c * (3.1416 * db * hb * tb) * 7850
    total_weight = cyl_weight + total_cones + base_weight
    total_with_waste = total_weight * (1 + user_data[user_id]["waste"])
    price = total_with_waste * labor
    update.message.reply_text(
        f"وزن مخزن: {int(cyl_weight+total_cones)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(base_weight)} کیلوگرم\n"
        f"وزن کلی: {int(total_weight)} کیلوگرم\n"
        f"وزن کلی با پرتی: {int(total_with_waste)} کیلوگرم\n"
        f"قیمت کل: {int(price)} تومان"
    )
    return ConversationHandler.END

def reset(update: Update, context: CallbackContext):
    user_data.clear()
    update.message.reply_text("داده‌ها ریست شد. از /start دوباره شروع کنید.")

app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
        ORIENTATION: [CallbackQueryHandler(orientation_handler)],
        TARGET_CHOICE: [CallbackQueryHandler(target_choice_handler)],
        ASK_PARAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_params)],
        ASK_CYLINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_cylinder)],
        ASK_CONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_cones)],
        ASK_BASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bases)],
        ASK_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_waste)],
        ASK_LABOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_labor)],
    },
    fallbacks=[CommandHandler("reset", reset)]
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("reset", reset))

if __name__ == "__main__":
    app.run_polling()
