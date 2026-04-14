#!/bin/sh
set -e

if [ -n "${DB_HOST}" ]; then
  until python -c "import os, socket; s=socket.create_connection((os.environ['DB_HOST'], int(os.environ.get('DB_PORT', '5432'))), 2); s.close()"; do
    echo "Waiting for database at ${DB_HOST}:${DB_PORT:-5432}..."
    sleep 2
  done

  python -c "import os, psycopg2; conn=psycopg2.connect(host=os.environ['DB_HOST'], port=os.environ.get('DB_PORT','5432'), dbname=os.environ.get('DB_NAME','ecommerce_demo'), user=os.environ.get('DB_USER','postgres'), password=os.environ.get('DB_PASSWORD','postgres')); conn.autocommit=True; cur=conn.cursor(); schema=os.environ.get('DB_SCHEMA'); cur.execute(f'CREATE SCHEMA IF NOT EXISTS \"{schema}\"'); cur.close(); conn.close()" 
fi

python manage.py migrate --noinput

case "${SERVICE_NAME}" in
  user_service)
    python manage.py seed_users
    ;;
  product_service)
    python manage.py seed_products
    ;;
  order_service)
    python manage.py seed_orders
    ;;
  payment_service)
    python manage.py seed_payments
    ;;
esac

python manage.py runserver 0.0.0.0:${PORT}
