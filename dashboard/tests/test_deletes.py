from django.contrib.auth.models import User
from django.test import TestCase

from charges.models import ChargePlan, IncomeType, Payment
from expenses.models import Expense, ExpenseCategory
from units.models import Unit
import datetime


class DeleteViewsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.user = User.objects.create_user("unit1", password="x")

    def test_staff_can_delete_unit(self):
        u = Unit.objects.create(number=9, owner_name="الف", owner_phone="09120000000")
        self.client.force_login(self.admin)
        resp = self.client.post(f"/units/{u.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Unit.objects.filter(pk=u.pk).exists())

    def test_nonstaff_cannot_delete_unit(self):
        u = Unit.objects.create(number=9, owner_name="الف", owner_phone="09120000000")
        self.client.force_login(self.user)
        resp = self.client.post(f"/units/{u.pk}/delete/")
        self.assertIn(resp.status_code, (302, 403))
        self.assertTrue(Unit.objects.filter(pk=u.pk).exists())

    def test_staff_can_delete_charge_plan(self):
        u = Unit.objects.create(number=9, owner_name="الف", owner_phone="09120000000")
        p = ChargePlan.objects.create(unit=u, year=1405, start_month=6, end_month=6, amount=500000)
        self.client.force_login(self.admin)
        resp = self.client.post(f"/payments/plans/{p.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ChargePlan.objects.filter(pk=p.pk).exists())

    def test_staff_can_delete_income_type(self):
        t = IncomeType.objects.create(title="تست", is_charge=False)
        self.client.force_login(self.admin)
        resp = self.client.post(f"/payments/income-types/{t.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(IncomeType.objects.filter(pk=t.pk).exists())

    def test_staff_can_delete_expense_category(self):
        c = ExpenseCategory.objects.create(title="تست")
        self.client.force_login(self.admin)
        resp = self.client.post(f"/expenses/categories/{c.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ExpenseCategory.objects.filter(pk=c.pk).exists())

    def test_staff_can_delete_payment(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        p = Payment.objects.create(
            unit=u, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(f"/payments/{p.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Payment.objects.filter(pk=p.pk).exists())

    def test_staff_can_delete_expense(self):
        c = ExpenseCategory.objects.create(title="تست")
        e = Expense.objects.create(
            category=c, spent_at=datetime.date(2026, 9, 1),
            amount=80000, description="تست",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(f"/expenses/{e.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Expense.objects.filter(pk=e.pk).exists())

    def test_category_with_expenses_not_deleted(self):
        c = ExpenseCategory.objects.create(title="تست")
        Expense.objects.create(
            category=c, spent_at=datetime.date(2026, 9, 1),
            amount=80000, description="تست",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(f"/expenses/categories/{c.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ExpenseCategory.objects.filter(pk=c.pk).exists())
