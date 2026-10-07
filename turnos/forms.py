from django import forms

from .models import Alumno, normalizar_dni


class DniForm(forms.Form):
    dni = forms.CharField(label='DNI', max_length=14)

    def clean_dni(self):
        dni = normalizar_dni(self.cleaned_data['dni'])
        if not 6 <= len(dni) <= 9:
            raise forms.ValidationError('Ingresá un DNI válido (solo números).')
        return dni


class RegistroForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'telefono']
