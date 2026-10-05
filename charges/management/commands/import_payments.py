import jdatetime
import openpyxl
from django.core.management.base import BaseCommand, CommandError

from charges.models import IncomeType, Payment
from units.models import Unit


def parse_jalali_date(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(" ", "")
    if not s:
        return None
    if s == "1398/17/08":
        s = "1398/07/08"
    try:
        if "/" in s:
            parts = [int(p) for p in s.split("/")]
            if len(parts) != 3:
                return None
            y, m, d = parts
        elif len(s) == 8 and s.isdigit():
            y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
        else:
            return None
        return jdatetime.date(y, m, d).togregorian()
    except (ValueError, TypeError):
        return None


def import_payments_from_sheet1(path, dry_run=False):
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except FileNotFoundError:
        raise CommandError(f"فایل پیدا نشد: {path}")
    if "Sheet1" not in wb.sheetnames:
        raise CommandError("شیت Sheet1 در فایل پیدا نشد.")
    ws = wb["Sheet1"]

    units = {u.number: u for u in Unit.objects.all()}
    income_types = {t.code: t for t in IncomeType.objects.all()}
    created, skipped, errors = 0, 0, []

    for lineno, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if lineno == 1:
            continue
        cells = (list(row) + [None] * 9)[:9]
        kind_code, year, month, unit_no, payer_name, _charge, amount, raw_date, note = cells
        payer_name = str(payer_name).strip() if payer_name else ""
        note = str(note).strip() if note else ""
        if kind_code is None and year is None and unit_no is None:
            skipped += 1
            continue
        kind_code = str(kind_code).strip()
        is_charge = kind_code == "INC-001"
        if not is_charge and kind_code not in income_types:
            errors.append(f"سطر {lineno}: کد درآمد «{kind_code}» در جدول انواع درآمد نیست.")
            continue
        try:
            unit_no = int(unit_no)
            year = int(year)
        except (TypeError, ValueError):
            errors.append(f"سطر {lineno}: واحد/سال عدد نیست.")
            continue
        if unit_no not in units:
            errors.append(f"سطر {lineno}: واحد {unit_no} در سامانه نیست.")
            continue
        if is_charge:
            try:
                month = int(month)
            except (TypeError, ValueError):
                errors.append(f"سطر {lineno}: ماه عدد نیست.")
                continue
            if not 1 <= month <= 12:
                errors.append(f"سطر {lineno}: ماه باید بین ۱ تا ۱۲ باشد.")
                continue
        else:
            month = None
        if amount is None:
            amount = 0
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            errors.append(f"سطر {lineno}: مبلغ عدد نیست.")
            continue
        if amount < 0:
            errors.append(f"سطر {lineno}: مبلغ منفی است.")
            continue
        paid_at = parse_jalali_date(raw_date)
        if raw_date is not None and str(raw_date).strip() and paid_at is None:
            errors.append(f"سطر {lineno}: تاریخ «{raw_date}» معتبر نیست.")
            continue
        if dry_run:
            created += 1
            continue
        if is_charge:
            _obj, was_created = Payment.objects.update_or_create(
                unit=units[unit_no], year=year, month=month, kind="charge",
                defaults={
                    "amount": amount, "paid_at": paid_at,
                    "payer_name": payer_name, "description": note,
                },
            )
            created += 1 if was_created else 0
        else:
            Payment.objects.create(
                unit=units[unit_no], year=year, month=None, kind="other",
                income_type=income_types[kind_code],
                amount=amount, paid_at=paid_at,
                payer_name=payer_name, description=note,
            )
            created += 1

    return {"created": created, "skipped": skipped, "errors": errors}


class Command(BaseCommand):
    help = "وارد کردن پرداخت‌های INC-001 از Sheet1 فایل اکسل"

    def add_arguments(self, parser):
        parser.add_argument("path", help="مسیر فایل xlsx")
        parser.add_argument("--dry-run", action="store_true", help="فقط بررسی بدون ذخیره")

    def handle(self, *args, **options):
        result = import_payments_from_sheet1(options["path"], dry_run=options["dry_run"])
        mode = "بررسی آزمایشی" if options["dry_run"] else "واقعی"
        self.stdout.write(
            f"[{mode}] جدید: {result['created']}، رد شده: {result['skipped']}"
        )
        for err in result["errors"]:
            self.stderr.write(f"خطا: {err}")
        if result["errors"]:
            raise CommandError(f"{len(result['errors'])} سطر خطا داشت.")
