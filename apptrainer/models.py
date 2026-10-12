from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q

DIAS_SEMANA = [
    (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
    (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
]


class Rutina(models.Model):
    """Plan semanal de un usuario. Cada usuario tiene como máximo una rutina activa."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rutinas'
    )
    nombre = models.CharField(max_length=80)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activa', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario'], condition=Q(activa=True), name='una_rutina_activa_por_usuario'
            )
        ]

    def __str__(self):
        return f'{self.nombre} ({self.usuario})'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.activa:
                Rutina.objects.filter(usuario_id=self.usuario_id, activa=True).exclude(
                    pk=self.pk
                ).update(activa=False)
            super().save(*args, **kwargs)


class Dia(models.Model):
    """Un día de entrenamiento de la rutina (Día 1, Día 2...)."""

    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='dias')
    orden = models.PositiveSmallIntegerField(default=1)
    titulo = models.CharField(max_length=60)
    enfoque = models.CharField(max_length=80, blank=True)
    dia_semana = models.PositiveSmallIntegerField(
        'día de la semana', choices=DIAS_SEMANA, null=True, blank=True,
        help_text='Qué día de la semana toca entrenar este día. Vacío = sin día fijo.',
    )

    class Meta:
        ordering = ['rutina', 'orden']
        verbose_name = 'día'
        constraints = [
            models.UniqueConstraint(fields=['rutina', 'orden'], name='dia_orden_unico'),
            models.UniqueConstraint(
                fields=['rutina', 'dia_semana'],
                condition=Q(dia_semana__isnull=False),
                name='dia_semana_unico_por_rutina',
            ),
        ]

    def __str__(self):
        return f'{self.titulo} · {self.rutina.nombre}'

    @property
    def nombre_dia_semana(self):
        return dict(DIAS_SEMANA).get(self.dia_semana, '')


class Bloque(models.Model):
    MOVILIDAD = 'movilidad'
    ZONA_MEDIA = 'zona_media'
    PRINCIPAL = 'principal'
    TIPOS = [
        (MOVILIDAD, 'Movilidad'),
        (ZONA_MEDIA, 'Zona media'),
        (PRINCIPAL, 'Trabajo principal'),
    ]

    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name='bloques')
    tipo = models.CharField(max_length=12, choices=TIPOS)
    orden = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['dia', 'orden']
        constraints = [
            models.UniqueConstraint(fields=['dia', 'orden'], name='bloque_orden_unico')
        ]

    def __str__(self):
        return f'{self.dia.titulo} · {self.get_tipo_display()}'


class Ejercicio(models.Model):
    bloque = models.ForeignKey(Bloque, on_delete=models.CASCADE, related_name='ejercicios')
    orden = models.PositiveSmallIntegerField(default=1)
    nombre = models.CharField(max_length=120)
    prescripcion = models.CharField(
        'series y reps', max_length=80, blank=True, help_text='Ej.: 3x10, 3xfallo, 3x6-6-6'
    )
    nota = models.TextField(blank=True)
    url_video = models.URLField('video', blank=True)
    material = models.CharField(max_length=80, blank=True)
    grupo = models.PositiveSmallIntegerField(
        'grupo combinado', null=True, blank=True,
        help_text='Ejercicios del mismo bloque con el mismo número se hacen combinados.',
    )

    class Meta:
        ordering = ['bloque', 'orden']
        constraints = [
            models.UniqueConstraint(fields=['bloque', 'orden'], name='ejercicio_orden_unico')
        ]

    def __str__(self):
        return self.nombre


class Sesion(models.Model):
    """Un día de rutina realizado (o iniciado) en una fecha concreta."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sesiones'
    )
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name='sesiones')
    fecha = models.DateField()
    completada = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'sesiones'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'dia', 'fecha'], name='sesion_unica')
        ]

    def __str__(self):
        return f'{self.usuario} · {self.dia.titulo} · {self.fecha}'


class EjercicioHecho(models.Model):
    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='hechos')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, related_name='hechos')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'ejercicios hechos'
        constraints = [
            models.UniqueConstraint(fields=['sesion', 'ejercicio'], name='hecho_unico')
        ]


class PesoEjercicio(models.Model):
    """Peso (kg) levantado en un ejercicio durante una sesión."""

    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='pesos')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, related_name='pesos')
    kg = models.DecimalField(
        'peso (kg)', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(500)],
    )

    class Meta:
        verbose_name = 'peso por ejercicio'
        verbose_name_plural = 'pesos por ejercicio'
        constraints = [
            models.UniqueConstraint(fields=['sesion', 'ejercicio'], name='peso_ejercicio_unico')
        ]

    def __str__(self):
        return f'{self.ejercicio} · {self.kg} kg'


class RegistroPeso(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pesos'
    )
    fecha = models.DateField()
    kg = models.DecimalField(
        'peso (kg)', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(20), MaxValueValidator(400)],
    )
    nota = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'registro de peso'
        verbose_name_plural = 'registros de peso'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'fecha'], name='peso_unico_por_fecha')
        ]

    def __str__(self):
        return f'{self.usuario} · {self.fecha} · {self.kg} kg'
