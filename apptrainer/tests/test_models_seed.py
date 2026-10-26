import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from apptrainer.models import Bloque, Dia, Ejercicio, Rutina


def test_seed_carga_la_rutina_del_documento(con_rutina):
    rutina = Rutina.objects.get(usuario=con_rutina)
    assert rutina.dias.count() == 3
    assert Ejercicio.objects.filter(bloque__dia__rutina=rutina).count() == 40
    dia1 = rutina.dias.get(orden=1)
    assert [b.tipo for b in dia1.bloques.order_by('orden')] == ['movilidad', 'zona_media', 'principal']
    assert Ejercicio.objects.filter(bloque__dia=dia1, nombre='Hip thrust').exists()


def test_seed_conserva_los_links_de_youtube(con_rutina):
    con_video = Ejercicio.objects.filter(bloque__dia__rutina__usuario=con_rutina).exclude(url_video='')
    assert con_video.count() == 13
    assert all(e.url_video.startswith('https://www.youtube.com/') for e in con_video)


def test_seed_es_idempotente(con_rutina):
    call_command('seed_rutina', usuario='grecia', stdout=open('/dev/null', 'w'))
    assert Rutina.objects.filter(usuario=con_rutina).count() == 1
    assert Dia.objects.count() == 3


def test_seed_falla_si_no_existe_el_usuario(db):
    with pytest.raises(CommandError, match='createsuperuser'):
        call_command('seed_rutina', usuario='nadie')


def test_combinados_comparten_grupo_dentro_del_bloque(con_rutina):
    principal = Bloque.objects.get(dia__rutina__usuario=con_rutina, dia__orden=1, tipo='principal')
    grupos = list(principal.ejercicios.values_list('grupo', flat=True))
    assert grupos == [1, 1, 2, 2, None]


def test_una_sola_rutina_activa_por_usuario(usuario):
    a = Rutina.objects.create(usuario=usuario, nombre='A')
    b = Rutina.objects.create(usuario=usuario, nombre='B')
    a.refresh_from_db()
    assert not a.activa and b.activa


def test_restriccion_de_base_impide_dos_activas(usuario):
    Rutina.objects.create(usuario=usuario, nombre='A')
    with pytest.raises(IntegrityError), transaction.atomic():
        Rutina.objects.bulk_create([Rutina(usuario=usuario, nombre='B', activa=True)])
