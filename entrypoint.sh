#!/bin/sh
set -e
uv run python manage.py migrate --noinput
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2
