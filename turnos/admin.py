import datetime as dt

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone

from . import services
from .models import Alumno, Clase, Movimiento, Reserva


class PagoForm(forms.Form):
    monto = forms.DecimalField(label='Monto pagado ($)', min_value=1, decimal_places=2)
    precio_clase = forms.DecimalField(
        label='Precio por clase ($)', min_value=1, initial=settings.PRECIO_CLASE_DEFAULT
    )
    nota = forms.CharField(label='Nota', required=False)


class RecurrentesForm(forms.Form):
    DIAS = [(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
            (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')]
    dias = forms.MultipleChoiceField(
        label='Días', choices=DIAS, widget=forms.CheckboxSelectMultiple,
        initial=[0, 1, 2, 3, 4],
    )
    horas = forms.CharField(label='Horas (separadas por coma)', initial='8, 9, 18, 19',
                            help_text='Ej: 8, 9, 18:30, 19')
    semanas = forms.IntegerField(label='Cantidad de semanas', min_value=1, max_value=26, initial=4)
    desde = forms.DateField(label='Desde', widget=forms.DateInput(attrs={'type': 'date'}))
    cupo_maximo = forms.IntegerField(min_value=1, initial=settings.CUPO_DEFAULT)
    precio = forms.DecimalField(initial=settings.PRECIO_CLASE_DEFAULT, min_value=0)
    duracion_min = forms.IntegerField(label='Duración (min)', min_value=15,
                                      initial=settings.DURACION_CLASE_DEFAULT)

    def clean_horas(self):
        horas = []
        for parte in self.cleaned_data['horas'].split(','):
            parte = parte.strip()
            if not parte:
                continue
            try:
                h, _, m = parte.partition(':')
                horas.append(dt.time(int(h), int(m or 0)))
            except ValueError:
                raise forms.ValidationError(f'Hora inválida: "{parte}"')
        if not horas:
            raise forms.ValidationError('Indicá al menos una hora.')
        return horas


class MovimientoInline(admin.TabularInline):
    model = Movimiento
    extra = 0
    fields = ('fecha', 'tipo', 'monto', 'precio_clase', 'clases', 'nota')


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni', 'telefono', 'saldo_clases', 'disponibles', 'activo')
    list_filter = ('activo',)
    search_fields = ('dni', 'apellido', 'nombre', 'telefono')
    inlines = [MovimientoInline]
    actions = ['registrar_pago']

    @admin.display(description='Saldo')
    def saldo_clases(self, obj):
        return obj.saldo

    @admin.display(description='Disponibles (sin reservas)')
    def disponibles(self, obj):
        return obj.saldo_disponible

    @admin.action(description='Registrar pago (acredita clases)')
    def registrar_pago(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Elegí un solo alumno.', messages.ERROR)
            return None
        alumno = queryset.get()
        form = PagoForm(request.POST if 'aplicar' in request.POST else None)
        if 'aplicar' in request.POST and form.is_valid():
            mov = services.registrar_pago(
                alumno, form.cleaned_data['monto'], form.cleaned_data['precio_clase'],
                form.cleaned_data['nota'],
            )
            self.message_user(request, f'Pago registrado: +{mov.clases} clases. {mov.nota}')
            return None
        return render(request, 'admin/turnos/pago.html', {
            **self.admin_site.each_context(request), 'form': form, 'alumno': alumno,
            'title': 'Registrar pago', 'opts': self.model._meta,
        })


class ReservaInline(admin.TabularInline):
    model = Reserva
    extra = 0
    autocomplete_fields = ['alumno']


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora_inicio', 'ocupacion', 'cupo_maximo', 'precio', 'estado')
    list_filter = ('estado', 'fecha')
    date_hierarchy = 'fecha'
    inlines = [ReservaInline]
    actions = ['cancelar_clases']
    change_list_template = 'admin/turnos/clase_changelist.html'

    @admin.display(description='Ocupados')
    def ocupacion(self, obj):
        return f'{obj.lugares_ocupados} / {obj.cupo_maximo}'

    @admin.action(description='Cancelar clases seleccionadas')
    def cancelar_clases(self, request, queryset):
        n = queryset.update(estado=Clase.CANCELADA)
        self.message_user(request, f'{n} clase(s) canceladas. Las reservas quedan sin efecto para el calendario.')

    def get_urls(self):
        return [path('recurrentes/', self.admin_site.admin_view(self.recurrentes),
                     name='turnos_clase_recurrentes')] + super().get_urls()

    def recurrentes(self, request):
        form = RecurrentesForm(request.POST or None, initial={'desde': timezone.localdate()})
        if request.method == 'POST' and form.is_valid():
            d = form.cleaned_data
            creadas, salteadas = services.crear_clases_recurrentes(
                dias={int(x) for x in d['dias']}, horas=d['horas'], semanas=d['semanas'],
                desde=d['desde'], cupo=d['cupo_maximo'], precio=d['precio'],
                duracion=d['duracion_min'],
            )
            self.message_user(request, f'Se crearon {creadas} clases ({salteadas} ya existían).')
            return redirect(reverse('admin:turnos_clase_changelist'))
        return render(request, 'admin/turnos/recurrentes.html', {
            **self.admin_site.each_context(request), 'form': form,
            'title': 'Crear clases recurrentes', 'opts': self.model._meta,
        })


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'clase', 'estado', 'creada_en')
    list_filter = ('estado', 'clase__fecha')
    search_fields = ('alumno__dni', 'alumno__apellido', 'alumno__nombre')
    autocomplete_fields = ['alumno']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'alumno', 'tipo', 'monto', 'clases', 'nota')
    list_filter = ('tipo', 'fecha')
    search_fields = ('alumno__dni', 'alumno__apellido', 'alumno__nombre')
    autocomplete_fields = ['alumno']
