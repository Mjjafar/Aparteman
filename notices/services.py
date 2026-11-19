"""تشخیص حق شارژ از تعرفه‌ها و محاسبه وضعیت پرداخت هر واحد."""

from charges.models import JALALI_MONTHS, ChargePlan, Payment
from notices.models import join_fa
from units.models import Unit


def charge_for_month(unit, year, month):
    """مبلغ حق شارژ واحد در یک ماه شمسی؛ در صورت چند تعرفه، آخرین ثبت‌شده ملاک است."""
    plan = (
        ChargePlan.objects.filter(
            unit=unit, year=year, start_month__lte=month, end_month__gte=month
        )
        .order_by("-pk")
        .first()
    )
    return plan.amount if plan else None


def detect_charge(unit, year, months):
    """جمع حق شارژ ماه‌های انتخابی + ماه‌هایی که تعرفه ندارند."""
    total = 0
    missing = []
    for month in months:
        amount = charge_for_month(unit, year, month)
        if amount is None:
            missing.append(month)
        else:
            total += amount
    return total, missing


def payment_status(year, months, unit_ids):
    """وضعیت پرداخت شارژ هر واحد برای ماه‌های اطلاعیه.

    یک ماه «پرداخت‌شده» است اگر برای همان واحد/سال/ماه رکورد پرداخت
    از نوع شارژ ماهیانه ثبت شده باشد.
    """
    months = sorted({int(m) for m in months})
    total = len(months)
    paid_map = {}
    if months and unit_ids:
        payments = Payment.objects.filter(
            kind="charge", year=year, month__in=months, unit_id__in=unit_ids
        ).values_list("unit_id", "month")
        for unit_id, month in payments:
            paid_map.setdefault(unit_id, set()).add(month)

    statuses = {}
    for unit_id in unit_ids:
        paid_count = len(paid_map.get(unit_id, set()))
        if total and paid_count >= total:
            code = "paid"
        elif paid_count:
            code = "partial"
        else:
            code = "unpaid"
        statuses[unit_id] = {"code": code, "paid_count": paid_count, "total": total}
    return statuses


def build_rows(year, months, work_amount=0):
    """ردیف‌های اطلاعیه: حق شارژ هر واحد از تعرفه تشخیص داده می‌شود."""
    months = sorted({int(m) for m in months})
    rows = []
    missing = []
    for unit in Unit.objects.order_by("number"):
        charge, missing_months = detect_charge(unit, year, months)
        if missing_months:
            missing.append(
                {
                    "unit": unit,
                    "months": missing_months,
                    "months_display": join_fa(
                        JALALI_MONTHS[m - 1] for m in missing_months
                    ),
                }
            )
        rows.append(
            {
                "unit": unit,
                "resident_name": unit.resident_at(year, months[-1]) if months else "",
                "charge_amount": charge,
                "work_share": work_amount or 0,
            }
        )
    return rows, missing


def attach_status(rows, year, months):
    """افزودن مبلغ قابل پرداخت و وضعیت پرداخت به ردیف‌ها."""
    statuses = payment_status(year, months, [r["unit"].pk for r in rows])
    for row in rows:
        row["payable"] = row["charge_amount"] + row["work_share"]
        row["status"] = statuses[row["unit"].pk]
    return rows


def totals_for(rows):
    return {
        "charge": sum(r["charge_amount"] for r in rows),
        "work": sum(r["work_share"] for r in rows),
        "payable": sum(r["payable"] for r in rows),
    }
