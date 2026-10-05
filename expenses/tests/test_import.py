import tempfile

import openpyxl
from django.test import TestCase

from expenses.management.commands.import_expenses import (
    import_expenses_from_sheet2,
    parse_amount,
)
from expenses.models import Expense, ExpenseCategory


def make_expense_workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet2"
    ws.append(["ردیف", "کد هزینه", "عنوان", "توضیحات", "شناسه قبض", "شناسه پرداخت", "تاریخ", "مبلغ"])
    for r in rows:
        ws.append(r)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


class ParseAmountTest(TestCase):
    def test_text_amount(self):
        self.assertEqual(parse_amount("358800"), 358800)

    def test_none_and_negative(self):
        self.assertIsNone(parse_amount(None))
        self.assertIsNone(parse_amount(-5))


class ImportExpensesTest(TestCase):
    def setUp(self):
        ExpenseCategory.objects.create(code="EXP-001", title="قبض آب", requires_bill_ids=True)
        ExpenseCategory.objects.create(code="EXP-004", title="نظافت")

    def test_valid_rows_imported(self):
        path = make_expense_workbook([
            (1, "EXP-001", "پرداخت قبض آب", "شماره قبض 1013", "B1", "P1", "1397/04/01", 43500),
            (2, "EXP-004", "نظافت", None, None, None, "1397/04/01", 30000),
        ])
        result = import_expenses_from_sheet2(path)
        self.assertEqual(result["created"], 2)
        self.assertEqual(result["errors"], [])
        bill = Expense.objects.get(amount=43500)
        self.assertEqual(bill.bill_id, "B1")
        self.assertEqual(bill.description, "شماره قبض 1013")
        plain = Expense.objects.get(amount=30000)
        self.assertEqual(plain.description, "نظافت")

    def test_bill_without_ids_imported(self):
        path = make_expense_workbook([
            (1, "EXP-001", "قبض آب", None, None, None, "1397/04/01", 50000),
        ])
        result = import_expenses_from_sheet2(path)
        self.assertEqual(result["created"], 1)

    def test_empty_date_imported(self):
        path = make_expense_workbook([
            (1, "EXP-004", "نظافت", None, None, None, None, 30000),
        ])
        result = import_expenses_from_sheet2(path)
        self.assertEqual(result["created"], 1)
        self.assertIsNone(Expense.objects.get().spent_at)

    def test_unknown_code_rejected(self):
        path = make_expense_workbook([
            (1, "EXP-999", "نامشخص", None, None, None, "1397/04/01", 1000),
        ])
        result = import_expenses_from_sheet2(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)
