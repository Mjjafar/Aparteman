import jdatetime
from django.utils import timezone

WEEKDAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_fa_digits(value):
    return str(value).translate(_FA_DIGITS)


def today_jalali_str():
    now = timezone.localtime(timezone.now())
    j = jdatetime.datetime.fromgregorian(datetime=now)
    text = f"{WEEKDAYS_FA[j.weekday()]} {j.day} {MONTHS_FA[j.month - 1]} {j.year}"
    return to_fa_digits(text)
