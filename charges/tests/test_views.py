from django.contrib.auth.models import User
from django.test import TestCase

from units.models import Unit


class PaymentAccessTest(TestCase):
    def test_unit_user_cannot_create_payment(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        user = User.objects.create_user("unit1", password="x")
        u.user = user
        u.save()
        self.client.force_login(user)
        resp = self.client.post("/payments/new/", {"amount": 1000})
        self.assertIn(resp.status_code, (302, 403))
        self.assertNotEqual(resp.status_code, 200)

    def test_staff_can_create_payment(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": u.pk,
                "year": 1405,
                "month": 6,
                "payer_kind": "tenant",
                "payer_name": "مستاجر",
                "paid_at": "1405/06/20",
                "amount": 500000,
                "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 302)


class UnitLabelTest(TestCase):
    def test_unit_dropdown_shows_tenant_or_owner(self):
        from charges.forms import ChargePlanForm, PaymentForm

        Unit.objects.create(
            number=1, owner_name="مالک یک", owner_phone="09120000001",
            tenant_name="ساکن یک", tenant_phone="09120000002",
        )
        Unit.objects.create(
            number=2, owner_name="مالک دو", owner_phone="09120000003",
        )
        plan_choices = [c[1] for c in ChargePlanForm().fields["unit"].choices if c[0]]
        pay_choices = [c[1] for c in PaymentForm().fields["unit"].choices if c[0]]
        self.assertIn("واحد 1 — ساکن یک", plan_choices)
        self.assertIn("واحد 2 — مالک دو", plan_choices)
        self.assertIn("واحد 1 — ساکن یک", pay_choices)
        self.assertIn("واحد 2 — مالک دو", pay_choices)


class PaymentEditTest(TestCase):
    def test_staff_can_edit_payment(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": u.pk, "year": 1405, "month": 6,
                "payer_kind": "tenant", "payer_name": "مستاجر",
                "paid_at": "1405/06/20", "amount": 500000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 302)
        from charges.models import Payment

        p = Payment.objects.get()
        resp = self.client.post(
            f"/payments/{p.pk}/edit/",
            {
                "unit": u.pk, "year": 1405, "month": 6,
                "payer_kind": "tenant", "payer_name": "مستاجر",
                "paid_at": "1405/06/20", "amount": 600000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.amount, 600000)

    def test_nonstaff_cannot_edit_payment(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        p = Payment.objects.create(
            unit=u, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.get(f"/payments/{p.pk}/edit/")
        self.assertIn(resp.status_code, (302, 403))


class PaymentChargeAutofillTest(TestCase):
    def setUp(self):
        from charges.models import ChargePlan

        self.unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        ChargePlan.objects.create(
            unit=self.unit, year=1405, start_month=6, end_month=8, amount=500000,
        )
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_charge_amount_api(self):
        resp = self.client.get(
            "/payments/charge-amount/",
            {"unit": self.unit.pk, "year": 1405, "month": 7},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"amount": 500000})

    def test_charge_amount_api_outside_period(self):
        resp = self.client.get(
            "/payments/charge-amount/",
            {"unit": self.unit.pk, "year": 1405, "month": 10},
        )
        self.assertEqual(resp.json(), {"amount": None})

    def test_form_has_no_payer_fields_but_has_charge_amount(self):
        from charges.forms import PaymentForm

        form = PaymentForm()
        self.assertNotIn("payer_kind", form.fields)
        self.assertNotIn("payer_name", form.fields)
        self.assertIn("charge_amount", form.fields)

    def test_amount_above_charge_rejected(self):
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 7,
                "payer_kind": "x", "payer_name": "x",
                "paid_at": "1405/07/01", "amount": 600000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "بیشتر باشد")

    def test_zero_amount_rejected(self):
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 7,
                "paid_at": "1405/07/01", "amount": 0, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "بیشتر از صفر")

    def test_valid_payment_accepted(self):
        from charges.models import Payment

        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 7,
                "paid_at": "1405/07/01", "amount": 500000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Payment.objects.count(), 1)


class JalaliMonthDisplayTest(TestCase):
    def test_month_dropdown_uses_persian_names(self):
        from charges.forms import ChargePlanForm, PaymentForm

        for form_cls, field in [
            (PaymentForm, "month"),
            (ChargePlanForm, "start_month"),
            (ChargePlanForm, "end_month"),
        ]:
            labels = [c[1] for c in form_cls().fields[field].choices if c[0]]
            self.assertIn("شهریور", labels)
            self.assertNotIn("6", labels)

    def test_tables_show_persian_month(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=u, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        for url in ["/payments/", "/statement/"]:
            resp = self.client.get(url)
            self.assertContains(resp, "شهریور")


class DuplicateChargePaymentTest(TestCase):
    def setUp(self):
        import datetime

        from charges.models import Payment

        self.unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=self.unit, year=1405, month=6,
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge",
        )
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_duplicate_charge_payment_rejected_in_form(self):
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 6,
                "paid_at": "1405/06/20", "amount": 500000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "تکراری")

    def test_duplicate_charge_payment_rejected_at_db(self):
        import datetime

        from django.db import IntegrityError

        from charges.models import Payment

        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                unit=self.unit, year=1405, month=6,
                paid_at=datetime.date(2026, 9, 2), amount=500000, kind="charge",
            )

    def test_other_income_can_repeat(self):
        import datetime

        from charges.models import Payment

        Payment.objects.create(
            unit=self.unit, year=1405, month=None,
            paid_at=datetime.date(2026, 9, 1), amount=100000, kind="other",
        )
        Payment.objects.create(
            unit=self.unit, year=1405, month=None,
            paid_at=datetime.date(2026, 9, 2), amount=200000, kind="other",
        )
        self.assertEqual(Payment.objects.filter(kind="other").count(), 2)

    def test_editing_same_record_is_allowed(self):
        import datetime

        from charges.models import Payment

        p = Payment.objects.get()
        resp = self.client.post(
            f"/payments/{p.pk}/edit/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 6,
                "paid_at": "1405/06/20", "amount": 400000, "kind": "charge",
            },
        )
        self.assertEqual(resp.status_code, 302)
