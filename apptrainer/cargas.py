"""Cálculo y formato del peso levantado (barra + discos, mancuernas o total)."""
from dataclasses import dataclass
from decimal import Decimal

from .models import CARGA_BARRA, CARGA_MANCUERNAS, CARGA_TOTAL

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
    if modo == CARGA_MANCUERNAS and mancuerna is not None:
        return f'2 × {kg_texto(mancuerna)} = {kg_texto(total)} kg'
    return f'{kg_texto(total)} kg'
