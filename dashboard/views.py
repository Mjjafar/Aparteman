from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from charges.models import Payment
from config.jalali_forms import JALALI_MONTH_CHOICES
from dashboard.services import fund_summary
from expenses.models import Expense


def _scoped_payments(request):
    qs = Payment.objects.select_related("unit", "income_type")
    if not request.user.is_staff:
        qs = qs.filter(unit__user=request.user)
    return qs


@login_required
def home(request):
    summary = fund_summary()
    payments = _scoped_payments(request).order_by("-year", "-month", "unit__number")[:10]
    expenses = Expense.objects.select_related("category").order_by("-spent_at")[:10]
    return render(
        request,
        "dashboard/home.html",
        {"summary": summary, "payments": payments, "expenses": expenses},
    )


@login_required
def statement(request):
    from django.db.models import Count

    from charges.models import JALALI_MONTHS

    payments = _scoped_payments(request)
    expenses = Expense.objects.select_related("category")

    year = request.GET.get("year", "").strip()
    month = request.GET.get("month", "").strip()

    if year:
        payments = payments.filter(year=year)
        try:
            expenses = expenses.filter(spent_at__year=int(year) - 621)
        except ValueError:
            pass
    if month:
        payments = payments.filter(month=month)

    paid_total = payments.aggregate(s=Sum("amount"))["s"] or 0
    spent_total = expenses.aggregate(s=Sum("amount"))["s"] or 0

    payment_rows = list(
        payments.values("year", "month")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-year", "-month")
    )
    for row in payment_rows:
        row["month_name"] = JALALI_MONTHS[row["month"] - 1] if row["month"] else "—"

    payment_years = []
    for row in payment_rows:
        if payment_years and payment_years[-1]["year"] == row["year"]:
            group = payment_years[-1]
        else:
            group = {"year": row["year"], "total": 0, "count": 0, "months": []}
            payment_years.append(group)
        group["total"] += row["total"]
        group["count"] += row["count"]
        group["months"].append(row)

    expense_groups = {}
    for expense in expenses:
        if expense.spent_at:
            import jdatetime

            jdate = jdatetime.date.fromgregorian(date=expense.spent_at)
            key = (jdate.year, jdate.month)
        else:
            key = (None, None)
        group = expense_groups.setdefault(key, {"total": 0, "count": 0})
        group["total"] += expense.amount
        group["count"] += 1
    expense_rows = [
        {"year": year, "month": month, "total": group["total"], "count": group["count"]}
        for (year, month), group in sorted(
            expense_groups.items(), key=lambda item: ((item[0][0] or 0), (item[0][1] or 0)), reverse=True
        )
    ]
    for row in expense_rows:
        row["month_name"] = JALALI_MONTHS[row["month"] - 1] if row["month"] else "—"

    expense_years = []
    for row in expense_rows:
        if expense_years and expense_years[-1]["year"] == row["year"]:
            group = expense_years[-1]
        else:
            group = {"year": row["year"], "total": 0, "count": 0, "months": []}
            expense_years.append(group)
        group["total"] += row["total"]
        group["count"] += row["count"]
        group["months"].append(row)

    return render(
        request,
        "dashboard/statement.html",
        {
            "payment_rows": payment_rows,
            "payment_years": payment_years,
            "expense_rows": expense_rows,
            "expense_years": expense_years,
            "paid_total": paid_total,
            "spent_total": spent_total,
            "balance": paid_total - spent_total,
            "filters": {"year": year, "month": month},
            "jalali_months": JALALI_MONTH_CHOICES,
        },
    )
