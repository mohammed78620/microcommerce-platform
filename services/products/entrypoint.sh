#!/usr/bin/env bash
set -e


echo "Apply database migrations"
uv run manage.py makemigrations --noinput
uv run manage.py migrate --noinput


# 👇 THIS LINE IS KEY
exec "$@"