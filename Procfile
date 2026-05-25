web: python manage.py migrate --no-input && python manage.py loaddata data.json 2>/dev/null || true && gunicorn schoolmgmt_project.wsgi:application --workers 1 --bind 0.0.0.0:10000
