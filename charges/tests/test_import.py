import tempfile

import openpyxl
from django.test import TestCase

from charges.management.commands.import_chargeplans import (
    import_chargeplans_from_sheet2,
)
from charges.models import ChargePlan
from units.models import Unit


def make_workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet2"
    ws.append(["unit", "year", "mounth1", "month2", "name", "charg"])
    for r in rows:
        ws.append(r)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


class ImportChargePlansTest(TestCase):
    def setUp(self):
        self.unit1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        self.unit2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")

    def test_valid_rows_imported(self):
        path = make_workbook([
            (1, 1397, 4, 5, "ساکن", 25000),
            (2, 1397, 4, 5, "ساکن", 30000),
        ])
        result = import_chargeplans_from_sheet2(path)
        self.assertEqual(result["created"], 2)
        self.assertEqual(result["errors"], [])
        plan = ChargePlan.objects.get(unit=self.unit1, year=1397, start_month=4)
        self.assertEqual(plan.end_month, 5)
        self.assertEqual(plan.amount, 25000)

    def test_zero_amount_skipped_with_error(self):
        path = make_workbook([(1, 1397, 4, 5, "ساکن", 0)])
        result = import_chargeplans_from_sheet2(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(ChargePlan.objects.count(), 0)

    def test_reversed_months_rejected(self):
        path = make_workbook([(1, 1403, 7, 2, "ساکن", 50000)])
        result = import_chargeplans_from_sheet2(path)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(ChargePlan.objects.count(), 0)

    def test_duplicate_key_updates(self):
        ChargePlan.objects.create(
            unit=self.unit1, year=1397, start_month=4, end_month=5, amount=10000,
        )
        path = make_workbook([(1, 1397, 4, 5, "ساکن", 25000)])
        result = import_chargeplans_from_sheet2(path)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(ChargePlan.objects.get().amount, 25000)

    def test_dry_run_saves_nothing(self):
        path = make_workbook([(1, 1397, 4, 5, "ساکن", 25000)])
        result = import_chargeplans_from_sheet2(path, dry_run=True)
        self.assertEqual(result["created"], 1)
        self.assertEqual(ChargePlan.objects.count(), 0)
