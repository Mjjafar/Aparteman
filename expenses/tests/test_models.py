import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from expenses.models import Expense, ExpenseCategory


class ExpenseBillIdsTest(TestCase):
    def test_bill_category_requires_ids(self):
        cat = ExpenseCategory.objects.create(title="قبض برق", requires_bill_ids=True)
        e = Expense(
            category=cat, spent_at=datetime.date(2026, 9, 1),
            amount=150000, description="برق مشاع",
        )
        with self.assertRaises(ValidationError):
            e.full_clean()

    def test_repair_without_ids_ok(self):
        cat = ExpenseCategory.objects.create(title="تعمیرات", requires_bill_ids=False)
        e = Expense(
            category=cat, spent_at=datetime.date(2026, 9, 1),
            amount=80000, description="قفل در",
        )
        e.full_clean()
