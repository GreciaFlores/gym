"""Cómo se anota el peso de cada ejercicio (tipos de carga disponibles, el habitual y si los
discos se anotan por lado). La usa `seed_rutina`; las migraciones llevan su propia copia.

Tipos de carga: "barra" (barra + discos), "mancuernas" (cada una, cuenta x2),
"lados" (solo discos de cada lado, sin barra, cuenta x2) y "total".
"""

TOTAL, BARRA, MANCUERNAS, LADOS = 'total', 'barra', 'mancuernas', 'lados'

# Tipo de carga habitual de los ejercicios que ofrecen más de una opción.
CARGA_HABITUAL = {
    'Sentadilla sumo': TOTAL,
    'Sentadilla goblet': TOTAL,
    'Peso muerto rumano': BARRA,
    'Bíceps con barra': BARRA,
    'Empuje de rodillas en landmine': BARRA,
    'Bíceps martillo iso alternado': MANCUERNAS,
    'Máquina de espalda': TOTAL,
    'Tríceps tras nuca': TOTAL,
    'Sentadilla con empuje': MANCUERNAS,
    'Vuelos laterales': MANCUERNAS,
}

_SOLO_TOTAL = {'modos_permitidos': TOTAL, 'carga_habitual': TOTAL}

# Ejercicios con tipos de carga restringidos (el resto ofrece barra, mancuernas y total).
AJUSTES = {
    # Día 1
    'Máquina de aducción': _SOLO_TOTAL,
    'Drop serie en máquina de abducción': _SOLO_TOTAL,
    'Plancha sobre fitball': _SOLO_TOTAL,
    'Hip thrust': {'modos_permitidos': BARRA, 'carga_habitual': BARRA, 'carga_por_lado': True},
    'Elevaciones de cadera en colchoneta': _SOLO_TOTAL,
    # Día 2
    'Plancha constructora': _SOLO_TOTAL,
    'Oblicuos con banda': _SOLO_TOTAL,
    'Flexiones de brazo': _SOLO_TOTAL,
    'Fondos en cajón': _SOLO_TOTAL,
    'Remo horizontal en máquina': {'modos_permitidos': LADOS, 'carga_habitual': LADOS},
    # Día 3
    'Plancha dinámica con banda en rodillas': _SOLO_TOTAL,
    'Bicho muerto': _SOLO_TOTAL,
    'Puente con fitball en rodillas': _SOLO_TOTAL,
    'Sentadilla búlgara': {'modos_permitidos': MANCUERNAS, 'carga_habitual': MANCUERNAS},
    'Step up': {'modos_permitidos': f'{MANCUERNAS},{TOTAL}', 'carga_habitual': MANCUERNAS},
    'Posteriores en TRX': _SOLO_TOTAL,
}


def ajustes_de(nombre):
    """Campos de carga del ejercicio para guardarlos al crearlo (dict listo para Ejercicio(**...))."""
    base = {'carga_habitual': CARGA_HABITUAL.get(nombre, TOTAL)}
    base.update(AJUSTES.get(nombre, {}))
    return base
