"""Imagen y tipo de carga habitual de cada ejercicio, por nombre.

La usa `seed_rutina` y la migración de datos que completa los ejercicios ya cargados.
Las imágenes viven en static/apptrainer/ejercicios/<imagen>.svg.
"""

TOTAL, BARRA, MANCUERNAS = 'total', 'barra', 'mancuernas'

# nombre del ejercicio: (imagen, carga habitual)
CATALOGO = {
    # Movilidad
    'Movilidad de tobillo': ('movilidad-tobillo', TOTAL),
    'Movilidad de cadera en zancada con balanceo': ('movilidad-cadera-zancada', TOTAL),
    'Movilidad de cadera en sentadilla profunda': ('movilidad-cadera-sentadilla', TOTAL),
    'Movilidad de hombros con banda': ('movilidad-hombros-banda', TOTAL),
    'Movilidad del tórax en fitball': ('movilidad-torax-fitball', TOTAL),
    'Rotación torácica acostado': ('rotacion-toracica', TOTAL),
    'Movilidad escapular': ('movilidad-escapular', TOTAL),
    'Movilidad de hombro y dorsal con pared': ('movilidad-hombro-pared', TOTAL),
    # Zona media
    'Máquina de aducción': ('aduccion', TOTAL),
    'Drop serie en máquina de abducción': ('abduccion', TOTAL),
    'Plancha sobre fitball': ('plancha-fitball', TOTAL),
    'Plancha constructora': ('plancha', TOTAL),
    'Oblicuos con banda': ('oblicuos-banda', TOTAL),
    'Plancha dinámica con banda en rodillas': ('plancha-banda', TOTAL),
    'Bicho muerto': ('bicho-muerto', TOTAL),
    'Puente con fitball en rodillas': ('puente-fitball', TOTAL),
    # Trabajo principal
    'Hip thrust': ('hip-thrust', BARRA),
    'Elevaciones de cadera en colchoneta': ('puente-gluteo', TOTAL),
    'Sentadilla sumo': ('sentadilla-sumo', TOTAL),
    'Sentadilla goblet': ('sentadilla-goblet', TOTAL),
    'Peso muerto rumano': ('peso-muerto-rumano', BARRA),
    'Flexiones de brazo': ('flexiones', TOTAL),
    'Bíceps con barra': ('biceps-barra', BARRA),
    'Empuje de rodillas en landmine': ('landmine', BARRA),
    'Bíceps martillo iso alternado': ('biceps-martillo', MANCUERNAS),
    'Máquina de espalda': ('maquina-espalda', TOTAL),
    'Fondos en cajón': ('fondos-cajon', TOTAL),
    'Remo horizontal en máquina': ('remo-maquina', TOTAL),
    'Tríceps tras nuca': ('triceps-tras-nuca', TOTAL),
    'Sentadilla con empuje': ('sentadilla-empuje', MANCUERNAS),
    'Sentadilla búlgara': ('sentadilla-bulgara', MANCUERNAS),
    'Vuelos laterales': ('vuelos-laterales', MANCUERNAS),
    'Step up': ('step-up', MANCUERNAS),
    'Posteriores en TRX': ('trx-posteriores', TOTAL),
}

# Ajustes de carga por ejercicio: tipos disponibles y si los discos se anotan por lado.
AJUSTES = {
    'Hip thrust': {'modos_permitidos': 'barra,total', 'carga_por_lado': True},
}

# Texto breve que describe cada imagen (accesibilidad y lectura rápida).
DESCRIPCIONES = {
    'movilidad-tobillo': 'Rodilla adelantada sobre el pie apoyado',
    'movilidad-cadera-zancada': 'Zancada profunda llevando la cadera atrás y adelante',
    'movilidad-cadera-sentadilla': 'Sentadilla profunda abriendo la cadera con los codos',
    'movilidad-hombros-banda': 'Brazos arriba abriendo la banda',
    'movilidad-torax-fitball': 'Espalda sobre el fitball, brazos tras la cabeza',
    'rotacion-toracica': 'Acostada de lado, abriendo el brazo hacia atrás',
    'movilidad-escapular': 'Brazos al frente, hombros subiendo y bajando',
    'movilidad-hombro-pared': 'Brazos arriba apoyados en la pared',
    'aduccion': 'Sentada en máquina, piernas cerrando',
    'abduccion': 'Sentada en máquina, piernas abriendo',
    'plancha-fitball': 'Antebrazos sobre el fitball, cuerpo en línea',
    'plancha': 'Plancha sobre antebrazos, cuerpo recto',
    'oblicuos-banda': 'De pie, girando el torso contra la banda',
    'plancha-banda': 'Plancha con banda en rodillas, llevando una rodilla',
    'bicho-muerto': 'Boca arriba, brazo y pierna opuestos se extienden',
    'puente-fitball': 'Puente con los pies sobre el fitball',
    'hip-thrust': 'Espalda alta en el banco, barra en la cadera, cadera arriba',
    'puente-gluteo': 'Puente de glúteos en colchoneta',
    'sentadilla-sumo': 'Sentadilla con pies abiertos y peso entre las piernas',
    'sentadilla-goblet': 'Sentadilla sosteniendo una mancuerna al pecho',
    'peso-muerto-rumano': 'Bisagra de cadera con la barra cerca de las piernas',
    'flexiones': 'Flexión de brazos con el cuerpo en línea',
    'biceps-barra': 'De pie, subiendo la barra con los codos pegados',
    'landmine': 'Empuje de la barra landmine desde el pecho',
    'biceps-martillo': 'Curl martillo con mancuernas, palmas enfrentadas',
    'maquina-espalda': 'Jalón en máquina llevando la barra al pecho',
    'fondos-cajon': 'Fondos con las manos en el cajón',
    'remo-maquina': 'Remo sentada llevando los codos atrás',
    'triceps-tras-nuca': 'Peso tras la nuca, extendiendo los codos arriba',
    'sentadilla-empuje': 'Sentadilla y empuje de mancuernas arriba',
    'sentadilla-bulgara': 'Sentadilla con el pie de atrás en el banco',
    'vuelos-laterales': 'Brazos abriendo a los lados con mancuernas',
    'step-up': 'Subiendo al cajón con una pierna',
    'trx-posteriores': 'Talones en el TRX, elevando la cadera',
}


def datos_de(nombre):
    """(imagen, carga_habitual) del ejercicio; valores vacíos si no está en el catálogo."""
    return CATALOGO.get(nombre, ('', TOTAL))


def ajustes_de(nombre):
    """Campos extra del ejercicio (tipos de carga disponibles, discos por lado)."""
    return AJUSTES.get(nombre, {})
