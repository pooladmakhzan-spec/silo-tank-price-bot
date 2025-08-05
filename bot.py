from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# توکن ربات را اینجا وارد کن
BOT_TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# دیکشنری برای ذخیره موقت داده‌های هر کاربر
user_data = {}

# مراحل پرسش
questions = [
    "قطر مخزن را به متر وارد کنید:",
    "ارتفاع استوانه مخزن را به متر وارد کنید:",
    "ضخامت بدنه را به میلی‌متر وارد کنید:",
    "ارتفاع قیف بالایی را به سانتی‌متر وارد کنید:",
    "ارتفاع قیف پایینی را به سانتی‌متر وارد کنید:",
    "ضخامت قیف‌ها را به میلی‌متر وارد کنید:",
    "تعداد پایه‌ها را وارد کنید:",
    "ارتفاع هر پایه را به سانتی‌متر وارد کنید:",
    "قطر لوله پایه را به اینچ وارد کنید:",
    "ضخامت لوله پایه را به میلی‌متر وارد کنید:",
    "دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کنید:"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"step": 0, "answers": []}
    await update.message.reply_text("محاسبه قیمت مخزن و پایه‌ها آغاز شد.\n" + questions[0])

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data.pop(update.effective_user.id, None)
    await update.message.reply_text("داده‌های شما پاک شد. برای شروع دوباره دستور /start را وارد کنید.")

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        await update.message.reply_text("لطفاً با دستور /start محاسبه را آغاز کنید.")
        return

    try:
        value = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد وارد کنید.")
        return

    user_data[user_id]["answers"].append(value)
    step = user_data[user_id]["step"] + 1
    user_data[user_id]["step"] = step

    if step < len(questions):
        await update.message.reply_text(questions[step])
    else:
        result = calculate(user_data[user_id]["answers"])
        await update.message.reply_text(result)
        user_data.pop(user_id)

def calculate(data):
    # داده‌ها
    d_m, h_cyl, t_body_mm, h_cone_top_cm, h_cone_bottom_cm, t_cone_mm, n_legs, h_leg_cm, d_leg_inch, t_leg_mm, wage = data

    # ثابت‌ها
    density = 7850  # kg/m³
    pi = 3.1416

    # تبدیل واحدها
    r_m = d_m / 2
    t_body = t_body_mm / 1000
    h_cone_top = h_cone_top_cm / 100
    h_cone_bottom = h_cone_bottom_cm / 100
    t_cone = t_cone_mm / 1000
    h_leg = h_leg_cm / 100
    d_leg_outer = d_leg_inch * 0.0254
    t_leg = t_leg_mm / 1000

    # محاسبه وزن بدنه استوانه
    area_cyl = 2 * pi * r_m * h_cyl * t_body
    weight_cyl = area_cyl * density

    # محاسبه وزن قیف‌ها (شعاع کوچک تقریباً صفر)
    vol_cone_top = (pi * h_cone_top * (r_m ** 2)) / 3
    vol_cone_bottom = (pi * h_cone_bottom * (r_m ** 2)) / 3
    weight_cones = (vol_cone_top + vol_cone_bottom) * t_cone * density * (2 / (r_m))  # تخمین بر اساس ضخامت

    # وزن مخزن (بدنه + قیف‌ها)
    weight_tank = weight_cyl + weight_cones

    # محاسبه وزن پایه‌ها (لوله)
    d_leg_inner = d_leg_outer - 2 * t_leg
    area_leg = (pi / 4) * (d_leg_outer ** 2 - d_leg_inner ** 2)
    weight_leg = area_leg * h_leg * density
    weight_legs = weight_leg * n_legs

    # وزن کلی بدون پرتی
    total_weight = weight_tank + weight_legs

    # وزن با پرتی ۱۰ درصد
    total_weight_scrap = total_weight * 1.10

    # قیمت نهایی
    total_price = total_weight_scrap * wage

    # پیام خروجی
    result = (
        f"وزن مخزن (بدنه + قیف‌ها): {weight_tank:.2f} کیلوگرم\n"
        f"وزن پایه‌ها: {weight_legs:.2f} کیلوگرم\n"
        f"وزن کلی بدون پرتی: {total_weight:.2f} کیلوگرم\n"
        f"وزن کلی با احتساب ۱۰٪ پرتی: {total_weight_scrap:.2f} کیلوگرم\n"
        f"قیمت نهایی: {total_price:,.0f} تومان"
    )
    return result

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))
    app.run_polling()

if __name__ == "__main__":
    main()
