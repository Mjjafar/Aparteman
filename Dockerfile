FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first for better layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && rm -rf /root/.cache

COPY . .

# Build static files at image time (dummy key is enough for collectstatic).
RUN DJANGO_SECRET_KEY=build-only-placeholder \
    uv run --no-sync python manage.py collectstatic --noinput --clear

# Run as non-root; entrypoint drops from root via setpriv so that
# root-owned bind mounts (fresh VPS clone) are chown'ed on startup.
RUN useradd -m -u 10001 app \
    && mkdir -p /app/data /app/media \
    && chown -R app:app /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/', timeout=4)" || exit 1

ENTRYPOINT ["sh", "entrypoint.sh"]
