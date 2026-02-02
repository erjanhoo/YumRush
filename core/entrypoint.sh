#!/bin/sh
set -e

: "${PORT:=8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec daphne -b 0.0.0.0 -p "$PORT" core.asgi:application
