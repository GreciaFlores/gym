from django.db import migrations

_SOLO_TOTAL = {'modos_permitidos': 'total', 'carga_habitual': 'total'}

# Cómo se anota el peso en cada ejercicio (según las indicaciones de Grecia).
AJUSTES = {
    # Día 1
    'Máquina de aducción': _SOLO_TOTAL,
    'Drop serie en máquina de abducción': _SOLO_TOTAL,
    'Plancha sobre fitball': _SOLO_TOTAL,
    'Hip thrust': {'modos_permitidos': 'barra', 'carga_habitual': 'barra', 'carga_por_lado': True},
    'Elevaciones de cadera en colchoneta': _SOLO_TOTAL,
    # Día 2
    'Plancha constructora': _SOLO_TOTAL,
    'Oblicuos con banda': _SOLO_TOTAL,
    'Flexiones de brazo': _SOLO_TOTAL,
    'Fondos en cajón': _SOLO_TOTAL,
    'Remo horizontal en máquina': {'modos_permitidos': 'lados', 'carga_habitual': 'lados'},
    # Día 3
    'Plancha dinámica con banda en rodillas': _SOLO_TOTAL,
    'Bicho muerto': _SOLO_TOTAL,
    'Puente con fitball en rodillas': _SOLO_TOTAL,
    'Sentadilla búlgara': {'modos_permitidos': 'mancuernas', 'carga_habitual': 'mancuernas'},
    'Step up': {'modos_permitidos': 'mancuernas,total', 'carga_habitual': 'mancuernas'},
    'Posteriores en TRX': _SOLO_TOTAL,
}


def aplicar(apps, schema_editor):
    """Restringe los tipos de carga que ofrece cada ejercicio.

    Solo cambia la configuración de los ejercicios: los pesos ya registrados (sesiones,
    barra, discos, mancuernas) no se tocan y siguen viéndose tal cual se guardaron.
    """
    Ejercicio = apps.get_model('apptrainer', 'Ejercicio')
    for nombre, campos in AJUSTES.items():
        Ejercicio.objects.filter(nombre=nombre).update(**campos)


class Migration(migrations.Migration):

    dependencies = [
        ('apptrainer', '0008_sin_imagenes_recordatorios_y_discos_por_lado'),
    ]

    operations = [
        migrations.RunPython(aplicar, migrations.RunPython.noop),
    ]
