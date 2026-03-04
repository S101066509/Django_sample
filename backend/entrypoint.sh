#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding database via Django dbshell..."
python manage.py dbshell < /app/seed.sql

echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
