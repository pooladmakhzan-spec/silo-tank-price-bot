from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

users_data = {}

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    users_data[chat_id] = {
        "state": "waiting_thickness",
        "thickness": None,
        "diameter": None,
        "height": None,
        "cone_height_top": None,
        "cone_height_bottom": None,
        "cone_thickness": None,
        "wage_per_kg": None,
        "cone_density": 7850,
        "pipe_density": 7850,
        "cone_small_radius": 0,
        "cone_big_radius": None,
        "cone_weight": 0,
        "cylinder_weight": 0,
        "cone_weight_top": 0,
        "cone_weight_bottom": 0,
        "base_count": None,
        "base_height_cm": None,
        "base_diameter_inch": None,
        "base_thickness_mm": None,
        "base_weight_total": 0,
        "waste_percent": None,
    }
    update.message.reply_text(
        "سلام! ضخامت بدنه مخزن به میلی‌متر رو وارد کن."
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if chat_id not in users_data:
        update.message.reply_text("لطفا ابتدا /start را بزنید.")
        return

    data = users_data[chat_id]
    state = data["state"]

    def to_float(value):
        try:
            return float(value.replace(",", "."))
        except:
            return None

    if state == "waiting_thickness":
        thickness = to_float(text)
        if thickness is None or thickness <= 0:
            update.message.reply_text("ضخامت باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["thickness"] = thickness / 1000  # میلی‌متر به متر
        data["state"] = "waiting_diameter"
        update.message.reply_text("قطر مخزن به متر را وارد کن.")
        return

    if state == "waiting_diameter":
        diameter = to_float(text)
        if diameter is None or diameter <= 0:
            update.message.reply_text("قطر باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["diameter"] = diameter
        data["state"] = "waiting_height"
        update.message.reply_text("ارتفاع بدنه مخزن به متر را وارد کن.")
        return

    if state == "waiting_height":
        height = to_float(text)
        if height is None or height <= 0:
            update.message.reply_text("ارتفاع باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["height"] = height
        data["state"] = "waiting_cone_height_top"
        update.message.reply_text("ارتفاع قیف بالای مخزن به سانتی‌متر را وارد کن.")
        return

    if state == "waiting_cone_height_top":
        cone_height_top = to_float(text)
        if cone_height_top is None or cone_height_top < 0:
            update.message.reply_text("ارتفاع قیف باید صفر یا مثبت باشد. دوباره وارد کن.")
            return
        data["cone_height_top"] = cone_height_top / 100  # سانتی‌متر به متر
        data["state"] = "waiting_cone_height_bottom"
        update.message.reply_text("ارتفاع قیف پایین مخزن به سانتی‌متر را وارد کن.")
        return

    if state == "waiting_cone_height_bottom":
        cone_height_bottom = to_float(text)
        if cone_height_bottom is None or cone_height_bottom < 0:
            update.message.reply_text("ارتفاع قیف باید صفر یا مثبت باشد. دوباره وارد کن.")
            return
        data["cone_height_bottom"] = cone_height_bottom / 100
        data["state"] = "waiting_cone_thickness"
        update.message.reply_text("ضخامت قیف به میلی‌متر را وارد کن.")
        return

    if state == "waiting_cone_thickness":
        cone_thickness = to_float(text)
        if cone_thickness is None or cone_thickness <= 0:
            update.message.reply_text("ضخامت قیف باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["cone_thickness"] = cone_thickness / 1000
        data["state"] = "waiting_wage"
        update.message.reply_text("دستمزد ساخت به ازای هر کیلوگرم (تومان) را وارد کن.")
        return

    if state == "waiting_wage":
        wage = to_float(text)
        if wage is None or wage <= 0:
            update.message.reply_text("دستمزد باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["wage_per_kg"] = wage
        data["state"] = "waiting_base_count"
        update.message.reply_text("تعداد پایه‌ها را وارد کن.")
        return

    if state == "waiting_base_count":
        base_count = to_float(text)
        if base_count is None or base_count < 0 or int(base_count) != base_count:
            update.message.reply_text("تعداد پایه باید عدد صحیح و غیرمنفی باشد. دوباره وارد کن.")
            return
        data["base_count"] = int(base_count)
        data["state"] = "waiting_base_height"
        update.message.reply_text("ارتفاع هر پایه به سانتی‌متر را وارد کن.")
        return

    if state == "waiting_base_height":
        base_height = to_float(text)
        if base_height is None or base_height <= 0:
            update.message.reply_text("ارتفاع پایه باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["base_height_cm"] = base_height
        data["state"] = "waiting_base_diameter"
        update.message.reply_text("قطر پایه به اینچ را وارد کن.")
        return

    if state == "waiting_base_diameter":
        base_diameter = to_float(text)
        if base_diameter is None or base_diameter <= 0:
            update.message.reply_text("قطر پایه باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["base_diameter_inch"] = base_diameter
        data["state"] = "waiting_base_thickness"
        update.message.reply_text("ضخامت پایه به میلی‌متر را وارد کن.")
        return

    if state == "waiting_base_thickness":
        base_thickness = to_float(text)
        if base_thickness is None or base_thickness <= 0:
            update.message.reply_text("ضخامت پایه باید عدد مثبت باشد. دوباره وارد کن.")
            return
        data["base_thickness_mm"] = base_thickness / 1000
        data["state"] = "waiting_waste_percent"
        update.message.reply_text("درصد ضایعات (پرتی) را وارد کن (مثلاً 10).")
        return

    if state == "waiting_waste_percent":
        waste_percent = to_float(text)
        if waste_percent is None or waste_percent < 0:
            update.message.reply_text("درصد پرتی باید عدد غیرمنفی باشد. دوباره وارد کن.")
            return
        data["waste_percent"] = waste_percent
        # حالا محاسبات انجام میشه:
        weight_cylinder = calc_cylinder_weight(
            data["diameter"],
            data["height"],
            data["thickness"]
        )
        weight_cone_top = calc_cone_weight(
            data["diameter"] / 2,
            data["cone_height_top"],
            data["cone_thickness"]
        )
        weight_cone_bottom = calc_cone_weight(
            data["diameter"] / 2,
            data["cone_height_bottom"],
            data["cone_thickness"]
        )
        total_cone_weight = weight_cone_top + weight_cone_bottom
        base_weight_total = 0
        if data["base_count"] > 0:
            base_weight_total = calc_pipe_weight(
                data["base_height_cm"] / 100,
                data["base_diameter_inch"] * 0.0254,
                data["base_thickness_mm"]
            ) * data["base_count"]

        total_weight = weight_cylinder + total_cone_weight + base_weight_total
        total_weight_with_waste = total_weight * (1 + data["waste_percent"] / 100)
        price = total_weight_with_waste * data["wage_per_kg"]

        result_message = (
            f"وزن استوانه: {round(weight_cylinder)} کیلوگرم\n"
            f"وزن قیف بالا: {round(weight_cone_top)} کیلوگرم\n"
            f"وزن قیف پایین: {round(weight_cone_bottom)} کیلوگرم\n"
            f"وزن کل قیف‌ها: {round(total_cone_weight)} کیلوگرم\n"
            f"وزن کل پایه‌ها: {round(base_weight_total)} کیلوگرم\n"
            f"وزن کل مخزن (بدنه + قیف + پایه): {round(total_weight)} کیلوگرم\n"
            f"وزن کل با احتساب {data['waste_percent']} درصد پرتی: {round(total_weight_with_waste)} کیلوگرم\n"
            f"قیمت نهایی: {round(price)} تومان"
        )

        update.message.reply_text(result_message)
        data["state"] = "done"
        return

    if state == "done":
        update.message.reply_text("برای شروع مجدد /start را بزنید.")
        return

def calc_cylinder_weight(diameter, height, thickness):
    import math
    radius = diameter / 2
    area = 2 * math.pi * radius * height  # سطح جانبی استوانه
    volume = area * thickness  # حجم ورق
    density = 7850  # چگالی فولاد کیلوگرم بر متر مکعب
    weight = volume * density
    return weight

def calc_cone_weight(radius, height, thickness):
    import math
    # وزن مخروط توخالی: مساحت سطح مخروط * ضخامت * چگالی
    slant_height = math.sqrt(height**2 + radius**2)
    lateral_area = math.pi * radius * slant_height  # سطح جانبی مخروط
    volume = lateral_area * thickness
    density = 7850
    weight = volume * density
    return weight

def calc_pipe_weight(height, diameter, thickness):
    import math
    outer_radius = diameter / 2
    inner_radius = outer_radius - thickness
    volume = math.pi * height * (outer_radius**2 - inner_radius**2)
    density = 7850
    weight = volume * density
    return weight

def reset(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in users_data:
        del users_data[chat_id]
    update.message.reply_text("داده‌های قبلی پاک شد. برای شروع دوباره /start را بزنید.")

def main():
    updater = Updater(token="8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("reset", reset))
    dispatcher.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
