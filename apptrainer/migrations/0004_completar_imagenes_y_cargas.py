from django.db import migrations


# Copia fija del catálogo de esa época: (imagen, tipo de carga habitual) por nombre de ejercicio.
# (La migración no debe depender de código que cambia con el tiempo.)
CATALOGO = {'Movilidad de tobillo': ('movilidad-tobillo', 'total'),
 'Movilidad de cadera en zancada con balanceo': ('movilidad-cadera-zancada', 'total'),
 'Movilidad de cadera en sentadilla profunda': ('movilidad-cadera-sentadilla', 'total'),
 'Movilidad de hombros con banda': ('movilidad-hombros-banda', 'total'),
 'Movilidad del tórax en fitball': ('movilidad-torax-fitball', 'total'),
 'Rotación torácica acostado': ('rotacion-toracica', 'total'),
 'Movilidad escapular': ('movilidad-escapular', 'total'),
 'Movilidad de hombro y dorsal con pared': ('movilidad-hombro-pared', 'total'),
 'Máquina de aducción': ('aduccion', 'total'),
 'Drop serie en máquina de abducción': ('abduccion', 'total'),
 'Plancha sobre fitball': ('plancha-fitball', 'total'),
 'Plancha constructora': ('plancha', 'total'),
 'Oblicuos con banda': ('oblicuos-banda', 'total'),
 'Plancha dinámica con banda en rodillas': ('plancha-banda', 'total'),
 'Bicho muerto': ('bicho-muerto', 'total'),
 'Puente con fitball en rodillas': ('puente-fitball', 'total'),
 'Hip thrust': ('hip-thrust', 'barra'),
 'Elevaciones de cadera en colchoneta': ('puente-gluteo', 'total'),
 'Sentadilla sumo': ('sentadilla-sumo', 'total'),
 'Sentadilla goblet': ('sentadilla-goblet', 'total'),
 'Peso muerto rumano': ('peso-muerto-rumano', 'barra'),
 'Flexiones de brazo': ('flexiones', 'total'),
 'Bíceps con barra': ('biceps-barra', 'barra'),
 'Empuje de rodillas en landmine': ('landmine', 'barra'),
 'Bíceps martillo iso alternado': ('biceps-martillo', 'mancuernas'),
 'Máquina de espalda': ('maquina-espalda', 'total'),
 'Fondos en cajón': ('fondos-cajon', 'total'),
 'Remo horizontal en máquina': ('remo-maquina', 'total'),
 'Tríceps tras nuca': ('triceps-tras-nuca', 'total'),
 'Sentadilla con empuje': ('sentadilla-empuje', 'mancuernas'),
 'Sentadilla búlgara': ('sentadilla-bulgara', 'mancuernas'),
 'Vuelos laterales': ('vuelos-laterales', 'mancuernas'),
 'Step up': ('step-up', 'mancuernas'),
 'Posteriores en TRX': ('trx-posteriores', 'total')}


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
