import datetime as dt
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apptrainer.models import Dia, Ejercicio, RegistroPeso, Rutina, Sesion

from .conftest import fecha_de_semana


# ---------- acceso ----------

@pytest.mark.parametrize('nombre', ['hoy', 'semana', 'peso', 'peso_excel'])
def test_las_paginas_exigen_login(client, nombre):
    r = client.get(reverse(f'apptrainer:{nombre}'))
    assert r.status_code == 302
    assert r['Location'].startswith(reverse('apptrainer:login'))


def test_login_correcto_lleva_a_hoy(client, usuario):
    r = client.post(reverse('apptrainer:login'), {'username': 'grecia', 'password': 'clave-segura-123'})
    assert r.status_code == 302 and r['Location'] == reverse('apptrainer:hoy')


def test_login_incorrecto_muestra_error(client, usuario):
    r = client.post(reverse('apptrainer:login'), {'username': 'grecia', 'password': 'mal'})
    assert r.status_code == 200
    assert 'nombre de usuario y una contraseña correctos' in r.content.decode()


def test_logout_solo_por_post(cliente):
    assert cliente.get(reverse('apptrainer:logout')).status_code == 405
    r = cliente.post(reverse('apptrainer:logout'))
    assert r.status_code == 302


def test_healthz_no_requiere_login(client, db):
    r = client.get('/healthz')
    assert r.status_code == 200 and r.content == b'ok'


def test_manifest_y_service_worker(client):
    m = client.get(reverse('apptrainer:manifest'))
    assert m.status_code == 200 and m['Content-Type'].startswith('application/manifest+json')
    assert b'"display": "standalone"' in m.content
    sw = client.get(reverse('apptrainer:sw'))
    assert sw.status_code == 200 and 'javascript' in sw['Content-Type']
    assert b'/static/' in sw.content


# ---------- hoy / semana ----------

def test_hoy_sin_rutina_muestra_estado_vacio(cliente):
    r = cliente.get(reverse('apptrainer:hoy'))
    assert r.status_code == 200 and 'Aún no tienes una rutina' in r.content.decode()


def test_hoy_muestra_el_dia_que_toca(cliente, con_rutina):
    Dia.objects.filter(rutina__usuario=con_rutina).update(dia_semana=None)
    Dia.objects.filter(rutina__usuario=con_rutina, orden=2).update(dia_semana=timezone.localdate().weekday())
    r = cliente.get(reverse('apptrainer:hoy'))
    html = r.content.decode()
    assert 'Hoy toca' in html and 'Día 2' in html and 'Tren superior' in html


def test_hoy_en_descanso_sugiere_el_proximo(cliente, con_rutina):
    manana = (timezone.localdate().weekday() + 1) % 7
    Dia.objects.filter(rutina__usuario=con_rutina).update(dia_semana=None)
    Dia.objects.filter(rutina__usuario=con_rutina, orden=3).update(dia_semana=manana)
    html = cliente.get(reverse('apptrainer:hoy')).content.decode()
    assert 'Día de descanso' in html and 'Día 3' in html


def test_semana_lista_los_tres_dias(cliente, con_rutina):
    html = cliente.get(reverse('apptrainer:semana')).content.decode()
    assert all(f'Día {n}' in html for n in (1, 2, 3))
    assert html.count('Pendiente') == 3


# ---------- día y checks ----------

def test_dia_muestra_bloques_y_combinados(cliente, con_rutina):
    dia = Dia.objects.get(rutina__usuario=con_rutina, orden=1)
    html = cliente.get(reverse('apptrainer:dia', args=[dia.pk])).content.decode()
    for texto in ('Movilidad', 'Zona media', 'Trabajo principal', 'Hip thrust', 'Combinado', '3x6-6-6'):
        assert texto in html
    assert 'target="_blank" rel="noopener noreferrer"' in html


def test_marcar_ejercicio_crea_sesion_y_progreso(cliente, con_rutina):
    ej = Ejercicio.objects.filter(bloque__dia__rutina__usuario=con_rutina, nombre='Hip thrust').get()
    r = cliente.post(reverse('apptrainer:alternar', args=[ej.pk]), HTTP_X_REQUESTED_WITH='fetch')
    data = r.json()
    assert data['hecho'] is True and data['hechos'] == 1 and data['completada'] is False
    assert Sesion.objects.filter(usuario=con_rutina, fecha=timezone.localdate()).count() == 1
    # segunda vez: se desmarca
    data = cliente.post(reverse('apptrainer:alternar', args=[ej.pk]), HTTP_X_REQUESTED_WITH='fetch').json()
    assert data['hecho'] is False and data['hechos'] == 0


def test_completar_todos_marca_la_sesion_completada(cliente, con_rutina):
    dia = Dia.objects.get(rutina__usuario=con_rutina, orden=1)
    ejercicios = Ejercicio.objects.filter(bloque__dia=dia)
    for e in ejercicios:
        data = cliente.post(reverse('apptrainer:alternar', args=[e.pk]), HTTP_X_REQUESTED_WITH='fetch').json()
    assert data['completada'] is True and data['porcentaje'] == 100
    assert Sesion.objects.get(usuario=con_rutina, dia=dia).completada
    # desmarcar uno la reabre
    data = cliente.post(reverse('apptrainer:alternar', args=[ejercicios[0].pk]), HTTP_X_REQUESTED_WITH='fetch').json()
    assert data['completada'] is False
    assert not Sesion.objects.get(usuario=con_rutina, dia=dia).completada


def test_marcar_sin_js_redirige_al_dia(cliente, con_rutina):
    ej = Ejercicio.objects.filter(bloque__dia__rutina__usuario=con_rutina).first()
    r = cliente.post(reverse('apptrainer:alternar', args=[ej.pk]))
    assert r.status_code == 302
    assert r['Location'] == f"{reverse('apptrainer:dia', args=[ej.bloque.dia_id])}?fecha={timezone.localdate().isoformat()}"


def test_marcar_exige_post(cliente, con_rutina):
    ej = Ejercicio.objects.filter(bloque__dia__rutina__usuario=con_rutina).first()
    assert cliente.get(reverse('apptrainer:alternar', args=[ej.pk])).status_code == 405


def test_resumen_semanal_cuenta_dias_completados(cliente, con_rutina):
    dia = Dia.objects.get(rutina__usuario=con_rutina, orden=1)
    for e in Ejercicio.objects.filter(bloque__dia=dia):
        cliente.post(reverse('apptrainer:alternar', args=[e.pk]), HTTP_X_REQUESTED_WITH='fetch')
    html = cliente.get(reverse('apptrainer:hoy')).content.decode()
    assert '1/3' in html


# ---------- aislamiento entre usuarios (clave para escalar a más alumnos) ----------

def test_no_se_puede_ver_ni_marcar_la_rutina_de_otro(client, con_rutina, otro_usuario):
    dia = Dia.objects.get(rutina__usuario=con_rutina, orden=1)
    ej = Ejercicio.objects.filter(bloque__dia=dia).first()
    client.force_login(otro_usuario)
    assert client.get(reverse('apptrainer:dia', args=[dia.pk])).status_code == 404
    assert client.post(reverse('apptrainer:alternar', args=[ej.pk])).status_code == 404
    assert not Sesion.objects.exists()


def test_cada_usuario_ve_solo_su_peso(client, usuario, otro_usuario):
    RegistroPeso.objects.create(usuario=usuario, fecha=timezone.localdate(), kg=Decimal('61.5'))
    client.force_login(otro_usuario)
    assert '61,5' not in client.get(reverse('apptrainer:peso')).content.decode()
    registro = RegistroPeso.objects.get()
    assert client.post(reverse('apptrainer:peso_eliminar', args=[registro.pk])).status_code == 404
    assert RegistroPeso.objects.count() == 1


# ---------- peso ----------

def test_registrar_peso_con_coma_decimal(cliente, usuario):
    r = cliente.post(reverse('apptrainer:peso'), {'fecha': timezone.localdate().isoformat(), 'kg': '65,4', 'nota': 'en ayunas'})
    assert r.status_code == 302
    registro = RegistroPeso.objects.get(usuario=usuario)
    assert registro.kg == Decimal('65.40') and registro.nota == 'en ayunas'


def test_registrar_peso_con_punto_decimal(cliente, usuario):
    cliente.post(reverse('apptrainer:peso'), {'fecha': timezone.localdate().isoformat(), 'kg': '65.4'})
    assert RegistroPeso.objects.get(usuario=usuario).kg == Decimal('65.40')


def test_mismo_dia_actualiza_en_vez_de_duplicar(cliente, usuario):
    f = timezone.localdate().isoformat()
    cliente.post(reverse('apptrainer:peso'), {'fecha': f, 'kg': '65'})
    cliente.post(reverse('apptrainer:peso'), {'fecha': f, 'kg': '64,2'})
    assert RegistroPeso.objects.filter(usuario=usuario).count() == 1
    assert RegistroPeso.objects.get(usuario=usuario).kg == Decimal('64.20')


@pytest.mark.parametrize('kg', ['abc', '5', '1000', '-3', ''])
def test_peso_invalido_se_rechaza(cliente, usuario, kg):
    r = cliente.post(reverse('apptrainer:peso'), {'fecha': timezone.localdate().isoformat(), 'kg': kg})
    assert r.status_code == 200
    assert not RegistroPeso.objects.exists()


def test_fecha_futura_se_rechaza(cliente):
    futura = (timezone.localdate() + dt.timedelta(days=2)).isoformat()
    r = cliente.post(reverse('apptrainer:peso'), {'fecha': futura, 'kg': '65'})
    assert r.status_code == 200 and 'no puede ser futura' in r.content.decode()
    assert not RegistroPeso.objects.exists()


def test_eliminar_peso(cliente, usuario):
    registro = RegistroPeso.objects.create(usuario=usuario, fecha=timezone.localdate(), kg=65)
    assert cliente.post(reverse('apptrainer:peso_eliminar', args=[registro.pk])).status_code == 302
    assert not RegistroPeso.objects.exists()


def test_pagina_peso_con_datos_incluye_grafica(cliente, usuario):
    hoy = timezone.localdate()
    for i, kg in enumerate(['66', '65.5', '65.1']):
        RegistroPeso.objects.create(usuario=usuario, fecha=hoy - dt.timedelta(days=14 - 7 * i), kg=Decimal(kg))
    html = cliente.get(reverse('apptrainer:peso')).content.decode()
    assert 'id="datos-peso"' in html and 'id="grafica"' in html
