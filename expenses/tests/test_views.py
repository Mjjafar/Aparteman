from django.contrib.auth.models import User
from django.test import TestCase


class ExpenseAccessTest(TestCase):
    def test_unit_user_cannot_create_expense(self):
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.post("/expenses/new/", {"amount": 1000})
        self.assertIn(resp.status_code, (302, 403))
        self.assertNotEqual(resp.status_code, 200)

    def test_staff_can_create_expense(self):
        from expenses.models import ExpenseCategory

        cat = ExpenseCategory.objects.create(title="تعمیرات")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/expenses/new/",
            {
                "category": cat.pk,
                "spent_at": "1405/06/20",
                "amount": 80000,
                "description": "قفل در",
            },
        )
        self.assertEqual(resp.status_code, 302)


class ExpenseEditTest(TestCase):
    def test_staff_can_edit_expense(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        cat = ExpenseCategory.objects.create(title="تعمیرات")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/expenses/new/",
            {
                "category": cat.pk, "spent_at": "1405/06/20",
                "amount": 80000, "description": "قفل در",
            },
        )
        self.assertEqual(resp.status_code, 302)
        e = Expense.objects.get()
        resp = self.client.post(
            f"/expenses/{e.pk}/edit/",
            {
                "category": cat.pk, "spent_at": "1405/06/21",
                "amount": 90000, "description": "قفل در و پنجره",
            },
        )
        self.assertEqual(resp.status_code, 302)
        e.refresh_from_db()
        self.assertEqual(e.amount, 90000)
        self.assertEqual(e.description, "قفل در و پنجره")

    def test_nonstaff_cannot_edit_expense(self):
        import datetime

        from django.contrib.auth.models import User

        from expenses.models import Expense, ExpenseCategory

        cat = ExpenseCategory.objects.create(title="تعمیرات")
        e = Expense.objects.create(
            category=cat, spent_at=datetime.date(2026, 9, 1),
            amount=80000, description="تست",
        )
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.get(f"/expenses/{e.pk}/edit/")
        self.assertIn(resp.status_code, (302, 403))
