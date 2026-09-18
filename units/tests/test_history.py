import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from units.models import OwnershipHistory, TenancyHistory, Unit


class UnitHistoryTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.unit = Unit.objects.create(
            number=1, owner_name="مالک اول", owner_phone="09120000001",
            tenant_name="ساکن اول", tenant_phone="09120000002",
        )

    def test_detail_page_shows_histories(self):
        OwnershipHistory.objects.create(
            unit=self.unit, name="مالک اول", phone="09120000001",
            start_date=datetime.date(2024, 1, 1),
        )
        self.client.force_login(self.admin)
        resp = self.client.get(f"/units/{self.unit.pk}/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "مالک اول")
        self.assertContains(resp, "سوابق مالکیت")

    def test_owner_change_closes_previous_and_updates_unit(self):
        OwnershipHistory.objects.create(
            unit=self.unit, name="مالک اول", phone="09120000001",
            start_date=datetime.date(2024, 1, 1),
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            f"/units/{self.unit.pk}/change-owner/",
            {"name": "مالک دوم", "phone": "09120000009", "start_date": "1405/06/27"},
        )
        self.assertEqual(resp.status_code, 302)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.owner_name, "مالک دوم")
        old = OwnershipHistory.objects.get(name="مالک اول")
        self.assertIsNotNone(old.end_date)
        new = OwnershipHistory.objects.get(name="مالک دوم")
        self.assertIsNone(new.end_date)

    def test_tenant_change_closes_previous_and_updates_unit(self):
        TenancyHistory.objects.create(
            unit=self.unit, name="ساکن اول", phone="09120000002",
            start_date=datetime.date(2024, 1, 1),
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            f"/units/{self.unit.pk}/change-tenant/",
            {"name": "ساکن دوم", "phone": "09120000008", "start_date": "1405/06/27"},
        )
        self.assertEqual(resp.status_code, 302)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.tenant_name, "ساکن دوم")
        old = TenancyHistory.objects.get(name="ساکن اول")
        self.assertIsNotNone(old.end_date)

    def test_past_ownership_can_be_added(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            f"/units/{self.unit.pk}/past-owner/",
            {
                "name": "مالک قدیمی", "phone": "09120000007",
                "start_date": "1400/01/01", "end_date": "1402/05/10",
            },
        )
        self.assertEqual(resp.status_code, 302)
        rec = OwnershipHistory.objects.get(name="مالک قدیمی")
        self.assertEqual(str(rec.end_date), "2023-08-01")

    def test_nonstaff_cannot_change_owner(self):
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.post(
            f"/units/{self.unit.pk}/change-owner/",
            {"name": "هکر", "phone": "09000000000", "start_date": "1405/06/27"},
        )
        self.assertIn(resp.status_code, (302, 403))
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.owner_name, "مالک اول")
