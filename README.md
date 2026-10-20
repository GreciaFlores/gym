# AppTrainer · Rutina y peso

App web (instalable en el celular) para guardar la **rutina semanal** y llevar el **registro de peso**. Vive en este mismo proyecto, en `/app/`, junto al módulo de reservas de abajo.

- **Hoy:** qué día toca, progreso y resumen de la semana.
- **Semana:** los días de la rutina con su estado (pendiente / en curso / completado).
- **Hoy:** el día que toca y el **cierre semanal**: semana pasada frente a la semana en curso, día por día, con la carga total y la diferencia. Se puede ver el **total** o el **detalle** (barra + discos, mancuernas).
- **Día:** movilidad, zona media y trabajo principal, con checks, ejercicios combinados, material, videos, una **ilustración** y las **indicaciones del entrenador** tal cual las escribió. Se elige la **fecha** de la sesión y el **peso levantado** de cada ejercicio (menos movilidad) como **barra + discos**, **mancuernas** (× 2) o **total**; el hip thrust se anota como **barra + cada lado** (× 2). Cada día tiene una caja de **comentarios**. Un botón guarda todo y muestra el **resumen**.
- **Excel:** desde "Mi semana" se elige el rango de fechas (o la semana pasada, o todo el historial) y se descarga el registro con el detalle de cada carga.
- El peso corporal (`/app/peso/`) sigue en el código pero ya no aparece en el menú.
- **Peso:** registro semanal, gráfica con media móvil, historial y **descarga en Excel**.
- Login con usuario y contraseña. Cada usuario ve **solo sus datos** (listo para que un entrenador sume alumnos).
- Panel `/admin/` para editar rutinas, días, bloques y ejercicios.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_rutina --usuario TU_USUARIO   # carga la rutina de 3 días (no pisa un historial existente; --forzar lo borra)
python manage.py runserver                           # http://127.0.0.1:8000/app/
```

Publicación en producción: [docs/publicar-en-render.md](docs/publicar-en-render.md) (`render.yaml` incluido).

Las ilustraciones de los ejercicios se generan con `python scripts/generar_ilustraciones.py` (SVG en `apptrainer/static/apptrainer/ejercicios/`); la imagen, el tipo de carga y los ajustes de cada ejercicio (por ejemplo, discos por lado) están en `apptrainer/catalogo.py` y se pueden cambiar en `/admin/`.

Las migraciones son aditivas: aplicarlas no borra ni reescribe el historial (hay un test que lo comprueba).

> **Para evolucionar:** `Ejercicio.prescripcion` es texto libre (`3x10`, `3xfallo`) y el peso se anota una vez por ejercicio. La próxima fase puede registrar kg y reps por serie.

---

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
