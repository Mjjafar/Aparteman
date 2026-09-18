from dashboard.jalali import today_jalali_str
from dashboard.services import scoped_fund_summary


def fund_summary_context(request):
    ctx = {"today_jalali": today_jalali_str()}
    if request.user.is_authenticated:
        ctx["fund"] = scoped_fund_summary(request.user)
    return ctx
