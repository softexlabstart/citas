from django import forms
from .models import Horario


class HorarioAdminForm(forms.ModelForm):
    TIME_CHOICES = [('', '---------')]
    for i in range(24):
        for j in [0, 30]:
            time_str = f'{i:02d}:{j:02d}:00'
            TIME_CHOICES.append((time_str, time_str.rsplit(':', 1)[0]))

    hora_inicio = forms.ChoiceField(choices=TIME_CHOICES, required=True)
    hora_fin = forms.ChoiceField(choices=TIME_CHOICES, required=True)

    class Meta:
        model = Horario
        fields = '__all__'