from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from charges.models import Payment
from config.jalali_forms import JALALI_MONTH_CHOICES
from dashboard.services import fund_summary
from expenses.models import Expense
from units.models import Unit


def _scoped_payments(request):
    qs = Payment.objects.select_related("unit")
    if not request.user.is_staff:
        qs = qs.filter(unit__user=request.user)
    return qs


@login_required
def home(request):
    summary = fund_summary()
    payments = _scoped_payments(request).order_by("-paid_at")[:10]
    expenses = Expense.objects.select_related("category").order_by("-spent_at")[:10]
    return render(
        request,
        "dashboard/home.html",
        {"summary": summary, "payments": payments, "expenses": expenses},
    )


@login_required
def statement(request):
    payments = _scoped_payments(request)
    expenses = Expense.objects.select_related("category")

    unit_no = request.GET.get("unit", "").strip()
    year = request.GET.get("year", "").strip()
    month = request.GET.get("month", "").strip()

    if request.user.is_staff and unit_no:
        payments = payments.filter(unit__number=unit_no)
    if year:
        payments = payments.filter(year=year)
        expenses = expenses.filter(spent_at__year=int(year) - 621)
    if month:
        payments = payments.filter(month=month)

    paid_total = payments.aggregate(s=Sum("amount"))["s"] or 0
    spent_total = expenses.aggregate(s=Sum("amount"))["s"] or 0
    units = Unit.objects.all() if request.user.is_staff else Unit.objects.none()

    return render(
        request,
        "dashboard/statement.html",
        {
            "payments": payments.order_by("-paid_at"),
            "expenses": expenses.order_by("-spent_at"),
            "paid_total": paid_total,
            "spent_total": spent_total,
            "balance": paid_total - spent_total,
            "units": units,
            "filters": {"unit": unit_no, "year": year, "month": month},
            "jalali_months": JALALI_MONTH_CHOICES,
        },
    )
