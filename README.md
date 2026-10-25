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
3. Cada deploy corre `build.sh`: instala dependencias, `collectstatic`, `migrate`, `ensure_superuser` (crea el usuario solo si no existe y no le cambia la clave) y, si `SEED_DEMO=True`, `seed_demo` (idempotente: no duplica datos ni vuelve a armar los escenarios).
4. Render inyecta `RENDER_EXTERNAL_HOSTNAME`: se agrega solo a `ALLOWED_HOSTS` y a `CSRF_TRUSTED_ORIGINS` (`https://<host>`). `DJANGO_BEHIND_PROXY=True` hace que el QR salga con `https://`.

Notas: el plan gratuito duerme el servicio tras un rato sin tráfico (el primer request tarda) y la base gratuita de Render vence a los 30 días. Los estáticos los sirve WhiteNoise. Con 2 workers de gunicorn el límite de intentos del check-in es por proceso (ver arriba).

## Tests

```bash
pytest
```

## PostgreSQL

Definí `DATABASE_URL=postgres://usuario:clave@host:5432/gym` en `.env` y corré `migrate`.

## Fuera de alcance (por ahora)

WhatsApp, pagos online, login con contraseña, notificaciones.
