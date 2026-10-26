import datetime as dt

import pytest
from django.utils import timezone

from turnos import services
from turnos.checkin import codigo_checkin
from turnos.models import Clase

URL = '/admin/turnos/clase/qr-actual/'
DIA = dt.date(2026, 11, 3)


def a_las(h, m=0):
    return timezone.make_aware(dt.datetime.combine(DIA, dt.time(h, m)))


@pytest.fixture
def ahora(monkeypatch):
    """Devuelve una función que fija el reloj del test en DIA a la hora dada."""
    def _fijar(h, m=0):
        instante = a_las(h, m)
        monkeypatch.setattr(timezone, 'now', lambda: instante)
    return _fijar


@pytest.fixture
def clases(db):
    return (Clase.objects.create(fecha=DIA, hora_inicio=dt.time(8)),
            Clase.objects.create(fecha=DIA, hora_inicio=dt.time(9)))


def cuantos(html):
    return html.count('data-qr-clase=')


def test_exige_login(client):
    r = client.get(URL)
    assert r.status_code == 302 and r.url.startswith('/admin/login/')


def test_ninguna_ventana_abierta_muestra_la_proxima(admin_client, clases, ahora):
    ahora(7, 0)
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 0
    assert 'Próxima clase <strong>08:00</strong>' in html
    assert 'el QR aparece a las <strong>07:30</strong>' in html
    assert codigo_checkin(clases[0]) not in html


def test_una_ventana_abierta(admin_client, clases, ahora):
    ahora(8, 10)  # la de las 9 recién abre a las 8:30
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 1
    assert f'data-qr-clase="{clases[0].pk}"' in html
    assert codigo_checkin(clases[0]) in html
    assert codigo_checkin(clases[1]) not in html
    assert '<h2 class="qr-hora">08:00</h2>' in html
    assert 'Próxima clase' not in html


def test_dos_ventanas_solapadas_se_muestran_juntas(admin_client, clases, ahora):
    ahora(8, 40)
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 2
    assert codigo_checkin(clases[0]) in html and codigo_checkin(clases[1]) in html
    assert html.index('<h2 class="qr-hora">08:00</h2>') < html.index('<h2 class="qr-hora">09:00</h2>')
    assert 'qr-grid' in html  # grilla que apila en mobile (auto-fit)


def test_lista_de_checkins_debajo_de_cada_qr(admin_client, clases, alumno_con_saldo, ahora):
    services.registrar_checkin(alumno_con_saldo, clases[1])
    ahora(8, 40)
    html = admin_client.get(URL).content.decode()
    en_la_de_las_8, en_la_de_las_9 = html.split('<h2 class="qr-hora">09:00</h2>')
    assert 'Todavía nadie' in en_la_de_las_8 and 'Ana Pérez' not in en_la_de_las_8
    assert 'Ana Pérez' in en_la_de_las_9 and 'Ya hicieron check-in (1)' in en_la_de_las_9


def test_clase_cancelada_excluida(admin_client, clases, ahora):
    clases[0].estado = Clase.CANCELADA
    clases[0].save()
    ahora(8, 40)
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 1
    assert codigo_checkin(clases[0]) not in html and codigo_checkin(clases[1]) in html


def test_clase_cancelada_tampoco_es_la_proxima(admin_client, clases, ahora):
    clases[0].estado = Clase.CANCELADA
    clases[0].save()
    ahora(7, 0)
    assert 'Próxima clase <strong>09:00</strong>' in admin_client.get(URL).content.decode()


def test_clases_de_otro_dia_no_aparecen(admin_client, db, ahora):
    Clase.objects.create(fecha=DIA + dt.timedelta(days=1), hora_inicio=dt.time(8))
    ahora(8, 10)
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 0 and 'No quedan clases' in html


def test_ventana_cerrada_y_sin_proxima(admin_client, clases, ahora):
    ahora(10, 30)
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 0 and 'No quedan clases con check-in hoy' in html


def test_cambia_sola_de_clase_con_el_tiempo(admin_client, clases, ahora):
    ahora(8, 20)
    assert codigo_checkin(clases[1]) not in admin_client.get(URL).content.decode()
    ahora(9, 30)  # cerró la de las 8 (termina 9:00); queda solo la de las 9
    html = admin_client.get(URL).content.decode()
    assert cuantos(html) == 1 and codigo_checkin(clases[1]) in html
    assert codigo_checkin(clases[0]) not in html


def test_autorefresh_y_url_absoluta(admin_client, clases, ahora):
    ahora(8, 10)
    html = admin_client.get(URL).content.decode()
    assert 'http-equiv="refresh" content="15"' in html
    assert f'http://testserver/checkin/{clases[0].pk}/?code={codigo_checkin(clases[0])}' in html
    assert '<svg' in html


def test_indice_destaca_el_link_a_qr_actual(admin_client):
    html = admin_client.get('/admin/').content.decode()
    assert 'QR actual (dejar abierto)' in html and URL in html
    assert '/admin/turnos/clase/hoy/' in html  # el botón anterior sigue
