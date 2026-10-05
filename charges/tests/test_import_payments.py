import datetime
import tempfile

import openpyxl
from django.test import TestCase

from charges.management.commands.import_payments import (
    import_payments_from_sheet1,
    parse_jalali_date,
)
from charges.models import Payment
from units.models import Unit


def make_payments_workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Type", "year", "mounth", "unit", "Name", "charg", "pardakht", "date", None])
    for r in rows:
        ws.append(r)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


class ParseJalaliDateTest(TestCase):
    def test_eight_digit(self):
        self.assertEqual(parse_jalali_date("13970427"), datetime.date(2018, 7, 18))

    def test_slash(self):
        self.assertEqual(parse_jalali_date("1398/11/11"), datetime.date(2020, 1, 31))

    def test_empty_and_invalid(self):
        self.assertIsNone(parse_jalali_date(None))
        self.assertIsNone(parse_jalali_date("  "))
        self.assertIsNone(parse_jalali_date("1398/13/08"))

    def test_known_typo_fixed(self):
        import datetime

        self.assertEqual(parse_jalali_date("1398/17/08"), datetime.date(2019, 9, 30))


class ImportPaymentsTest(TestCase):
    def setUp(self):
        self.unit1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        self.unit2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")

    def test_valid_rows_imported_with_empty_date(self):
        path = make_payments_workbook([
            ("INC-001", 1405, 1, 1, "ساکن", 350000, 350000, "1405/3/31", None),
            ("INC-001", 1405, 2, 1, "ساکن", 350000, 350000, None, None),
        ])
        result = import_payments_from_sheet1(path)
        self.assertEqual(result["created"], 2)
        self.assertEqual(result["errors"], [])
        dated = Payment.objects.get(year=1405, month=1)
        self.assertEqual(str(dated.paid_at), "2026-06-21")
        undated = Payment.objects.get(year=1405, month=2)
        self.assertIsNone(undated.paid_at)

    def test_zero_amount_imported(self):
        path = make_payments_workbook([
            ("INC-001", 1403, 2, 2, "ساکن", 200000, 0, "1403/3/8", None),
        ])
        result = import_payments_from_sheet1(path)
        self.assertEqual(result["created"], 1)
        self.assertEqual(Payment.objects.get().amount, 0)

    def test_non_inc001_skipped(self):
        path = make_payments_workbook([
            ("INC-002", 1398, 6, 1, "ساکن", 200000, 200000, "1398/06/20", None),
        ])
        result = import_payments_from_sheet1(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(Payment.objects.count(), 0)


class ImportOtherIncomeTest(TestCase):
    def setUp(self):
        from charges.models import IncomeType

        self.unit1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        IncomeType.objects.create(code="INC-002", title="تعمیرات")

    def test_other_income_imported_with_income_type(self):
        from charges.management.commands.import_payments import import_payments_from_sheet1
        from charges.models import Payment
        from charges.tests.test_import_payments import make_payments_workbook

        path = make_payments_workbook([
            ("INC-002", 1398, 6, 1, "ساکن", 200000, 200000, "1398/06/20", "حق تعمیرات"),
        ])
        result = import_payments_from_sheet1(path)
        self.assertEqual(result["created"], 1)
        p = Payment.objects.get()
        self.assertEqual(p.kind, "other")
        self.assertIsNone(p.month)
        self.assertEqual(p.income_type.code, "INC-002")
        self.assertEqual(p.payer_name, "ساکن")
        self.assertEqual(p.description, "حق تعمیرات")

    def test_unknown_income_code_rejected(self):
        from charges.management.commands.import_payments import import_payments_from_sheet1
        from charges.models import Payment
        from charges.tests.test_import_payments import make_payments_workbook

        path = make_payments_workbook([
            ("INC-999", 1398, 6, 1, "ساکن", 200000, 200000, "1398/06/20", "x"),
        ])
        result = import_payments_from_sheet1(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(Payment.objects.count(), 0)
