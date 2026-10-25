import datetime as dt
from decimal import Decimal

import pytest
from django.utils import timezone

from turnos import services
from turnos.checkin import ALFABETO, codigo_checkin, codigo_valido
from turnos.models import Clase, Movimiento, Reserva
from turnos.services import CheckinError


@pytest.fixture
def clase(hacer_clase):
    return hacer_clase(dias=1)


# --- registrar_checkin ---

def test_checkin_con_reserva(alumno_con_saldo, clase):
    services.reservar(alumno_con_saldo, clase)
    mov, saldo, sin_saldo = services.registrar_checkin(alumno_con_saldo, clase)
    assert (mov.tipo, mov.clases, mov.clase, mov.nota) == (
        Movimiento.CONSUMO, -1, clase, 'check-in qr')
    assert saldo == 6 and sin_saldo is False
    assert alumno_con_saldo.saldo == 6
    reserva = Reserva.objects.get(alumno=alumno_con_saldo, clase=clase)
    assert reserva.estado == Reserva.ASISTIDA


def test_checkin_sin_reserva(alumno_con_saldo, clase):
    mov, saldo, _ = services.registrar_checkin(alumno_con_saldo, clase)
    assert mov.clases == -1 and saldo == 6
    assert not Reserva.objects.filter(alumno=alumno_con_saldo, clase=clase).exists()


def test_checkin_origen_en_la_nota(alumno_con_saldo, clase):
    mov, _, _ = services.registrar_checkin(alumno_con_saldo, clase, origen='manual')
    assert mov.nota == 'check-in manual'


def test_doble_checkin_rechazado(alumno_con_saldo, clase):
    services.registrar_checkin(alumno_con_saldo, clase)
    with pytest.raises(CheckinError, match='Ya registraste'):
        services.registrar_checkin(alumno_con_saldo, clase)
    assert alumno_con_saldo.saldo == 6


def test_checkin_sin_saldo(alumno, clase):
    with pytest.raises(CheckinError, match='Sin clases disponibles'):
        services.registrar_checkin(alumno, clase)
    assert not Movimiento.objects.filter(tipo=Movimiento.CONSUMO).exists()


def test_checkin_clase_cancelada(alumno_con_saldo, clase):
    clase.estado = Clase.CANCELADA
    clase.save()
    with pytest.raises(CheckinError, match='cancelada'):
        services.registrar_checkin(alumno_con_saldo, clase)
    assert alumno_con_saldo.saldo == 7


def test_checkin_alumno_inactivo(alumno_con_saldo, clase):
    alumno_con_saldo.activo = False
    alumno_con_saldo.save()
    with pytest.raises(CheckinError, match='inactiva'):
        services.registrar_checkin(alumno_con_saldo, clase)
    assert alumno_con_saldo.saldo == 7


def test_checkin_error_es_reserva_error():
    assert issubclass(CheckinError, services.ReservaError)


def test_checkin_ultima_clase_deja_saldo_cero(alumno, clase):
    services.registrar_pago(alumno, Decimal('14000'), Decimal('14000'))
    _, saldo, _ = services.registrar_checkin(alumno, clase)
    assert saldo == 0


def test_checkin_con_reservas_sin_saldo(alumno, hacer_clase):
    """Con saldo 1 y reservas en dos clases futuras, el check-in avisa que falta saldo."""
    services.registrar_pago(alumno, Decimal('14000'), Decimal('14000'))  # +1
    hoy, manana, pasado = hacer_clase(dias=1), hacer_clase(dias=2), hacer_clase(dias=3)
    for c in (hoy, manana, pasado):  # reservar valida saldo_disponible: se fuerza el alta
        Reserva.objects.create(alumno=alumno, clase=c)
    _, saldo, sin_saldo = services.registrar_checkin(alumno, hoy)
    assert saldo == 0
    assert sin_saldo is True  # quedan 2 reservas futuras confirmadas y 0 clases


def test_restriccion_unica_de_consumo_por_alumno_clase(alumno_con_saldo, clase):
    from django.db import IntegrityError, transaction
    services.registrar_checkin(alumno_con_saldo, clase)
    with pytest.raises(IntegrityError), transaction.atomic():
        Movimiento.objects.create(
            alumno=alumno_con_saldo, clase=clase, tipo=Movimiento.CONSUMO, clases=-1)


def test_ajustes_con_clase_no_chocan_con_la_restriccion(alumno_con_saldo, clase):
    services.registrar_checkin(alumno_con_saldo, clase)
    Movimiento.objects.create(
        alumno=alumno_con_saldo, clase=clase, tipo=Movimiento.AJUSTE, clases=1)
    assert alumno_con_saldo.saldo == 7


# --- saldo_disponible / reservas ---

def test_saldo_disponible_no_descuenta_dos_veces(alumno_con_saldo, clase):
    services.reservar(alumno_con_saldo, clase)
    assert alumno_con_saldo.saldo == 7
    assert alumno_con_saldo.saldo_disponible == 6  # la reserva compromete 1
    services.registrar_checkin(alumno_con_saldo, clase)
    assert alumno_con_saldo.saldo == 6
    assert alumno_con_saldo.clases_comprometidas == 0  # asistida ya no cuenta
    assert alumno_con_saldo.saldo_disponible == 6  # y no 5


def test_reserva_pasada_sin_checkin_no_modifica_el_saldo(alumno_con_saldo, hacer_clase):
    """No-show sin penalidad: solo el check-in consume una clase."""
    pasada = hacer_clase(dias=-1)
    Reserva.objects.create(alumno=alumno_con_saldo, clase=pasada)  # confirmada, sin asistir
    assert alumno_con_saldo.saldo == 7
    assert alumno_con_saldo.clases_comprometidas == 0
    assert alumno_con_saldo.saldo_disponible == 7
    assert not Movimiento.objects.filter(tipo=Movimiento.CONSUMO).exists()


# --- código de check-in ---

def test_codigo_formato_y_estable(clase):
    code = codigo_checkin(clase)
    assert len(code) == 4
    assert set(code) <= set(ALFABETO)
    assert not set(code) & set('0O1I')
    assert code == codigo_checkin(clase)


def test_codigo_cambia_con_el_secreto(clase, settings):
    original = codigo_checkin(clase)
    settings.CHECKIN_SECRET = 'otro-secreto'
    assert codigo_checkin(clase) != original


def test_codigo_valido_en_ventana(clase):
    ok = codigo_checkin(clase)
    assert codigo_valido(clase, ok, clase.inicio)
    assert codigo_valido(clase, ok.lower(), clase.inicio)  # insensible a mayúsculas
    assert codigo_valido(clase, f' {ok} ', clase.inicio)


def test_codigo_de_otra_clase_rechazado(clase, hacer_clase):
    otra = hacer_clase(dias=2)
    assert not codigo_valido(clase, codigo_checkin(otra), clase.inicio)


def test_codigo_vacio_o_none_rechazado(clase):
    assert not codigo_valido(clase, '', clase.inicio)
    assert not codigo_valido(clase, None, clase.inicio)


@pytest.mark.parametrize('delta_min, esperado', [
    (-31, False),   # antes de la ventana
    (-30, True),    # justo 30 min antes
    (0, True),      # inicio
    (59, True),     # durante la clase
    (60, True),     # fin exacto (duración 60)
    (61, False),    # terminada
])
def test_codigo_ventana(clase, delta_min, esperado):
    ahora = clase.inicio + dt.timedelta(minutes=delta_min)
    assert codigo_valido(clase, codigo_checkin(clase), ahora) is esperado


def test_codigo_ventana_usa_zona_argentina(clase):
    """El mismo instante en UTC se interpreta en hora argentina."""
    ahora_utc = clase.inicio.astimezone(dt.timezone.utc)
    assert codigo_valido(clase, codigo_checkin(clase), ahora_utc)
    assert timezone.localtime(ahora_utc).tzinfo is not None
