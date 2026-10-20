from django.db import migrations

# (nombre, nota que cargó la versión anterior, nota textual del entrenador)
NOTAS = [
    ('Máquina de aducción', 'Mantener 3 seg cerrando.', 'Mantengo 3 seg cerrando'),
    ('Drop serie en máquina de abducción', 'Ir bajando el peso.', 'Vas bajando el peso'),
    ('Plancha sobre fitball', '10 respiraciones profundas por serie.', 'Respiraciones profundas'),
    ('Sentadilla sumo', 'Superserie con sentadilla goblet.', 'Superserie'),
    ('Bíceps con barra', '', 'Barra normal'),
    ('Máquina de espalda', 'Agarre prono.', 'Agarre prono'),
    ('Remo horizontal en máquina', 'Agarre neutro. Superserie con tríceps tras nuca.', 'Agarre neutro. Superserie'),
    ('Tríceps tras nuca', 'Con disco o mancuerna.', 'Con disco o mancuerna'),
    ('Sentadilla con empuje', 'Alternar con máquina sissy (usar mancuernas).', 'Alternar con máquina sysy (usar mancuernas)'),
]


def restaurar_textos(apps, schema_editor):
    """Deja las indicaciones del entrenador tal cual el documento.

    Solo cambia las notas que siguen siendo las que cargó la versión anterior: si alguien
    las editó a mano en el panel, no se tocan. El historial no se modifica.
    """
    Ejercicio = apps.get_model('apptrainer', 'Ejercicio')
    for nombre, vieja, nueva in NOTAS:
        Ejercicio.objects.filter(nombre=nombre, nota=vieja).update(nota=nueva)
    Ejercicio.objects.filter(nombre='Bíceps martillo isométrico alternado').update(
        nombre='Bíceps martillo iso alternado')


class Migration(migrations.Migration):

    dependencies = [
        ('apptrainer', '0004_completar_imagenes_y_cargas'),
    ]

    operations = [
        migrations.RunPython(restaurar_textos, migrations.RunPython.noop),
    ]
