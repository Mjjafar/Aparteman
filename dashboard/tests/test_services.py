import datetime

from django.test import TestCase

from charges.models import Payment
from dashboard.services import fund_summary
from expenses.models import Expense, ExpenseCategory
from units.models import Unit


class FundSummaryTest(TestCase):
    def test_balance_counts_other_income(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=u, year=1405, month=6, payer_kind="tenant", payer_name="مستاجر",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        Payment.objects.create(
            unit=u, year=1405, month=None, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 2), amount=200000, kind="other",
        )
        cat = ExpenseCategory.objects.create(code="EXP-001", title="قبض آب مشترک کل ساختمان")
        Expense.objects.create(
            category=cat, spent_at=datetime.date(2026, 9, 3),
            amount=300000, description="آب",
        )
        s = fund_summary()
        self.assertEqual(s["total_paid"], 700000)
        self.assertEqual(s["total_spent"], 300000)
        self.assertEqual(s["balance"], 400000)


class BuildingFundForUnitUserTest(TestCase):
    def test_unit_user_sees_building_totals_plus_own(self):
        from django.contrib.auth.models import User

        from dashboard.services import scoped_fund_summary
        from expenses.models import Expense, ExpenseCategory
        from units.models import Unit

        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        user = User.objects.create_user("unit1", password="x")
        u1.user = user
        u1.save()
        Payment.objects.create(unit=u1, year=1405, month=6, paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge")
        Payment.objects.create(unit=u2, year=1405, month=6, paid_at=datetime.date(2026, 9, 2), amount=300000, kind="charge")
        cat = ExpenseCategory.objects.create(code="EXP-T01", title="تست")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 3), amount=200000, description="x")
        fund = scoped_fund_summary(user)
        self.assertEqual(fund["total_paid"], 800000)
        self.assertEqual(fund["total_spent"], 200000)
        self.assertEqual(fund["balance"], 600000)
        self.assertEqual(fund["own_paid"], 500000)

    def test_staff_has_no_own_card(self):
        from django.contrib.auth.models import User

        from dashboard.services import scoped_fund_summary

        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        fund = scoped_fund_summary(admin)
        self.assertNotIn("own_paid", fund)
