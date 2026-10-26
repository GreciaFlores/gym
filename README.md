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
- Reservar no descuenta saldo: la reserva es una intención. Lo único que consume una clase es el **check-in**; un no-show no tiene penalidad.
- La reserva con check-in pasa a `asistida` y sigue ocupando su lugar en el cupo.
- Color de clase: verde disponible · amarillo ≤2 lugares · gris completa, pasada o cancelada.

## Check-in con QR

- Para dejarlo abierto todo el día en el celular del entrenador: **QR actual (dejar abierto)** en el índice del admin. Muestra el QR de la(s) clase(s) con la ventana abierta (dos lado a lado si se solapan), o "Próxima clase HH:MM, el QR aparece a las HH:MM", y cambia solo cada 15 s.
1. En el admin, **Clases de hoy** (link en el índice) → **Mostrar QR**. Pantalla pensada para el celular: QR grande, código de 4 caracteres, alumnos que ya hicieron check-in; se refresca cada 15 s.
2. El alumno escanea el QR → `/checkin/<clase>/?code=XXXX` → se identifica con su DNI (si hace falta) → **Confirmar check-in** (descuenta 1 clase). Sin QR: `/checkin/` y tipear el código.
3. El código es válido desde 30 min antes del inicio hasta el fin de la clase. Se firma con `CHECKIN_SECRET` (obligatoria si `DJANGO_DEBUG=False`).
4. Límite: 5 códigos inválidos cada 10 min por sesión y por alumno (no por IP: en el gimnasio todos comparten IP pública). Usa el cache de Django (`LocMemCache`), que es **por proceso**: con varios workers el límite efectivo es mayor. Es aceptable para este riesgo.

### Detrás de un proxy (Render)

Con `DJANGO_BEHIND_PROXY=True` Django confía en `X-Forwarded-Proto`: el QR sale con `https://` y los POST pasan la verificación CSRF. Si hace falta, `DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com`.

### Probar desde el celular en la red local

```bash
ip route get 1 | awk '{print $7; exit}'      # IP local, ej. 192.168.1.20
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20 python manage.py runserver 0.0.0.0:8000
```

Abrí `http://192.168.1.20:8000/admin/turnos/clase/hoy/` (la URL del QR usa el host con el que entraste: entrá por la IP, no por `localhost`). El celular debe estar en el mismo WiFi y el firewall debe permitir el puerto 8000. Para probar necesitás una clase de hoy con la ventana abierta (30 min antes del inicio hasta el fin).

## Deploy staging en Render

El staging se despliega con un Blueprint propio: **`render.staging.yaml`**. No se llama `render.yaml` a propósito: Render toma `render.yaml` como el Blueprint por defecto del repo, que es el de producción (`apptrainer` + `apptrainer-db`). Con otro nombre, el staging no lo pisa ni lo modifica, y todos sus recursos tienen nombres distintos (`apptrainer-staging`, `apptrainer-staging-db`).

1. En Render: **New → Blueprint**, elegí este repo y en *Blueprint file path* escribí `render.staging.yaml`. Sigue la branch `feature/checkin-qr`.
2. Completá las variables que pide (`sync: false`): `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` (opcional) y `TRAINER_NAME`. `DJANGO_SECRET_KEY` y `CHECKIN_SECRET` se generan solas.
3. Cada deploy corre `build.staging.sh`. Reutiliza `build.sh` (el de producción: `pip install` + `collectstatic`, que no se modifica) y agrega `migrate` (el plan gratuito no tiene `preDeployCommand`), `ensure_superuser` (crea el usuario solo si no existe y no le cambia la clave) y, si `SEED_DEMO=True`, `seed_demo` (idempotente: no duplica datos ni vuelve a armar los escenarios).
4. La configuración es la de producción (`PYTHON_VERSION=3.13.5`, `DJANGO_TIME_ZONE`, HTTPS y cookies seguras con `DJANGO_DEBUG=False`, `/healthz`). Render inyecta `RENDER_EXTERNAL_HOSTNAME` y `settings.py` lo agrega solo a `ALLOWED_HOSTS` y a `CSRF_TRUSTED_ORIGINS`. `CHECKIN_SECRET` se genera sola.
5. La rutina de AppTrainer (`seed_rutina`) **no** se carga en el build: falla si el usuario ya registró entrenamientos y con `--forzar` los borra, así que no es seguro correrla en cada deploy.

Notas: el plan gratuito duerme el servicio tras un rato sin tráfico (el primer request tarda) y la base gratuita de Render vence a los 30 días. Los estáticos los sirve WhiteNoise. Con 2 workers de gunicorn el límite de intentos del check-in es por proceso (ver arriba).

## Tests

```bash
pytest
```

## PostgreSQL

Definí `DATABASE_URL=postgres://usuario:clave@host:5432/gym` en `.env` y corré `migrate`.

## Fuera de alcance (por ahora)

WhatsApp, pagos online, login con contraseña, notificaciones.
