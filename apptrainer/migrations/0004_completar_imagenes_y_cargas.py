from django.db import migrations

from apptrainer.catalogo import CATALOGO


def completar(apps, schema_editor):
    """Asigna imagen y tipo de carga a los ejercicios ya cargados (por nombre).

    No toca sesiones ni pesos: el historial queda intacto.
    """
    Ejercicio = apps.get_model('apptrainer', 'Ejercicio')
    for nombre, (imagen, carga) in CATALOGO.items():
        Ejercicio.objects.filter(nombre=nombre, imagen='').update(imagen=imagen, carga_habitual=carga)


class Migration(migrations.Migration):

    dependencies = [
        ('apptrainer', '0003_carga_detallada_e_imagen'),
    ]

    operations = [
        migrations.RunPython(completar, migrations.RunPython.noop),
    ]
