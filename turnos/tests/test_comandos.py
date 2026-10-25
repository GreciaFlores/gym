import datetime as dt
import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from turnos.models import Alumno, Clase, Movimiento, Reserva

User = get_user_model()


def correr(nombre):
    out = io.StringIO()
    call_command(nombre, stdout=out)
    return out.getvalue()


def foto():
    return (Alumno.objects.count(), Clase.objects.count(), Reserva.objects.count(),
            Movimiento.objects.count(), Clase.objects.filter(estado=Clase.CANCELADA).count())


@pytest.fixture
def lunes_temprano(monkeypatch):
    ahora = timezone.make_aware(dt.datetime(2026, 11, 2, 7, 0))  # lunes
    monkeypatch.setattr(timezone, 'now', lambda: ahora)


def test_seed_demo_es_idempotente(db, lunes_temprano):
    correr('seed_demo')
    primera = foto()
    assert primera[0] == 5 and primera[4] == 1
    correr('seed_demo')
    correr('seed_demo')
    assert foto() == primera


def test_seed_demo_en_otro_dia_no_cancela_mas_clases(db, monkeypatch):
    monkeypatch.setattr(timezone, 'now', lambda: timezone.make_aware(dt.datetime(2026, 11, 2, 7, 0)))
    correr('seed_demo')
    monkeypatch.setattr(timezone, 'now', lambda: timezone.make_aware(dt.datetime(2026, 11, 4, 12, 0)))
    correr('seed_demo')
    assert Clase.objects.filter(estado=Clase.CANCELADA).count() == 1


def test_ensure_superuser_crea_y_no_falla_si_existe(db, monkeypatch):
    monkeypatch.setenv('DJANGO_SUPERUSER_USERNAME', 'entrenador')
    monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'clave-segura-123')
    monkeypatch.setenv('DJANGO_SUPERUSER_EMAIL', 'e@x.com')
    assert 'creado' in correr('ensure_superuser')
    assert 'ya existe' in correr('ensure_superuser')
    u = User.objects.get(username='entrenador')
    assert u.is_superuser and u.is_staff and u.check_password('clave-segura-123')
    assert User.objects.count() == 1


def test_ensure_superuser_no_pisa_la_clave_de_uno_existente(db, monkeypatch):
    User.objects.create_superuser('entrenador', '', 'original')
    monkeypatch.setenv('DJANGO_SUPERUSER_USERNAME', 'entrenador')
    monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'otra')
    correr('ensure_superuser')
    assert User.objects.get(username='entrenador').check_password('original')


def test_ensure_superuser_sin_variables_no_hace_nada(db, monkeypatch):
    for v in ('DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_PASSWORD', 'DJANGO_SUPERUSER_EMAIL'):
        monkeypatch.delenv(v, raising=False)
    assert 'sin definir' in correr('ensure_superuser')
    assert User.objects.count() == 0
