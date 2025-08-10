from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import math

# مراحل کلی
CHOOSING_PRODUCT, TANK_THICKNESS, TANK_DIAMETER, TANK_HEIGHT, TANK_CONE_TOP, TANK_CONE_BOTTOM, TANK_WASTE, TANK_WAGE, \
SILO_DIAMETER, SILO_HEIGHT, SILO_CAPACITY, SILO_FRAME, SILO_BRACING, SILO_WASTE, SILO_WAGE, \
SCREW_LENGTH, SCREW_OUTER_DIAMETER, SCREW_OUTER_THICKNESS, SCREW_SHAFT_DIAMETER, SCREW_SHAFT_THICKNESS, SCREW_PITCH, SCREW_BLADE_THICKNESS, SCREW_BLADE_RADIUS, MOTOR_PRICE, LATHE_WAGE, TRANS_SHAFT_DIAMETER, TRANS_SHAFT_LENGTH, TRANS_SHAFT_PRICE, SCREW_WAGE = range(29)

steel_density = 7850  # kg/m3
user_data = {}

def reset_user_data(user_id):
    user_data.pop(user_id, None)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛢️ مخزن", callback_data='tank')],
        [InlineKeyboardButton("🌾 سیلو", callback_data='silo')],
        [InlineKeyboardButton("⚙️ اسکرو کانوایر", callback_data='screw')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام 👋\nلطفاً محصول مورد نظر را انتخاب کنید:", reply_markup=reply_markup)
    return CHOOSING_PRODUCT

async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    user_id = query.from_user.id
    reset_user_data(user_id)
    user_data[user_id] = {"product": choice}

    if choice == 'tank':
        await query.message.reply_text("🏗️ ضخامت بدنه مخزن (میلی‌متر) را وارد کنید:")
        return TANK_THICKNESS
    elif choice == 'silo':
        await query.message.reply_text("🌾 قطر سیلو (متر) را وارد کنید:")
        return SILO_DIAMETER
    elif choice == 'screw':
        await query.message.reply_text("⚙️ طول اسکرو (سانتی‌متر) را وارد کنید:")
        return SCREW_LENGTH

### مخزن ###
async def tank_thickness(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['tank_thickness'] = v
        await update.message.reply_text("📏 قطر بدنه مخزن (متر) را وارد کنید:")
        return TANK_DIAMETER
    except:
        await update.message.reply_text("❌ لطفاً عدد معتبر وارد کنید:")
        return TANK_THICKNESS

async def tank_diameter(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['tank_diameter'] = v
        await update.message.reply_text("📐 ارتفاع بدنه مخزن (متر) را وارد کنید:")
        return TANK_HEIGHT
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_DIAMETER

async def tank_height(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['tank_height'] = v
        await update.message.reply_text("🔻 ارتفاع قیف بالایی مخزن (سانتی‌متر) را وارد کنید:")
        return TANK_CONE_TOP
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_HEIGHT

async def tank_cone_top(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['tank_cone_top'] = v
        await update.message.reply_text("🔺 ارتفاع قیف پایینی مخزن (سانتی‌متر) را وارد کنید:")
        return TANK_CONE_BOTTOM
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_CONE_TOP

async def tank_cone_bottom(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['tank_cone_bottom'] = v
        await update.message.reply_text("⚠️ درصد پرتی فولاد (%) را وارد کنید:")
        return TANK_WASTE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_CONE_BOTTOM

async def tank_waste(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        if v < 0: raise ValueError()
        user_data[user_id]['tank_waste'] = v
        await update.message.reply_text("💰 دستمزد ساخت هر کیلوگرم (تومان) را وارد کنید:")
        return TANK_WAGE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_WASTE

async def tank_wage(update, context):
    user_id = update.message.from_user.id
    try:
        wage = int(update.message.text)
        if wage < 0: raise ValueError()
        data = user_data[user_id]
        data['tank_wage'] = wage
        # محاسبه وزن مخزن
        t = data['tank_thickness'] / 1000  # متر
        d = data['tank_diameter']
        r = d / 2
        h = data['tank_height']
        cone_top = data['tank_cone_top'] / 100  # متر
        cone_bottom = data['tank_cone_bottom'] / 100  # متر
        waste = data['tank_waste']

        # بدنه استوانه
        surface_cylinder = 2 * math.pi * r * h
        volume_cylinder = surface_cylinder * t

        # قیف‌ها (مخروط)
        volume_cone_top = (math.pi * r ** 2 * cone_top) / 3
        volume_cone_bottom = (math.pi * r ** 2 * cone_bottom) / 3

        # حجم ورق قیف = سطح مخروط * ضخامت ورق (تقریبی)
        volume_cone_top_steel = volume_cone_top * t
        volume_cone_bottom_steel = volume_cone_bottom * t

        total_volume = volume_cylinder + volume_cone_top_steel + volume_cone_bottom_steel

        weight = total_volume * steel_density
        weight_with_waste = weight * (1 + waste / 100)
        price = int(weight_with_waste * wage)

        text = (
            f"✅ محاسبه مخزن انجام شد:\n\n"
            f"⚖️ وزن بدون پرتی: {int(weight)} کیلوگرم\n"
            f"⚠️ وزن با پرتی: {int(weight_with_waste)} کیلوگرم\n"
            f"💰 قیمت کل: {price} تومان\n\n"
            "🔄 برای شروع مجدد /start را بزنید."
        )
        await update.message.reply_text(text)
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TANK_WAGE

### سیلو ###
async def silo_diameter(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['silo_diameter'] = v
        await update.message.reply_text("📐 ارتفاع سیلو (متر) را وارد کنید:")
        return SILO_HEIGHT
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_DIAMETER

async def silo_height(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['silo_height'] = v
        await update.message.reply_text("⚖️ ظرفیت سیلو (تن) را وارد کنید:")
        return SILO_CAPACITY
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_HEIGHT

async def silo_capacity(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['silo_capacity'] = v
        await update.message.reply_text("🧱 تعداد کلاف سیلو را وارد کنید:")
        return SILO_FRAME
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_CAPACITY

async def silo_frame(update, context):
    user_id = update.message.from_user.id
    try:
        v = int(update.message.text)
        user_data[user_id]['silo_frame'] = v
        await update.message.reply_text("🧱 تعداد بادبند سیلو را وارد کنید:")
        return SILO_BRACING
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_FRAME

async def silo_bracing(update, context):
    user_id = update.message.from_user.id
    try:
        v = int(update.message.text)
        user_data[user_id]['silo_bracing'] = v
        await update.message.reply_text("⚠️ درصد پرتی فولاد (%) را وارد کنید:")
        return SILO_WASTE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_BRACING

async def silo_waste(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['silo_waste'] = v
        await update.message.reply_text("💰 دستمزد ساخت هر کیلوگرم (تومان) را وارد کنید:")
        return SILO_WAGE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_WASTE

async def silo_wage(update, context):
    user_id = update.message.from_user.id
    try:
        wage = int(update.message.text)
        data = user_data[user_id]
        data['silo_wage'] = wage

        # محاسبه وزن سیلو (یک نمونه ساده است)
        t = 0.008  # فرض ضخامت ورق 8 میلی‌متر
        d = data['silo_diameter']
        r = d / 2
        h = data['silo_height']
        frame = data['silo_frame']
        bracing = data['silo_bracing']
        waste = data['silo_waste']

        # بدنه استوانه
        surface_cylinder = 2 * math.pi * r * h
        volume_cylinder = surface_cylinder * t

        # وزن اسکلت
        # فرض کنیم هر کلاف و بادبند 50 کیلوگرم است (میتونی تغییر بدی)
        weight_frame = (frame + bracing) * 50

        weight = volume_cylinder * steel_density + weight_frame
        weight_with_waste = weight * (1 + waste / 100)
        price = int(weight_with_waste * wage)

        text = (
            f"✅ محاسبه سیلو انجام شد:\n\n"
            f"⚖️ وزن بدون پرتی: {int(weight)} کیلوگرم\n"
            f"⚠️ وزن با پرتی: {int(weight_with_waste)} کیلوگرم\n"
            f"💰 قیمت کل: {price} تومان\n\n"
            "🔄 برای شروع مجدد /start را بزنید."
        )
        await update.message.reply_text(text)
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SILO_WAGE

### اسکرو کانوایر ###
async def screw_length(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_length'] = v
        await update.message.reply_text("📏 قطر خارجی اسکرو (سانتی‌متر) را وارد کنید:")
        return SCREW_OUTER_DIAMETER
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_LENGTH

async def screw_outer_diameter(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_outer_diameter'] = v
        await update.message.reply_text("⚙️ ضخامت خارجی اسکرو (میلی‌متر) را وارد کنید:")
        return SCREW_OUTER_THICKNESS
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_OUTER_DIAMETER

async def screw_outer_thickness(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_outer_thickness'] = v
        await update.message.reply_text("⚙️ قطر شفت داخلی اسکرو (میلی‌متر) را وارد کنید:")
        return SCREW_SHAFT_DIAMETER
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_OUTER_THICKNESS

async def screw_shaft_diameter(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_shaft_diameter'] = v
        await update.message.reply_text("⚙️ ضخامت شفت داخلی اسکرو (میلی‌متر) را وارد کنید:")
        return SCREW_SHAFT_THICKNESS
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_SHAFT_DIAMETER

async def screw_shaft_thickness(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_shaft_thickness'] = v
        await update.message.reply_text("📐 گام اسکرو (سانتی‌متر) را وارد کنید:")
        return SCREW_PITCH
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_SHAFT_THICKNESS

async def screw_pitch(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_pitch'] = v
        await update.message.reply_text("⚙️ ضخامت تیغه اسکرو (میلی‌متر) را وارد کنید:")
        return SCREW_BLADE_THICKNESS
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_PITCH

async def screw_blade_thickness(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_blade_thickness'] = v
        await update.message.reply_text("📏 شعاع تیغه اسکرو (سانتی‌متر) را وارد کنید:")
        return SCREW_BLADE_RADIUS
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_BLADE_THICKNESS

async def screw_blade_radius(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['screw_blade_radius'] = v
        await update.message.reply_text("💰 قیمت موتور اسکرو (تومان) را وارد کنید:")
        return MOTOR_PRICE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return SCREW_BLADE_RADIUS

async def motor_price(update, context):
    user_id = update.message.from_user.id
    try:
        v = int(update.message.text)
        user_data[user_id]['motor_price'] = v
        await update.message.reply_text("💰 دستمزد تراشکاری (تومان) را وارد کنید:")
        return LATHE_WAGE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return MOTOR_PRICE

async def lathe_wage(update, context):
    user_id = update.message.from_user.id
    try:
        v = int(update.message.text)
        user_data[user_id]['lathe_wage'] = v
        await update.message.reply_text("📏 قطر شفت انتقال (میلی‌متر) را وارد کنید:")
        return TRANS_SHAFT_DIAMETER
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return LATHE_WAGE

async def trans_shaft_diameter(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['trans_shaft_diameter'] = v
        await update.message.reply_text("📏 طول شفت انتقال (سانتی‌متر) را وارد کنید:")
        return TRANS_SHAFT_LENGTH
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TRANS_SHAFT_DIAMETER

async def trans_shaft_length(update, context):
    user_id = update.message.from_user.id
    try:
        v = float(update.message.text)
        user_data[user_id]['trans_shaft_length'] = v
        await update.message.reply_text("💰 قیمت شفت انتقال (تومان) را وارد کنید:")
        return TRANS_SHAFT_PRICE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TRANS_SHAFT_LENGTH

async def trans_shaft_price(update, context):
    user_id = update.message.from_user.id
    try:
        v = int(update.message.text)
        user_data[user_id]['trans_shaft_price'] = v
        await update.message.reply_text("💰 دستمزد ساخت اسکرو (تومان) را وارد کنید:")
        return SCREW_WAGE
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کنید:")
        return TRANS_SHAFT_PRICE

async def screw_wage(update, context):
    user_id = update.message.from_user.id
    try:
        wage = int(update.message.text)
        data = user_data[user_id]
        data['screw_wage'] = wage

        # محاسبه حجم و وزن اسکرو (تقریبی)
        length_m = data['screw_length'] / 100
        outer_d = data['screw_outer_diameter'] / 100
        outer_t = data['screw_outer_thickness'] / 1000
        shaft_d = data['screw_shaft_diameter'] / 1000
        shaft_t = data['screw_shaft_thickness'] / 1000
        blade_t = data['screw_blade_thickness'] / 1000
        blade_r = data['screw_blade_radius'] / 100
        pitch = data['screw_pitch'] / 100
        motor_price = data['motor_price']
        lathe_wage = data['lathe_wage']
        trans_d = data['trans_shaft_diameter'] / 1000
        trans_l = data['trans_shaft_length'] / 100
        trans_price = data['trans_shaft_price']

        # حجم لوله خارجی
        volume_outer = math.pi * ((outer_d / 2) ** 2) * length_m
        # حجم لوله داخلی (شفت)
        volume_shaft = math.pi * ((shaft_d / 2) ** 2) * length_m
        # حجم فولاد بدنه لوله = حجم لوله خارجی - حجم لوله داخلی
        volume_pipe_steel = volume_outer - volume_shaft

        # حجم تیغه اسکرو (تقریبی: تیغه ضخامت * طول * عرض (π*r) )
        volume_blade = blade_t * length_m * (2 * math.pi * blade_r)

        # حجم شفت انتقال
        volume_trans_shaft = math.pi * ((trans_d / 2) ** 2) * trans_l

        total_volume = volume_pipe_steel + volume_blade + volume_trans_shaft

        weight = total_volume * steel_density

        total_price = int(weight * wage + motor_price + lathe_wage + trans_price)

        text = (
            f"✅ محاسبه اسکرو کانوایر انجام شد:\n\n"
            f"⚖️ وزن کل: {int(weight)} کیلوگرم\n"
            f"💰 قیمت کل: {total_price} تومان\n\n"
            "🔄 برای شروع مجدد /start را بزنید."
        )
        await update.message.reply_text(text)
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("❌ خطا در ورودی‌ها یا محاسبه، لطفاً عدد معتبر وارد کنید.")
        return SCREW_WAGE

async def cancel(update, context):
    await update.message.reply_text("❌ عملیات لغو شد. برای شروع مجدد /start را بزنید.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token("8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_PRODUCT: [CallbackQueryHandler(choose_product)],

            # مخزن
            TANK_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_thickness)],
            TANK_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_diameter)],
            TANK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_height)],
            TANK_CONE_TOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_top)],
            TANK_CONE_BOTTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_cone_bottom)],
            TANK_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_waste)],
            TANK_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tank_wage)],

            # سیلو
            SILO_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_diameter)],
            SILO_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_height)],
            SILO_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_capacity)],
            SILO_FRAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_frame)],
            SILO_BRACING: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_bracing)],
            SILO_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_waste)],
            SILO_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, silo_wage)],

            # اسکرو
            SCREW_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_length)],
            SCREW_OUTER_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_diameter)],
            SCREW_OUTER_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_outer_thickness)],
            SCREW_SHAFT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_diameter)],
            SCREW_SHAFT_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_shaft_thickness)],
            SCREW_PITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_pitch)],
            SCREW_BLADE_THICKNESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_blade_thickness)],
            SCREW_BLADE_RADIUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_blade_radius)],
            MOTOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, motor_price)],
            LATHE_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lathe_wage)],
            TRANS_SHAFT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_diameter)],
            TRANS_SHAFT_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_length)],
            TRANS_SHAFT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trans_shaft_price)],
            SCREW_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, screw_wage)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
