import datetime as dt
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from turnos import services
from turnos.models import Alumno, Clase, Movimiento, Reserva

ALUMNOS = [
    # dni, nombre, apellido, teléfono, pago
    ('30111222', 'Ana', 'Pérez', '1155550001', Decimal('100000')),   # +7 (resto 2.000)
    ('31222333', 'Bruno', 'Gómez', '1155550002', Decimal('56000')),  # +4
    ('32333444', 'Carla', 'Sosa', '1155550003', Decimal('14000')),   # +1 (queda justo)
    ('33444555', 'Diego', 'López', '1155550004', Decimal('140000')), # +10
    ('34555666', 'Eli', 'Ruiz', '1155550005', None),                 # sin saldo
]


class Command(BaseCommand):
    help = 'Crea datos de ejemplo (2 semanas de clases, 5 alumnos y reservas). Es idempotente.'

    @transaction.atomic
    def handle(self, *args, **opts):
        hoy = timezone.localdate()
        lunes = hoy - dt.timedelta(days=hoy.weekday())
        horas = [dt.time(8), dt.time(9), dt.time(18), dt.time(19)]
        services.crear_clases_recurrentes({0, 1, 2, 3, 4}, horas, 2, desde=lunes, cupo=5)

        alumnos = {}
        for dni, nombre, apellido, tel, pago in ALUMNOS:
            a, nuevo = Alumno.objects.get_or_create(
                dni=dni, defaults={'nombre': nombre, 'apellido': apellido, 'telefono': tel})
            alumnos[dni] = a
            if nuevo and pago:
                services.registrar_pago(a, pago, 14000)
        if not Movimiento.objects.filter(nota__contains='ajuste demo').exists():
            Movimiento.objects.create(alumno=alumnos['31222333'], tipo=Movimiento.CONSUMO,
                                      clases=-1, nota='Clase tomada (ajuste demo)')

        futuras = list(Clase.objects.filter(estado=Clase.ABIERTA).order_by('fecha', 'hora_inicio'))
        futuras = [c for c in futuras if not c.ya_paso]
        if len(futuras) < 4:
            self.stdout.write(self.style.WARNING('Hay pocas clases futuras; se omiten reservas.'))
            return

        ana, bruno, diego = alumnos['30111222'], alumnos['31222333'], alumnos['33444555']
        # Clase completa (cupo 3, 3 reservas) -> gris
        llena = futuras[0]
        llena.cupo_maximo = 3
        llena.save(update_fields=['cupo_maximo'])
        for a in (ana, bruno, diego):
            Reserva.objects.get_or_create(alumno=a, clase=llena)
        # Clase con 2 lugares libres (cupo 4, 2 reservas) -> amarillo
        casi = futuras[1]
        casi.cupo_maximo = 4
        casi.save(update_fields=['cupo_maximo'])
        for a in (ana, diego):
            Reserva.objects.get_or_create(alumno=a, clase=casi)
        # Clase cancelada
        cancelada = futuras[-1]
        cancelada.estado = Clase.CANCELADA
        cancelada.save(update_fields=['estado'])
        # 1 lugar tomado en la tercera clase para ver variedad
        Reserva.objects.get_or_create(alumno=alumnos['33444555'], clase=futuras[2])
        # Una reserva cancelada de ejemplo
        Reserva.objects.get_or_create(alumno=alumnos['32333444'], clase=futuras[2],
                                      defaults={'estado': Reserva.CANCELADA})

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Clase.objects.count()} clases, {Alumno.objects.count()} alumnos.'))
        self.stdout.write('DNIs de prueba: 30111222 (7 clases), 31222333 (3), 32333444 (1), '
                          '33444555 (10), 34555666 (sin saldo).')
