import jdatetime
from django import template

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa_num(value):
    """English digits to Persian digits with thousand separators."""
    if value is None:
        return "—"
    try:
        grouped = f"{int(value):,}".replace(",", "٬")
    except (TypeError, ValueError):
        return str(value).translate(_FA_DIGITS)
    return grouped.translate(_FA_DIGITS)


@register.filter
def fa_date(value):
    """Gregorian date to Persian 'YYYY/MM/DD' string."""
    if not value:
        return "—"
    try:
        return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d").translate(
            _FA_DIGITS
        )
    except (ValueError, AttributeError):
        return str(value)
