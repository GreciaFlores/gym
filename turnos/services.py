"""Reglas de negocio. Las vistas y el admin solo llaman a estas funciones."""
from decimal import Decimal
from typing import NamedTuple

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Alumno, Clase, Movimiento, Reserva

MSG_SIN_SALDO = 'Sin clases disponibles, coordiná el pago con tu entrenador'
MSG_YA_CHECKIN = 'Ya registraste tu asistencia en esta clase.'


class ReservaError(Exception):
    """Error de negocio con mensaje apto para mostrar al alumno."""


class CheckinError(ReservaError):
    """Error de negocio del check-in."""


class CheckinResultado(NamedTuple):
    movimiento: Movimiento
    saldo: int
    reservas_sin_saldo: bool  # hay más reservas futuras confirmadas que clases de saldo


def registrar_pago(alumno, monto, precio_clase=None, nota=''):
    """Registra un pago y acredita clases enteras; el resto queda anotado."""
    monto = Decimal(monto)
    precio = Decimal(precio_clase if precio_clase is not None else settings.PRECIO_CLASE_DEFAULT)
    if monto <= 0 or precio <= 0:
        raise ValueError('Monto y precio deben ser mayores a cero.')
    clases, resto = divmod(monto, precio)
    partes = [f'Resto ${resto:,.0f}'.replace(',', '.')] if resto else []
    if nota:
        partes.append(nota)
    return Movimiento.objects.create(
        alumno=alumno,
        tipo=Movimiento.PAGO,
        monto=monto,
        precio_clase=precio,
        clases=int(clases),
        nota=' · '.join(partes),
    )


@transaction.atomic
def reservar(alumno, clase):
    # Bloquea la clase para que dos reservas simultáneas no pasen del cupo.
    clase = Clase.objects.select_for_update().get(pk=clase.pk)
    if not alumno.activo:
        raise ReservaError('Tu cuenta está inactiva, hablá con tu entrenador.')
    if clase.estado == Clase.CANCELADA:
        raise ReservaError('La clase fue cancelada.')
    if clase.ya_paso:
        raise ReservaError('La clase ya pasó.')
    existente = Reserva.objects.filter(alumno=alumno, clase=clase).first()
    if existente and existente.estado == Reserva.CONFIRMADA:
        raise ReservaError('Ya tenés un lugar en esta clase.')
    if clase.lugares_libres <= 0:
        raise ReservaError('La clase está completa.')
    if alumno.saldo_disponible <= 0:
        raise ReservaError(MSG_SIN_SALDO)
    if existente:  # re-reserva tras cancelar: la restricción única impide crear otra
        existente.estado = Reserva.CONFIRMADA
        existente.save(update_fields=['estado'])
        return existente
    return Reserva.objects.create(alumno=alumno, clase=clase)


@transaction.atomic
def cancelar(alumno, clase):
    reserva = Reserva.objects.filter(
        alumno=alumno, clase=clase, estado=Reserva.CONFIRMADA
    ).first()
    if not reserva:
        raise ReservaError('No tenés una reserva confirmada en esta clase.')
    if clase.ya_paso:
        raise ReservaError('La clase ya pasó, no se puede cancelar.')
    reserva.estado = Reserva.CANCELADA
    reserva.save(update_fields=['estado'])
    return reserva


@transaction.atomic
def registrar_checkin(alumno, clase, origen='qr'):
    """Descuenta 1 clase por asistencia. Lo único que consume saldo es el check-in:
    una reserva sin check-in no descuenta nada. Devuelve CheckinResultado."""
    # Bloquea al alumno para serializar check-ins simultáneos.
    alumno = Alumno.objects.select_for_update().get(pk=alumno.pk)
    clase = Clase.objects.get(pk=clase.pk)
    if not alumno.activo:
        raise CheckinError('Tu cuenta está inactiva, hablá con tu entrenador.')
    if clase.estado == Clase.CANCELADA:
        raise CheckinError('La clase fue cancelada.')
    consumos = Movimiento.objects.filter(alumno=alumno, clase=clase, tipo=Movimiento.CONSUMO)
    if consumos.exists():
        raise CheckinError(MSG_YA_CHECKIN)
    if alumno.saldo < 1:
        raise CheckinError(MSG_SIN_SALDO)
    try:
        with transaction.atomic():  # savepoint: la restricción única es la red de seguridad
            movimiento = Movimiento.objects.create(
                alumno=alumno, clase=clase, tipo=Movimiento.CONSUMO, clases=-1,
                nota=f'check-in {origen}',
            )
    except IntegrityError:
        raise CheckinError(MSG_YA_CHECKIN)
    Reserva.objects.filter(
        alumno=alumno, clase=clase, estado=Reserva.CONFIRMADA
    ).update(estado=Reserva.ASISTIDA)
    saldo = alumno.saldo
    return CheckinResultado(movimiento, saldo, alumno.reservas_futuras().count() > saldo)


def crear_clases_recurrentes(dias, horas, semanas, desde=None, cupo=None, precio=None, duracion=None):
    """Crea clases para `dias` (0=lunes) y `horas` (time) durante `semanas`.
    Saltea las que ya existen. Devuelve (creadas, salteadas)."""
    import datetime as dt

    desde = desde or timezone.localdate()
    cupo = cupo or settings.CUPO_DEFAULT
    precio = precio if precio is not None else settings.PRECIO_CLASE_DEFAULT
    duracion = duracion or settings.DURACION_CLASE_DEFAULT
    creadas = salteadas = 0
    for n in range(semanas * 7):
        dia = desde + dt.timedelta(days=n)
        if dia.weekday() not in dias:
            continue
        for hora in horas:
            _, nueva = Clase.objects.get_or_create(
                fecha=dia, hora_inicio=hora,
                defaults={'cupo_maximo': cupo, 'precio': precio, 'duracion_min': duracion},
            )
            if nueva:
                creadas += 1
            else:
                salteadas += 1
    return creadas, salteadas
