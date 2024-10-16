# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .validators import validate_password_strength
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Patient


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
    )
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={'placeholder': 'Correo electrónico'}),
    )
    password1 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        validators=[validate_password_strength],
    )
    password2 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'}),
        help_text="Vuelve a ingresar la misma contraseña para confirmarla."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        help_texts = {
            'username': None,
            'password1': None,
            'password2': None,
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
    )
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                _("Esta cuenta está inactiva."),
                code='inactive',
            )

    # Modificamos los mensajes de error del formulario
    error_messages = {
        'invalid_login': _(
            "Usuario o contraseña incorrectos. Verifica tus credenciales."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }
    
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'surname', 'date_of_birth', 'gender', 'address', 'phone_number', 
                  'email', 'medical_history', 'allergies', 'emergency_contact_name', 
                  'emergency_contact_phone', 'notes']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('M', 'Male'), ('F', 'Female')]),
            'medical_history': forms.Textarea(attrs={'rows': 4}),
            'allergies': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }