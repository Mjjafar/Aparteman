from django.db.models import Sum

from charges.models import Payment
from expenses.models import Expense


def fund_summary():
    total_paid = Payment.objects.aggregate(s=Sum("amount"))["s"] or 0
    total_spent = Expense.objects.aggregate(s=Sum("amount"))["s"] or 0
    return {
        "total_paid": total_paid,
        "total_spent": total_spent,
        "balance": total_paid - total_spent,
    }


def unit_balance(unit):
    paid = (
        Payment.objects.filter(unit=unit).aggregate(s=Sum("amount"))["s"] or 0
    )
    return {"unit": unit, "total_paid": paid}


def scoped_fund_summary(user):
    """Fund cards: staff sees the whole building, a unit user sees only its unit."""
    if user.is_staff:
        return fund_summary()
    from units.models import Unit

    unit = Unit.objects.filter(user=user).first()
    if unit is None:
        return {"total_paid": 0, "total_spent": 0, "balance": 0}
    paid = Payment.objects.filter(unit=unit).aggregate(s=Sum("amount"))["s"] or 0
    return {"total_paid": paid, "total_spent": 0, "balance": paid}
