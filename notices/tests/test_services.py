from django.test import TestCase

from charges.models import ChargePlan, IncomeType, Payment
from notices.services import (
    attach_status,
    build_rows,
    detect_charge,
    payment_status,
    totals_for,
)
from units.models import Unit


def make_unit(number, tenant=""):
    return Unit.objects.create(
        number=number,
        owner_name=f"مالک {number}",
        owner_phone="09120000000",
        tenant_name=tenant,
    )


class ChargeDetectionTest(TestCase):
    def setUp(self):
        self.unit1 = make_unit(1, tenant="ساکن یک")
        self.unit2 = make_unit(2)
        ChargePlan.objects.create(
            unit=self.unit1, year=1405, start_month=1, end_month=3, amount=500000
        )
        ChargePlan.objects.create(
            unit=self.unit2, year=1405, start_month=2, end_month=2, amount=300000
        )

    def test_sums_selected_months(self):
        total, missing = detect_charge(self.unit1, 1405, [1, 2, 3])
        self.assertEqual(total, 1500000)
        self.assertEqual(missing, [])

    def test_reports_months_without_plan(self):
        total, missing = detect_charge(self.unit2, 1405, [1, 2, 3])
        self.assertEqual(total, 300000)
        self.assertEqual(missing, [1, 3])

    def test_latest_plan_wins_on_overlap(self):
        ChargePlan.objects.create(
            unit=self.unit1, year=1405, start_month=2, end_month=2, amount=600000
        )
        total, _ = detect_charge(self.unit1, 1405, [2])
        self.assertEqual(total, 600000)

    def test_other_year_is_ignored(self):
        total, missing = detect_charge(self.unit1, 1404, [1])
        self.assertEqual(total, 0)
        self.assertEqual(missing, [1])


class BuildRowsTest(TestCase):
    def setUp(self):
        self.unit = make_unit(1, tenant="ساکن یک")
        ChargePlan.objects.create(
            unit=self.unit, year=1405, start_month=1, end_month=2, amount=400000
        )

    def test_resident_name_and_work_share(self):
        rows, missing = build_rows(1405, [1, 2], work_amount=250000)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["resident_name"], "ساکن یک")
        self.assertEqual(row["charge_amount"], 800000)
        self.assertEqual(row["work_share"], 250000)
        self.assertEqual(missing, [])

    def test_missing_plan_is_reported_per_unit(self):
        _, missing = build_rows(1405, [1, 2, 3], work_amount=0)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["unit"], self.unit)
        self.assertEqual(missing[0]["months"], [3])
        self.assertIn("خرداد", missing[0]["months_display"])


class PaymentStatusTest(TestCase):
    def setUp(self):
        self.unit1 = make_unit(1)
        self.unit2 = make_unit(2)
        self.unit3 = make_unit(3)
        self.income = IncomeType.objects.create(
            code="INC-001", title="شارژ ماهیانه", is_charge=True
        )
        for month in (1, 2):
            Payment.objects.create(
                unit=self.unit1, year=1405, month=month, amount=500000,
                kind="charge", income_type=self.income,
            )
        Payment.objects.create(
            unit=self.unit2, year=1405, month=1, amount=500000,
            kind="charge", income_type=self.income,
        )

    def test_partial_paid_and_unpaid(self):
        statuses = payment_status(
            1405, [1, 2, 3], [self.unit1.pk, self.unit2.pk, self.unit3.pk]
        )
        self.assertEqual(statuses[self.unit1.pk]["code"], "partial")
        self.assertEqual(statuses[self.unit1.pk]["paid_count"], 2)
        self.assertEqual(statuses[self.unit2.pk]["code"], "partial")
        self.assertEqual(statuses[self.unit3.pk]["code"], "unpaid")

    def test_all_months_paid(self):
        Payment.objects.create(
            unit=self.unit1, year=1405, month=3, amount=500000,
            kind="charge", income_type=self.income,
        )
        statuses = payment_status(1405, [1, 2, 3], [self.unit1.pk])
        self.assertEqual(statuses[self.unit1.pk]["code"], "paid")

    def test_other_kind_does_not_count_as_paid(self):
        Payment.objects.create(
            unit=self.unit3, year=1405, month=None, amount=500000,
            kind="other", income_type=self.income,
        )
        statuses = payment_status(1405, [1], [self.unit3.pk])
        self.assertEqual(statuses[self.unit3.pk]["code"], "unpaid")

    def test_payment_of_other_year_does_not_count(self):
        Payment.objects.create(
            unit=self.unit3, year=1404, month=1, amount=500000,
            kind="charge", income_type=self.income,
        )
        statuses = payment_status(1405, [1], [self.unit3.pk])
        self.assertEqual(statuses[self.unit3.pk]["code"], "unpaid")


class AttachAndTotalsTest(TestCase):
    def setUp(self):
        self.unit = make_unit(1)
        ChargePlan.objects.create(
            unit=self.unit, year=1405, start_month=1, end_month=1, amount=100000
        )

    def test_payable_and_totals(self):
        rows, _ = build_rows(1405, [1], work_amount=50000)
        rows = attach_status(rows, 1405, [1])
        self.assertEqual(rows[0]["payable"], 150000)
        totals = totals_for(rows)
        self.assertEqual(totals, {"charge": 100000, "work": 50000, "payable": 150000})
