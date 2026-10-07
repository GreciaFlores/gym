import datetime as dt

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import services
from .forms import DniForm, RegistroForm
from .models import Alumno, Clase, Reserva

SESSION_KEY = 'alumno_id'
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']


def alumno_actual(request):
    alumno_id = request.session.get(SESSION_KEY)
    if not alumno_id:
        return None
    alumno = Alumno.objects.filter(pk=alumno_id, activo=True).first()
    if alumno is None:
        request.session.pop(SESSION_KEY, None)
    return alumno


def _lunes(fecha):
    return fecha - dt.timedelta(days=fecha.weekday())


def _semana_param(request):
    try:
        return _lunes(dt.date.fromisoformat(request.GET.get('semana', '')))
    except ValueError:
        return _lunes(timezone.localdate())


def _volver(request):
    semana = request.POST.get('semana')
    url = '/'
    if semana:
        try:
            url = f'/?semana={dt.date.fromisoformat(semana).isoformat()}'
        except ValueError:
            pass
    return redirect(url)


def index(request):
    alumno = alumno_actual(request)
    lunes = _semana_param(request)
    domingo = lunes + dt.timedelta(days=6)

    clases = list(
        Clase.objects.filter(fecha__range=(lunes, domingo)).annotate(
            ocupados=Count('reservas', filter=Q(reservas__estado=Reserva.CONFIRMADA))
        )
    )
    mias = set()
    if alumno:
        mias = set(
            alumno.reservas.filter(estado=Reserva.CONFIRMADA, clase__in=clases)
            .values_list('clase_id', flat=True)
        )
    saldo_ok = bool(alumno and alumno.saldo_disponible > 0)
    hoy = timezone.localdate()
    dias = []
    for n in range(7):
        fecha = lunes + dt.timedelta(days=n)
        items = []
        for c in (c for c in clases if c.fecha == fecha):
            reservada = c.pk in mias
            puede = c.color != 'gris'
            items.append({
                'clase': c,
                'reservada': reservada,
                'puede_reservar': puede and not reservada,
                'sin_saldo': puede and not reservada and bool(alumno) and not saldo_ok,
                'puede_cancelar': reservada and not c.ya_paso,
            })
        dias.append({
            'fecha': fecha, 'nombre': DIAS[n], 'es_hoy': fecha == hoy, 'items': items,
        })

    return render(request, 'turnos/index.html', {
        'trainer_name': settings.TRAINER_NAME,
        'trainer_bio': settings.TRAINER_BIO,
        'alumno': alumno,
        'dias': dias,
        'lunes': lunes,
        'domingo': domingo,
        'rango': f'{lunes.day} de {MESES[lunes.month - 1]} – {domingo.day} de {MESES[domingo.month - 1]}',
        'semana_anterior': lunes - dt.timedelta(days=7),
        'semana_siguiente': lunes + dt.timedelta(days=7),
        'semana_actual': _lunes(hoy),
        'form': DniForm(),
    })


@require_POST
def identificar(request):
    form = DniForm(request.POST)
    if not form.is_valid():
        for err in form.errors.get('dni', []):
            messages.error(request, err)
        return _volver(request)
    dni = form.cleaned_data['dni']
    alumno = Alumno.objects.filter(dni=dni).first()
    if alumno is None:
        request.session['dni_pendiente'] = dni
        return redirect('registro')
    if not alumno.activo:
        messages.error(request, 'Tu cuenta está inactiva, hablá con tu entrenador.')
        return _volver(request)
    request.session[SESSION_KEY] = alumno.pk
    messages.success(request, f'¡Hola, {alumno.nombre}!')
    return _volver(request)


def registro(request):
    dni = request.session.get('dni_pendiente')
    if not dni:
        return redirect('index')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if Alumno.objects.filter(dni=dni).exists():  # carrera: ya lo registraron
            return redirect('index')
        alumno = form.save(commit=False)
        alumno.dni = dni
        alumno.save()
        request.session.pop('dni_pendiente', None)
        request.session[SESSION_KEY] = alumno.pk
        messages.success(request, f'¡Listo, {alumno.nombre}! Te registraste. Coordiná el pago con tu entrenador para sumar clases.')
        return redirect('index')
    return render(request, 'turnos/registro.html', {
        'form': form, 'dni': dni, 'trainer_name': settings.TRAINER_NAME,
    })


@require_POST
def salir(request):
    request.session.pop(SESSION_KEY, None)
    return _volver(request)


def _accion(request, pk, funcion, ok):
    alumno = alumno_actual(request)
    if not alumno:
        messages.error(request, 'Primero identificate con tu DNI.')
        return _volver(request)
    clase = get_object_or_404(Clase, pk=pk)
    try:
        funcion(alumno, clase)
    except services.ReservaError as e:
        messages.error(request, str(e))
    else:
        messages.success(request, ok.format(clase=clase))
    return _volver(request)


@require_POST
def reservar(request, pk):
    return _accion(request, pk, services.reservar, 'Reservaste la clase del {clase.fecha:%d/%m} a las {clase.hora_inicio:%H:%M}.')


@require_POST
def cancelar(request, pk):
    return _accion(request, pk, services.cancelar, 'Cancelaste tu reserva del {clase.fecha:%d/%m} a las {clase.hora_inicio:%H:%M}.')
