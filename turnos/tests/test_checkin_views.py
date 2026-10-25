import datetime as dt
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.utils import timezone

from turnos import services
from turnos.checkin import codigo_checkin
from turnos.models import Alumno, Clase, Movimiento, Reserva


@pytest.fixture(autouse=True)
def limpiar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def clase(hacer_clase, monkeypatch):
    """Clase de mañana a las 10:00 con el reloj fijado 10 min antes: ventana abierta."""
    c = hacer_clase(dias=1)
    ahora = c.inicio - dt.timedelta(minutes=10)
    monkeypatch.setattr(timezone, 'now', lambda: ahora)
    return c


@pytest.fixture
def url(clase):
    return f'/checkin/{clase.pk}/'


@pytest.fixture
def code(clase):
    return codigo_checkin(clase)


@pytest.fixture
def logueado(client, alumno_con_saldo):
    client.post('/identificar/', {'dni': alumno_con_saldo.dni})
    return client


def consumos():
    return Movimiento.objects.filter(tipo=Movimiento.CONSUMO).count()


# --- GET / POST ---

def test_get_valido_muestra_confirmar_y_no_descuenta(logueado, url, code, alumno_con_saldo):
    r = logueado.get(url, {'code': code})
    assert r.status_code == 200
    assert 'Confirmar check-in' in r.content.decode()
    assert consumos() == 0
    assert alumno_con_saldo.saldo == 7


def test_post_descuenta_una_vez(logueado, url, code, alumno_con_saldo):
    r = logueado.post(url, {'code': code})
    assert r.status_code == 200
    html = r.content.decode()
    assert 'Te quedan 6 clases' in html
    assert consumos() == 1 and alumno_con_saldo.saldo == 6


def test_post_repetido_no_descuenta_dos_veces(logueado, url, code, alumno_con_saldo):
    logueado.post(url, {'code': code})
    r = logueado.post(url, {'code': code})
    assert 'Ya registraste' in r.content.decode()
    assert consumos() == 1 and alumno_con_saldo.saldo == 6


def test_post_con_reserva_la_marca_asistida(logueado, url, code, alumno_con_saldo, clase):
    services.reservar(alumno_con_saldo, clase)
    logueado.post(url, {'code': code})
    assert Reserva.objects.get(alumno=alumno_con_saldo).estado == Reserva.ASISTIDA


def test_aviso_reservas_sin_saldo(client, alumno, hacer_clase, clase, url, code):
    services.registrar_pago(alumno, Decimal('14000'), Decimal('14000'))  # saldo 1
    for c in (hacer_clase(dias=2), hacer_clase(dias=3)):
        Reserva.objects.create(alumno=alumno, clase=c)
    client.post('/identificar/', {'dni': alumno.dni})
    html = client.post(url, {'code': code}).content.decode()
    assert 'Te quedan 0 clases' in html
    assert 'Tenés reservas sin saldo, renová con el entrenador' in html


def test_sin_saldo_ofrece_link_al_saldo(client, alumno, url, code):
    client.post('/identificar/', {'dni': alumno.dni})
    html = client.post(url, {'code': code}).content.decode()
    assert 'Sin clases disponibles' in html
    assert 'Ver mi saldo' in html
    assert consumos() == 0


def test_clase_cancelada_en_check_in(logueado, url, code, clase):
    clase.estado = Clase.CANCELADA
    clase.save()
    r = logueado.post(url, {'code': code})
    assert r.status_code == 400  # no se revela nada de la clase
    assert consumos() == 0


# --- Sin sesión ---

def test_sin_sesion_pide_dni_y_vuelve_al_checkin(client, alumno_con_saldo, url, code):
    r = client.get(url, {'code': code})
    html = r.content.decode()
    assert 'Ingresá tu DNI' in html
    assert f'value="{url}?code={code}"' in html
    r = client.post('/identificar/', {'dni': alumno_con_saldo.dni, 'next': f'{url}?code={code}'})
    assert r.url == f'{url}?code={code}'
    assert 'Confirmar check-in' in client.get(r.url).content.decode()
    assert consumos() == 0


def test_post_sin_sesion_redirige_al_get(client, url, code):
    r = client.post(url, {'code': code})
    assert r.status_code == 302 and r.url == f'{url}?code={code}'
    assert consumos() == 0


def test_alumno_nuevo_vuelve_al_checkin_tras_registrarse(client, db, url, code):
    r = client.post('/identificar/', {'dni': '40999888', 'next': f'{url}?code={code}'})
    assert r.url == '/registro/'
    r = client.post('/registro/', {'nombre': 'Eva', 'apellido': 'Ruiz', 'telefono': '11'})
    assert r.url == f'{url}?code={code}'


@pytest.mark.parametrize('malo', [
    'https://evil.com/', '//evil.com/x', 'javascript:alert(1)', 'http://testserver.evil.com/',
])
def test_next_externo_rechazado(client, alumno_con_saldo, malo):
    r = client.post('/identificar/', {'dni': alumno_con_saldo.dni, 'next': malo})
    assert r.url == '/'


def test_next_externo_rechazado_en_registro(client, db):
    client.post('/identificar/', {'dni': '40999888', 'next': 'https://evil.com/'})
    r = client.post('/registro/', {'nombre': 'Eva', 'apellido': 'Ruiz', 'telefono': '11'})
    assert r.url == '/'


# --- Código inválido / ventana / límite ---

def test_codigo_invalido_no_revela_la_clase(logueado, url, clase):
    r = logueado.get(url, {'code': 'ZZZZ'})
    html = r.content.decode()
    assert r.status_code == 400
    assert 'no es válido' in html
    assert 'Confirmar' not in html and '10:00' not in html
    assert consumos() == 0


def test_codigo_invalido_en_post_no_descuenta(logueado, url):
    logueado.post(url, {'code': 'ZZZZ'})
    assert consumos() == 0


def test_codigo_de_otra_clase(logueado, url, hacer_clase):
    otra = hacer_clase(dias=2)
    assert logueado.get(url, {'code': codigo_checkin(otra)}).status_code == 400


def test_fuera_de_ventana_mismo_mensaje_generico(logueado, url, code, clase, monkeypatch):
    tarde = clase.inicio + dt.timedelta(minutes=90)
    monkeypatch.setattr(timezone, 'now', lambda: tarde)
    r = logueado.post(url, {'code': code})
    assert r.status_code == 400 and 'no es válido' in r.content.decode()
    assert consumos() == 0


def test_get_sin_codigo_redirige_al_plan_b(client, url):
    assert client.get(url).url == '/checkin/'


def test_limite_de_intentos_por_sesion(logueado, url, code):
    for _ in range(5):
        assert logueado.get(url, {'code': 'ZZZZ'}).status_code == 400
    r = logueado.get(url, {'code': 'ZZZZ'})
    assert r.status_code == 429 and 'Demasiados intentos, esperá unos minutos' in r.content.decode()
    # bloqueado incluso con el código correcto
    assert logueado.post(url, {'code': code}).status_code == 429
    assert consumos() == 0


def test_limite_por_alumno_no_se_evita_cambiando_de_sesion(
        client, django_assert_num_queries, alumno_con_saldo, url, code):
    from django.test import Client
    client.post('/identificar/', {'dni': alumno_con_saldo.dni})
    for _ in range(5):
        client.get(url, {'code': 'ZZZZ'})
    otro = Client()  # cookies nuevas, mismo DNI
    otro.post('/identificar/', {'dni': alumno_con_saldo.dni})
    assert otro.post(url, {'code': code}).status_code == 429
    assert consumos() == 0


def test_no_hay_limite_por_ip(client, alumno_con_saldo, url, code):
    """Otra sesión y otro alumno desde la misma IP no se ven afectados."""
    from django.test import Client
    for _ in range(5):
        client.get(url, {'code': 'ZZZZ'}, REMOTE_ADDR='10.0.0.1')
    otro = Client()
    otro.post('/identificar/', {'dni': alumno_con_saldo.dni}, REMOTE_ADDR='10.0.0.1')
    assert otro.post(url, {'code': code}, REMOTE_ADDR='10.0.0.1').status_code == 200


# --- Plan B ---

def test_plan_b_lista_solo_clases_con_ventana_abierta(client, url, clase, hacer_clase):
    hacer_clase(dias=3)  # fuera de ventana
    otra = hacer_clase(dias=1, hora=dt.time(18, 0))  # misma fecha, ventana no abierta
    html = client.get('/checkin/').content.decode()
    assert '10:00' in html and '18:00' not in html and otra.hora_inicio


def test_plan_b_codigo_correcto_redirige_a_confirmar(client, clase, code):
    r = client.post('/checkin/', {'clase': clase.pk, 'code': code.lower()})
    assert r.url == f'/checkin/{clase.pk}/?code={code}'


def test_plan_b_codigo_incorrecto_cuenta_intento(client, clase):
    for _ in range(5):
        assert client.post('/checkin/', {'clase': clase.pk, 'code': 'ZZZZ'}).status_code == 400
    assert client.post('/checkin/', {'clase': clase.pk, 'code': 'ZZZZ'}).status_code == 429


# --- Efectos sobre reservas ---

def test_reservar_tras_checkin_no_reabre_la_reserva(alumno_con_saldo, clase):
    services.reservar(alumno_con_saldo, clase)
    services.registrar_checkin(alumno_con_saldo, clase)
    with pytest.raises(services.ReservaError, match='Ya tenés un lugar'):
        services.reservar(alumno_con_saldo, clase)
    assert Reserva.objects.get(alumno=alumno_con_saldo).estado == Reserva.ASISTIDA


def test_asistida_sigue_ocupando_cupo(alumno_con_saldo, clase):
    services.reservar(alumno_con_saldo, clase)
    libres = clase.lugares_libres
    services.registrar_checkin(alumno_con_saldo, clase)
    assert clase.lugares_libres == libres
