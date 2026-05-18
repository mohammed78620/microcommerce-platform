#!/usr/bin/env bash
set -e


echo "Apply database migrations"
uv run manage.py migrate --noinput


exec "$@"
EOF