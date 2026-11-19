from django.contrib.auth.models import User
from django.test import TestCase

from charges.models import ChargePlan, IncomeType, Payment
from notices.models import Notice, NoticeRow
from units.models import Unit


class NoticeViewTest(TestCase):
    def setUp(self):
        self.unit1 = Unit.objects.create(
            number=1, owner_name="مالک یک", owner_phone="09120000001",
            tenant_name="ساکن یک",
        )
        self.unit2 = Unit.objects.create(
            number=2, owner_name="مالک دو", owner_phone="09120000002"
        )
        ChargePlan.objects.create(
            unit=self.unit1, year=1405, start_month=1, end_month=3, amount=500000
        )
        ChargePlan.objects.create(
            unit=self.unit2, year=1405, start_month=1, end_month=3, amount=400000
        )
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        resp = self.client.get("/notices/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_non_staff_cannot_open_list(self):
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.get("/notices/")
        self.assertEqual(resp.status_code, 302)

    def test_preview_detects_charge_amounts(self):
        resp = self.client.post(
            "/notices/new/",
            {
                "year": 1405,
                "months": [1, 2],
                "work_title": "تعمیر آسانسور",
                "work_amount": 100000,
                "action": "preview",
            },
        )
        self.assertEqual(resp.status_code, 200)
        rows = {row["unit"].number: row for row in resp.context["preview_rows"]}
        self.assertEqual(rows[1]["charge_amount"], 1000000)  # 500000 × 2 ماه
        self.assertEqual(rows[1]["payable"], 1100000)
        self.assertEqual(rows[1]["work_share"], 100000)
        self.assertEqual(rows[1]["resident_name"], "ساکن یک")
        self.assertContains(resp, "تعمیر آسانسور")
        self.assertFalse(Notice.objects.exists())

    def test_preview_warns_about_missing_plans(self):
        resp = self.client.post(
            "/notices/new/",
            {"year": 1405, "months": [1, 4], "action": "preview"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["missing_plans"]), 2)
        self.assertContains(resp, "تعرفه حق شارژ ثبت نشده")

    def test_save_creates_notice_and_rows(self):
        resp = self.client.post(
            "/notices/new/",
            {
                "year": 1405,
                "months": [1, 2, 3],
                "work_title": "نقاشی راه‌پله",
                "work_amount": 50000,
                "action": "save",
            },
        )
        self.assertEqual(resp.status_code, 302)
        notice = Notice.objects.get()
        self.assertEqual(notice.months, [1, 2, 3])
        self.assertEqual(notice.work_title, "نقاشی راه‌پله")
        self.assertEqual(notice.created_by, self.admin)
        self.assertEqual(notice.rows.count(), 2)
        row = notice.rows.get(unit=self.unit1)
        self.assertEqual(row.charge_amount, 1500000)
        self.assertEqual(row.work_share, 50000)
        self.assertEqual(row.resident_name, "ساکن یک")
        self.assertEqual(resp.url, f"/notices/{notice.pk}/")

    def test_save_without_work_amount(self):
        self.client.post(
            "/notices/new/",
            {"year": 1405, "months": [1], "work_title": "", "work_amount": "", "action": "save"},
        )
        notice = Notice.objects.get()
        self.assertIsNone(notice.work_amount)
        self.assertEqual(notice.rows.get(unit=self.unit1).work_share, 0)

    def test_save_requires_at_least_one_month(self):
        resp = self.client.post(
            "/notices/new/", {"year": 1405, "months": [], "action": "save"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Notice.objects.exists())

    def test_detail_shows_live_payment_status(self):
        income = IncomeType.objects.create(
            code="INC-001", title="شارژ ماهیانه", is_charge=True
        )
        Payment.objects.create(
            unit=self.unit1, year=1405, month=1, amount=500000,
            kind="charge", income_type=income,
        )
        notice = Notice.objects.create(year=1405, months=[1, 2], work_title="")
        NoticeRow.objects.create(
            notice=notice, unit=self.unit1, resident_name="ساکن یک",
            charge_amount=1000000, work_share=0,
        )
        NoticeRow.objects.create(
            notice=notice, unit=self.unit2, resident_name="مالک دو",
            charge_amount=800000, work_share=0,
        )
        resp = self.client.get(f"/notices/{notice.pk}/")
        self.assertEqual(resp.status_code, 200)
        rows = {row["unit"].number: row for row in resp.context["rows"]}
        self.assertEqual(rows[1]["status"]["code"], "partial")
        self.assertEqual(rows[2]["status"]["code"], "unpaid")
        self.assertContains(resp, "پرداخت نشده")
        self.assertContains(resp, "جزئی")

    def test_delete_notice(self):
        notice = Notice.objects.create(year=1405, months=[1])
        resp = self.client.post(f"/notices/{notice.pk}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Notice.objects.exists())
