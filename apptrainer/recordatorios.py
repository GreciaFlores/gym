"""Recordatorios por correo: avisa si terminaste el día de entrenamiento y faltan los pesos.

Regla: en un día de entrenamiento (el que la rutina asigna al día de la semana de hoy), pasada
la hora configurada (`RECORDATORIO_HORA`), si marcaste ejercicios como hechos que llevan peso
(todos menos movilidad) y no anotaste su peso, se envía UN correo con la lista de lo que falta.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from . import services
from .models import Bloque, Ejercicio, Recordatorio

log = logging.getLogger(__name__)


def ejercicios_sin_peso(usuario, dia, fecha):
    """Ejercicios con peso (todos menos movilidad) marcados como hechos y sin peso anotado."""
    hechos = services.hechos_de(usuario, dia, fecha)
    con_peso = services.pesos_de(usuario, dia, fecha)
    ejercicios = (
        Ejercicio.objects.filter(bloque__dia=dia).exclude(bloque__tipo=Bloque.MOVILIDAD)
        .select_related('bloque').order_by('bloque__orden', 'orden')
    )
    return [e for e in ejercicios if e.pk in hechos and e.pk not in con_peso]


def _enlace(dia, fecha):
    base = (settings.APP_URL or '').rstrip('/')
    ruta = f"{reverse('apptrainer:dia', args=[dia.pk])}?fecha={fecha.isoformat()}"
    return f'{base}{ruta}' if base else ruta


def armar_correo(usuario, dia, fecha, pendientes):
    nombre = usuario.first_name or usuario.username
    detalle = f' ({dia.enfoque})' if dia.enfoque else ''
    lista = '\n'.join(f'  • {e.nombre}' for e in pendientes)
    asunto = f'AppTrainer: faltan los pesos de {dia.titulo}'
    cuerpo = (
        f'Hola {nombre},\n\n'
        f'Hoy hiciste {dia.titulo}{detalle}, pero todavía no anotaste el peso de:\n\n{lista}\n\n'
        f'Anótalos aquí para no perder tu progreso:\n{_enlace(dia, fecha)}\n\n'
        'Si no quieres recibir estos avisos, quita tu correo en el panel de administración.\n'
        '— AppTrainer\n'
    )
    return asunto, cuerpo


def enviar_pendientes(ahora=None, ignorar_hora=False, simular=False, usuario=None):
    """Envía los recordatorios que correspondan. Devuelve una lista de dicts con lo hecho:
    [{'usuario', 'dia', 'pendientes', 'estado'}] donde estado es 'enviado', 'simulado' o 'error'."""
    ahora = ahora or timezone.localtime()
    if not ignorar_hora and ahora.hour < settings.RECORDATORIO_HORA:
        return []
    fecha = ahora.date()

    usuarios = get_user_model().objects.filter(is_active=True).exclude(email='')
    if usuario is not None:
        usuarios = usuarios.filter(pk=usuario.pk)

    resultados = []
    for u in usuarios:
        rutina = services.rutina_activa(u)
        dia = services.dia_de_hoy(rutina, fecha) if rutina else None
        if dia is None or Recordatorio.objects.filter(usuario=u, dia=dia, fecha=fecha).exists():
            continue
        pendientes = ejercicios_sin_peso(u, dia, fecha)
        if not pendientes:
            continue
        item = {'usuario': u, 'dia': dia, 'pendientes': pendientes}
        if simular:
            resultados.append({**item, 'estado': 'simulado'})
            continue
        asunto, cuerpo = armar_correo(u, dia, fecha, pendientes)
        try:
            send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [u.email], fail_silently=False)
        except Exception:  # un fallo de correo no debe frenar a los demás ni perder el aviso
            log.exception('No se pudo enviar el recordatorio a %s', u.username)
            resultados.append({**item, 'estado': 'error'})
            continue
        Recordatorio.objects.create(
            usuario=u, dia=dia, fecha=fecha, pendientes=', '.join(e.nombre for e in pendientes))
        resultados.append({**item, 'estado': 'enviado'})
    return resultados
