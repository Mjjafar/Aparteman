import jdatetime
from django import forms


class JalaliDateField(forms.DateField):
    """Accepts '1405/06/20', stores Gregorian date."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("input_formats", ["%Y/%m/%d"])
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str) and "/" in value:
            try:
                return jdatetime.datetime.strptime(value.strip(), "%Y/%m/%d").togregorian().date()
            except ValueError:
                raise forms.ValidationError("تاریخ شمسی معتبر نیست (مثل 1405/06/20).")
        return super().to_python(value)

    def prepare_value(self, value):
        if value is not None and hasattr(value, "year"):
            try:
                return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")
            except (ValueError, AttributeError):
                pass
        return super().prepare_value(value)


JALALI_MONTH_CHOICES = [
    (1, "فروردین"), (2, "اردیبهشت"), (3, "خرداد"), (4, "تیر"),
    (5, "مرداد"), (6, "شهریور"), (7, "مهر"), (8, "آبان"),
    (9, "آذر"), (10, "دی"), (11, "بهمن"), (12, "اسفند"),
]


class JalaliMonthField(forms.TypedChoiceField):
    """Dropdown of Persian month names, coerced to int 1-12."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", JALALI_MONTH_CHOICES)
        kwargs.setdefault("coerce", int)
        kwargs.setdefault("empty_value", None)
        super().__init__(*args, **kwargs)
