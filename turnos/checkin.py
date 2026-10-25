"""Código de check-in de cada clase y ventana en la que es válido."""
import datetime as dt
import hashlib
import hmac

from django.conf import settings
from django.utils import timezone

# 32 símbolos sin ambiguos (sin 0/O/1/I). 256 es múltiplo de 32: el mapeo es uniforme.
ALFABETO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
LARGO_CODIGO = 4
MINUTOS_ANTES = 30


def codigo_checkin(clase):
    """Código de 4 caracteres, derivado por HMAC-SHA256 de `id:fecha` de la clase."""
    mensaje = f'{clase.id}:{clase.fecha}'.encode()
    digest = hmac.new(settings.CHECKIN_SECRET.encode(), mensaje, hashlib.sha256).digest()
    return ''.join(ALFABETO[b % len(ALFABETO)] for b in digest[:LARGO_CODIGO])


def ventana_checkin(clase):
    """(desde, hasta): 30 min antes del inicio hasta el fin de la clase."""
    desde = clase.inicio - dt.timedelta(minutes=MINUTOS_ANTES)
    hasta = clase.inicio + dt.timedelta(minutes=clase.duracion_min)
    return desde, hasta


def codigo_valido(clase, code, ahora):
    """True si `code` es el de la clase y `ahora` (aware) cae dentro de la ventana."""
    esperado = codigo_checkin(clase)
    recibido = str(code or '').strip().upper()
    coincide = hmac.compare_digest(recibido.encode(), esperado.encode())
    desde, hasta = ventana_checkin(clase)
    ahora = timezone.localtime(ahora)  # zona horaria del proyecto (Argentina)
    return coincide and desde <= ahora <= hasta
