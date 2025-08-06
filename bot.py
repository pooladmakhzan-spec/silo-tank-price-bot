from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes

# Define states for conversation
MAIN_MENU = 0
PRICING_DIAMETER = 1
PRICING_HEIGHT = 2
PRICING_THICKNESS_CYL = 3
PRICING_CONE_BOTTOM_H = 4
PRICING_CONE_BOTTOM_THICK = 5
PRICING_CONE_TOP_H = 6
PRICING_CONE_TOP_THICK = 7
PRICING_SUPPORT_COUNT = 8
PRICING_SUPPORT_HEIGHT = 9
PRICING_SUPPORT_DIAMETER = 10
PRICING_SUPPORT_THICKNESS = 11
PRICING_WASTE = 12
PRICING_COST = 13

ORIENTATION = 14
CALC_FIND = 15
CALC_DIAMETER = 16
CALC_LENGTH = 17
CALC_VOLUME = 18
CALC_BOTTOM_H = 19
CALC_TOP_H = 20

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("قیمت‌گذاری مخزن", callback_data='pricing')],
        [InlineKeyboardButton("محاسبه طول، حجم یا قطر مخزن", callback_data='calc')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفا یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    return MAIN_MENU

# Callback for main menu choices
async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == 'pricing':
        await query.edit_message_text("قیمت‌گذاری مخزن انتخاب شد.\nلطفا قطر بدنه مخزن (متر) را وارد کنید:")
        return PRICING_DIAMETER
    elif choice == 'calc':
        # Ask orientation
        keyboard = [
            [InlineKeyboardButton("عمودی", callback_data='vertical')],
            [InlineKeyboardButton("افقی", callback_data='horizontal')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("محاسبه طول، حجم یا قطر مخزن انتخاب شد.\nلطفا جهت مخزن را انتخاب کنید:", reply_markup=reply_markup)
        return ORIENTATION
    else:
        await query.edit_message_text("گزینه نامعتبر است.")
        return ConversationHandler.END

# Pricing conversation handlers
async def pricing_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        context.user_data['pricing'] = {'diameter': diameter}
        await update.message.reply_text("ارتفاع بدنه مخزن (متر) را وارد کنید:")
        return PRICING_HEIGHT
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_DIAMETER

async def pricing_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        context.user_data['pricing']['height'] = height
        await update.message.reply_text("ضخامت بدنه (میلیمتر) را وارد کنید:")
        return PRICING_THICKNESS_CYL
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_HEIGHT

async def pricing_thickness_cyl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        context.user_data['pricing']['thickness_cyl'] = thickness
        await update.message.reply_text("ارتفاع قیف پایین (سانتیمتر) را وارد کنید:")
        return PRICING_CONE_BOTTOM_H
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_THICKNESS_CYL

async def pricing_cone_bottom_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_bottom_h = float(update.message.text)
        context.user_data['pricing']['cone_bottom_h'] = cone_bottom_h
        await update.message.reply_text("ضخامت قیف پایین (میلیمتر) را وارد کنید:")
        return PRICING_CONE_BOTTOM_THICK
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_CONE_BOTTOM_H

async def pricing_cone_bottom_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_bottom_thick = float(update.message.text)
        context.user_data['pricing']['cone_bottom_thick'] = cone_bottom_thick
        await update.message.reply_text("ارتفاع قیف بالا (سانتیمتر) را وارد کنید:")
        return PRICING_CONE_TOP_H
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_CONE_BOTTOM_THICK

async def pricing_cone_top_h(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_top_h = float(update.message.text)
        context.user_data['pricing']['cone_top_h'] = cone_top_h
        await update.message.reply_text("ضخامت قیف بالا (میلیمتر) را وارد کنید:")
        return PRICING_CONE_TOP_THICK
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_CONE_TOP_H

async def pricing_cone_top_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cone_top_thick = float(update.message.text)
        context.user_data['pricing']['cone_top_thick'] = cone_top_thick
        await update.message.reply_text("تعداد پایه‌ها را وارد کنید:")
        return PRICING_SUPPORT_COUNT
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_CONE_TOP_THICK

async def pricing_support_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        context.user_data['pricing']['support_count'] = count
        await update.message.reply_text("ارتفاع هر پایه (متر) را وارد کنید:")
        return PRICING_SUPPORT_HEIGHT
    except:
        await update.message.reply_text("لطفا یک عدد صحیح وارد کنید.")
        return PRICING_SUPPORT_COUNT

async def pricing_support_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        context.user_data['pricing']['support_height'] = height
        await update.message.reply_text("قطر هر پایه (سانتیمتر) را وارد کنید:")
        return PRICING_SUPPORT_DIAMETER
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_SUPPORT_HEIGHT

async def pricing_support_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        diameter = float(update.message.text)
        context.user_data['pricing']['support_diameter'] = diameter
        await update.message.reply_text("ضخامت هر پایه (میلیمتر) را وارد کنید:")
        return PRICING_SUPPORT_THICKNESS
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_SUPPORT_DIAMETER

async def pricing_support_thickness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        thickness = float(update.message.text)
        context.user_data['pricing']['support_thickness'] = thickness
        await update.message.reply_text("درصد پرتی (%) را وارد کنید:")
        return PRICING_WASTE
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_SUPPORT_THICKNESS

async def pricing_waste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        waste = float(update.message.text)
        context.user_data['pricing']['waste'] = waste
        await update.message.reply_text("دستمزد به ازای هر کیلوگرم (تومان) را وارد کنید:")
        return PRICING_COST
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return PRICING_WASTE

async def pricing_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cost_per_kg = float(update.message.text)
        data = context.user_data['pricing']
        data['cost_per_kg'] = cost_per_kg

        # Calculate weights
        import math
        density = 7850  # kg/m^3 for steel (approx.)

        # Cylinder
        d = data['diameter']
        h = data['height']
        t_cyl = data['thickness_cyl'] / 1000  # mm to m
        radius = d / 2
        cylinder_area = 2 * math.pi * radius * h
        weight_cyl = cylinder_area * t_cyl * density

        # Bottom cone
        h_cb = data['cone_bottom_h'] / 100  # cm to m
        t_cb = data['cone_bottom_thick'] / 1000
        slant_cb = math.sqrt(radius**2 + h_cb**2)
        area_cb = math.pi * radius * slant_cb
        weight_cb = area_cb * t_cb * density

        # Top cone
        h_ct = data['cone_top_h'] / 100  # cm to m
        t_ct = data['cone_top_thick'] / 1000
        slant_ct = math.sqrt(radius**2 + h_ct**2)
        area_ct = math.pi * radius * slant_ct
        weight_ct = area_ct * t_ct * density

        # Supports
        count = data['support_count']
        support_h = data['support_height']
        support_d_cm = data['support_diameter']
        support_t = data['support_thickness'] / 1000
        support_r = (support_d_cm / 100) / 2  # cm to m radius
        inner_r = support_r - support_t
        if inner_r < 0:
            inner_r = 0
        support_volume = math.pi * (support_r**2 - inner_r**2) * support_h
        weight_supports = support_volume * density * count

        weight_tank = weight_cyl + weight_cb + weight_ct
        weight_total = weight_tank + weight_supports
        weight_with_waste = weight_total * (1 + data['waste'] / 100)

        price_total = weight_with_waste * cost_per_kg

        # Reply with results
        response = f"وزن مخزن بدون پرتی: {weight_tank:.2f} کیلوگرم\n"
        response += f"وزن پایه‌ها: {weight_supports:.2f} کیلوگرم\n"
        response += f"وزن کلی: {weight_total:.2f} کیلوگرم\n"
        response += f"وزن کلی با پرتی: {weight_with_waste:.2f} کیلوگرم\n"
        response += f"قیمت کل: {price_total:.2f} تومان"
        await update.message.reply_text(response)

        return ConversationHandler.END
    except:
        await update.message.reply_text("خطا در محاسبه. لطفاً ورودی‌ها را بررسی کنید.")
        return ConversationHandler.END

# Calculation conversation handlers
async def calc_orientation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    orient = query.data  # 'vertical' or 'horizontal'
    context.user_data['calc'] = {'orientation': orient}
    # Ask what to find
    keyboard = [
        [InlineKeyboardButton("طول", callback_data='length')],
        [InlineKeyboardButton("حجم", callback_data='volume')],
        [InlineKeyboardButton("قطر", callback_data='diameter')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"مخزن {'عمودی' if orient == 'vertical' else 'افقی'} انتخاب شد.\n"
    text += "لطفا چیزی را که می‌خواهید محاسبه کنید انتخاب کنید:"
    await query.edit_message_text(text, reply_markup=reply_markup)
    return CALC_FIND

async def calc_find_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    find = query.data  # 'length', 'volume', 'diameter'
    context.user_data['calc']['find'] = find
    if find == 'volume':
        await query.edit_message_text("محاسبه حجم انتخاب شد.\nلطفا قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER
    elif find == 'length':
        await query.edit_message_text("محاسبه طول انتخاب شد.\nلطفا قطر مخزن (متر) را وارد کنید:")
        return CALC_DIAMETER
    elif find == 'diameter':
        await query.edit_message_text("محاسبه قطر انتخاب شد.\nلطفا طول مخزن (متر) را وارد کنید:")
        return CALC_LENGTH
    else:
        await query.edit_message_text("گزینه نامعتبر است.")
        return ConversationHandler.END

async def calc_diameter_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    find = context.user_data['calc']['find']
    try:
        value = float(update.message.text)
        if find == 'volume':
            context.user_data['calc']['diameter'] = value
            await update.message.reply_text("ارتفاع بدنه (متر) را وارد کنید:")
            return CALC_LENGTH
        elif find == 'length':
            context.user_data['calc']['diameter'] = value
            await update.message.reply_text("حجم مخزن (متر مکعب) را وارد کنید:")
            return CALC_VOLUME
        else:  # find == 'diameter'
            context.user_data['calc']['length'] = value
            await update.message.reply_text("حجم مخزن (متر مکعب) را وارد کنید:")
            return CALC_VOLUME
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return CALC_DIAMETER

async def calc_length_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    find = context.user_data['calc']['find']
    try:
        value = float(update.message.text)
        if find == 'volume':
            context.user_data['calc']['length'] = value
            await update.message.reply_text("ارتفاع قیف پایین (متر) را وارد کنید:")
            return CALC_BOTTOM_H
        elif find == 'length':
            context.user_data['calc']['volume'] = value
            await update.message.reply_text("ارتفاع قیف پایین (متر) را وارد کنید:")
            return CALC_BOTTOM_H
        else:  # find == 'diameter'
            context.user_data['calc']['volume'] = value
            await update.message.reply_text("ارتفاع قیف پایین (متر) را وارد کنید:")
            return CALC_BOTTOM_H
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return CALC_LENGTH

async def calc_bottom_h_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        value = float(update.message.text)
        context.user_data['calc']['cone_bottom_h'] = value
        await update.message.reply_text("ارتفاع قیف بالا (متر) را وارد کنید:")
        return CALC_TOP_H
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return CALC_BOTTOM_H

async def calc_top_h_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    find = context.user_data['calc']['find']
    orient = context.user_data['calc']['orientation']
    try:
        value = float(update.message.text)
        context.user_data['calc']['cone_top_h'] = value

        import math
        data = context.user_data['calc']
        if find == 'volume':
            d = data['diameter']
            L = data['length']
            h_b = data['cone_bottom_h']
            h_t = data['cone_top_h']
            r = d / 2
            vol_cyl = math.pi * r * r * L
            vol_cb = (1/3) * math.pi * r * r * h_b
            vol_ct = (1/3) * math.pi * r * r * h_t if orient == 'horizontal' else 0
            V_total = vol_cyl + vol_cb + vol_ct
            await update.message.reply_text(f"حجم مخزن: {V_total:.3f} متر مکعب")
        elif find == 'length':
            d = data['diameter']
            V = data['volume']
            h_b = data['cone_bottom_h']
            h_t = data['cone_top_h']
            r = d / 2
            vol_cb = (1/3) * math.pi * r * r * h_b
            vol_ct = (1/3) * math.pi * r * r * h_t if orient == 'horizontal' else 0
            try:
                L_calc = (V - vol_cb - vol_ct) / (math.pi * r * r)
                await update.message.reply_text(f"طول مخزن: {L_calc:.3f} متر")
            except:
                await update.message.reply_text("خطا در محاسبه طول. لطفا ورودی‌ها را بررسی کنید.")
        elif find == 'diameter':
            L = data['length']
            V = data['volume']
            h_b = data['cone_bottom_h']
            h_t = data['cone_top_h']
            try:
                part = L + (h_b/3) + (h_t/3 if orient == 'horizontal' else 0)
                if part == 0:
                    raise ValueError
                X = V / part
                r_sq = X / math.pi
                if r_sq < 0:
                    raise ValueError
                d_calc = 2 * math.sqrt(r_sq)
                await update.message.reply_text(f"قطر مخزن: {d_calc:.3f} متر")
            except:
                await update.message.reply_text("خطا در محاسبه قطر. لطفا ورودی‌ها را بررسی کنید.")

        return ConversationHandler.END
    except:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کنید.")
        return CALC_TOP_H

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات متوقف شد.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token('TOKEN').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_choice, pattern='^(pricing|calc)$')],
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
            PRICING_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cost)],

            ORIENTATION: [CallbackQueryHandler(calc_orientation, pattern='^(vertical|horizontal)$')],
            CALC_FIND: [CallbackQueryHandler(calc_find_choice, pattern='^(length|volume|diameter)$')],
            CALC_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_diameter_input)],
            CALC_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_length_input)],
            CALC_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_length_input)],
            CALC_BOTTOM_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_bottom_h_input)],
            CALC_TOP_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_top_h_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
