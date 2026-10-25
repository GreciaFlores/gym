"""Check-in por QR: páginas públicas para el alumno."""
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from . import services
from .checkin import (
    codigo_valido, intentos_bloqueados, registrar_intento_fallido, ventana_checkin,
)
from .models import Clase, Reserva
from .views import alumno_actual


def _render(request, template, status=200, **ctx):
    ctx.setdefault('trainer_name', settings.TRAINER_NAME)
    return render(request, template, ctx, status=status)


def _bloqueado(request):
    return _render(request, 'turnos/checkin_error.html', status=429,
                   mensaje='Demasiados intentos, esperá unos minutos.')


def _codigo_invalido(request):
    # Mensaje genérico: no distingue código incorrecto de fuera de ventana ni revela la clase.
    return _render(
        request, 'turnos/checkin_error.html', status=400, ir_a_lista=True,
        mensaje='El código no es válido o la clase todavía no está habilitada '
                '(se habilita 30 minutos antes de empezar).',
    )


def checkin_clase(request, pk):
    alumno = alumno_actual(request)
    if intentos_bloqueados(request, alumno):
        return _bloqueado(request)
    datos = request.POST if request.method == 'POST' else request.GET
    code = datos.get('code', '').strip()
    if not code and request.method != 'POST':
        return redirect('checkin_lista')
    clase = Clase.objects.filter(pk=pk, estado=Clase.ABIERTA).first()
    if clase is None or not codigo_valido(clase, code, timezone.now()):
        registrar_intento_fallido(request, alumno)
        return _codigo_invalido(request)

    if alumno is None:
        if request.method == 'POST':
            return redirect(f"{reverse('checkin', args=[clase.pk])}?{urlencode({'code': code})}")
        return _render(request, 'turnos/checkin_identificar.html', clase=clase,
                       next=request.get_full_path())
    if request.method != 'POST':  # el GET nunca crea movimientos
        return _render(request, 'turnos/checkin.html', clase=clase, alumno=alumno, code=code)
    try:
        resultado = services.registrar_checkin(alumno, clase)
    except services.CheckinError as e:
        return _render(request, 'turnos/checkin_error.html', mensaje=str(e),
                       sin_saldo=e.sin_saldo)
    return _render(request, 'turnos/checkin_ok.html', clase=clase, alumno=alumno,
                   saldo=resultado.saldo, reservas_sin_saldo=resultado.reservas_sin_saldo)


def _clases_con_ventana_abierta():
    ahora = timezone.now()
    clases = Clase.objects.filter(fecha=timezone.localdate(), estado=Clase.ABIERTA)
    return [c for c in clases if ventana_checkin(c)[0] <= ahora <= ventana_checkin(c)[1]]


def checkin_lista(request):
    """Plan B: sin QR, el alumno elige la clase de hoy y tipea el código."""
    alumno = alumno_actual(request)
    clases = _clases_con_ventana_abierta()
    error = None
    if request.method == 'POST':
        if intentos_bloqueados(request, alumno):
            return _bloqueado(request)
        code = request.POST.get('code', '').strip().upper()
        elegida = next((c for c in clases if str(c.pk) == request.POST.get('clase')), None)
        if elegida is not None and codigo_valido(elegida, code, timezone.now()):
            return redirect(f"{reverse('checkin', args=[elegida.pk])}?{urlencode({'code': code})}")
        registrar_intento_fallido(request, alumno)
        error = 'El código no es válido para esa clase.'
    return _render(request, 'turnos/checkin_lista.html', clases=clases, error=error,
                   status=400 if error else 200)
