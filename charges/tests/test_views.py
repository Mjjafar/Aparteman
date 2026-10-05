from django.contrib.auth.models import User
from django.test import TestCase

from units.models import Unit

from charges.models import IncomeType


def ensure_charge_type():
    obj, _ = IncomeType.objects.get_or_create(
        code="INC-001", defaults={"title": "شارژ ماهیانه", "is_charge": True}
    )
    return obj




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
                "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/06/20", "amount": 500000, "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/06/20", "amount": 600000, "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/07/01", "amount": 600000, "income_type": ensure_charge_type().pk,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "بیشتر باشد")

    def test_zero_amount_rejected(self):
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405, "month": 7,
                "paid_at": "1405/07/01", "amount": 0, "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/07/01", "amount": 500000, "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/06/20", "amount": 500000, "income_type": ensure_charge_type().pk,
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
                "paid_at": "1405/06/20", "amount": 400000, "income_type": ensure_charge_type().pk,
            },
        )
        self.assertEqual(resp.status_code, 302)


class IncomeTypeCodeTest(TestCase):
    def test_create_assigns_code_automatically(self):
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/payments/income-types/new/",
            {"code": "IGNORED", "title": "درآمد تست"},
        )
        self.assertEqual(resp.status_code, 302)
        from charges.models import IncomeType

        obj = IncomeType.objects.get(title="درآمد تست")
        self.assertTrue(obj.code.startswith("INC-"))
        self.assertNotEqual(obj.code, "IGNORED")

    def test_list_shows_code(self):
        from charges.models import IncomeType

        IncomeType.objects.create(code="INC-011", title="ت")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/income-types/")
        self.assertContains(resp, "INC-011")
        self.assertNotContains(resp, "شرح")


class ChargePlanEditTest(TestCase):
    def test_staff_can_edit_charge_plan(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        from charges.models import ChargePlan

        p = ChargePlan.objects.create(
            unit=u, year=1405, start_month=1, end_month=6, amount=350000,
        )
        resp = self.client.post(
            f"/payments/plans/{p.pk}/edit/",
            {"unit": u.pk, "year": 1405, "start_month": 1, "end_month": 6, "amount": 400000},
        )
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.amount, 400000)

    def test_nonstaff_cannot_edit_charge_plan(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        from charges.models import ChargePlan

        p = ChargePlan.objects.create(
            unit=u, year=1405, start_month=1, end_month=6, amount=350000,
        )
        user = User.objects.create_user("unit1", password="x")
        self.client.force_login(user)
        resp = self.client.get(f"/payments/plans/{p.pk}/edit/")
        self.assertIn(resp.status_code, (302, 403))

    def test_list_has_row_numbers_and_edit_links(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        from charges.models import ChargePlan

        p = ChargePlan.objects.create(
            unit=u, year=1405, start_month=1, end_month=6, amount=350000,
        )
        resp = self.client.get("/payments/plans/")
        self.assertContains(resp, "ردیف")
        self.assertContains(resp, f"/payments/plans/{p.pk}/edit/")


class IncomeTypeAutoCodeTest(TestCase):
    def test_create_without_code_or_description(self):
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/payments/income-types/new/",
            {"title": "درآمد خودکار", "is_charge": False},
        )
        self.assertEqual(resp.status_code, 302)
        from charges.models import IncomeType

        obj = IncomeType.objects.get(title="درآمد خودکار")
        self.assertTrue(obj.code.startswith("INC-"))

    def test_form_has_no_code_field_but_has_description(self):
        from charges.forms import IncomeTypeForm

        form = IncomeTypeForm()
        self.assertNotIn("code", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("title", form.fields)


class PaymentListOrderingTest(TestCase):
    def test_ordered_by_income_year_month_unit_with_row_numbers(self):
        import datetime

        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        from charges.models import IncomeType, Payment

        t1 = IncomeType.objects.create(code="INC-001", title="شارژ", is_charge=True)
        t2 = IncomeType.objects.create(code="INC-002", title="تعمیرات")
        Payment.objects.create(unit=u1, year=1405, month=2, paid_at=datetime.date(2026, 9, 1), amount=100, kind="charge", income_type=t1)
        Payment.objects.create(unit=u2, year=1404, month=None, paid_at=datetime.date(2026, 9, 2), amount=200, kind="other", income_type=t2)
        Payment.objects.create(unit=u1, year=1405, month=1, paid_at=datetime.date(2026, 9, 3), amount=100, kind="charge", income_type=t1)
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/")
        rows = list(resp.context["payments"].values_list("income_type__code", "year", "month", "unit__number"))
        self.assertEqual(rows, [("INC-001", 1405, 1, 1), ("INC-001", 1405, 2, 1), ("INC-002", 1404, None, 2)])
        self.assertContains(resp, "ردیف")


class IncomeDescriptionTest(TestCase):
    def test_create_with_description_and_list_shows_it(self):
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(
            "/payments/income-types/new/",
            {"title": "درآمد توضیح‌دار", "description": "شرح تستی"},
        )
        self.assertEqual(resp.status_code, 302)
        from charges.models import IncomeType

        self.assertEqual(IncomeType.objects.get(title="درآمد توضیح‌دار").description, "شرح تستی")
        resp = self.client.get("/payments/income-types/")
        self.assertContains(resp, "شرح تستی")

    def test_payment_list_shows_description(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=u, year=1405, month=1, paid_at=datetime.date(2026, 9, 1),
            amount=100, kind="charge", description="یادداشت تستی",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/")
        self.assertContains(resp, "یادداشت تستی")


class PaymentNoteCheckboxTest(TestCase):
    def test_list_shows_checkbox_not_full_note(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(
            unit=u, year=1405, month=1, paid_at=datetime.date(2026, 9, 1),
            amount=100, kind="charge", description="یادداشت طولانی تستی",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/")
        self.assertContains(resp, 'class="note-tick"')
        content = resp.content.decode()
        body = content.split("<tbody>")[1].split("</tbody>")[0]
        self.assertNotIn(">یادداشت طولانی تستی<", body)
        self.assertIn('title="یادداشت طولانی تستی"', body)

    def test_edit_page_shows_full_note(self):
        import datetime

        from charges.models import Payment

        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        p = Payment.objects.create(
            unit=u, year=1405, month=1, paid_at=datetime.date(2026, 9, 1),
            amount=100, kind="charge", description="یادداشت طولانی تستی",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get(f"/payments/{p.pk}/edit/")
        self.assertContains(resp, "یادداشت طولانی تستی")


class PaymentIncomeTypeFieldTest(TestCase):
    def setUp(self):
        from charges.models import IncomeType

        self.unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        self.charge_type = IncomeType.objects.create(code="INC-001", title="شارژ ماهیانه", is_charge=True)
        self.repair_type = IncomeType.objects.create(code="INC-002", title="تعمیرات")
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_form_uses_income_type_not_kind(self):
        from charges.forms import PaymentForm

        form = PaymentForm()
        self.assertIn("income_type", form.fields)
        self.assertNotIn("kind", form.fields)
        labels = [c[1] for c in form.fields["income_type"].choices if c[0]]
        self.assertTrue(any("شارژ ماهیانه" in label for label in labels))

    def test_charge_payment_requires_month(self):
        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405,
                "income_type": self.charge_type.pk,
                "paid_at": "1405/06/20", "amount": 500000,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ماه اجباری")

    def test_other_income_without_month_accepted(self):
        from charges.models import Payment

        resp = self.client.post(
            "/payments/new/",
            {
                "unit": self.unit.pk, "year": 1405,
                "income_type": self.repair_type.pk,
                "paid_at": "1405/06/20", "amount": 200000,
            },
        )
        self.assertEqual(resp.status_code, 302)
        p = Payment.objects.get()
        self.assertEqual(p.kind, "other")
        self.assertIsNone(p.month)
        self.assertEqual(p.income_type.code, "INC-002")


class PaymentListFilterTest(TestCase):
    def setUp(self):
        import datetime

        from charges.models import IncomeType, Payment

        self.u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        self.u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        self.t1 = IncomeType.objects.create(code="INC-001", title="شارژ ماهیانه", is_charge=True)
        self.t2 = IncomeType.objects.create(code="INC-002", title="تعمیرات")
        Payment.objects.create(unit=self.u1, year=1404, month=5, paid_at=datetime.date(2026, 9, 1), amount=100, kind="charge", income_type=self.t1)
        Payment.objects.create(unit=self.u2, year=1405, month=1, paid_at=datetime.date(2026, 9, 2), amount=200, kind="charge", income_type=self.t1)
        Payment.objects.create(unit=self.u1, year=1405, month=None, paid_at=datetime.date(2026, 9, 3), amount=300, kind="other", income_type=self.t2)
        self.admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(self.admin)

    def test_no_code_in_type_column(self):
        resp = self.client.get("/payments/")
        body = resp.content.decode().split("<tbody>")[1].split("</tbody>")[0]
        self.assertNotIn("INC-001", body)
        self.assertContains(resp, "شارژ ماهیانه")

    def test_default_shows_all(self):
        resp = self.client.get("/payments/")
        self.assertEqual(len(resp.context["payments"]), 3)

    def test_filter_by_year(self):
        resp = self.client.get("/payments/?year=1405")
        self.assertEqual(len(resp.context["payments"]), 2)

    def test_filter_by_month(self):
        resp = self.client.get("/payments/?month=5")
        self.assertEqual(len(resp.context["payments"]), 1)

    def test_filter_by_income_type(self):
        resp = self.client.get(f"/payments/?income_type={self.t2.pk}")
        self.assertEqual(len(resp.context["payments"]), 1)

    def test_combined_filters(self):
        resp = self.client.get(f"/payments/?year=1405&income_type={self.t1.pk}")
        self.assertEqual(len(resp.context["payments"]), 1)

    def test_all_option_present(self):
        resp = self.client.get("/payments/")
        self.assertContains(resp, "همه موارد")
        self.assertContains(resp, "نمایش لیست همه رکوردها")


class PaymentResidentNameTest(TestCase):
    def test_list_shows_historical_resident(self):
        import datetime

        from charges.models import Payment
        from units.models import TenancyHistory

        u = Unit.objects.create(
            number=1, owner_name="مالک", owner_phone="09120000000",
            tenant_name="فعلی", tenant_phone="09120000009",
        )
        TenancyHistory.objects.create(
            unit=u, name="قدیمی", phone="09120000001",
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2020, 6, 1),
        )
        Payment.objects.create(
            unit=u, year=1397, month=4, paid_at=datetime.date(2018, 7, 1),
            amount=100, kind="charge",
        )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/")
        body = resp.content.decode().split("<tbody>")[1].split("</tbody>")[0]
        self.assertIn("قدیمی", body)
        self.assertNotIn("فعلی", body)


class PaymentUnitFilterTest(TestCase):
    def test_filter_by_unit_number(self):
        import datetime

        from charges.models import Payment

        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        for u in (u1, u2):
            Payment.objects.create(
                unit=u, year=1405, month=1, paid_at=datetime.date(2026, 9, 1),
                amount=100, kind="charge",
            )
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/payments/?unit=2")
        self.assertEqual(len(resp.context["payments"]), 1)
        self.assertEqual(resp.context["payments"][0].unit.number, 2)
        resp = self.client.get("/payments/")
        self.assertContains(resp, "شماره واحد")
