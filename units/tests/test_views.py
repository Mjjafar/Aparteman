from django.contrib.auth.models import User
from django.test import TestCase

from units.models import Unit


class UnitUserAssignTest(TestCase):
    def test_set_login_redirects_to_combined_edit(self):
        unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get(f"/units/{unit.pk}/set-login/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, f"/units/{unit.pk}/edit/")


class UnitEditCombinedTest(TestCase):
    def test_edit_updates_profile_and_login_together(self):
        unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin2", "b@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            f"/units/{unit.pk}/edit/",
            {
                "number": 1,
                "owner_name": "مالک جدید",
                "owner_phone": "09120000009",
                "tenant_name": "",
                "tenant_phone": "",
                "username": "unit1",
                "password": "NewPass#1",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/units/")
        unit.refresh_from_db()
        self.assertEqual(unit.owner_name, "مالک جدید")
        self.assertEqual(unit.user.username, "unit1")
        self.assertTrue(unit.user.check_password("NewPass#1"))

    def test_edit_without_password_keeps_old_password(self):
        unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        user = User.objects.create_user("unit1", password="OldPass#1")
        unit.user = user
        unit.save()
        admin = User.objects.create_superuser("admin2", "b@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            f"/units/{unit.pk}/edit/",
            {
                "number": 1,
                "owner_name": "مالک جدید",
                "owner_phone": "09120000000",
                "tenant_name": "",
                "tenant_phone": "",
                "username": "unit1",
                "password": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        unit.refresh_from_db()
        self.assertTrue(unit.user.check_password("OldPass#1"))
