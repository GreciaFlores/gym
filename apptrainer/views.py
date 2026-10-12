from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from . import services
from .forms import PesoForm
from .models import Dia, Ejercicio, RegistroPeso

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def health(request):
    """Chequeo para el hosting: la app responde y la base de datos también."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return HttpResponse('db error', status=503, content_type='text/plain')
    return HttpResponse('ok', content_type='text/plain')


def _agrupar(ejercicios):
    """Agrupa ejercicios consecutivos con el mismo `grupo` (combinados) en una lista."""
    items = []
    for e in ejercicios:
        if items and e.grupo is not None and items[-1][-1].grupo == e.grupo:
            items[-1].append(e)
        else:
            items.append([e])
    return items


def _armar_bloques(usuario, dia, fecha):
    hechos = services.hechos_de(usuario, dia, fecha)
    bloques = []
    for b in dia.bloques.prefetch_related('ejercicios').order_by('orden'):
        ejercicios = list(b.ejercicios.all())
        for e in ejercicios:
            e.hecho = e.pk in hechos
        bloques.append({
            'tipo': b.tipo,
            'titulo': b.get_tipo_display(),
            'items': _agrupar(ejercicios),
            'hechos': sum(e.hecho for e in ejercicios),
            'total': len(ejercicios),
        })
    return bloques, len(hechos)


@login_required
def hoy(request):
    usuario, fecha = request.user, timezone.localdate()
    rutina = services.rutina_activa(usuario)
    contexto = {'rutina': rutina, 'fecha': fecha, 'seccion': 'hoy'}
    if rutina:
        dia = services.dia_de_hoy(rutina, fecha)
        hechas, total_dias = services.resumen_semana(usuario, rutina, fecha)
        contexto.update(hechas=hechas, total_dias=total_dias)
        if dia:
            total = services.total_ejercicios(dia)
            n_hechos = len(services.hechos_de(usuario, dia, fecha))
            contexto.update(dia=dia, n_hechos=n_hechos, total=total,
                            porcentaje=round(100 * n_hechos / total) if total else 0)
        else:
            proximo, fecha_proximo = services.proximo_dia(rutina, fecha)
            contexto.update(proximo=proximo, fecha_proximo=fecha_proximo)
    serie = services.serie_peso(usuario)
    if serie:
        contexto.update(ultimo_peso=serie[-1])
    return render(request, 'apptrainer/hoy.html', contexto)


@login_required
def semana(request):
    usuario, fecha = request.user, timezone.localdate()
    rutina = services.rutina_activa(usuario)
    filas = []
    if rutina:
        sesiones = services.estado_semana(usuario, rutina, fecha)
        for d in rutina.dias.order_by('orden'):
            s = sesiones.get(d.pk)
            filas.append({
                'dia': d,
                'es_hoy': d.dia_semana == fecha.weekday(),
                'completada': bool(s and s.completada),
                'en_curso': bool(s and not s.completada and s.n_hechos),
            })
    return render(request, 'apptrainer/semana.html',
                  {'rutina': rutina, 'filas': filas, 'seccion': 'semana', 'fecha': fecha})


@login_required
def dia_detalle(request, pk):
    dia = get_object_or_404(Dia, pk=pk, rutina__usuario=request.user)
    fecha = timezone.localdate()
    bloques, n_hechos = _armar_bloques(request.user, dia, fecha)
    total = sum(b['total'] for b in bloques)
    return render(request, 'apptrainer/dia.html', {
        'dia': dia, 'bloques': bloques, 'fecha': fecha, 'seccion': 'semana',
        'n_hechos': n_hechos, 'total': total,
        'porcentaje': round(100 * n_hechos / total) if total else 0,
    })


@login_required
@require_POST
def alternar(request, pk):
    ejercicio = get_object_or_404(
        Ejercicio.objects.select_related('bloque__dia'),
        pk=pk, bloque__dia__rutina__usuario=request.user,
    )
    hecho, hechos, total, completada = services.alternar_ejercicio(
        request.user, ejercicio, timezone.localdate()
    )
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({
            'hecho': hecho, 'hechos': hechos, 'total': total, 'completada': completada,
            'porcentaje': round(100 * hechos / total) if total else 0,
        })
    return redirect('apptrainer:dia', pk=ejercicio.bloque.dia_id)


@login_required
def peso(request):
    usuario = request.user
    if request.method == 'POST':
        form = PesoForm(request.POST)
        if form.is_valid():
            _, creado = RegistroPeso.objects.update_or_create(
                usuario=usuario, fecha=form.cleaned_data['fecha'],
                defaults={'kg': form.cleaned_data['kg'], 'nota': form.cleaned_data['nota']},
            )
            messages.success(request, 'Peso guardado.' if creado else 'Peso actualizado para esa fecha.')
            return redirect('apptrainer:peso')
    else:
        form = PesoForm()
    serie = services.serie_peso(usuario)
    grafica = [
        {'fecha': f['fecha'].isoformat(), 'kg': float(f['kg']), 'media': float(f['media'])}
        for f in serie
    ]
    resumen = None
    if serie:
        resumen = {
            'actual': serie[-1]['kg'],
            'cambio_total': serie[-1]['kg'] - serie[0]['kg'] if len(serie) > 1 else None,
            'cambio_ultimo': serie[-1]['variacion'],
        }
    return render(request, 'apptrainer/peso.html', {
        'form': form, 'serie': list(reversed(serie)), 'grafica': grafica,
        'resumen': resumen, 'seccion': 'peso',
    })


@login_required
@require_POST
def peso_eliminar(request, pk):
    get_object_or_404(RegistroPeso, pk=pk, usuario=request.user).delete()
    messages.success(request, 'Registro eliminado.')
    return redirect('apptrainer:peso')


@login_required
@require_GET
def peso_excel(request):
    contenido = services.exportar_pesos_excel(request.user)
    nombre = f'apptrainer-peso-{timezone.localdate().isoformat()}.xlsx'
    respuesta = HttpResponse(contenido, content_type=XLSX)
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


@require_GET
def service_worker(request):
    """Se sirve desde /app/sw.js para que su alcance cubra toda la app."""
    prefijo_static = '/' + settings.STATIC_URL.lstrip('/')
    respuesta = render(request, 'apptrainer/sw.js', {'STATIC_URL': prefijo_static},
                       content_type='text/javascript')
    respuesta['Cache-Control'] = 'no-cache'
    return respuesta


@require_GET
def manifest(request):
    return render(request, 'apptrainer/manifest.webmanifest', content_type='application/manifest+json')


@never_cache
def offline(request):
    return render(request, 'apptrainer/offline.html')
