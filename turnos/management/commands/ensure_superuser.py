import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Crea el superusuario definido en DJANGO_SUPERUSER_USERNAME / _PASSWORD (y _EMAIL, opcional). '
        'No hace nada si faltan las variables y no falla si el usuario ya existe.'
    )

    def handle(self, *args, **opts):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD sin definir: no se crea superusuario.')
            return
        User = get_user_model()
        if User.objects.filter(**{User.USERNAME_FIELD: username}).exists():
            self.stdout.write(f'El superusuario "{username}" ya existe: no se modifica.')
            return
        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado.'))
