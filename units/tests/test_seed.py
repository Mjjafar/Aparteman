from django.test import TestCase

from expenses.models import ExpenseCategory
from units.models import Unit


class SeedTest(TestCase):
    fixtures = ["seed.json"]

    def test_seven_units_and_bill_categories(self):
        self.assertEqual(Unit.objects.count(), 7)
        self.assertTrue(
            ExpenseCategory.objects.filter(title="قبض برق مشاعات ساختمان", requires_bill_ids=True).exists()
        )
