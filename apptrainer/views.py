import datetime as dt

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from . import services
from .cargas import armar_carga, kg_texto
from .forms import KgField, PesoForm
from .models import CARGA_BARRA, CARGA_MANCUERNAS, CARGA_TOTAL, TIPOS_CARGA, Bloque, Dia, Ejercicio, RegistroPeso

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
ETIQUETAS_MODO = [(CARGA_BARRA, 'Barra'), (CARGA_MANCUERNAS, 'Mancuernas'), (CARGA_TOTAL, 'Total')]


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


def _carga_para_mostrar(e, guardado, previo, escritos):
    """Datos que necesita la plantilla para dibujar los campos de peso de un ejercicio."""
    if escritos is not None:  # se volvió a mostrar tras un error: respeta lo tipeado
        return {
            'modo': escritos['modo'], 'total': escritos['total'], 'barra': escritos['barra'],
            'discos': escritos['discos'], 'mancuerna': escritos['mancuerna'],
        }
    base = guardado or None
    modo = (guardado.modo if guardado else previo.modo if previo else e.carga_habitual)
    return {
        'modo': modo,
        'total': kg_texto(base.kg) if base and base.modo == CARGA_TOTAL else '',
        'barra': kg_texto(base.kg_barra) if base else '',
        'discos': kg_texto(base.kg_discos) if base else '',
        'mancuerna': kg_texto(base.kg_mancuerna) if base else '',
    }


def _armar_bloques(usuario, dia, fecha, escritos=None, errores=None):
    """Bloques del día con el estado de cada ejercicio en `fecha`.

    `escritos` ({ejercicio_id: campos tipeados}) y `errores` ({ejercicio_id: mensaje})
    permiten volver a mostrar lo escrito cuando el guardado falló por un peso inválido.
    """
    escritos, errores = escritos or {}, errores or {}
    hechos = services.hechos_de(usuario, dia, fecha)
    guardados = services.pesos_de(usuario, dia, fecha)
    previos = services.ultimos_pesos(usuario, dia, fecha)
    bloques = []
    for b in dia.bloques.prefetch_related('ejercicios').order_by('orden'):
        ejercicios = list(b.ejercicios.all())
        con_peso = b.tipo != Bloque.MOVILIDAD
        for e in ejercicios:
            e.hecho = e.pk in hechos
            e.guardado = guardados.get(e.pk)
            e.kg = e.guardado.kg if e.guardado else None
            e.previo = previos.get(e.pk)
            e.carga = _carga_para_mostrar(e, e.guardado, e.previo, escritos.get(e.pk))
            e.kg_error = errores.get(e.pk, '')
        bloques.append({
            'tipo': b.tipo,
            'titulo': b.get_tipo_display(),
            'con_peso': con_peso,
            'ejercicios': ejercicios,
            'items': _agrupar(ejercicios),
            'hechos': sum(e.hecho for e in ejercicios),
            'total': len(ejercicios),
        })
    return bloques, len(hechos)


def _contexto_dia(usuario, dia, fecha, escritos=None, errores=None):
    bloques, n_hechos = _armar_bloques(usuario, dia, fecha, escritos, errores)
    total = sum(b['total'] for b in bloques)
    hoy = timezone.localdate()
    return {
        'dia': dia, 'bloques': bloques, 'fecha': fecha, 'seccion': 'semana',
        'n_hechos': n_hechos, 'total': total,
        'porcentaje': round(100 * n_hechos / total) if total else 0,
        'modos': ETIQUETAS_MODO,
        'hoy_iso': hoy.isoformat(), 'manana_iso': (hoy + dt.timedelta(days=1)).isoformat(),
        'es_hoy': fecha == hoy, 'es_manana': fecha == hoy + dt.timedelta(days=1),
    }


def _dia_del_usuario(request, pk):
    return get_object_or_404(Dia, pk=pk, rutina__usuario=request.user)


def _url_dia(nombre, pk, fecha):
    return f"{reverse(nombre, args=[pk])}?fecha={fecha.isoformat()}"


@login_required
def hoy(request):
    usuario, fecha = request.user, timezone.localdate()
    rutina = services.rutina_activa(usuario)
    contexto = {'rutina': rutina, 'fecha': fecha, 'seccion': 'hoy'}
    if rutina:
        dia = services.dia_de_hoy(rutina, fecha)
        hechas, total_dias = services.resumen_semana(usuario, rutina, fecha)
        contexto.update(hechas=hechas, total_dias=total_dias, cierre=services.cierre_semanal(usuario, rutina, fecha))
        if dia:
            total = services.total_ejercicios(dia)
            n_hechos = len(services.hechos_de(usuario, dia, fecha))
            contexto.update(dia=dia, n_hechos=n_hechos, total=total,
                            porcentaje=round(100 * n_hechos / total) if total else 0)
        else:
            proximo, fecha_proximo = services.proximo_dia(rutina, fecha)
            contexto.update(proximo=proximo, fecha_proximo=fecha_proximo)
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
    lunes = services.lunes_de(fecha)
    una_semana = dt.timedelta(days=6)
    return render(request, 'apptrainer/semana.html', {
        'rutina': rutina, 'filas': filas, 'seccion': 'semana', 'fecha': fecha,
        'lunes': lunes, 'domingo': lunes + una_semana,
        'lunes_anterior': lunes - dt.timedelta(days=7), 'domingo_anterior': lunes - dt.timedelta(days=1),
    })


@login_required
@require_GET
def semana_excel(request):
    """Excel del registro de entrenamientos entre ?desde= y ?hasta= (por defecto, la semana
    actual) o, con ?todo=1, todo el historial."""
    hoy = timezone.localdate()
    if request.GET.get('todo') == '1':
        desde = hasta = None
        sufijo = 'historial'
    else:
        desde, hasta = services.rango_valido(request.GET.get('desde'), request.GET.get('hasta'), hoy)
        sufijo = f'{desde.isoformat()}_a_{hasta.isoformat()}'
    contenido = services.exportar_registro_excel(request.user, desde, hasta)
    respuesta = HttpResponse(contenido, content_type=XLSX)
    respuesta['Content-Disposition'] = f'attachment; filename="apptrainer-registro-{sufijo}.xlsx"'
    return respuesta


@login_required
def dia_detalle(request, pk):
    dia = _dia_del_usuario(request, pk)
    fecha = services.fecha_valida(request.GET.get('fecha'))
    return render(request, 'apptrainer/dia.html', _contexto_dia(request.user, dia, fecha))


@login_required
@require_POST
def dia_guardar(request, pk):
    """Guarda el peso de todos los ejercicios del día (barra + discos, mancuernas o total)."""
    dia = _dia_del_usuario(request, pk)
    fecha = services.fecha_valida(request.POST.get('fecha'))
    campo = KgField()
    ejercicios = Ejercicio.objects.filter(bloque__dia=dia).exclude(bloque__tipo=Bloque.MOVILIDAD)
    modos_validos = {m for m, _ in TIPOS_CARGA}

    cargas, escritos, errores = {}, {}, {}
    for e in ejercicios:
        modo = request.POST.get(f'modo_{e.pk}')
        if modo not in modos_validos:
            modo = CARGA_TOTAL  # envío antiguo o sin selector: un solo peso total
        crudo = {
            'modo': modo,
            'total': request.POST.get(f'kg_{e.pk}', '').strip(),
            'barra': request.POST.get(f'barra_{e.pk}', '').strip(),
            'discos': request.POST.get(f'discos_{e.pk}', '').strip(),
            'mancuerna': request.POST.get(f'mancuerna_{e.pk}', '').strip(),
        }
        escritos[e.pk] = crudo
        # Solo se validan los campos que usa el modo elegido.
        usados = {CARGA_BARRA: ('barra', 'discos'), CARGA_MANCUERNAS: ('mancuerna',), CARGA_TOTAL: ('total',)}[modo]
        try:
            limpios = {nombre: campo.clean(crudo[nombre]) for nombre in usados}
            cargas[e.pk] = armar_carga(modo, **limpios)
        except ValidationError as exc:
            errores[e.pk] = exc.messages[0]
        except ValueError as exc:
            errores[e.pk] = str(exc)

    if errores:
        messages.error(request, 'Revisa los pesos marcados en rojo: no se guardó nada todavía.')
        contexto = _contexto_dia(request.user, dia, fecha, escritos, errores)
        return render(request, 'apptrainer/dia.html', contexto, status=422)

    services.guardar_pesos(request.user, dia, fecha, cargas)
    messages.success(request, 'Registro guardado.')
    return redirect(_url_dia('apptrainer:dia_resumen', dia.pk, fecha))


@login_required
def dia_resumen(request, pk):
    """Vista previa de lo registrado en un día y fecha."""
    dia = _dia_del_usuario(request, pk)
    fecha = services.fecha_valida(request.GET.get('fecha'))
    contexto = _contexto_dia(request.user, dia, fecha)
    con_peso = [e for b in contexto['bloques'] if b['con_peso'] for e in b['ejercicios']]
    contexto.update(
        n_con_peso=sum(e.kg is not None for e in con_peso),
        total_con_peso=len(con_peso),
        url_editar=_url_dia('apptrainer:dia', dia.pk, fecha),
    )
    return render(request, 'apptrainer/resumen.html', contexto)


@login_required
@require_POST
def alternar(request, pk):
    ejercicio = get_object_or_404(
        Ejercicio.objects.select_related('bloque__dia'),
        pk=pk, bloque__dia__rutina__usuario=request.user,
    )
    fecha = services.fecha_valida(request.POST.get('fecha'))
    hecho, hechos, total, completada = services.alternar_ejercicio(request.user, ejercicio, fecha)
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({
            'hecho': hecho, 'hechos': hechos, 'total': total, 'completada': completada,
            'porcentaje': round(100 * hechos / total) if total else 0,
        })
    return redirect(_url_dia('apptrainer:dia', ejercicio.bloque.dia_id, fecha))


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
