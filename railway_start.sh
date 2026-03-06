#!/bin/bash

# Exit on error
set -o errexit

echo "--- Pushing Migrations ---"
python manage.py migrate --noinput

echo "--- Collecting Static Files ---"
python manage.py collectstatic --noinput --clear

echo "--- Initializing Admin Superuser ---"
python manage.py initadmin

echo "--- Starting Gunicorn ---"
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
