web: gunicorn config.wsgi:application --workers 2 --threads 2 --timeout 60 --access-logfile -
release: python manage.py migrate --no-input
