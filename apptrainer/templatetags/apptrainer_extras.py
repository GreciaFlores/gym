from django import template

from apptrainer.cargas import kg_texto

register = template.Library()


@register.filter
def kg(valor):
    """Decimal -> '52' o '52,5' (sin ceros de más)."""
    return kg_texto(valor)


@register.filter
def signo(valor):
    """Diferencia con signo: +5, -2,5, 0."""
    if valor is None:
        return ''
    texto = kg_texto(valor)
    return f'+{texto}' if valor > 0 else texto
