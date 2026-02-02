#!/bin/sh
set -e

: "${PORT:=8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py populate_db

exec daphne -b 0.0.0.0 -p "$PORT" core.asgi:application
