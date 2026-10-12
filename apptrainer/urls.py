from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'apptrainer'

urlpatterns = [
    path('', views.hoy, name='hoy'),
    path('semana/', views.semana, name='semana'),
    path('dia/<int:pk>/', views.dia_detalle, name='dia'),
    path('ejercicio/<int:pk>/alternar/', views.alternar, name='alternar'),
    path('peso/', views.peso, name='peso'),
    path('peso/<int:pk>/eliminar/', views.peso_eliminar, name='peso_eliminar'),
    path('peso/exportar.xlsx', views.peso_excel, name='peso_excel'),
    path('entrar/', auth_views.LoginView.as_view(
        template_name='apptrainer/login.html', redirect_authenticated_user=True), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('sw.js', views.service_worker, name='sw'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sin-conexion/', views.offline, name='offline'),
]
