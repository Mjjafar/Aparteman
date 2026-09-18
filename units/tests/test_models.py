import datetime

from django.test import TestCase

from units.models import OwnershipHistory, TenancyHistory, Unit


class UnitModelTest(TestCase):
    def test_str_and_unique_number(self):
        u = Unit.objects.create(number=3, owner_name="رضا", owner_phone="09120000000")
        self.assertEqual(str(u), "واحد 3")

    def test_tenant_optional(self):
        u = Unit.objects.create(number=4, owner_name="مالک", owner_phone="09120000001")
        self.assertEqual(u.tenant_name, "")

    def test_ownership_history_order(self):
        u = Unit.objects.create(number=5, owner_name="اول", owner_phone="09120000000")
        OwnershipHistory.objects.create(
            unit=u, name="اول", phone="09120000000",
            start_date=datetime.date(2025, 1, 1),
        )
        OwnershipHistory.objects.create(
            unit=u, name="دوم", phone="09120000002",
            start_date=datetime.date(2026, 1, 1),
        )
        self.assertEqual(u.ownerships.first().name, "دوم")

    def test_tenancy_history_order(self):
        u = Unit.objects.create(number=6, owner_name="مالک", owner_phone="09120000000")
        TenancyHistory.objects.create(
            unit=u, name="ساکن اول", phone="09120000003",
            start_date=datetime.date(2025, 6, 1),
            end_date=datetime.date(2025, 12, 1),
        )
        TenancyHistory.objects.create(
            unit=u, name="ساکن دوم", phone="09120000004",
            start_date=datetime.date(2026, 1, 1),
        )
        self.assertEqual(u.tenancies.first().name, "ساکن دوم")
