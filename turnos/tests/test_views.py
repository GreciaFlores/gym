import datetime as dt

import pytest
from django.urls import reverse

from turnos import services
from turnos.models import Alumno, Reserva


def test_landing_carga_con_clases(client, hacer_clase):
    clase = hacer_clase(dias=0, hora=dt.time(23, 59))
    r = client.get('/')
    assert r.status_code == 200
    assert '0 de 5' not in r.content.decode()
    assert '5 de 5 lugares' in r.content.decode() or clase.ya_paso


def test_semana_invalida_no_rompe(client, db):
    assert client.get('/?semana=basura').status_code == 200


def test_identificar_existente(client, alumno_con_saldo):
    r = client.post('/identificar/', {'dni': '30.111.222'}, follow=True)
    assert 'Ana' in r.content.decode()
    assert 'Saldo: <strong>7</strong>' in r.content.decode()


def test_identificar_nuevo_y_registro(client, db):
    r = client.post('/identificar/', {'dni': '40999888'})
    assert r.url == reverse('registro')
    r = client.post('/registro/', {'nombre': 'Eva', 'apellido': 'Ruiz', 'telefono': '11'})
    assert Alumno.objects.get(dni='40999888').nombre == 'Eva'
    assert client.session['alumno_id']


def test_reservar_y_cancelar_por_http(client, alumno_con_saldo, hacer_clase):
    clase = hacer_clase()
    client.post('/identificar/', {'dni': alumno_con_saldo.dni})
    client.post(f'/clase/{clase.pk}/reservar/')
    assert Reserva.objects.filter(estado='confirmada').count() == 1
    client.post(f'/clase/{clase.pk}/cancelar/')
    assert Reserva.objects.filter(estado='confirmada').count() == 0


def test_reservar_sin_saldo_muestra_mensaje(client, alumno, hacer_clase):
    clase = hacer_clase()
    client.post('/identificar/', {'dni': alumno.dni})
    r = client.post(f'/clase/{clase.pk}/reservar/', follow=True)
    assert 'Sin clases disponibles, coordiná el pago con tu entrenador' in r.content.decode()


def test_reservar_sin_identificarse(client, hacer_clase):
    clase = hacer_clase()
    client.post(f'/clase/{clase.pk}/reservar/')
    assert Reserva.objects.count() == 0


def test_reservar_requiere_post(client, hacer_clase):
    assert client.get(f'/clase/{hacer_clase().pk}/reservar/').status_code == 405


def test_seed_demo_idempotente(db):
    from django.core.management import call_command
    call_command('seed_demo')
    call_command('seed_demo')
    assert Alumno.objects.filter(dni='34555666').first().saldo == 0
    assert Alumno.objects.get(dni='30111222').saldo == 7


def test_admin_recurrentes(admin_client, db):
    r = admin_client.get('/admin/turnos/clase/recurrentes/')
    assert r.status_code == 200
    r = admin_client.post('/admin/turnos/clase/recurrentes/', {
        'dias': ['0', '1'], 'horas': '8, 18:30', 'semanas': 1, 'desde': '2030-01-07',
        'cupo_maximo': 5, 'precio': 14000, 'duracion_min': 60,
    })
    assert r.status_code == 302
    from turnos.models import Clase
    assert Clase.objects.count() == 4


def test_admin_registrar_pago(admin_client, alumno):
    r = admin_client.post('/admin/turnos/alumno/', {
        'action': 'registrar_pago', '_selected_action': [alumno.pk], 'aplicar': '1',
        'monto': '100000', 'precio_clase': '14000', 'nota': '',
    })
    assert r.status_code == 302
    assert alumno.saldo == 7


def test_admin_changelists(admin_client, alumno_con_saldo, hacer_clase):
    services.reservar(alumno_con_saldo, hacer_clase())
    for m in ('alumno', 'clase', 'reserva', 'movimiento'):
        assert admin_client.get(f'/admin/turnos/{m}/').status_code == 200
    assert admin_client.get('/admin/turnos/alumno/?q=30111222').status_code == 200
