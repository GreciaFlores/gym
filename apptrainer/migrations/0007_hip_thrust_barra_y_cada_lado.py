from django.db import migrations


def ajustar(apps, schema_editor):
    """Hip thrust: se anota la barra y el peso de cada lado, sin la opción de mancuernas.

    Solo cambia la configuración del ejercicio. Los registros ya guardados (sesiones y pesos)
    no se tocan: conservan su detalle original.
    """
    Ejercicio = apps.get_model('apptrainer', 'Ejercicio')
    Ejercicio.objects.filter(nombre='Hip thrust').update(modos_permitidos='barra,total', carga_por_lado=True)


class Migration(migrations.Migration):

    dependencies = [
        ('apptrainer', '0006_comentarios_y_carga_por_lado'),
    ]

    operations = [
        migrations.RunPython(ajustar, migrations.RunPython.noop),
    ]
