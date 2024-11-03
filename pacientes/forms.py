from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Patient, Session, Specialist, Room
from .validators import validate_password_strength

# CustomUserCreationForm y CustomAuthenticationForm se mantienen igual
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
        fields = [
            'name', 'surname', 'date_of_birth', 'gender', 'photo',
            'marital_status', 'address', 'phone_number', 'email',
            'medical_diagnosis', 'attachments', 'therapy', 'education',
            'therapist', 'medical_history', 'allergies',
            'emergency_contact_name', 'emergency_contact_phone',
            'notes', 'status'
        ]
        labels = {
            'name': 'Nombre',
            'surname': 'Apellido',
            'date_of_birth': 'Fecha de Nacimiento',
            'gender': 'Género',
            'photo': 'Foto',
            'marital_status': 'Estado Civil',
            'address': 'Dirección',
            'phone_number': 'Número de Teléfono',
            'email': 'Correo Electrónico',
            'medical_diagnosis': 'Diagnóstico Médico',
            'attachments': 'Archivos Adjuntos',
            'therapy': 'Terapia',
            'education': 'Educación',
            'therapist': 'Terapeuta',
            'medical_history': 'Historial Médico',
            'allergies': 'Alergias',
            'emergency_contact_name': 'Nombre del Contacto de Emergencia',
            'emergency_contact_phone': 'Teléfono del Contacto de Emergencia',
            'notes': 'Notas',
            'status': 'Estado'
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino')]),
            'medical_history': forms.Textarea(attrs={'rows': 4}),
            'medical_diagnosis': forms.Textarea(attrs={'rows': 4}),
            'allergies': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'status': forms.Select(choices=[
                ('Active', 'Activo'),
                ('Discharged', 'Alta'),
                ('Suspended', 'Suspendido')
            ],
                attrs={'required': False})
        }

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'time', 'specialist', 'room', 'objective', 'activity', 
                 'materials', 'observation', 'attachment', 'is_reserved', 
                 'reserved_date', 'reserved_time', 'new_activity']
        
        labels = {
             'date': 'Fecha',
            'time': 'Hora',
            'patient': 'Paciente',
            'specialist': 'Especialista',
            'room': 'Sala',
            'objective': 'Objetivo',
            'activity': 'Actividad',
            'materials': 'Materiales',
            'observation': 'Observación',
            'attachment': 'Archivo Adjunto',
           
            'is_reserved': 'Reservar fecha',
            'reserved_date': 'Fecha de reserva',
            'reserved_time': 'Hora de reserva',
            'new_activity': 'Nueva actividad'
        }
        
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'reserved_date': forms.DateInput(attrs={'type': 'date'}),
            'reserved_time': forms.TimeInput(attrs={'type': 'time'}),
            'objective': forms.TextInput(attrs={'class': 'form-control'}),
            'activity': forms.Textarea(attrs={'rows': 4}),
            'materials': forms.Textarea(attrs={'rows': 4}),
            'observation': forms.Textarea(attrs={'rows': 4}),
            'new_activity': forms.Textarea(attrs={'rows': 4}),
        }

class SpecialistForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = ['name', 'surname', 'specialty', 'email', 'phone']
        labels = {
            'name': 'Nombre',
            'surname': 'Apellido',
            'specialty': 'Especialidad',
            'email': 'Correo Electrónico',
            'phone': 'Teléfono'
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'location', 'specialists']
        labels = {
            'name': 'Nombre',
            'capacity': 'Capacidad',
            'location': 'Ubicación',
            'specialists': 'Especialistas'
        }
        
class ReservationFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Fecha inicial',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='Fecha final',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )