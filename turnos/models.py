import datetime as dt

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


def normalizar_dni(valor):
    """Deja solo los dígitos (acepta '30.123.456')."""
    return ''.join(c for c in str(valor) if c.isdigit())


class Alumno(models.Model):
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    dni = models.CharField('DNI', max_length=10, unique=True)
    telefono = models.CharField('teléfono', max_length=30)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f'{self.apellido}, {self.nombre} ({self.dni})'

    def save(self, *args, **kwargs):
        self.dni = normalizar_dni(self.dni)
        super().save(*args, **kwargs)

    @property
    def saldo(self):
        """Clases acreditadas: suma del libro de movimientos."""
        return self.movimientos.aggregate(t=Sum('clases'))['t'] or 0

    @property
    def clases_comprometidas(self):
        """Reservas futuras confirmadas (todavía no consumidas)."""
        return self.reservas_futuras().count()

    @property
    def saldo_disponible(self):
        return self.saldo - self.clases_comprometidas

    def reservas_futuras(self):
        ahora = timezone.localtime()
        return self.reservas.filter(
            estado=Reserva.CONFIRMADA, clase__estado=Clase.ABIERTA
        ).filter(
            models.Q(clase__fecha__gt=ahora.date())
            | models.Q(clase__fecha=ahora.date(), clase__hora_inicio__gt=ahora.time())
        )


class Clase(models.Model):
    ABIERTA = 'abierta'
    CANCELADA = 'cancelada'
    ESTADOS = [(ABIERTA, 'Abierta'), (CANCELADA, 'Cancelada')]

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    duracion_min = models.PositiveIntegerField(
        'duración (min)', default=settings.DURACION_CLASE_DEFAULT
    )
    cupo_maximo = models.PositiveIntegerField('cupo máximo', default=settings.CUPO_DEFAULT)
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, default=settings.PRECIO_CLASE_DEFAULT
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default=ABIERTA)

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['fecha', 'hora_inicio'], name='clase_unica_por_horario'
            )
        ]

    def __str__(self):
        return f'{self.fecha:%d/%m/%Y} {self.hora_inicio:%H:%M}'

    @property
    def inicio(self):
        """Inicio como datetime aware en la zona horaria del proyecto."""
        return timezone.make_aware(dt.datetime.combine(self.fecha, self.hora_inicio))

    @property
    def ya_paso(self):
        return self.inicio <= timezone.now()

    @property
    def lugares_ocupados(self):
        if hasattr(self, 'ocupados'):  # anotado por la vista para evitar N+1
            return self.ocupados
        return self.reservas.filter(estado=Reserva.CONFIRMADA).count()

    @property
    def lugares_libres(self):
        return max(self.cupo_maximo - self.lugares_ocupados, 0)

    @property
    def color(self):
        """verde = disponible, amarillo = quedan <=2, gris = completa/pasada/cancelada."""
        if self.estado == self.CANCELADA or self.ya_paso or self.lugares_libres == 0:
            return 'gris'
        if self.lugares_libres <= 2:
            return 'amarillo'
        return 'verde'


class Reserva(models.Model):
    CONFIRMADA = 'confirmada'
    CANCELADA = 'cancelada'
    ASISTIDA = 'asistida'
    ESTADOS = [(CONFIRMADA, 'Confirmada'), (CANCELADA, 'Cancelada'), (ASISTIDA, 'Asistida')]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='reservas')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='reservas')
    estado = models.CharField(max_length=10, choices=ESTADOS, default=CONFIRMADA)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['clase__fecha', 'clase__hora_inicio']
        constraints = [
            models.UniqueConstraint(fields=['alumno', 'clase'], name='reserva_unica_por_alumno')
        ]

    def __str__(self):
        return f'{self.alumno} → {self.clase} ({self.estado})'


class Movimiento(models.Model):
    PAGO = 'pago'
    CONSUMO = 'consumo'
    AJUSTE = 'ajuste'
    TIPOS = [(PAGO, 'Pago'), (CONSUMO, 'Consumo'), (AJUSTE, 'Ajuste')]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='movimientos')
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_clase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    clase = models.ForeignKey(
        Clase, null=True, blank=True, on_delete=models.PROTECT, related_name='movimientos'
    )
    clases = models.IntegerField(help_text='Positivo suma clases, negativo resta.')
    nota = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-fecha', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'clase'],
                condition=models.Q(tipo='consumo'),
                name='consumo_unico_por_alumno_clase',
            )
        ]

    def __str__(self):
        return f'{self.alumno} {self.tipo} {self.clases:+d}'
