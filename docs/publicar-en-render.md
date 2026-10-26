# Publicar AppTrainer en Render (paso a paso)

Tiempo estimado: 20 minutos. No necesitas instalar nada en tu computadora.

## 1. Antes de empezar
- Cuenta en [GitHub](https://github.com) con este repositorio (ya lo tienes).
- Cuenta en [Render](https://render.com) (puedes entrar con tu cuenta de GitHub).
- Una tarjeta para los planes de pago.

## 2. Crear los servicios
1. En Render: **New +** → **Blueprint**.
2. Conecta tu cuenta de GitHub y elige el repositorio `gym`.
3. Render lee el archivo `render.yaml` y te muestra lo que va a crear:
   - **apptrainer** (la web, plan *Starter*): no se duerme.
   - **apptrainer-db** (PostgreSQL gestionado): guarda tus datos con backups.
4. Revisa los planes y pulsa **Apply**. El primer despliegue tarda unos minutos.

> Ajusta `DJANGO_TIME_ZONE` en `render.yaml` a tu país antes de aplicar, por ejemplo `America/Mexico_City`.
> Esto decide en qué momento "cambia el día" para marcar tus ejercicios.

## 3. Crear tu usuario y cargar la rutina
Cuando el servicio esté en verde, abre la pestaña **Shell** de `apptrainer` en Render y ejecuta:

```bash
python manage.py createsuperuser           # elige usuario y contraseña
python manage.py seed_rutina --usuario TU_USUARIO
```

## 4. Usarla
- Abre `https://apptrainer.onrender.com/app/` (el dominio exacto lo ves en Render).
- **Android (Chrome):** menú ⋮ → *Instalar app*.
- **iPhone (Safari):** Compartir → *Agregar a pantalla de inicio*.
- El panel de administración está en `/admin/`.

## 5. Dominio propio (opcional)
En Render → apptrainer → **Settings → Custom Domains**. Después agrega el dominio en la variable
`DJANGO_ALLOWED_HOSTS` y `https://tu-dominio.com` en `DJANGO_CSRF_TRUSTED_ORIGINS`.

## Qué cuidar
- **Backups:** el plan de pago de PostgreSQL incluye backups; además puedes descargar tu peso en Excel desde la app.
- **Secretos:** `DJANGO_SECRET_KEY` la genera Render. Nunca la subas a GitHub.
- **Otros hostings:** el repo trae `Procfile` y `build.sh`, por lo que funciona igual en Railway, Fly.io o Heroku.
