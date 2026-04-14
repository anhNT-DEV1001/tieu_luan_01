#!/bin/sh
set -e

until python app/manage.py migrate --noinput; do
  echo "Waiting for database..."
  sleep 2
done

python app/manage.py runserver 0.0.0.0:8000
