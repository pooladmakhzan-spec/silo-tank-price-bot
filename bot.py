from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

import math

# توکن شما
TOKEN = "8361649022:AAEkrO2nWlAxmrMLCbFhIoQry49vBKDjxDY"

# مراحل
CHOOSING_MODE, MODE1_THICKNESS, MODE1_DIAMETER, MODE1_HEIGHT, MODE1_CONE_HEIGHT, MODE1_CONE_THICKNESS, MODE1_NUM_LEGS, MODE1_LEG_HEIGHT, MODE1_LEG_DIAMETER, MODE1_LEG_THICKNESS, MODE1_WAGE, MODE1_WASTE, MODE2_CALC_TYPE, MODE2_KNOWN1, MODE2_KNOWN2, MODE2_CONE_HEIGHT, MODE2_ORIENTATION = range(17)

user_data_store = {}

# --- محاسبات وزن و قیمت ---
def calculate_tank_weight(thickness_mm, diameter_m, height_m, cone_height_cm, cone_thickness_mm):
    density = 7850
    thickness_m = thickness_mm / 1000
    cone_thickness_m = cone_thickness_mm / 1000
    radius = diameter_m / 2
    cone_height_m = cone_height_cm / 100

    # استوانه
    cylinder_area = 2 * math.pi * radius * height_m
    cylinder_weight = cylinder_area * thickness_m * density

    # قیف‌ها
    if cone_height_cm > 0:
        slant = math.sqrt(radius**2 + cone_height_m**2)
        cone_area = math.pi * radius * slant
        cones_weight = 2 * cone_area * cone_thickness_m * density
    else:
        cones_weight = 0

    return cylinder_weight + cones_weight

def calculate_leg_weight(num_legs, leg_height_cm, leg_diameter_inch, leg_thickness_mm):
    density = 7850
    leg_height_m = leg_height_cm / 100
    outer_radius_m = (leg_diameter_inch * 0.0254) / 2
    inner_radius_m = outer_radius_m - (leg_thickness_mm / 1000)
    leg_volume = math.pi * (outer_radius_m**2 - inner_radius_m**2) * leg_height_m
    leg_weight = leg_volume * density
    return num_legs * leg_weight

# --- محاسبات حجم/قطر/طول ---
def calculate_volume(diameter_m, height_m, cone_height_cm, orientation):
    radius = diameter_m / 2
    cone_height_m = cone_height_cm / 100

    cylinder_volume = math.pi * radius**2 * height_m
    cone_volume = (1/3) * math.pi * radius**2 * cone_height_m

    if orientation == "افقی":
        total_volume = cylinder_volume + 2 * cone_volume
    else:
        total_volume = cylinder_volume + cone_volume
    return total_volume

def calculate_length_from_volume(volume_liters, diameter_m, cone_height_cm, orientation):
    radius = diameter_m / 2
    cone_height_m = cone_height_cm / 100
    volume_m3 = volume_liters / 1000
    cone_volume = (1/3) * math.pi * radius**2 * cone_height_m

    if orientation == "افقی":
        length = (volume_m3 - 2 * cone_volume) / (math.pi * radius**2)
        total_length = length + 2 * cone_height_m
    else:
        length = (volume_m3 - cone_volume) / (math.pi * radius**2)
        total_length = length + cone_height_m
    return length, total_length

def calculate_diameter_from_volume(volume_liters, height_m, cone_height_cm, orientation):
    volume_m3 = volume_liters / 1000
    cone_height_m = cone_height_cm / 100

    def f(d):
        r = d / 2
        cylinder_volume = math.pi * r**2 * height_m
        cone_volume = (1/3) * math.pi * r**2 * cone_height_m
        return cylinder_volume + (2 * cone_volume if orientation == "افقی" else cone_volume) - volume_m3

    d = 1.0
    for _ in range(100):
        r = d / 2
        f_val = f(d)
        f_prime = (2 * math.pi * r * height_m + 
                   (2/3 if orientation == "افقی" else 1/3) * math.pi * r * cone_height_m)
        d -= f_val / f_prime
    return d

# --- شروع ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["محاسبه وزن و قیمت مخزن", "محاسبه حجم/قطر/طول"]]
    await update.message.reply_text("لطفاً یکی از گزینه‌ها را انتخاب کنید:", 
                                     reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CHOOSING_MODE

# ادامه کد برای حالت‌ها و محاسبات...
