#!/usr/bin/env bash
# Build para el hosting (Render): instala dependencias y prepara los estáticos.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
