import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.utils import timezone

from turnos import services
from turnos.checkin import codigo_checkin
from turnos.models import Clase, Reserva

BASE_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture
def clase_hoy(db):
    return Clase.objects.create(fecha=timezone.localdate(), hora_inicio=dt.time(10, 0))


@pytest.mark.parametrize('ruta', ['/admin/turnos/clase/hoy/', '/admin/turnos/clase/hoy/1/qr/'])
def test_admin_exige_login(client, ruta):
    r = client.get(ruta)
    assert r.status_code == 302 and r.url.startswith('/admin/login/')


def test_alumno_comun_no_entra_al_admin(client, alumno_con_saldo):
    client.post('/identificar/', {'dni': alumno_con_saldo.dni})
    assert client.get('/admin/turnos/clase/hoy/').status_code == 302


def test_clases_hoy_lista_con_conteos_y_ventana(admin_client, clase_hoy, alumno_con_saldo):
    Reserva.objects.create(alumno=alumno_con_saldo, clase=clase_hoy)
    services.registrar_checkin(alumno_con_saldo, clase_hoy)
    Clase.objects.create(fecha=timezone.localdate(), hora_inicio=dt.time(11, 0),
                         estado=Clase.CANCELADA)
    Clase.objects.create(fecha=timezone.localdate() + dt.timedelta(days=1),
                         hora_inicio=dt.time(10, 0))
    html = admin_client.get('/admin/turnos/clase/hoy/').content.decode()
    assert '10:00' in html and '11:00' not in html  # cancelada y de otro día fuera
    assert '1 / 5' in html  # reservas
    assert f'/admin/turnos/clase/hoy/{clase_hoy.pk}/qr/' in html
    assert 'Mostrar QR' in html


def test_qr_muestra_svg_codigo_url_absoluta_y_alumnos(admin_client, clase_hoy, alumno_con_saldo):
    services.registrar_checkin(alumno_con_saldo, clase_hoy)
    r = admin_client.get(f'/admin/turnos/clase/hoy/{clase_hoy.pk}/qr/')
    html = r.content.decode()
    code = codigo_checkin(clase_hoy)
    assert '<svg' in html
    assert code in html
    assert f'http://testserver/checkin/{clase_hoy.pk}/?code={code}' in html
    assert 'http-equiv="refresh" content="15"' in html
    assert 'Ana Pérez' in html


def test_qr_de_clase_de_otro_dia_redirige(admin_client, db):
    c = Clase.objects.create(fecha=timezone.localdate() + dt.timedelta(days=2),
                             hora_inicio=dt.time(10, 0))
    r = admin_client.get(f'/admin/turnos/clase/hoy/{c.pk}/qr/')
    assert r.status_code == 302 and r.url == '/admin/turnos/clase/hoy/'


def test_indice_del_admin_tiene_link_a_clases_de_hoy(admin_client):
    assert '/admin/turnos/clase/hoy/' in admin_client.get('/admin/').content.decode()


def test_qr_con_https_detras_de_proxy(admin_client, clase_hoy, settings):
    settings.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Un proxy real envía Host; sin él el cliente de tests agregaría :80 al esquema https.
    r = admin_client.get(f'/admin/turnos/clase/hoy/{clase_hoy.pk}/qr/',
                         HTTP_X_FORWARDED_PROTO='https', HTTP_HOST='testserver')
    assert f'https://testserver/checkin/{clase_hoy.pk}/?code=' in r.content.decode()


def test_qr_sin_proxy_ignora_el_header(admin_client, clase_hoy):
    r = admin_client.get(f'/admin/turnos/clase/hoy/{clase_hoy.pk}/qr/',
                         HTTP_X_FORWARDED_PROTO='https')
    assert f'http://testserver/checkin/{clase_hoy.pk}/?code=' in r.content.decode()


def _setting(env_extra, expr):
    env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings', **env_extra}
    out = subprocess.run(
        [sys.executable, '-c', f'from django.conf import settings as s; print({expr})'],
        cwd=BASE_DIR, env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def test_variable_behind_proxy_activa_el_header():
    assert _setting({'DJANGO_BEHIND_PROXY': 'True'}, 's.SECURE_PROXY_SSL_HEADER') == \
        "('HTTP_X_FORWARDED_PROTO', 'https')"
    assert _setting({'DJANGO_BEHIND_PROXY': ''}, 's.SECURE_PROXY_SSL_HEADER') == 'None'


def test_csrf_trusted_origins_desde_variable():
    out = _setting({'DJANGO_CSRF_TRUSTED_ORIGINS': 'https://a.com, https://b.com'},
                   's.CSRF_TRUSTED_ORIGINS')
    assert out == "['https://a.com', 'https://b.com']"
    assert _setting({'DJANGO_CSRF_TRUSTED_ORIGINS': ''}, 's.CSRF_TRUSTED_ORIGINS') == '[]'
