from django.contrib import admin

from .models import Bloque, Dia, Ejercicio, EjercicioHecho, RegistroPeso, Rutina, Sesion


class DiaInline(admin.TabularInline):
    model = Dia
    extra = 0
    show_change_link = True


class BloqueInline(admin.TabularInline):
    model = Bloque
    extra = 0
    show_change_link = True


class EjercicioInline(admin.StackedInline):
    model = Ejercicio
    extra = 0
    fields = ['orden', 'nombre', 'prescripcion', 'grupo', 'material', 'url_video', 'nota']


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'activa', 'creada_en']
    list_filter = ['activa']
    search_fields = ['nombre', 'usuario__username']
    inlines = [DiaInline]


@admin.register(Dia)
class DiaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'rutina', 'enfoque', 'dia_semana', 'orden']
    list_filter = ['rutina__usuario']
    inlines = [BloqueInline]


@admin.register(Bloque)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'orden']
    inlines = [EjercicioInline]


class HechoInline(admin.TabularInline):
    model = EjercicioHecho
    extra = 0


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'dia', 'fecha', 'completada']
    list_filter = ['completada', 'fecha']
    search_fields = ['usuario__username']
    inlines = [HechoInline]


@admin.register(RegistroPeso)
class RegistroPesoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha', 'kg', 'nota']
    list_filter = ['usuario']
    date_hierarchy = 'fecha'
