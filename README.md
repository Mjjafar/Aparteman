# حساب ساختمان (آپارتمان ۷ واحدی)

سایت جنگویی حساب شارژ و مخارج ساختمان: پروفایل واحد، تاریخچه مالک/مستاجر،
تعرفه ماهانه شمسی، ثبت پرداخت (شارژ + متفرقه)، مخارج با شناسه قبض/پرداخت،
داشبورد صندوق و صورت‌حساب چاپی.

## توسعه لوکال (Windows)

```cmd
cd C:\Aparteman
uv sync
uv run python manage.py migrate
uv run python manage.py loaddata fixtures/seed.json
uv run python manage.py createsuperuser
uv run python manage.py test
uv run python manage.py runserver
```

بعد در مرورگر: http://127.0.0.1:8000 (ورود با ادمین، بعد یوزر هر واحد از `/units/<id>/set-login/`)

## Mirror پایتون (اینترنت ضعیف)

آدرس Mirror در `pyproject.toml` بخش `[tool.uv]` ثبت شده:

```toml
[tool.uv]
index-url = "https://repo.hmirror.ir/python/simple/"
```

## استقرار روی VPS با Docker

```bash
cp .env.example .env   # و مقادیر را عوض کنید
docker compose up -d --build
# ساخت ادمین داخل کانتینر:
docker compose exec web uv run python manage.py createsuperuser
# لود دیتای اولیه:
docker compose exec web uv run python manage.py loaddata fixtures/seed.json
```

سایت روی پورت 8000 بالا می‌آید. دیتابیس SQLite در `./data` و فاکتورها در
`./media` ذخیره می‌شوند (volume شده‌اند، با rebuild پاک نمی‌شوند).

## بکاپ

بکاپ فقط کپی فایل است:

```bash
cp data/db.sqlite3 "backup-$(date +%F).sqlite3"
```
