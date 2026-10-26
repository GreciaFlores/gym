# Recordatorios por correo

AppTrainer te manda **un correo** si terminaste un día de entrenamiento y **faltan los pesos**.

## Cuándo avisa
Todas estas condiciones juntas:

- Hoy es un día de entrenamiento (el que tu rutina tiene asignado a ese día de la semana).
- Ya pasó la hora configurada (por defecto, **21:00**, hora de tu zona horaria).
- Marcaste ejercicios como hechos que llevan peso (todos menos movilidad) y **no anotaste su peso**.
- Tu usuario tiene un correo guardado.

Manda **un solo aviso por día** con la lista de lo que falta y un enlace directo al día. No avisa si no
marcaste ni anotaste nada ese día, ni los días de descanso.

## Qué tienes que configurar (una sola vez)

### 1. Tu correo en tu usuario
En `https://TU-APP.onrender.com/admin/` → **Usuarios** → tu usuario → campo **Correo electrónico** → Guardar.

### 2. Un correo desde el cual enviar (SMTP)
La app necesita una cuenta para enviar. Con Gmail:

1. Activa la verificación en dos pasos en tu cuenta de Google.
2. Crea una **contraseña de aplicación** (Cuenta de Google → Seguridad → Contraseñas de aplicaciones).
   Es una clave de 16 letras, distinta de tu contraseña normal.
3. Guárdala solo en Render (nunca en GitHub).

### 3. Variables de entorno en Render
En el servicio **apptrainer** → **Environment**:

| Variable | Valor |
|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_HOST_USER` | tu correo de Gmail |
| `EMAIL_HOST_PASSWORD` | la contraseña de aplicación |
| `DEFAULT_FROM_EMAIL` | (opcional) `AppTrainer <tu-correo@gmail.com>` |
| `APP_URL` | (opcional) `https://TU-APP.onrender.com`; Render ya la completa si no la defines |
| `RECORDATORIO_HORA` | (opcional) hora desde la cual avisa, de 0 a 23. Por defecto `21` |

Otros proveedores (Outlook, Brevo, SendGrid, Mailgun…) funcionan igual: usa su servidor SMTP y credenciales.

### 4. Un Cron Job en Render que lo ejecute cada hora
En Render: **New +** → **Cron Job**.

- **Repository / Branch:** el mismo repo y rama que la web.
- **Runtime:** Python 3.
- **Build Command:** `pip install -r requirements.txt`
- **Command:** `python manage.py enviar_recordatorios`
- **Schedule:** `0 * * * *` (cada hora en punto)
- **Environment:** las mismas variables de la web: `DATABASE_URL`, `DJANGO_SECRET_KEY`,
  `DJANGO_DEBUG=False`, `DJANGO_TIME_ZONE` y las del correo de arriba.
  Tip: crea un **Environment Group** con todas y asócialo a la web y al cron.

El programa solo actúa pasada la hora configurada y recuerda lo que ya envió, así que correr cada hora
es seguro: no repite avisos.

## Probar que funciona
En la pestaña **Shell** de la web (o del cron):

```bash
python manage.py enviar_recordatorios --simular --ahora   # muestra qué mandaría, sin enviar
python manage.py enviar_recordatorios --ahora             # envía de verdad, sin esperar la hora
python manage.py enviar_recordatorios --ahora --usuario TU_USUARIO
```

Para una prueba real: marca un ejercicio como hecho (sin peso) en el día que toca hoy y corre el segundo comando.

## Si no llega
- Revisa la carpeta de spam.
- `Falta configurar el correo`: faltan las variables `EMAIL_HOST`, `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`.
- Error de autenticación: con Gmail usa la contraseña de aplicación, no la normal.
- En `/admin/` → **Recordatorios enviados** ves cuáles se mandaron y cuándo.
- Para dejar de recibirlos: borra tu correo en el usuario (en `/admin/`).

## Datos que no se tocan
Los recordatorios solo **leen** tu registro; no modifican tus pesos ni tu historial.
