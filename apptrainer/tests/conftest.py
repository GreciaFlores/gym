import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user('grecia', password='clave-segura-123', first_name='Grecia')


@pytest.fixture
def otro_usuario(db):
    return get_user_model().objects.create_user('otra', password='clave-segura-123')


@pytest.fixture
def con_rutina(usuario):
    call_command('seed_rutina', usuario='grecia', stdout=open('/dev/null', 'w'))
    return usuario


@pytest.fixture
def cliente(client, usuario):
    client.force_login(usuario)
    return client


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def dia_semana_hoy():
    return timezone.localdate().weekday()


def fecha_de_semana(dia_semana):
    """Fecha de esta semana (lunes=0) para un día de la semana."""
    hoy = timezone.localdate()
    return hoy - dt.timedelta(days=hoy.weekday()) + dt.timedelta(days=dia_semana)
