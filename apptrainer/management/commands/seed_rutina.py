from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apptrainer.models import Bloque, Dia, Ejercicio, Rutina

MOV, MEDIA, PRINCIPAL = Bloque.MOVILIDAD, Bloque.ZONA_MEDIA, Bloque.PRINCIPAL

YT_TOBILLO = 'https://www.youtube.com/shorts/h1zgwXSA5XY'
YT_CADERA_ZANCADA = 'https://www.youtube.com/shorts/rSx63cIHGA0'
YT_CADERA_SENTADILLA = 'https://www.youtube.com/shorts/pR7wmQtB4sA'
YT_TORAX_FITBALL = 'https://www.youtube.com/watch?v=oU2gQDsDiDA'
YT_ROTACION_TORACICA = 'https://www.youtube.com/shorts/dTwCidVgWso'
YT_ESCAPULAR = 'https://www.youtube.com/shorts/nZQvwTXwYaM'
YT_HOMBRO_PARED = 'https://www.youtube.com/shorts/L9HYbrTq-Xs'

# Cada ejercicio: (nombre, prescripción, nota, material, video, grupo).
# Mismo número de grupo dentro de un bloque = ejercicios combinados.
RUTINA = {
    'nombre': 'Rutina semanal',
    'dias': [
        {
            'titulo': 'Día 1', 'enfoque': 'Glúteo y pierna', 'dia_semana': 0,
            'bloques': [
                (MOV, [
                    ('Movilidad de tobillo', '', '', '', YT_TOBILLO, None),
                    ('Movilidad de cadera en zancada con balanceo', '', '', '', YT_CADERA_ZANCADA, None),
                    ('Movilidad de tobillo', '', '', '', YT_TOBILLO, None),
                    ('Movilidad de cadera en sentadilla profunda', '', '', '', YT_CADERA_SENTADILLA, None),
                ]),
                (MEDIA, [
                    ('Máquina de aducción', '3x12', 'Mantener 3 seg cerrando.', 'Máquina', '', 1),
                    ('Drop serie en máquina de abducción', '3x8-8-8', 'Ir bajando el peso.', 'Máquina', '', 1),
                    ('Plancha sobre fitball', '3x10', '10 respiraciones profundas por serie.', 'Fitball', '', None),
                ]),
                (PRINCIPAL, [
                    ('Hip thrust', '3x10', '', '', '', 1),
                    ('Elevaciones de cadera en colchoneta', '3x10', '', 'Colchoneta', '', 1),
                    ('Sentadilla sumo', '3x6-6-6', 'Superserie con sentadilla goblet.', '', '', 2),
                    ('Sentadilla goblet', '3x10', '', '', '', 2),
                    ('Peso muerto rumano', '3x10', '', '', '', None),
                ]),
            ],
        },
        {
            'titulo': 'Día 2', 'enfoque': 'Tren superior', 'dia_semana': 2,
            'bloques': [
                (MOV, [
                    ('Movilidad de hombros con banda', '', '', 'Banda roja', '', None),
                    ('Movilidad de tobillo', '', '', '', YT_TOBILLO, None),
                    ('Movilidad de cadera en zancada con balanceo', '', '', '', YT_CADERA_ZANCADA, None),
                    ('Movilidad de tobillo', '', '', '', YT_TOBILLO, None),
                    ('Movilidad de cadera en sentadilla profunda', '', '', '', YT_CADERA_SENTADILLA, None),
                    ('Movilidad del tórax en fitball', '', '', 'Fitball', YT_TORAX_FITBALL, None),
                ]),
                (MEDIA, [
                    ('Plancha constructora', '3x12', '', '', '', None),
                    ('Oblicuos con banda', '3x10 por lado', '', 'Banda', '', None),
                ]),
                (PRINCIPAL, [
                    ('Flexiones de brazo', '3xfallo', '', '', '', 1),
                    ('Bíceps con barra', '3x10', '', 'Barra', '', 1),
                    ('Empuje de rodillas en landmine', '3x10', '', 'Landmine', '', 2),
                    ('Bíceps martillo isométrico alternado', '3x10', '', 'Mancuernas', '', 2),
                    ('Máquina de espalda', '3x10', 'Agarre prono.', 'Máquina', '', 3),
                    ('Fondos en cajón', '3xfallo', '', 'Cajón', '', 3),
                    ('Remo horizontal en máquina', '3x8', 'Agarre neutro. Superserie con tríceps tras nuca.', 'Máquina', '', 4),
                    ('Tríceps tras nuca', '3x12', 'Con disco o mancuerna.', 'Disco o mancuerna', '', 4),
                ]),
            ],
        },
        {
            'titulo': 'Día 3', 'enfoque': 'Pierna unilateral', 'dia_semana': 4,
            'bloques': [
                (MOV, [
                    ('Movilidad del tórax en fitball', '', '', 'Fitball', YT_TORAX_FITBALL, None),
                    ('Rotación torácica acostado', '', '', '', YT_ROTACION_TORACICA, None),
                    ('Movilidad escapular', '', '', '', YT_ESCAPULAR, None),
                    ('Movilidad de hombro y dorsal con pared', '', '', 'Pared', YT_HOMBRO_PARED, None),
                ]),
                (MEDIA, [
                    ('Plancha dinámica con banda en rodillas', '', '', 'Banda', '', None),
                    ('Bicho muerto', '', '', '', '', None),
                    ('Puente con fitball en rodillas', '', '', 'Fitball', '', None),
                ]),
                (PRINCIPAL, [
                    ('Sentadilla con empuje', '3x12', 'Alternar con máquina sissy (usar mancuernas).', 'Mancuernas', '', None),
                    ('Sentadilla búlgara', '3x10', '', '', '', 1),
                    ('Vuelos laterales', '3x12', '', 'Mancuernas', '', 1),
                    ('Step up', '3x8', '', 'Cajón', '', 2),
                    ('Posteriores en TRX', '3xfallo', '', 'TRX', '', 2),
                ]),
            ],
        },
    ],
}


class Command(BaseCommand):
    help = 'Carga la rutina semanal (3 días) en un usuario existente. Reemplaza su rutina "Rutina semanal".'

    def add_arguments(self, parser):
        parser.add_argument('--usuario', required=True, help='Nombre de usuario que recibirá la rutina.')

    @transaction.atomic
    def handle(self, *args, usuario, **opts):
        try:
            user = get_user_model().objects.get(username=usuario)
        except get_user_model().DoesNotExist:
            raise CommandError(
                f'No existe el usuario "{usuario}". Créalo con: python manage.py createsuperuser'
            )

        # Idempotente: volver a correrlo reemplaza la rutina cargada antes por este comando.
        Rutina.objects.filter(usuario=user, nombre=RUTINA['nombre']).delete()
        rutina = Rutina.objects.create(usuario=user, nombre=RUTINA['nombre'], activa=True)
        for orden_dia, d in enumerate(RUTINA['dias'], start=1):
            dia = Dia.objects.create(
                rutina=rutina, orden=orden_dia, titulo=d['titulo'],
                enfoque=d['enfoque'], dia_semana=d['dia_semana'],
            )
            for orden_bloque, (tipo, ejercicios) in enumerate(d['bloques'], start=1):
                bloque = Bloque.objects.create(dia=dia, tipo=tipo, orden=orden_bloque)
                Ejercicio.objects.bulk_create([
                    Ejercicio(
                        bloque=bloque, orden=i, nombre=nombre, prescripcion=prescripcion,
                        nota=nota, material=material, url_video=video, grupo=grupo,
                    )
                    for i, (nombre, prescripcion, nota, material, video, grupo)
                    in enumerate(ejercicios, start=1)
                ])
        total = Ejercicio.objects.filter(bloque__dia__rutina=rutina).count()
        self.stdout.write(self.style.SUCCESS(
            f'Rutina cargada para "{usuario}": {len(RUTINA["dias"])} días, {total} ejercicios.'
        ))
