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

        cat = ExpenseCategory.objects.create(code="EXP-T01", title="تعمیرات")
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

        cat = ExpenseCategory.objects.create(code="EXP-T02", title="تعمیرات")
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

        cat = ExpenseCategory.objects.create(code="EXP-T03", title="تعمیرات")
        e = Expense.objects.create(
            category=cat, spent_at=datetime.date(2026, 9, 1),
            amount=80000, description="تست",
        )
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.get(f"/expenses/{e.pk}/edit/")
        self.assertIn(resp.status_code, (302, 403))


class ExpenseCategoryAutoCodeTest(TestCase):
    def test_create_without_code_assigns_next(self):
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/expenses/categories/",
            {"title": "تست خودکار", "requires_bill_ids": False},
        )
        self.assertEqual(resp.status_code, 302)
        from expenses.models import ExpenseCategory

        obj = ExpenseCategory.objects.get(title="تست خودکار")
        self.assertTrue(obj.code.startswith("EXP-"))
        resp = self.client.get("/expenses/categories/")
        self.assertNotContains(resp, 'name="code"')


class ExpenseListFilterTest(TestCase):
    def setUp(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        self.c1 = ExpenseCategory.objects.create(code="EXP-001", title="قبض آب")
        self.c2 = ExpenseCategory.objects.create(code="EXP-002", title="نظافت")
        Expense.objects.create(category=self.c1, spent_at=datetime.date(2026, 9, 2), amount=100, description="ب")
        Expense.objects.create(category=self.c2, spent_at=datetime.date(2026, 9, 1), amount=200, description="الف")
        Expense.objects.create(category=self.c1, spent_at=None, amount=300, description="بدون تاریخ")
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_ordered_by_date_oldest_first(self):
        resp = self.client.get("/expenses/")
        got = list(resp.context["expenses"].values_list("amount", flat=True))
        self.assertEqual(got, [200, 100, 300])

    def test_filter_by_category(self):
        resp = self.client.get(f"/expenses/?category={self.c1.pk}")
        self.assertEqual(len(resp.context["expenses"]), 2)

    def test_all_option_present(self):
        resp = self.client.get("/expenses/")
        self.assertContains(resp, "همه موارد")
        self.assertContains(resp, "نوع هزینه")


class ExpenseFilterTotalTest(TestCase):
    def test_filtered_total_shown(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        c1 = ExpenseCategory.objects.create(code="EXP-001", title="قبض آب")
        c2 = ExpenseCategory.objects.create(code="EXP-002", title="نظافت")
        Expense.objects.create(category=c1, spent_at=datetime.date(2026, 9, 1), amount=100000, description="ب")
        Expense.objects.create(category=c2, spent_at=datetime.date(2026, 9, 2), amount=50000, description="الف")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get(f"/expenses/?category={c1.pk}")
        self.assertEqual(resp.context["filtered_total"], 100000)
        self.assertContains(resp, "۱۰۰٬۰۰۰")

    def test_no_total_without_filter(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        c1 = ExpenseCategory.objects.create(code="EXP-001", title="قبض آب")
        Expense.objects.create(category=c1, spent_at=datetime.date(2026, 9, 1), amount=100000, description="ب")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/expenses/")
        self.assertNotContains(resp, "filter-total")


class ExpenseDescriptionOptionalTest(TestCase):
    def test_create_without_description(self):
        from expenses.models import Expense, ExpenseCategory

        cat = ExpenseCategory.objects.create(code="EXP-T99", title="تست")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/expenses/new/",
            {"category": cat.pk, "spent_at": "1405/06/20", "amount": 1000},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Expense.objects.get().description, "")

    def test_edit_without_description(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        cat = ExpenseCategory.objects.create(code="EXP-T99", title="تست")
        e = Expense.objects.create(
            category=cat, spent_at=datetime.date(2026, 9, 1),
            amount=1000, description="قدیمی",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            f"/expenses/{e.pk}/edit/",
            {"category": cat.pk, "spent_at": "1405/06/20", "amount": 2000},
        )
        self.assertEqual(resp.status_code, 302)
        e.refresh_from_db()
        self.assertEqual(e.description, "")
