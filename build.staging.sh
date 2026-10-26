#!/usr/bin/env bash
# Build de STAGING en Render. Reutiliza ./build.sh (el de producción: pip install + collectstatic)
# y agrega lo que el plan gratuito no ofrece: no hay preDeployCommand, así que se migra acá.
# Es idempotente: se puede correr en cada deploy sin duplicar datos.
set -o errexit

./build.sh
python manage.py migrate --no-input
python manage.py ensure_superuser

# Datos de ejemplo del gimnasio (clases, alumnos y reservas), solo si SEED_DEMO=True.
if [ "$(echo "${SEED_DEMO:-}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  python manage.py seed_demo
fi
