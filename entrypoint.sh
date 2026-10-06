#!/bin/sh
set -e

# If started as root (default), prepare writable dirs then drop to app user.
# This handles fresh VPS clones where ./data and ./media are root-owned,
# and avoids SQLite "unable to open database file" errors.
if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/data /app/media
  touch /app/data/db.sqlite3
  chown -R app:app /app/data /app/media
  chmod 755 /app/data /app/media
  exec setpriv --reuid=app --regid=app --clear-groups env HOME=/home/app sh /app/entrypoint.sh "$@"
fi

# Apply migrations on every (re)start so VPS redeploys stay current.
uv run --no-sync python manage.py migrate --noinput

# Auto-create the admin user from env vars on first deploy.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  uv run --no-sync python - <<'EOF' || true
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
if username and password:
    user, created = User.objects.update_or_create(
        username=username, defaults={"email": email, "is_staff": True, "is_superuser": True}
    )
    user.set_password(password)
    user.save()
    print(f"Superuser '{username}' ensured ({'created' if created else 'updated'}).")
EOF
fi

# Optional seed on first deploy (fixtures/seed.json). Disabled by default
# so redeploys never duplicate data. Skips automatically when units exist.
if [ "${LOAD_SEED:-False}" = "True" ] && [ -f fixtures/seed.json ]; then
  # NOTE: don't use `manage.py shell -c` here; it prints an extra
  # "N objects imported automatically" banner that breaks the comparison.
  UNIT_COUNT=$(uv run --no-sync python - <<'EOF'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from units.models import Unit

print(Unit.objects.count())
EOF
)
  if [ "$UNIT_COUNT" = "0" ]; then
    uv run --no-sync python manage.py loaddata fixtures/seed.json
  else
    echo "Seed skipped: units already exist."
  fi
fi

exec uv run --no-sync gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
