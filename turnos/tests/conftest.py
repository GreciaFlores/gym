import datetime as dt
from decimal import Decimal

import pytest
from django.utils import timezone

from turnos import services
from turnos.models import Alumno, Clase


@pytest.fixture
def alumno(db):
    return Alumno.objects.create(nombre='Ana', apellido='Pérez', dni='30111222', telefono='1155550000')


@pytest.fixture
def alumno_con_saldo(alumno):
    services.registrar_pago(alumno, Decimal('100000'), Decimal('14000'))  # +7
    return alumno


@pytest.fixture
def hacer_clase(db):
    def _hacer(dias=1, hora=dt.time(10, 0), cupo=5, **kw):
        fecha = timezone.localdate() + dt.timedelta(days=dias)
        return Clase.objects.create(fecha=fecha, hora_inicio=hora, cupo_maximo=cupo, **kw)
    return _hacer
