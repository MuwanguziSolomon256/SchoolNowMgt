#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --no-input

echo "Ensuring default school exists..."
python manage.py ensure_default_school

echo "Loading data..."
python manage.py loaddata data.json 2>/dev/null || echo "No data.json to load"

echo "Starting gunicorn..."
exec gunicorn schoolmgmt_project.wsgi:application --workers 1 --bind 0.0.0.0:10000
