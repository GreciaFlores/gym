from django.urls import path

from . import views, views_checkin

urlpatterns = [
    path('', views.index, name='index'),
    path('identificar/', views.identificar, name='identificar'),
    path('registro/', views.registro, name='registro'),
    path('salir/', views.salir, name='salir'),
    path('clase/<int:pk>/reservar/', views.reservar, name='reservar'),
    path('checkin/', views_checkin.checkin_lista, name='checkin_lista'),
    path('checkin/<int:pk>/', views_checkin.checkin_clase, name='checkin'),
    path('clase/<int:pk>/cancelar/', views.cancelar, name='cancelar'),
]
