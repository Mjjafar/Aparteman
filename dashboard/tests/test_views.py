import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from charges.models import Payment
from units.models import Unit


class StatementTest(TestCase):
    def test_statement_filters_by_unit(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        Payment.objects.create(
            unit=u1, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/statement/?unit=1&year=1405&month=6")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "۵۰۰٬۰۰۰")

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
        self.assertNotContains(resp, "۵۰۰٬۰۰۰")


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
