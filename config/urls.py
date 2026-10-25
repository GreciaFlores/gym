from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Panel del entrenador'
admin.site.site_title = 'Panel del entrenador'
admin.site.index_template = 'admin/turnos/index.html'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('turnos.urls')),
]
