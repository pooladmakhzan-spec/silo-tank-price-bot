import math
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"
STEEL_DENSITY = 7850  # kg/m³

# States
(
    MAIN_MENU,
    # Pricing
    P_DIA, P_HGT, P_BODY_T, P_CB_T, P_CT_T, P_CH, P_LC, P_LH, P_LD, P_LT, P_WASTE, P_WAGE,
    # Calc
    C_ORIENT, C_CH, C_CHHEIGHT, C_CHDIAM, C_CONE_H, C_PARAM1, C_PARAM2
) = range(20)

user_data = {}

# --- Start & Menu ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("💰 قیمت‌گذاری", callback_data="pricing")],
        [InlineKeyboardButton("📐 طول/قطر/حجم", callback_data="calc")]
    ]
    await update.message.reply_text("انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    user_data[uid] = {}
    if q.data == "pricing":
        await q.edit_message_text("قطر مخزن (متر) را وارد کنید:")
        return P_DIA
    else:
        kb = [
            [InlineKeyboardButton("عمودی", callback_data="vertical"),
             InlineKeyboardButton("افقی", callback_data="horizontal")]
        ]
        await q.edit_message_text("نوع مخزن؟", reply_markup=InlineKeyboardMarkup(kb))
        return C_ORIENT

# --- Pricing Flow ---
async def p_dia(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["d"] = float(update.message.text)
    await update.message.reply_text("ارتفاع (متر):")
    return P_HGT

async def p_hgt(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["h"] = float(update.message.text)
    await update.message.reply_text("ضخامت بدنه (میلی‌متر):")
    return P_BODY_T

async def p_body_t(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["t_body"] = float(update.message.text)/1000
    await update.message.reply_text("ضخامت قیف پایین (میلی‌متر):")
    return P_CB_T

async def p_cb_t(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["t_cb"] = float(update.message.text)/1000
    await update.message.reply_text("ضخامت قیف بالا (میلی‌متر):")
    return P_CT_T

async def p_ct_t(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["t_ct"] = float(update.message.text)/1000
    await update.message.reply_text("ارتفاع قیف‌ها (سانتی‌متر):")
    return P_CH

async def p_ch(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["ch"] = float(update.message.text)/100
    await update.message.reply_text("تعداد پایه‌ها:")
    return P_LC

async def p_lc(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["legs"] = int(update.message.text)
    await update.message.reply_text("ارتفاع پایه (سانتی‌متر):")
    return P_LH

async def p_lh(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["lh"] = float(update.message.text)/100
    await update.message.reply_text("قطر پایه (اینچ):")
    return P_LD

async def p_ld(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["ld"] = float(update.message.text)*0.0254
    await update.message.reply_text("ضخامت پایه (میلی‌متر):")
    return P_LT

async def p_lt(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["lt"] = float(update.message.text)/1000
    await update.message.reply_text("درصد پرتی (%):")
    return P_WASTE

async def p_waste(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["waste"] = float(update.message.text)/100
    await update.message.reply_text("دستمزد (تومان/کیلوگرم):")
    return P_WAGE

async def p_wage(update, ctx):
    uid = update.message.from_user.id
    w = float(update.message.text)
    d,h = user_data[uid]["d"],user_data[uid]["h"]
    t_body,t_cb,t_ct = user_data[uid]["t_body"],user_data[uid]["t_cb"],user_data[uid]["t_ct"]
    ch = user_data[uid]["ch"]
    legs,lh,ld,lt = user_data[uid]["legs"],user_data[uid]["lh"],user_data[uid]["ld"],user_data[uid]["lt"]
    waste = user_data[uid]["waste"]
    r = d/2
    # بدنه
    body_w = (2*math.pi*r*h)*t_body*STEEL_DENSITY
    # قیف پایین
    sl = math.hypot(r,ch)
    w_cb = (math.pi*r*sl)*t_cb*STEEL_DENSITY
    # قیف بالا
    w_ct = (math.pi*r*sl)*t_ct*STEEL_DENSITY
    # پایه
    base_w = legs*(2*math.pi*(ld/2)*lh*lt*STEEL_DENSITY)
    tank_w = body_w + w_cb + w_ct
    total = tank_w + base_w
    total_w = total*(1+waste)
    price = total_w*w
    await update.message.reply_text(
        f"وزن مخزن: {int(tank_w)} کیلوگرم\n"
        f"وزن پایه‌ها: {int(base_w)} کیلوگرم\n"
        f"وزن کل: {int(total)} کیلوگرم\n"
        f"پر تی({int(waste*100)}%): {int(total_w)} کیلوگرم\n"
        f"قیمت: {int(price):,} تومان"
    )
    return ConversationHandler.END

# --- Calc Flow ---

async def c_orient(update, ctx):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    user_data[uid] = {"orient":q.data}
    await q.edit_message_text("ارتفاع قیف (سانتی‌متر) را وارد کنید:")
    return C_CONE_H

async def c_cone_h(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["ch"] = float(update.message.text)/100
    kb = [
        [InlineKeyboardButton("محاسبه طول", callback_data="length"),
         InlineKeyboardButton("محاسبه قطر", callback_data="diameter")],
        [InlineKeyboardButton("محاسبه حجم", callback_data="volume")]
    ]
    await update.message.reply_text("چی محاسبه کنیم؟", reply_markup=InlineKeyboardMarkup(kb))
    return C_CH

async def c_ch(update, ctx):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id
    user_data[uid]["action"] = q.data
    if q.data=="length":
        await q.edit_message_text("قطر (متر)؟")
        return C_CHDIAM
    if q.data=="diameter":
        await q.edit_message_text("طول (متر)؟")
        return C_CHHEIGHT
    await q.edit_message_text("قطر (متر)؟")
    return C_CHDIAM

async def c_diam(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["d"] = float(update.message.text)
    await update.message.reply_text("حجم (لیتر)؟")
    return C_PARAM2

async def c_height(update, ctx):
    uid = update.message.from_user.id
    user_data[uid]["l"] = float(update.message.text)
    await update.message.reply_text("حجم (لیتر)؟")
    return C_PARAM2

async def c_param2(update, ctx):
    uid = update.message.from_user.id
    data = user_data[uid]
    orient,action,ch = data["orient"],data["action"],data["ch"]
    v_l = float(update.message.text)
    v_m3 = v_l/1000
    if action=="length":
        r = data["d"]/2
        cone_vol = math.pi*r*r*ch/3
        use = v_m3 - (2*cone_vol if orient=="horizontal" else cone_vol)
        length = use/(math.pi*r*r)
        await update.message.reply_text(f"طول ≈ {length:.2f} متر")
    elif action=="diameter":
        l = data["l"]
        cone_vol = math.pi*(data["d"]/2)**2*ch/3
        use = v_m3 - (2*cone_vol if orient=="horizontal" else cone_vol)
        diameter = math.sqrt(use/(math.pi*l))*2
        await update.message.reply_text(f"قطر ≈ {diameter:.2f} متر")
    else:  # volume
        r = data["d"]/2
        cone_vol = math.pi*r*r*ch/3
        cyl = math.pi*r*r*data["l"]
        total = cyl + (2*cone_vol if orient=="horizontal" else cone_vol)
        await update.message.reply_text(f"حجم ≈ {total*1000:.0f} لیتر")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            P_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_diameter)],
            P_HGT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_height)],
            P_BODY_T: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_body_thickness)],
            P_CB_T: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_bottom_thickness)],
            P_CT_T: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_top_thickness)],
            P_CH: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_cone_height)],
            P_LC: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_count)],
            P_LH: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_height)],
            P_LD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_diameter)],
            P_LT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_leg_thickness)],
            P_WASTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_waste)],
            P_WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pricing_wage)],

            C_ORIENT: [CallbackQueryHandler(c_orient)],
            C_CONE_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_cone_h)],
            C_CH: [CallbackQueryHandler(c_ch)],
            C_CHDIAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_diam)],
            C_CHHEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_height)],
            C_PARAM2: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_param2)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
