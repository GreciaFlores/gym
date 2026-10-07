import datetime as dt
from decimal import Decimal

import pytest

from turnos import services
from turnos.models import Alumno, Movimiento, Reserva
from turnos.services import ReservaError


def test_saldo_es_suma_del_libro(alumno):
    Movimiento.objects.create(alumno=alumno, tipo='pago', clases=7, monto=100000)
    Movimiento.objects.create(alumno=alumno, tipo='consumo', clases=-2)
    Movimiento.objects.create(alumno=alumno, tipo='ajuste', clases=1)
    assert alumno.saldo == 6


def test_saldo_sin_movimientos_es_cero(alumno):
    assert alumno.saldo == 0


def test_pago_100000_con_precio_14000(alumno):
    mov = services.registrar_pago(alumno, Decimal('100000'), Decimal('14000'))
    assert mov.clases == 7
    assert '2.000' in mov.nota
    assert alumno.saldo == 7


def test_pago_exacto_no_deja_resto(alumno):
    mov = services.registrar_pago(alumno, Decimal('28000'), Decimal('14000'))
    assert mov.clases == 2 and mov.nota == ''


def test_pago_invalido(alumno):
    with pytest.raises(ValueError):
        services.registrar_pago(alumno, 0)


def test_reserva_ok_no_descuenta_saldo_pero_compromete(alumno_con_saldo, hacer_clase):
    services.reservar(alumno_con_saldo, hacer_clase())
    assert alumno_con_saldo.saldo == 7
    assert alumno_con_saldo.saldo_disponible == 6


def test_reserva_sin_cupo(alumno_con_saldo, hacer_clase):
    clase = hacer_clase(cupo=1)
    otro = Alumno.objects.create(nombre='Luis', apellido='Gómez', dni='1', telefono='1')
    services.registrar_pago(otro, 14000)
    services.reservar(otro, clase)
    with pytest.raises(ReservaError, match='completa'):
        services.reservar(alumno_con_saldo, clase)


def test_reserva_duplicada(alumno_con_saldo, hacer_clase):
    clase = hacer_clase()
    services.reservar(alumno_con_saldo, clase)
    with pytest.raises(ReservaError, match='Ya tenés'):
        services.reservar(alumno_con_saldo, clase)
    assert Reserva.objects.count() == 1


def test_reserva_sin_saldo(alumno, hacer_clase):
    with pytest.raises(ReservaError, match='Sin clases disponibles, coordiná el pago con tu entrenador'):
        services.reservar(alumno, hacer_clase())


def test_reserva_sin_saldo_disponible_por_comprometidas(alumno, hacer_clase):
    services.registrar_pago(alumno, 14000)  # 1 clase
    services.reservar(alumno, hacer_clase(dias=1))
    with pytest.raises(ReservaError, match='Sin clases disponibles'):
        services.reservar(alumno, hacer_clase(dias=2))


def test_reserva_clase_pasada(alumno_con_saldo, hacer_clase):
    with pytest.raises(ReservaError, match='ya pasó'):
        services.reservar(alumno_con_saldo, hacer_clase(dias=-1))


def test_reserva_clase_cancelada(alumno_con_saldo, hacer_clase):
    with pytest.raises(ReservaError, match='cancelada'):
        services.reservar(alumno_con_saldo, hacer_clase(estado='cancelada'))


def test_alumno_inactivo(alumno_con_saldo, hacer_clase):
    alumno_con_saldo.activo = False
    alumno_con_saldo.save()
    with pytest.raises(ReservaError, match='inactiva'):
        services.reservar(alumno_con_saldo, hacer_clase())


def test_cancelacion_libera_lugar_y_saldo(alumno_con_saldo, hacer_clase):
    clase = hacer_clase()
    services.reservar(alumno_con_saldo, clase)
    services.cancelar(alumno_con_saldo, clase)
    assert clase.lugares_libres == 5
    assert alumno_con_saldo.saldo_disponible == 7


def test_cancelar_sin_reserva(alumno_con_saldo, hacer_clase):
    with pytest.raises(ReservaError):
        services.cancelar(alumno_con_saldo, hacer_clase())


def test_re_reservar_tras_cancelar(alumno_con_saldo, hacer_clase):
    clase = hacer_clase()
    services.reservar(alumno_con_saldo, clase)
    services.cancelar(alumno_con_saldo, clase)
    services.reservar(alumno_con_saldo, clase)
    assert Reserva.objects.filter(estado='confirmada').count() == 1
    assert Reserva.objects.count() == 1


def test_colores(hacer_clase, alumno_con_saldo):
    assert hacer_clase(dias=1, hora=dt.time(8)).color == 'verde'
    assert hacer_clase(dias=1, hora=dt.time(9), cupo=2).color == 'amarillo'
    assert hacer_clase(dias=-1).color == 'gris'
    llena = hacer_clase(dias=2, cupo=1)
    services.reservar(alumno_con_saldo, llena)
    assert llena.color == 'gris'


def test_clases_recurrentes_sin_duplicar(db):
    desde = dt.date(2030, 1, 7)  # lunes
    c, s = services.crear_clases_recurrentes([0, 1], [dt.time(8), dt.time(9)], 2, desde=desde)
    assert (c, s) == (8, 0)
    c, s = services.crear_clases_recurrentes([0, 1], [dt.time(8), dt.time(9)], 2, desde=desde)
    assert (c, s) == (0, 8)
