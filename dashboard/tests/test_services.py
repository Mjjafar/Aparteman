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
        cat = ExpenseCategory.objects.create(title="قبض آب")
        Expense.objects.create(
            category=cat, spent_at=datetime.date(2026, 9, 3),
            amount=300000, description="آب",
        )
        s = fund_summary()
        self.assertEqual(s["total_paid"], 700000)
        self.assertEqual(s["total_spent"], 300000)
        self.assertEqual(s["balance"], 400000)
