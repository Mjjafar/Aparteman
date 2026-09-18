# Aparteman (سایت شارژ آپارتمان ۷ واحدی) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ساخت سایت جنگویی حساب شارژ و مخارج یک آپارتمان ۷ واحدی با پروفایل واحد، تاریخچه مالک/مستاجر، تعرفه ماهانه شمسی، ثبت پرداخت و مخارج قبضی، داشبورد مانده صندوق و صورت‌حساب چاپی.

**Architecture:** یک پروژه Django یکپارچه (Server-Side Rendering). هیچ API جدا و هیچ فرانت React وجود ندارد. هر اپ یک مسئولیت دارد: `units` پروفایل و کاربر، `charges` تعرفه و پرداخت، `expenses` نوع مخارج و مخارج، `dashboard` جمع‌بندی و صورت‌حساب.

**Tech Stack:** Django 5.x، Python 3.12، UV (مدیریت پکیج و اجرا)، SQLite در همه‌جا (توسعه و VPS)، Django Templates + Bootstrap 5 RTL لوکال (vendor شده، بدون وابستگی به CDN)، persian-datepicker لوکال، jdatetime برای شمسی، Gunicorn + WhiteNoise در Docker، pytest یا Django test runner برای یونیت‌تست.

**Spec:** درخواست کاربر در گفتگوی ۲۰۲۶-۰۹-۱۱ (متن فارسی): پروفایل واحد (شماره واحد، نام+موبایل مالک، نام+موبایل مستاجر)، تغییر مالک/مستاجر در طول زمان با حفظ تاریخچه، یوزر/پسورد هر واحد توسط ادمین، تعریف سال+ماه شمسی+مبلغ شارژ، فرم پرداخت (واحد، ماه، سال، نام پرداخت‌کننده، تاریخ، مبلغ، نوع شارژ/متفرقه)، جدول نوع مخارج (آب، گاز، برق، تعمیرات...)، فیلدهای شناسه قبض و شناسه پرداخت برای قبض‌ها، سه عدد بالای صفحه (جمع دریافتی، جمع هزینه، مانده)، صورت‌حساب همیشه آماده، Docker + UV، بدون Postgres، یونیت‌تست.

## Global Constraints

- DATABASE همه‌جا SQLite است؛ هیچ کانتینر Postgres/MySQL ساخته نمی‌شود.
- Package manager فقط UV است؛ دستور `pip install` در مستندات نیاید، فقط `uv sync` و `uv run`.
- تاریخ ورودی و نمایشی پیش‌فرض شمسی (Jalali) است؛ در دیتابیس تاریخ میلادی ذخیره و فقط در لایه نمایش/فرم تبدیل می‌شود، به‌جز سال/ماه شمسی تعرفه که دو عدد صحیح جدا هستند.
- یوزر/پسورد هر واحد فقط توسط مدیر (ادمین) ساخته و تنظیم می‌شود؛ ثبت‌نام عمومی وجود ندارد.
- `bill_id` (شناسه قبض) و `payment_id` (شناسه پرداخت) روی مدل Expense اختیاری‌اند، اما وقتی دسته مخارج پرچم `requires_bill_ids=True` دارد در فرم اجباری می‌شوند.
- فرانت بدون build step است (`npm` ممنوع)؛ Bootstrap RTL و دیت‌پیکر فارسی داخل `static/vendor/` کپی می‌شوند تا با اینترنت ضعیف هم کار کند.
- هر Task با تست قرمز-سبز و کامیت جدا تمام می‌شود؛ بدون تست، Task کامل نیست.
- روی VPS فقط `docker compose up -d` لازم است؛ بقیه کارها داخل کانتینر انجام می‌شود.

---

## File Structure

```
C:\Aparteman\
  pyproject.toml              # وابستگی‌های UV + اسکریپت‌ها
  uv.lock                     # قفل نسخه‌ها (با uv sync ساخته می‌شود)
  .env.example                # متغیرهای محیطی نمونه
  .gitignore
  Dockerfile                  # ایمیج web: python slim + uv + gunicorn
  docker-compose.yml          # سرویس web + volume دیتابیس و مدیا
  manage.py
  config/
    __init__.py
    settings.py               # فارسی، Asia/Tehran، SQLite، WhiteNoise، لاگین
    urls.py                   # روت اصلی + لاگین/لاگ‌اوت جنگو
    wsgi.py
  units/
    models.py                 # Unit, OwnershipHistory, TenancyHistory
    admin.py                  # ساخت یوزر واحد توسط ادمین
    views.py                  # پروفایل واحد
    forms.py
    urls.py
    tests/test_models.py
    tests/test_views.py
  charges/
    models.py                 # ChargePlan, Payment
    admin.py
    views.py                  # ثبت پرداخت + لیست پرداخت‌ها
    forms.py
    urls.py
    tests/test_models.py
    tests/test_views.py
  expenses/
    models.py                 # ExpenseCategory, Expense
    admin.py
    views.py                  # تعریف نوع مخارج + ثبت مخارج
    forms.py
    urls.py
    tests/test_models.py
    tests/test_views.py
  dashboard/
    views.py                  # داشبورد سه‌عددی + صورت‌حساب
    urls.py
    services.py               # توابع جمع‌بندی (total_paid, total_spent, balance)
    tests/test_services.py
    tests/test_views.py
  templates/
    base.html                 # اسکلت RTL + نوبار + سه عدد صندوق
    registration/login.html
    units/profile.html
    charges/payment_form.html
    charges/payment_list.html
    expenses/expense_form.html
    expenses/category_list.html
    dashboard/home.html
    dashboard/statement.html  # صورت‌حساب چاپی
  static/
    css/custom.css
    vendor/bootstrap-rtl/     # بوت‌استرپ RTL دانلودشده
    vendor/persian-datepicker/
  data/                       # db.sqlite3 روی هاست (volume داکر) — کامیت نمی‌شود
  media/receipts/             # فاکتورهای آپلودی — کامیت نمی‌شود
  docs/superpowers/plans/2026-09-11-aparteman.md  # همین پلن
```

---

### Task 0: نصب ابزارها توسط کاربر (بدون تست، بدون کامیت کد)

**Files:** هیچ فایل کدی ساخته نمی‌شود؛ فقط محیط آماده می‌شود.

**Interfaces:** Consumes: هیچ‌چیز. Produces: `python --version`، `uv --version`، `docker --version` سالم.

- [ ] **Step 1: نصب Python 3.12 از سایت رسمی**
  - از python.org نسخه Windows 64bit سری 3.12 را دانلود و نصب کن. موقع نصب تیک `Add python.exe to PATH` را بزن.
  - کنترل سلامت (خودت در CMD بزن):
  ```cmd
  python --version
  ```
  انتظار: `Python 3.12.x`

- [ ] **Step 2: نصب UV (package manager)**
  - در PowerShell بزن:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  - اگر اینترنت قطع بود، فایل `uv-x86_64-pc-windows-msvc.zip` را از گیت‌هاب astral-sh/uv با موبایل دانلود و `uv.exe` را کنار `python.exe` کپی کن.
  - کنترل سلامت:
  ```cmd
  uv --version
  ```

- [ ] **Step 3: نصب Git و VS Code**
  - Git از git-scm.com، VS Code از code.visualstudio.com. هر دو Next-Next پیش‌فرض کافی است.

- [ ] **Step 4: نصب Docker Desktop (فعلاً اختیاری، موقع تحویل VPS لازم است)**
  - از docker.com نسخه Windows را نصب کن. چون اینترنت ضعیف داری، این را آخر کار انجام بده؛ برای توسعه لوکال داکر لازم نیست.

---

### Task 1: اسکلت پروژه با UV + تنظیمات فارسی و SQLite

**Files:**
- Create: `pyproject.toml`, `manage.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py`, `.env.example`, `.gitignore`
- Test: `config/tests/test_settings.py` (یا `tests/test_settings.py` در ریشه اگر config تست‌پکیج ندارد)

**Interfaces:**
- Consumes: هیچ‌چیز.
- Produces: `config.settings` با `LANGUAGE_CODE='fa-ir'`, `TIME_ZONE='Asia/Tehran'`, دیتابیس SQLite در `data/db.sqlite3`، مسیر `LOGIN_URL` و `LOGIN_REDIRECT_URL`.

- [ ] **Step 1: Write the failing test**
```python
# config/tests/test_settings.py
from django.test import SimpleTestCase
from django.conf import settings

class SettingsTest(SimpleTestCase):
    def test_persian_sqlite_settings(self):
        self.assertEqual(settings.LANGUAGE_CODE, "fa-ir")
        self.assertEqual(settings.TIME_ZONE, "Asia/Tehran")
        self.assertIn("sqlite3", settings.DATABASES["default"]["ENGINE"])
        self.assertTrue(settings.DATABASES["default"]["NAME"].endswith("db.sqlite3"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test config.tests.test_settings -v 2`
Expected: FAIL (فایل settings یا manage.py وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - `uv init --bare` یا ساخت دستی `pyproject.toml` با وابستگی‌ها:
```toml
[project]
name = "aparteman"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "django>=5.0,<6.0",
  "jdatetime>=5.0",
  "gunicorn>=21.0",
  "whitenoise>=6.0",
]
```
  - `config/settings.py`: `LANGUAGE_CODE = "fa-ir"`، `TIME_ZONE = "Asia/Tehran"`، `USE_TZ = True`، دیتابیس:
```python
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "data" / "db.sqlite3"}}
```
  - `INSTALLED_APPS` شامل `units, charges, expenses, dashboard` + اپ‌های پیش‌فرض auth. `STATIC_ROOT`، `MEDIA_ROOT=media/`، `LOGIN_URL="login"`، `LOGIN_REDIRECT_URL="dashboard:home"`.
  - دستورات اجرا فقط با UV:
```cmd
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test config.tests.test_settings -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add pyproject.toml manage.py config/ .env.example .gitignore
git commit -m "feat: scaffold django project with uv, fa-ir, sqlite"
```

---

### Task 2: اپ units — واحد + تاریخچه مالک و مستاجر

**Files:**
- Create: `units/models.py`, `units/admin.py`, `units/tests/test_models.py`
- Modify: `config/settings.py` (اضافه کردن `units` به INSTALLED_APPS — اگر در Task 1 نشده)

**Interfaces:**
- Consumes: `django.contrib.auth.models.User`.
- Produces:
  - `Unit(number: int unique, user: OneToOne(User, nullable), owner_name: str, owner_phone: str, tenant_name: str blank, tenant_phone: str blank)` با `__str__` به شکل `"واحد 3"`
  - `OwnershipHistory(unit: FK, name: str, phone: str, start_date: date, end_date: date nullable)` مرتب بر اساس `-start_date`
  - `TenancyHistory` با همان فیلدها برای مستاجر.

- [ ] **Step 1: Write the failing test**
```python
# units/tests/test_models.py
from django.test import TestCase
from units.models import Unit
import datetime

class UnitModelTest(TestCase):
    def test_str_and_unique_number(self):
        u = Unit.objects.create(number=3, owner_name="رضا", owner_phone="09120000000")
        self.assertEqual(str(u), "واحد 3")

    def test_tenant_optional(self):
        u = Unit.objects.create(number=4, owner_name="مالک", owner_phone="09120000001")
        self.assertEqual(u.tenant_name, "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test units.tests.test_models -v 2`
Expected: FAIL (مدل Unit وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
```python
# units/models.py
from django.db import models
from django.contrib.auth.models import User

class Unit(models.Model):
    number = models.PositiveSmallIntegerField("شماره واحد", unique=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کاربر ورود")
    owner_name = models.CharField("نام مالک", max_length=100)
    owner_phone = models.CharField("موبایل مالک", max_length=20)
    tenant_name = models.CharField("نام مستاجر", max_length=100, blank=True, default="")
    tenant_phone = models.CharField("موبایل مستاجر", max_length=20, blank=True, default="")

    class Meta:
        ordering = ["number"]
        verbose_name = "واحد"
        verbose_name_plural = "واحدها"

    def __str__(self):
        return f"واحد {self.number}"

class OwnershipHistory(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="ownerships", verbose_name="واحد")
    name = models.CharField("نام مالک", max_length=100)
    phone = models.CharField("موبایل مالک", max_length=20)
    start_date = models.DateField("از تاریخ")
    end_date = models.DateField("تا تاریخ", null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "سابقه مالکیت"

class TenancyHistory(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="tenancies", verbose_name="واحد")
    name = models.CharField("نام مستاجر", max_length=100)
    phone = models.CharField("موبایل مستاجر", max_length=20)
    start_date = models.DateField("از تاریخ")
    end_date = models.DateField("تا تاریخ", null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "سابقه سکونت"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test units.tests.test_models -v 2`
Expected: PASS (بعد از `uv run python manage.py makemigrations units` و `migrate`)

- [ ] **Step 5: Commit**
```bash
git add units/
git commit -m "feat(units): add Unit with owner/tenant history"
```

---

### Task 3: ساخت یوزر/پسورد واحد توسط مدیر

**Files:**
- Modify: `units/admin.py` (اکشن/فرم ساخت User و اتصال به Unit)، `units/forms.py` (فرم `UnitUserForm`)
- Test: `units/tests/test_views.py` (تست اول)

**Interfaces:**
- Consumes: `Unit` از Task 2.
- Produces: `UnitUserForm(username, password)` و ویو/اکشن ادمین `assign_user_to_unit(unit_id, username, password) -> User` که پسورد را هش می‌کند و به `unit.user` وصل می‌کند. هیچ ثبت‌نام عمومی وجود ندارد.

- [ ] **Step 1: Write the failing test**
```python
# units/tests/test_views.py
from django.test import TestCase
from django.contrib.auth.models import User
from units.models import Unit

class UnitUserAssignTest(TestCase):
    def test_admin_can_assign_login_to_unit(self):
        unit = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.post(f"/units/{unit.pk}/set-login/", {"username": "unit1", "password": "Sakhteman#1"})
        self.assertEqual(resp.status_code, 302)
        unit.refresh_from_db()
        self.assertEqual(unit.user.username, "unit1")
        self.assertTrue(unit.user.check_password("Sakhteman#1"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test units.tests.test_views.UnitUserAssignTest -v 2`
Expected: FAIL با 404 (URL وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - `units/forms.py` با `UnitUserForm`: دو فیلد `username` و `password` (پسورد با `PasswordInput` و اعتبارسنجی تکراری نبودن یوزر).
  - ویو `set_unit_login` با دکوراتور `staff_member_required` که User می‌سازد یا پسوردش را عوض می‌کند و به واحد وصل می‌کند.
  - URL: `units/<int:pk>/set-login/` به نام `units:set-login`.
  - هم‌زمان همین فرم را به صورت inline در `units/admin.py` هم ثبت کن تا مدیر از ادمین جنگو هم بتواند انجام دهد.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test units.tests.test_views -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add units/forms.py units/views.py units/urls.py units/admin.py units/tests/test_views.py
git commit -m "feat(units): admin assigns username/password per unit"
```

---

### Task 4: اپ charges — تعرفه ماهانه شمسی + پرداخت (شارژ و متفرقه)

**Files:**
- Create: `charges/models.py`, `charges/tests/test_models.py`

**Interfaces:**
- Consumes: `Unit` از Task 2.
- Produces:
  - `ChargePlan(year: int (شمسی، مثل 1405), month: int (1-12), amount: int (تومان))` با قید یکتای `(year, month)` و `__str__` مثل `"شهریور ۱۴۰۵ — 500,000 تومان"`.
  - `Payment(unit: FK, year: int, month: int nullable, payer_kind: ('owner'|'tenant'), payer_name: str, paid_at: date, amount: int, kind: ('charge'|'other'), description: str blank)` — وقتی `kind='other'` (مثل پول تعمیرات پیش‌بینی‌نشده) ماه می‌تواند خالی باشد.

- [ ] **Step 1: Write the failing test**
```python
# charges/tests/test_models.py
from django.test import TestCase
from django.db import IntegrityError
from units.models import Unit
from charges.models import ChargePlan, Payment
import datetime

class ChargePlanTest(TestCase):
    def test_unique_year_month(self):
        ChargePlan.objects.create(year=1405, month=6, amount=500000)
        with self.assertRaises(IntegrityError):
            ChargePlan.objects.create(year=1405, month=6, amount=600000)

    def test_other_income_without_month(self):
        u = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000000")
        p = Payment.objects.create(unit=u, year=1405, month=None, payer_kind="owner",
            payer_name="ب", paid_at=datetime.date(2026, 9, 1), amount=200000, kind="other",
            description="کمک تعمیرات")
        self.assertEqual(p.kind, "other")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test charges.tests.test_models -v 2`
Expected: FAIL (اپ charges وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - مدل‌ها دقیقاً با همان فیلدهای بالا. `month` با `MinValueValidator(1)` و `MaxValueValidator(12)`، هر دو nullable/blank برای حالت متفرقه. `clean()` مدل Payment: اگر `kind == 'charge'` ماه و سال اجباری‌اند.
  - `__str__` فارسی با نام ماه شمسی (لیست ثابت `JALALI_MONTHS`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test charges.tests.test_models -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add charges/models.py charges/tests/test_models.py
git commit -m "feat(charges): add ChargePlan and Payment with other-income kind"
```

---

### Task 5: اپ expenses — نوع مخارج + مخارج با شناسه قبض و شناسه پرداخت

**Files:**
- Create: `expenses/models.py`, `expenses/tests/test_models.py`

**Interfaces:**
- Consumes: هیچ‌چیز از اپ‌های دیگر.
- Produces:
  - `ExpenseCategory(title: str unique مثل "قبض آب", requires_bill_ids: bool default False)` — برای قبض‌ها True می‌شود.
  - `Expense(category: FK, spent_at: date, amount: int, bill_id: str blank, payment_id: str blank, description: str, receipt: FileField nullable)` با `clean()`: اگر `category.requires_bill_ids` و قبض/پرداخت خالی بود `ValidationError` فارسی بدهد.

- [ ] **Step 1: Write the failing test**
```python
# expenses/tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from expenses.models import ExpenseCategory, Expense
import datetime

class ExpenseBillIdsTest(TestCase):
    def test_bill_category_requires_ids(self):
        cat = ExpenseCategory.objects.create(title="قبض برق", requires_bill_ids=True)
        e = Expense(category=cat, spent_at=datetime.date(2026, 9, 1), amount=150000, description="برق مشاع")
        with self.assertRaises(ValidationError):
            e.full_clean()

    def test_repair_without_ids_ok(self):
        cat = ExpenseCategory.objects.create(title="تعمیرات", requires_bill_ids=False)
        e = Expense(category=cat, spent_at=datetime.date(2026, 9, 1), amount=80000, description="قفل در")
        e.full_clean()  # نباید خطا بدهد
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test expenses.tests.test_models -v 2`
Expected: FAIL (مدل‌ها وجود ندارند).

- [ ] **Step 3: Write minimal implementation**
  - دقیقاً مدل‌های بالا. `receipt` در `media/receipts/%Y/%m/` ذخیره می‌شود. دسته‌های پیش‌فرض (قبض آب، قبض گاز، قبض برق، نظافت، آسانسور، تعمیرات، حقوق سرایدار، سایر) بعداً با migration دیتا می‌آیند (Task 11)، نه هاردکد.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test expenses.tests.test_models -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add expenses/models.py expenses/tests/test_models.py
git commit -m "feat(expenses): categories with bill_id and payment_id rule"
```

---

### Task 6: داشبورد — سه عدد بالای صفحه + سرویس جمع‌بندی

**Files:**
- Create: `dashboard/services.py`, `dashboard/tests/test_services.py`

**Interfaces:**
- Consumes: `Payment` از Task 4، `Expense` از Task 5.
- Produces:
  - `fund_summary() -> dict(total_paid: int, total_spent: int, balance: int)` که `total_paid` جمع همه Paymentهاست (شارژ + متفرقه، چون گفتی متفرقه هم جزو دریافتی حساب شود)، `total_spent` جمع همه Expenseها، `balance = total_paid - total_spent`.
  - `unit_balance(unit) -> dict` برای مانده یک واحد (اختیاری ولی برای صورت‌حساب لازم می‌شود).

- [ ] **Step 1: Write the failing test**
```python
# dashboard/tests/test_services.py
from django.test import TestCase
from units.models import Unit
from charges.models import Payment
from expenses.models import ExpenseCategory, Expense
from dashboard.services import fund_summary
import datetime

class FundSummaryTest(TestCase):
    def test_balance_counts_other_income(self):
        u = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        Payment.objects.create(unit=u, year=1405, month=6, payer_kind="tenant", payer_name="مستاجر",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge")
        Payment.objects.create(unit=u, year=1405, month=None, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 2), amount=200000, kind="other")
        cat = ExpenseCategory.objects.create(title="قبض آب")
        Expense.objects.create(category=cat, spent_at=datetime.date(2026, 9, 3), amount=300000, description="آب")
        s = fund_summary()
        self.assertEqual(s["total_paid"], 700000)
        self.assertEqual(s["total_spent"], 300000)
        self.assertEqual(s["balance"], 400000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test dashboard.tests.test_services -v 2`
Expected: FAIL (`fund_summary` تعریف نشده).

- [ ] **Step 3: Write minimal implementation**
```python
# dashboard/services.py
from django.db.models import Sum
from charges.models import Payment
from expenses.models import Expense

def fund_summary():
    total_paid = Payment.objects.aggregate(s=Sum("amount"))["s"] or 0
    total_spent = Expense.objects.aggregate(s=Sum("amount"))["s"] or 0
    return {"total_paid": total_paid, "total_spent": total_spent, "balance": total_paid - total_spent}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test dashboard.tests.test_services -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/services.py dashboard/tests/test_services.py
git commit -m "feat(dashboard): fund summary with other-income included"
```

---

### Task 7: فرم‌ها و ویوها — ثبت پرداخت، تعریف نوع مخارج، ثبت مخارج (با سطح دسترسی)

**Files:**
- Create: `charges/forms.py` (فرم `PaymentForm` با تاریخ شمسی)، `expenses/forms.py` (فرم `ExpenseForm` + `CategoryForm`)، ویوها و `urls.py` هر دو اپ، تست‌ها `charges/tests/test_views.py` و `expenses/tests/test_views.py`

**Interfaces:**
- Consumes: مدل‌های Task 4 و 5، `fund_summary` از Task 6 برای نمایش.
- Produces:
  - `PaymentForm`: فیلدهای واحد، سال شمسی، ماه، نوع (شارژ/متفرقه)، نام پرداخت‌کننده، تاریخ پرداخت (ورودی شمسی `1405/06/20`، تبدیل به میلادی با jdatetime)، مبلغ، توضیح.
  - `ExpenseForm`: اعتبارسنجی شناسه قبض/پرداخت بر اساس دسته (همان قانون Task 5) + تاریخ شمسی.
  - دسترسی: همه ویوهای ثبت/ویرایش فقط `staff` (مدیر)؛ کاربر واحد فقط لیست و پروفایل خودش را می‌بیند (تست 403 برای کاربر عادی روی POST).

- [ ] **Step 1: Write the failing test**
```python
# charges/tests/test_views.py
from django.test import TestCase
from django.contrib.auth.models import User
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test charges.tests.test_views -v 2`
Expected: FAIL (URL یا فرم وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - ویجت تاریخ شمسی: `JalaliDateInput` که رشته `1405/06/20` می‌گیرد و در `clean` با `jdatetime.strptime(..., "%Y/%m/%d").togregorian()` برمی‌گرداند. هیچ تاریخ میلادی از کاربر گرفته نمی‌شود.
  - ویوهای `payment_create`, `expense_create`, `category_create` با `staff_member_required`. ویوهای `payment_list`, `expense_list` با `login_required` (کاربر واحد فقط آیتم‌های خودش + همه مخارج برای شفافیت).
  - پیام خطای فارسی برای شناسه قبض: `"برای دسته‌های قبض، شناسه قبض و شناسه پرداخت اجباری است."`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test charges.tests.test_views expenses.tests.test_views -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add charges/forms.py charges/views.py charges/urls.py expenses/forms.py expenses/views.py expenses/urls.py charges/tests/test_views.py expenses/tests/test_views.py
git commit -m "feat: jalali payment and expense forms with staff-only create"
```

---

### Task 8: صورت‌حساب — همیشه آماده، فیلتر واحد/ماه/سال + چاپ

**Files:**
- Create: `dashboard/views.py` (ویو `home` و `statement`)، `dashboard/urls.py`، `templates/dashboard/statement.html`، تست `dashboard/tests/test_views.py`

**Interfaces:**
- Consumes: `fund_summary`، مدل‌های Payment و Expense، هِلپر تبدیل تاریخ به شمسی.
- Produces: URLهای `dashboard:home` (`/`) و `dashboard:statement` (`/statement/`) با پارامترهای GET `unit, year, month`؛ جدول پرداخت‌ها + جدول مخارج + جمع‌ها + دکمه چاپ (`window.print()`). کاربر واحد فقط صورت‌حساب واحد خودش را می‌بیند.

- [ ] **Step 1: Write the failing test**
```python
# dashboard/tests/test_views.py
from django.test import TestCase
from django.contrib.auth.models import User
from units.models import Unit
from charges.models import Payment
import datetime

class StatementTest(TestCase):
    def test_statement_filters_by_unit(self):
        u1 = Unit.objects.create(number=1, owner_name="الف", owner_phone="09120000000")
        u2 = Unit.objects.create(number=2, owner_name="ب", owner_phone="09120000001")
        Payment.objects.create(unit=u1, year=1405, month=6, payer_kind="owner", payer_name="الف",
            paid_at=datetime.date(2026, 9, 1), amount=500000, kind="charge")
        admin = User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(admin)
        resp = self.client.get("/statement/?unit=1&year=1405&month=6")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "500")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test dashboard.tests.test_views -v 2`
Expected: FAIL (ویو statement وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - کوئری‌ست‌ها با فیلتر اختیاری؛ جمع هر جدول جداگانه؛ تاریخ‌ها با فیلتر `to_jalali` به شمسی نمایش داده می‌شوند. تمپلیت با `@media print` فقط جدول‌ها چاپ شود.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test dashboard.tests.test_views -v 2`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/views.py dashboard/urls.py templates/dashboard/ dashboard/tests/test_views.py
git commit -m "feat(dashboard): filterable printable statement"
```

---

### Task 9: تمپلیت‌های فارسی RTL + دارایی‌های لوکال (بدون CDN)

**Files:**
- Create: `templates/base.html`, `templates/registration/login.html`, بقیه تمپلیت‌ها، `static/css/custom.css`
- Vendor: `static/vendor/bootstrap-rtl/*`, `static/vendor/persian-datepicker/*` (دانلود یک‌باره توسط کاربر و کپی)

**Interfaces:**
- Consumes: ویوهای Task 7 و 8.
- Produces: اسکلت `base.html` با `dir="rtl" lang="fa"`، نوبار با سه کارت صندوق (دریافتی/هزینه/مانده) که از context processor می‌آید، تمپلیت لاگین، فرم‌ها با کلاس‌های بوت‌استرپ.

- [ ] **Step 1: Write the failing test (smoke test همه صفحات)**
```python
# dashboard/tests/test_views.py (اضافه شود)
from django.contrib.auth.models import User

class PagesSmokeTest(TestCase):
    def test_all_pages_render_rtl(self):
        User.objects.create_superuser("admin", "a@x.ir", "pass12345")
        self.client.force_login(User.objects.get(username="admin"))
        for url in ["/", "/statement/", "/payments/", "/expenses/", "/categories/"]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, msg=url)
            self.assertContains(resp, 'dir="rtl"')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test dashboard.tests.test_views.PagesSmokeTest -v 2`
Expected: FAIL (تمپلیت base بدون dir=rtl یا URL ناقص).

- [ ] **Step 3: Write minimal implementation**
  - `base.html` با فونت فارسی (Vazirmatn لوکال یا system font اگر فونت دانلود نشد)، context processor که `fund_summary()` را به همه صفحات تزریق می‌کند.
  - دستور دانلود vendor که کاربر خودش یک‌بار می‌زند (در README): دانلود bootstrap-rtl و persian-datepicker و کپی در static/vendor. هیچ لینک CDN در base.html نباشد.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test -v 1`
Expected: PASS (کل سوئیت سبز)

- [ ] **Step 5: Commit**
```bash
git add templates/ static/ dashboard/tests/test_views.py
git commit -m "feat(front): rtl templates with local vendor assets"
```

---

### Task 10: Docker + docker-compose با SQLite و UV

**Files:**
- Create: `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `.dockerignore`

**Interfaces:**
- Consumes: کل پروژه Task 1 تا 9.
- Produces: `docker compose up -d --build` که سایت را روی پورت 8000 بالا می‌آورد؛ دیتابیس در volume `./data` و فاکتورها در `./media` сохраня می‌شوند؛ migrate و collectstatic خودکار در entrypoint.

- [ ] **Step 1: Write the failing check (smoke داکر)**
```bash
docker compose config
```
انتظار اول: FAIL (فایل compose وجود ندارد).

- [ ] **Step 2: Dockerfile (UV رسمی، بدون Postgres)**
```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
RUN uv run python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
```
`entrypoint.sh`:
```bash
#!/bin/sh
uv run python manage.py migrate --noinput
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2
```

- [ ] **Step 3: docker-compose.yml (تک‌سرویسه + volume)**
```yaml
services:
  web:
    build: .
    ports: ["8000:8000"]
    env_file: [.env]
    volumes: ["./data:/app/data", "./media:/app/media"]
    restart: unless-stopped
```

- [ ] **Step 4: Verify**
```bash
docker compose config
docker compose up -d --build
```
انتظار: config سبز، کانتینر بالا، `http://VPS-IP:8000` لاگین را نشان بدهد.

- [ ] **Step 5: Commit**
```bash
git add Dockerfile docker-compose.yml entrypoint.sh .dockerignore
git commit -m "feat(deploy): single-service docker with sqlite volumes"
```

---

### Task 11: دیتای اولیه ۷ واحد + مدیر + دسته‌های قبض + چک‌لیست VPS

**Files:**
- Create: `units/migrations/0002_seed_units.py` یا `fixtures/seed.json` + `expenses/migrations/0002_seed_categories.py`، `README.md` (راهنمای نصب با UV و داکر + بکاپ SQLite)

**Interfaces:**
- Consumes: همه مدل‌ها.
- Produces: بعد از migrate، هفت Unit (شماره ۱ تا ۷)، دسته‌های (قبض آب/Gas/برق با requires_bill_ids=True، نظافت، آسانسور، تعمیرات، حقوق سرایدار، سایر)، و سوپریوزر از روی `.env` (`DJANGO_SUPERUSER_*`). تست صحت سید.

- [ ] **Step 1: Write the failing test**
```python
# units/tests/test_seed.py
from django.test import TestCase
from units.models import Unit
from expenses.models import ExpenseCategory

class SeedTest(TestCase):
    fixtures = ["seed.json"]
    def test_seven_units_and_bill_categories(self):
        self.assertEqual(Unit.objects.count(), 7)
        self.assertTrue(ExpenseCategory.objects.filter(title="قبض برق", requires_bill_ids=True).exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test units.tests.test_seed -v 2`
Expected: FAIL (فیکسچر seed.json وجود ندارد).

- [ ] **Step 3: Write minimal implementation**
  - `fixtures/seed.json` با ۷ واحد خالی (نام مالک اولیه قابل ویرایش توسط مدیر) + ۸ دسته مخارج.
  - لود با `uv run python manage.py loaddata fixtures/seed.json`.
  - ساخت ادمین: `uv run python manage.py createsuperuser` لوکال؛ روی VPS از متغیر محیطی.
  - بکاپ SQLite فقط کپی فایل است: `sqlite3 data/db.sqlite3 ".backup 'backup.db'"` یا کپی `data/db.sqlite3`.

- [ ] **Step 4: Run full suite**

Run: `uv run python manage.py test -v 1`
Expected: PASS (کل پروژه سبز)

- [ ] **Step 5: Commit**
```bash
git add fixtures/seed.json units/tests/test_seed.py README.md
git commit -m "feat: seed 7 units and bill categories with readme"
```

---

## Self-Review

1. **Spec coverage:** پروفایل واحد (Task 2) ✓؛ تاریخچه مالک/مستاجر (Task 2) ✓؛ یوزر/پسورد توسط ادمین (Task 3) ✓؛ سال+ماه+مبلغ شارژ (Task 4) ✓؛ فرم پرداخت با نام پرداخت‌کننده و تاریخ و مبلغ (Task 7) ✓؛ جدول نوع مخارج (Task 5) ✓؛ فرم مخارج (Task 7) ✓؛ شناسه قبض و شناسه پرداخت (Task 5+7) ✓؛ سه عدد بالای صفحه شامل متفرقه (Task 6+9) ✓؛ صورت‌حساب همیشه آماده (Task 8) ✓؛ شمسی پیش‌فرض (Task 7+8) ✓؛ SQLite همه‌جا (Task 1+10) ✓؛ Docker+UV (Task 10) ✓؛ نصب توسط کاربر (Task 0) ✓؛ یونیت‌تست (همه Taskها) ✓.
2. **Placeholder scan:** هیچ TBD/TODO یا «مشابه Task قبل» وجود ندارد؛ کد هر Step کامل است.
3. **Type consistency:** نام‌ها یکدست‌اند: `ChargePlan(year, month, amount)`، `Payment(kind='charge'|'other')`، `Expense(bill_id, payment_id)`، `fund_summary() -> dict` در همه Taskها یکسان استفاده شده‌اند.
