from django.contrib import admin
from django.urls import include, path

from apptrainer.views import health

admin.site.site_header = 'Panel del entrenador'
admin.site.site_title = 'Panel del entrenador'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', health, name='healthz'),
    path('app/', include('apptrainer.urls')),
    path('', include('turnos.urls')),
]
