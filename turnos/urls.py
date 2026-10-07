from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('identificar/', views.identificar, name='identificar'),
    path('registro/', views.registro, name='registro'),
    path('salir/', views.salir, name='salir'),
    path('clase/<int:pk>/reservar/', views.reservar, name='reservar'),
    path('clase/<int:pk>/cancelar/', views.cancelar, name='cancelar'),
]
