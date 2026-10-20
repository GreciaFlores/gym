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


@register.simple_tag
def imagen_url(nombre):
    """URL estática de la ilustración de un ejercicio; vacía si no existe el archivo."""
    from django.contrib.staticfiles.storage import staticfiles_storage

    if not nombre:
        return ''
    try:
        return staticfiles_storage.url(f'apptrainer/ejercicios/{nombre}.svg')
    except ValueError:  # con el manifest de producción, un archivo faltante lanza error
        return ''


@register.filter
def descripcion(nombre):
    """Texto breve que describe la ilustración (para lectores de pantalla)."""
    from apptrainer.catalogo import DESCRIPCIONES

    return DESCRIPCIONES.get(nombre, '')
