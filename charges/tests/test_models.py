import datetime

from django.db import IntegrityError
from django.test import TestCase

from charges.models import ChargePlan, Payment
from units.models import Unit


class ChargePlanTest(TestCase):
    def test_unique_unit_year_months(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        ChargePlan.objects.create(unit=u1, year=1405, start_month=6, end_month=8, amount=500000)
        with self.assertRaises(IntegrityError):
            ChargePlan.objects.create(unit=u1, year=1405, start_month=6, end_month=8, amount=600000)

    def test_different_units_can_have_different_amounts(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        ChargePlan.objects.create(unit=u1, year=1405, start_month=6, end_month=8, amount=500000)
        ChargePlan.objects.create(unit=u2, year=1405, start_month=6, end_month=8, amount=700000)
        self.assertEqual(ChargePlan.objects.filter(year=1405, start_month=6).count(), 2)

    def test_end_before_start_rejected(self):
        from django.core.exceptions import ValidationError

        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        plan = ChargePlan(unit=u1, year=1405, start_month=8, end_month=6, amount=500000)
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test_period_display(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        single = ChargePlan(unit=u1, year=1405, start_month=6, end_month=6, amount=500000)
        self.assertEqual(single.period_display(), "شهریور 1405")
        ranged = ChargePlan(unit=u1, year=1405, start_month=6, end_month=8, amount=500000)
        self.assertEqual(ranged.period_display(), "شهریور تا آبان 1405")

    def test_other_income_without_month(self):
        u = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000000")
        p = Payment.objects.create(
            unit=u, year=1405, month=None, payer_kind="owner",
            payer_name="ب", paid_at=datetime.date(2026, 9, 1),
            amount=200000, kind="other", description="کمک تعمیرات",
        )
        self.assertEqual(p.kind, "other")
