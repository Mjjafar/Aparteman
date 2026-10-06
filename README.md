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

پیش‌نیاز روی سرور: Docker + Docker Compose plugin و باز بودن پورت‌های 80 و
443 (برای حالت دامنه).

```bash
git clone <repo-url> /opt/aparteman && cd /opt/aparteman
cp .env.example .env
nano .env   # SECRET_KEY، رمز ادمین و هاست‌ها را عوض کنید
docker compose up -d --build
docker compose logs -f web   # صبر کنید تا migrate تمام شود
```

ادمین به‌صورت خودکار از `DJANGO_SUPERUSER_*` ساخته می‌شود. دیتابیس SQLite
در `./data` و فاکتورها در `./media` ذخیره می‌شوند (volume شده‌اند، با rebuild
پاک نمی‌شوند).

### حالت ۱: فقط IP (بدون دامنه، HTTP)

```env
DJANGO_ALLOWED_HOSTS=1.2.3.4
SITE_ADDRESS=:80
```

بعد سایت روی `http://1.2.3.4` بالا می‌آید.

### حالت ۲: دامنه (HTTPS خودکار با Let's Encrypt)

اول رکورد A دامنه را به IP سرور بدهید، بعد:

```env
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
SITE_ADDRESS=example.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

Caddy خودش گواهی می‌گیرد و تمدید می‌کند. سایت روی `https://example.com`
بالا می‌آید.

### لود دیتای اولیه (فقط دیپلوی اول)

```bash
# در .env بگذارید LOAD_SEED=True و یک بار ری‌استارت کنید:
docker compose up -d --force-recreate web
# بعد حتماً برگردانید به LOAD_SEED=False تا استقرارهای بعدی تکراری لود نکند.
```

### به‌روزرسانی نسخه جدید

```bash
git pull
docker compose up -d --build
# migrate به‌صورت خودکار در entrypoint اجرا می‌شود.
```

## بکاپ

بکاپ فقط کپی فایل است:

```bash
cp data/db.sqlite3 "backup-$(date +%F).sqlite3"
```
