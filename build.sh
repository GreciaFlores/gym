#!/usr/bin/env bash
# Build de Render: instala dependencias, junta estáticos y migra. Falla ante cualquier error.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py ensure_superuser

# Datos de ejemplo solo en entornos de prueba (idempotente: se puede correr en cada deploy).
if [ "$(echo "${SEED_DEMO:-}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  python manage.py seed_demo
fi
