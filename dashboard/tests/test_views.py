import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from charges.models import Payment
from units.models import Unit


class StatementTest(TestCase):
    def test_statement_ignores_unit_param_and_sums_all_units(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        Payment.objects.create(
            unit=u1, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        Payment.objects.create(
            unit=u2, year=1405, month=6, payer_kind="owner", payer_name="ب",
            paid_at=datetime.date(2026, 9, 2), amount=300000, kind="charge",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/statement/?unit=1&year=1405&month=6")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "۸۰۰٬۰۰۰")

    def test_unit_user_sees_only_own_statement(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        user = User.objects.create_user("unit1", password="x")
        u1.user = user
        u1.save()
        Payment.objects.create(
            unit=u2, year=1405, month=6, payer_kind="owner", payer_name="ب",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        self.client.force_login(user)
        resp = self.client.get("/statement/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode().split("<main")[1]
        self.assertNotIn("۵۰۰٬۰۰۰", body)


class PagesSmokeTest(TestCase):
    def test_all_pages_render_rtl(self):
        User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(User.objects.get(username="admin"))
        for url in ["/", "/statement/", "/payments/", "/expenses/", "/expenses/categories/"]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, msg=url)
            self.assertContains(resp, 'dir="rtl"')


class PersianNumbersTest(TestCase):
    def test_amounts_render_persian(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=u, year=1405, month=6,
            paid_at=datetime.date(2026, 9, 1), amount=1500000, kind="charge",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/")
        self.assertContains(resp, "۱٬۵۰۰٬۰۰۰")
        self.assertContains(resp, "۱۴۰۵/۰۶/۱۰")

    def test_change_owner_form_defaults_to_today(self):
        import jdatetime

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        today = jdatetime.date.today().strftime("%Y/%m/%d")
        resp = self.client.get(f"/units/{u.pk}/change-owner/")
        self.assertContains(resp, f'value="{today}"')


class MobileLayoutTest(TestCase):
    def test_tables_have_horizontal_scroll_wrapper(self):
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        for url in ["/payments/", "/expenses/", "/statement/", "/units/"]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, msg=url)
            self.assertContains(resp, "table-scroll", msg_prefix=url)


class DashboardHomePaymentsTest(TestCase):
    def test_home_shows_latest_period_first_with_row_numbers(self):
        import datetime

        from charges.models import IncomeType, Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        t = IncomeType.objects.create(code="INC-001", title="شارژ ماهیانه", is_charge=True)
        Payment.objects.create(unit=u, year=1397, month=4, paid_at=datetime.date(2026, 9, 1), amount=100, kind="charge", income_type=t)
        Payment.objects.create(unit=u, year=1405, month=6, paid_at=None, amount=200, kind="charge", income_type=t)
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/")
        rows = list(resp.context["payments"].values_list("year", "month"))
        self.assertEqual(rows, [(1405, 6), (1397, 4)])
        self.assertContains(resp, "ردیف")
        body = resp.content.decode().split("آخرین پرداخت")[1].split("</tbody>")[0]
        self.assertIn("الف", body)


class StatementMonthlySummaryTest(TestCase):
    def setUp(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        Payment.objects.create(unit=u1, year=1405, month=6, paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge")
        Payment.objects.create(unit=u2, year=1405, month=6, paid_at=datetime.date(2026, 9, 2), amount=300000, kind="charge")
        Payment.objects.create(unit=u1, year=1405, month=5, paid_at=datetime.date(2026, 8, 1), amount=100000, kind="charge")
        cat = ExpenseCategory.objects.create(code="EXP-T01", title="تست")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 3), amount=200000, description="الف")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 4), amount=50000, description="ب")
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_payment_rows_grouped_by_year_month(self):
        resp = self.client.get("/statement/")
        rows = list(resp.context["payment_rows"])
        self.assertEqual([(r["year"], r["month"], r["total"], r["count"]) for r in rows],
                         [(1405, 6, 800000, 2), (1405, 5, 100000, 1)])

    def test_expense_rows_grouped_by_year_month(self):
        resp = self.client.get("/statement/")
        rows = list(resp.context["expense_rows"])
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["total"], rows[0]["count"]), (250000, 2))

    def test_filters_apply_to_groups(self):
        resp = self.client.get("/statement/?year=1405&month=6")
        self.assertEqual(len(resp.context["payment_rows"]), 1)


class StatementYearGroupsTest(TestCase):
    def test_payments_grouped_by_year_with_months(self):
        import datetime

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(unit=u, year=1405, month=6, paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge")
        Payment.objects.create(unit=u, year=1405, month=5, paid_at=datetime.date(2026, 8, 1), amount=300000, kind="charge")
        Payment.objects.create(unit=u, year=1404, month=12, paid_at=datetime.date(2025, 3, 1), amount=100000, kind="charge")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/statement/")
        groups = list(resp.context["payment_years"])
        self.assertEqual([(g["year"], g["total"], g["count"]) for g in groups],
                         [(1405, 800000, 2), (1404, 100000, 1)])
        months = [m["month"] for m in groups[0]["months"]]
        self.assertEqual(months, [6, 5])
        self.assertContains(resp, "year-group-1405")
        self.assertContains(resp, "year-months-1405")


class StatementExpenseYearGroupsTest(TestCase):
    def test_expenses_grouped_by_year_with_months(self):
        import datetime

        from expenses.models import Expense, ExpenseCategory

        cat = ExpenseCategory.objects.create(code="EXP-T01", title="تست")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 3), amount=200000, description="الف")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 4), amount=50000, description="ب")
        Expense.objects.create(category=cat, spent_at=datetime.date(2025, 3, 1), amount=100000, description="ج")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/statement/")
        groups = list(resp.context["expense_years"])
        self.assertEqual([(g["year"], g["total"], g["count"]) for g in groups],
                         [(1405, 250000, 2), (1403, 100000, 1)])
        self.assertContains(resp, "exp-year-months-1405")
