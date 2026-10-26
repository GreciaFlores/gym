"""Cálculo y formato del peso levantado (barra + discos, mancuernas o total)."""
from dataclasses import dataclass
from decimal import Decimal

from .models import CARGA_BARRA, CARGA_LADOS, CARGA_MANCUERNAS, CARGA_TOTAL

MAXIMO_KG = Decimal('500')


@dataclass(frozen=True)
class Carga:
    modo: str
    kg: Decimal                      # total levantado
    barra: Decimal | None = None
    discos: Decimal | None = None
    mancuerna: Decimal | None = None
    por_lado: Decimal | None = None


def kg_texto(valor):
    """Decimal('12.50') -> '12,5'; Decimal('20') -> '20' (como se escribe y se lee)."""
    if valor is None:
        return ''
    return format(Decimal(valor).normalize(), 'f').replace('.', ',')


def armar_carga(modo, total=None, barra=None, discos=None, mancuerna=None, por_lado=None, lados=False):
    """Devuelve la Carga con su total calculado, o None si no se anotó nada.

    - barra: total = barra + discos (alcanza con uno de los dos). Con `lados=True` se anota
      el peso de cada lado: total = barra + 2 x cada lado.
    - mancuernas: total = 2 x peso por mancuerna.
    - lados: solo discos, sin barra: total = 2 x peso de cada lado.
    - total: se usa tal cual.
    Lanza ValueError con un mensaje legible si el total supera el máximo.
    """
    if modo == CARGA_BARRA and lados:
        if barra is None and por_lado is None:
            return None
        carga = Carga(modo, (barra or 0) + 2 * (por_lado or 0), barra=barra, por_lado=por_lado)
    elif modo == CARGA_BARRA:
        if barra is None and discos is None:
            return None
        carga = Carga(modo, (barra or 0) + (discos or 0), barra=barra, discos=discos)
    elif modo == CARGA_LADOS:
        if por_lado is None:
            return None
        carga = Carga(modo, por_lado * 2, por_lado=por_lado)
    elif modo == CARGA_MANCUERNAS:
        if mancuerna is None:
            return None
        carga = Carga(modo, mancuerna * 2, mancuerna=mancuerna)
    else:
        if total is None:
            return None
        carga = Carga(CARGA_TOTAL, total)
    if carga.kg > MAXIMO_KG:
        raise ValueError(f'El total no puede superar {kg_texto(MAXIMO_KG)} kg.')
    return carga


def detalle_texto(modo, barra, discos, mancuerna, total, por_lado=None):
    """Desglose legible: "20 + 30 = 50 kg", "20 + 2 × 15 = 50 kg", "2 × 12 = 24 kg" o "50 kg"."""
    if modo == CARGA_BARRA:
        if por_lado is not None:
            partes = ([kg_texto(barra)] if barra is not None else []) + [f'2 × {kg_texto(por_lado)}']
        else:
            partes = [kg_texto(v) for v in (barra, discos) if v is not None]
        return f"{' + '.join(partes)} = {kg_texto(total)} kg" if len(partes) > 1 or por_lado is not None else f'{kg_texto(total)} kg'
    if modo == CARGA_LADOS and por_lado is not None:
        return f'2 × {kg_texto(por_lado)} = {kg_texto(total)} kg'
    if modo == CARGA_MANCUERNAS and mancuerna is not None:
        return f'2 × {kg_texto(mancuerna)} = {kg_texto(total)} kg'
    return f'{kg_texto(total)} kg'


def lineas_detalle(modo, barra, discos, mancuerna, total, por_lado=None):
    """El desglose completo, un dato por línea, para mostrarlo por separado y con su nombre."""
    kg = lambda v: f'{kg_texto(v)} kg'  # noqa: E731
    if modo == CARGA_BARRA:
        lineas = []
        if barra is not None:
            lineas.append(('Barra', kg(barra)))
        if por_lado is not None:
            lineas.append(('Disco de cada lado', kg(por_lado)))
        elif discos is not None:
            lineas.append(('Discos (los dos lados)', kg(discos)))
        lineas.append(('Total' if por_lado is None else 'Total (barra + 2 lados)', kg(total)))
        return lineas
    if modo == CARGA_LADOS and por_lado is not None:
        return [('Discos de cada lado', kg(por_lado)), ('Total (2 lados)', kg(total))]
    if modo == CARGA_MANCUERNAS and mancuerna is not None:
        return [('Cada mancuerna', kg(mancuerna)), ('Total (2 mancuernas)', kg(total))]
    return [('Peso total', kg(total))]
