# Gym · Reservas de clases (MVP)

Landing para que los alumnos de un entrenador personal vean las clases de la semana, se identifiquen con su DNI y reserven. El entrenador gestiona todo desde el Django Admin.

**Stack:** Python 3.12+ (probado en 3.13) · Django 5 · SQLite (PostgreSQL vía `DATABASE_URL`) · Tailwind por CDN.

## Levantar en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # editá TRAINER_NAME / TRAINER_BIO
python manage.py migrate
python manage.py seed_demo      # datos de ejemplo
python manage.py createsuperuser
python manage.py runserver
```

- Landing: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

La landing usa Tailwind desde CDN: necesita internet para verse con estilos.

## Datos de ejemplo (`seed_demo`)

Crea 2 semanas de clases (lun–vie, 8/9/18/19 h), y 5 alumnos. Es idempotente.

| DNI | Alumno | Saldo |
|---|---|---|
| 30111222 | Ana Pérez | 7 (pago de $100.000, resto $2.000 en la nota) |
| 31222333 | Bruno Gómez | 3 |
| 32333444 | Carla Sosa | 1 |
| 33444555 | Diego López | 10 |
| 34555666 | Eli Ruiz | 0 (sin saldo) |

Incluye una clase completa, una con 2 lugares libres, clases pasadas, una cancelada y reservas varias.

## Panel del entrenador (admin)

- **Alumnos:** búsqueda por DNI/nombre/teléfono; muestra saldo. Acción **"Registrar pago"**: ingresa el monto y se acreditan las clases enteras (`monto // precio`); el resto queda en la nota.
- **Clases:** filtros por estado y fecha; botón **"Crear clases recurrentes"** (días, horas, N semanas, cupo, precio). Saltea las que ya existen.
- **Reservas** y **Movimientos** (libro de saldo): filtros y búsqueda por DNI.

## Reglas

- Saldo = suma de `clases` del libro de movimientos. Saldo disponible = saldo − reservas futuras confirmadas.
- Reservar no descuenta saldo (el consumo llegará con el check-in QR).
- Color de clase: verde disponible · amarillo ≤2 lugares · gris completa, pasada o cancelada.

## Tests

```bash
pytest
```

## PostgreSQL

Definí `DATABASE_URL=postgres://usuario:clave@host:5432/gym` en `.env` y corré `migrate`.

## Fuera de alcance (por ahora)

Check-in con QR, WhatsApp, pagos online, login con contraseña, notificaciones.
