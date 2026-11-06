#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
python manage.py seed
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 90
