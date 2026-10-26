"""Genera las ilustraciones esquemáticas de los ejercicios (SVG) en
apptrainer/static/apptrainer/ejercicios/. Uso: python scripts/generar_ilustraciones.py

Cada figura es un "muñeco" de palitos sobre un fondo pastel según el bloque
(movilidad = menta, zona media = durazno, trabajo principal = lila).
"""
from pathlib import Path

DESTINO = Path(__file__).resolve().parent.parent / 'apptrainer' / 'static' / 'apptrainer' / 'ejercicios'

CUERPO, LEJOS, EQUIPO, ACENTO, SUELO = '#5b3fb0', '#9d86e0', '#a99bd6', '#f58fb5', '#c9bdf0'
FONDO = {'movilidad': '#cdf3e4', 'media': '#ffe2cb', 'principal': '#ebe2ff'}


def _pts(puntos):
    return ' '.join(f'{x},{y}' for x, y in puntos)


def linea(puntos, color=CUERPO, ancho=6, trazo=None):
    extra = f' stroke-dasharray="{trazo}"' if trazo else ''
    return (f'<polyline points="{_pts(puntos)}" fill="none" stroke="{color}" stroke-width="{ancho}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def cabeza(x, y, r=7):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{CUERPO}" stroke-width="4"/>'


def circulo(x, y, r, relleno=ACENTO, borde=None):
    b = f' stroke="{borde}" stroke-width="3"' if borde else ''
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{relleno}"{b}/>'


def rect(x, y, w, h, relleno=EQUIPO, rx=4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{relleno}"/>'


def flecha(x1, y1, x2, y2, color=ACENTO):
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 8 * math.cos(ang - 0.5), y2 - 8 * math.sin(ang - 0.5))
    a2 = (x2 - 8 * math.cos(ang + 0.5), y2 - 8 * math.sin(ang + 0.5))
    return (linea([(x1, y1), (x2, y2)], color, 3.5) +
            f'<polyline points="{a1[0]:.1f},{a1[1]:.1f} {x2},{y2} {a2[0]:.1f},{a2[1]:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')


def arco(x1, y1, cx, cy, x2, y2, color=ACENTO):
    """Flecha curva: de (x1,y1) a (x2,y2) con punto de control (cx,cy)."""
    import math
    ang = math.atan2(y2 - cy, x2 - cx)
    a1 = (x2 - 8 * math.cos(ang - 0.5), y2 - 8 * math.sin(ang - 0.5))
    a2 = (x2 - 8 * math.cos(ang + 0.5), y2 - 8 * math.sin(ang + 0.5))
    return (f'<path d="M{x1},{y1} Q{cx},{cy} {x2},{y2}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<polyline points="{a1[0]:.1f},{a1[1]:.1f} {x2},{y2} {a2[0]:.1f},{a2[1]:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')


def suelo(y=104):
    return linea([(6, y), (114, y)], SUELO, 3)


def mancuerna(x, y, vertical=False):
    if vertical:
        return rect(x - 4, y - 9, 8, 18, ACENTO, 3) + rect(x - 7, y - 9, 14, 5, '#d4558a', 2) + rect(x - 7, y + 4, 14, 5, '#d4558a', 2)
    return rect(x - 9, y - 4, 18, 8, ACENTO, 3) + rect(x - 9, y - 7, 5, 14, '#d4558a', 2) + rect(x + 4, y - 7, 5, 14, '#d4558a', 2)


def pelota(x, y, r=17):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffc6dc" stroke="{ACENTO}" stroke-width="3"/>'
            f'<path d="M{x - r + 5},{y - 4} Q{x},{y - r + 3} {x + r - 5},{y - 4}" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>')


# Cada figura: (bloque, [elementos SVG]). Las extremidades lejanas van primero y más claras.
FIGURAS = {}


def figura(slug, bloque, *elementos):
    FIGURAS[slug] = (bloque, elementos)


# ---------------------------------------------------------------- MOVILIDAD
figura('movilidad-tobillo', 'movilidad', suelo(),
       linea([(104, 14), (104, 104)], EQUIPO, 5),
       linea([(50, 62), (38, 84), (24, 102), (38, 102)], LEJOS),
       linea([(50, 62), (84, 78), (72, 102), (88, 102)]),
       linea([(50, 62), (58, 36)]), linea([(58, 38), (80, 42), (98, 46)]), cabeza(61, 25),
       flecha(70, 58, 88, 66))

figura('movilidad-cadera-zancada', 'movilidad', suelo(),
       linea([(54, 74), (30, 92), (12, 102)], LEJOS),
       linea([(54, 74), (82, 76), (80, 102), (94, 102)]),
       linea([(54, 74), (54, 46)]), linea([(54, 48), (68, 60), (80, 72)]), cabeza(54, 36),
       arco(24, 66, 36, 54, 46, 70))

figura('movilidad-cadera-sentadilla', 'movilidad', suelo(),
       linea([(44, 86), (76, 78), (64, 102), (80, 102)]),
       linea([(44, 86), (54, 50)]), linea([(54, 52), (68, 64), (74, 78)]), cabeza(56, 39),
       flecha(86, 68, 98, 60))

figura('movilidad-hombros-banda', 'movilidad', suelo(),
       linea([(60, 68), (52, 102)]), linea([(60, 68), (68, 102)]),
       linea([(60, 40), (60, 68)]), linea([(60, 40), (42, 24), (32, 8)]), linea([(60, 40), (78, 24), (88, 8)]),
       cabeza(60, 28),
       f'<path d="M32,8 Q60,22 88,8" fill="none" stroke="{ACENTO}" stroke-width="4" stroke-linecap="round"/>')

figura('movilidad-torax-fitball', 'movilidad', suelo(),
       pelota(60, 84, 19),
       linea([(44, 76), (36, 90), (32, 102), (46, 102)]),
       linea([(80, 56), (62, 58), (46, 74)]), linea([(80, 58), (92, 46), (98, 58)]), cabeza(92, 36),
       arco(86, 82, 98, 72, 100, 58))

figura('rotacion-toracica', 'movilidad', suelo(),
       linea([(32, 92), (56, 78), (74, 92)], LEJOS),
       linea([(32, 92), (70, 92)]), linea([(70, 92), (96, 92)], LEJOS),
       linea([(70, 90), (66, 62), (48, 44)]), cabeza(82, 84),
       arco(40, 56, 46, 40, 58, 44))

figura('movilidad-escapular', 'movilidad', suelo(),
       linea([(60, 68), (52, 102)]), linea([(60, 68), (68, 102)]),
       linea([(60, 40), (60, 68)]), linea([(60, 42), (48, 58), (46, 76)]), linea([(60, 42), (72, 58), (74, 76)]),
       cabeza(60, 28), flecha(36, 46, 36, 30), flecha(84, 30, 84, 46))

figura('movilidad-hombro-pared', 'movilidad', suelo(),
       linea([(98, 10), (98, 104)], EQUIPO, 5),
       linea([(56, 66), (50, 102)], LEJOS), linea([(56, 66), (64, 102)]),
       linea([(58, 38), (56, 66)]), linea([(58, 40), (80, 26), (94, 12)]), cabeza(59, 27),
       flecha(86, 56, 86, 30))

# --------------------------------------------------------------- ZONA MEDIA
figura('aduccion', 'media', suelo(),
       rect(40, 68, 40, 7, EQUIPO),
       linea([(60, 66), (40, 78), (36, 102)], LEJOS), linea([(60, 66), (80, 78), (84, 102)]),
       linea([(60, 38), (60, 66)]), linea([(60, 40), (48, 54), (46, 62)]), linea([(60, 40), (72, 54), (74, 62)]),
       cabeza(60, 26), rect(28, 72, 8, 14, ACENTO, 3), rect(84, 72, 8, 14, ACENTO, 3),
       flecha(18, 80, 28, 80), flecha(102, 80, 92, 80))

figura('abduccion', 'media', suelo(),
       rect(40, 68, 40, 7, EQUIPO),
       linea([(60, 66), (34, 80), (28, 102)], LEJOS), linea([(60, 66), (86, 80), (92, 102)]),
       linea([(60, 38), (60, 66)]), linea([(60, 40), (48, 54), (46, 62)]), linea([(60, 40), (72, 54), (74, 62)]),
       cabeza(60, 26), rect(20, 74, 8, 14, ACENTO, 3), rect(92, 74, 8, 14, ACENTO, 3),
       flecha(26, 98, 12, 98), flecha(94, 98, 108, 98))

figura('plancha-fitball', 'media', suelo(),
       pelota(26, 85, 17),
       linea([(36, 62), (74, 78), (108, 100)]), linea([(36, 64), (28, 70)]), cabeza(26, 54))

figura('plancha', 'media', suelo(),
       linea([(32, 72), (70, 84), (106, 100)]),
       linea([(32, 74), (32, 98), (50, 98)]), cabeza(24, 66))

figura('oblicuos-banda', 'media', suelo(),
       linea([(60, 68), (52, 102)]), linea([(60, 68), (68, 102)]),
       linea([(60, 40), (60, 68)]), linea([(60, 42), (70, 54), (66, 50)]), linea([(60, 42), (74, 50), (68, 52)]),
       cabeza(60, 28),
       circulo(112, 52, 4, EQUIPO), linea([(68, 52), (112, 52)], ACENTO, 3, '4 4'),
       arco(40, 44, 36, 30, 52, 24))

figura('plancha-banda', 'media', suelo(),
       linea([(70, 78), (96, 92), (108, 102)], LEJOS),
       linea([(32, 66), (70, 78)]), linea([(70, 78), (56, 90), (64, 100)]),
       linea([(34, 68), (34, 102)]), cabeza(24, 58),
       f'<ellipse cx="62" cy="92" rx="11" ry="5" fill="none" stroke="{ACENTO}" stroke-width="4"/>',
       flecha(80, 92, 70, 92))

figura('bicho-muerto', 'media', suelo(),
       linea([(70, 92), (80, 66), (96, 66)], LEJOS), linea([(70, 92), (110, 92)]),
       linea([(32, 92), (70, 92)]), linea([(32, 92), (34, 56)]), linea([(32, 92), (10, 80)], LEJOS),
       cabeza(22, 92))

figura('puente-fitball', 'media', suelo(),
       pelota(98, 86, 16),
       linea([(26, 98), (56, 74)]), linea([(56, 74), (96, 80)]),
       linea([(28, 99), (50, 99)], LEJOS), cabeza(16, 98))

# ---------------------------------------------------------- TRABAJO PRINCIPAL
figura('hip-thrust', 'principal', suelo(),
       rect(8, 74, 32, 30, EQUIPO),
       linea([(26, 72), (62, 66)]), linea([(62, 66), (86, 80), (82, 102), (96, 102)]),
       linea([(26, 72), (38, 80)], LEJOS), cabeza(16, 66),
       linea([(50, 58), (74, 58)], EQUIPO, 4), circulo(50, 58, 9), circulo(74, 58, 9),
       flecha(64, 48, 64, 36))

figura('puente-gluteo', 'principal', suelo(),
       linea([(26, 98), (56, 74)]), linea([(56, 74), (78, 66), (86, 100), (100, 100)]),
       linea([(28, 99), (50, 99)], LEJOS), cabeza(16, 98), flecha(60, 58, 60, 44))

figura('sentadilla-sumo', 'principal', suelo(),
       linea([(60, 74), (36, 82), (28, 102)], LEJOS), linea([(60, 74), (84, 82), (92, 102)]),
       linea([(60, 44), (60, 74)]), linea([(60, 46), (50, 62), (58, 82)]), linea([(60, 46), (70, 62), (62, 82)]),
       cabeza(60, 32), circulo(60, 90, 9), rect(55, 82, 10, 6, '#d4558a', 2))

figura('sentadilla-goblet', 'principal', suelo(),
       linea([(44, 82), (76, 76), (64, 102), (80, 102)]),
       linea([(44, 82), (52, 48)]), linea([(52, 50), (60, 62), (68, 54)]), cabeza(54, 37),
       mancuerna(70, 52, True))

figura('peso-muerto-rumano', 'principal', suelo(),
       linea([(48, 66), (58, 84), (58, 102), (72, 102)]),
       linea([(48, 66), (84, 54)]), linea([(84, 56), (84, 88)]), cabeza(95, 52),
       linea([(70, 88), (98, 88)], EQUIPO, 4), circulo(70, 88, 11), circulo(98, 88, 11),
       flecha(36, 74, 28, 66))

figura('flexiones', 'principal', suelo(),
       linea([(14, 100), (46, 80), (82, 66)]), linea([(82, 68), (82, 102)]), cabeza(93, 60),
       flecha(104, 70, 104, 86))

figura('biceps-barra', 'principal', suelo(),
       linea([(60, 66), (58, 86), (58, 102), (70, 102)]),
       linea([(60, 36), (60, 66)]), linea([(60, 38), (60, 58), (80, 48)]), cabeza(61, 25),
       linea([(80, 40), (80, 56)], EQUIPO, 4), circulo(80, 48, 9), arco(92, 62, 100, 46, 92, 34))

figura('landmine', 'principal', suelo(),
       linea([(108, 102), (70, 34)], EQUIPO, 5), circulo(70, 34, 8),
       linea([(46, 68), (46, 86), (46, 102), (58, 102)]),
       linea([(48, 38), (46, 68)]), linea([(48, 40), (60, 40), (68, 36)]), cabeza(49, 26),
       flecha(84, 56, 94, 72))

figura('biceps-martillo', 'principal', suelo(),
       linea([(60, 68), (52, 102)]), linea([(60, 68), (68, 102)]),
       linea([(60, 40), (60, 68)]), linea([(60, 42), (44, 60), (44, 44)]), linea([(60, 42), (76, 60), (76, 44)]),
       cabeza(60, 28), mancuerna(44, 38, True), mancuerna(76, 38, True))

figura('maquina-espalda', 'principal', suelo(),
       rect(42, 82, 36, 7, EQUIPO),
       linea([(60, 78), (44, 86), (42, 102)], LEJOS), linea([(60, 78), (76, 86), (78, 102)]),
       linea([(60, 50), (60, 78)]), linea([(60, 52), (42, 44), (34, 26)]), linea([(60, 52), (78, 44), (86, 26)]),
       cabeza(60, 38), linea([(26, 24), (94, 24)], ACENTO, 5), linea([(60, 4), (60, 24)], EQUIPO, 3),
       flecha(14, 34, 14, 52), flecha(106, 34, 106, 52))

figura('fondos-cajon', 'principal', suelo(),
       rect(6, 76, 30, 28, EQUIPO),
       linea([(44, 92), (72, 92), (98, 100)]),
       linea([(40, 66), (44, 92)]), linea([(40, 68), (30, 84), (24, 76)]), cabeza(42, 54),
       flecha(60, 66, 60, 78))

figura('remo-maquina', 'principal', suelo(),
       rect(20, 90, 28, 7, EQUIPO),
       linea([(36, 86), (64, 82), (70, 100), (84, 100)]),
       linea([(36, 86), (34, 54)]), linea([(34, 56), (22, 68), (48, 66)]), cabeza(34, 43),
       linea([(48, 66), (104, 66)], ACENTO, 3, '4 4'), flecha(92, 54, 100, 54))

figura('triceps-tras-nuca', 'principal', suelo(),
       linea([(62, 68), (60, 86), (60, 102), (72, 102)]),
       linea([(62, 40), (62, 68)]), linea([(62, 42), (74, 14), (56, 14)]), cabeza(64, 29),
       circulo(52, 18, 7), flecha(94, 40, 94, 20))

figura('sentadilla-empuje', 'principal', suelo(),
       linea([(50, 76), (72, 84), (60, 102), (76, 102)]),
       linea([(50, 76), (54, 50)]), linea([(54, 52), (62, 34), (60, 18)]), cabeza(56, 40),
       mancuerna(60, 14), flecha(92, 56, 92, 30))

figura('sentadilla-bulgara', 'principal', suelo(),
       rect(4, 76, 26, 28, EQUIPO),
       linea([(60, 72), (46, 92), (26, 76)], LEJOS),
       linea([(60, 72), (84, 80), (80, 102), (94, 102)]),
       linea([(62, 44), (60, 72)]), linea([(62, 46), (66, 62), (68, 70)]), cabeza(62, 33),
       mancuerna(68, 76, True))

figura('vuelos-laterales', 'principal', suelo(),
       linea([(60, 68), (52, 102)]), linea([(60, 68), (68, 102)]),
       linea([(60, 40), (60, 68)]), linea([(60, 42), (36, 44), (20, 44)]), linea([(60, 42), (84, 44), (100, 44)]),
       cabeza(60, 28), mancuerna(16, 44, True), mancuerna(104, 44, True),
       flecha(20, 62, 20, 54), flecha(100, 62, 100, 54))

figura('step-up', 'principal', suelo(),
       rect(62, 80, 44, 24, EQUIPO),
       linea([(46, 64), (46, 86), (44, 102)], LEJOS),
       linea([(46, 64), (66, 62), (76, 80), (90, 80)]),
       linea([(46, 36), (46, 64)]), linea([(46, 38), (50, 54), (52, 68)]), cabeza(46, 24),
       mancuerna(52, 74, True), flecha(30, 50, 30, 36))

figura('trx-posteriores', 'principal', suelo(),
       linea([(96, 4), (96, 60)], EQUIPO, 3), linea([(88, 60), (104, 60)], ACENTO, 5),
       linea([(26, 98), (58, 76)]), linea([(58, 76), (94, 62)]),
       linea([(28, 99), (50, 99)], LEJOS), cabeza(16, 98), flecha(44, 62, 44, 50))


def svg(bloque, elementos):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">'
            f'<rect width="120" height="120" rx="22" fill="{FONDO[bloque]}"/>' + ''.join(elementos) + '</svg>\n')


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for slug, (bloque, elementos) in FIGURAS.items():
        (DESTINO / f'{slug}.svg').write_text(svg(bloque, elementos), encoding='utf8')
    print(f'{len(FIGURAS)} ilustraciones en {DESTINO}')


if __name__ == '__main__':
    main()
