from django import forms
from django.utils import timezone

from .models import RegistroPeso


class PesoForm(forms.ModelForm):
    class Meta:
        model = RegistroPeso
        fields = ['fecha', 'kg', 'nota']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'kg': forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': '65,4', 'autocomplete': 'off'}),
            'nota': forms.TextInput(attrs={'placeholder': 'Opcional: en ayunas, ciclo, etc.'}),
        }
        labels = {'kg': 'Peso (kg)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # localize=True: acepta "65,4" (teclado del celular) y "65.4".
        self.fields['kg'].localize = True
        self.fields['kg'].widget.is_localized = True
        self.fields['fecha'].initial = timezone.localdate

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha > timezone.localdate():
            raise forms.ValidationError('La fecha no puede ser futura.')
        return fecha
