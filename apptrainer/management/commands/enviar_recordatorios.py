from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apptrainer import recordatorios


class Command(BaseCommand):
    help = (
        'Envía por correo el recordatorio de pesos pendientes del día de entrenamiento. '
        'Pensado para correr cada hora; solo actúa pasada la hora RECORDATORIO_HORA y no repite '
        'el mismo aviso.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--ahora', action='store_true', help='Ignora la hora configurada (para probar).')
        parser.add_argument('--simular', action='store_true', help='Muestra qué enviaría, sin enviar nada.')
        parser.add_argument('--usuario', help='Limita el envío a este nombre de usuario.')

    def handle(self, *args, ahora=False, simular=False, usuario=None, **opts):
        if not simular and not settings.DEBUG and not settings.EMAIL_HOST:
            raise CommandError(
                'Falta configurar el correo: define EMAIL_HOST, EMAIL_HOST_USER y EMAIL_HOST_PASSWORD '
                '(ver docs/recordatorios-por-correo.md).'
            )
        filtro = None
        if usuario:
            try:
                filtro = get_user_model().objects.get(username=usuario)
            except get_user_model().DoesNotExist:
                raise CommandError(f'No existe el usuario "{usuario}".')

        resultados = recordatorios.enviar_pendientes(ignorar_hora=ahora, simular=simular, usuario=filtro)
        if not resultados:
            self.stdout.write('Sin recordatorios para enviar.')
        for r in resultados:
            faltan = ', '.join(e.nombre for e in r['pendientes'])
            self.stdout.write(f"{r['estado'].upper()}: {r['usuario'].username} · {r['dia'].titulo} · faltan: {faltan}")
        if any(r['estado'] == 'error' for r in resultados):
            raise CommandError('Algún recordatorio no se pudo enviar (revisa el log).')
