from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Patient, Session, Specialist, Room, Payment
from panelAdmin.models import Client
from django.core.exceptions import ValidationError


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'name', 'surname', 'date_of_birth', 'gender', 'photo',
            'marital_status', 'address','cost_session', 'phone_number', 'email',
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
        fields = [
            'patient', 'specialist', 'room', 'date', 'time', 
            'objective', 'activity', 'materials', 'observation', 
            'attachment', 'status', 'paid_in_advance'
        ]
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
            'status': 'Estado de la sesión',
            'paid_in_advance': 'Pagada'
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'objective': forms.TextInput(attrs={'class': 'form-control'}),
            'activity': forms.Textarea(attrs={'rows': 4}),
            'materials': forms.Textarea(attrs={'rows': 4}),
            'observation': forms.Textarea(attrs={'rows': 4}),
            'paid_in_advance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        specialist = cleaned_data.get('specialist')
        room = cleaned_data.get('room')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if not specialist or not room or not date or not time:
            return cleaned_data

        # Validar que el especialista no esté ocupado en el mismo horario
        if Session.objects.filter(specialist=specialist, date=date, time=time).exists():
            self.add_error('specialist', 'El especialista ya tiene una sesión en este horario.')

        # Validar que la sala no esté ocupada en el mismo horario
        if Session.objects.filter(room=room, date=date, time=time).exists():
            self.add_error('room', 'La sala ya está reservada en este horario.')

        return cleaned_data

class SpecialistForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    email = forms.EmailField(required=True, label='Correo Electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    password = forms.CharField(widget=forms.PasswordInput(), label='Contraseña')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label='Confirmar Contraseña')

    class Meta:
        model = Specialist
        fields = ['client', 'specialty', 'phone', 'dni', 'profile_image', 'role']
        labels = {
            'specialty': 'Especialidad',
            'phone': 'Teléfono',
            'dni': 'DNI',
            'profile_image': 'Imagen de Perfil',
            'role': 'Rol',
        }
        widgets = {
            'role': forms.Select(choices=Specialist.ROLES),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request and self.request.tenant:
            client = self.request.tenant
            # Filtrar para mostrar solo el cliente actual
            self.fields['client'].queryset = Client.objects.filter(id=client.id)
            self.fields['client'].initial = client
            self.fields['client'].widget.attrs['readonly'] = True
            self.fields['client'].disabled = True

            # Verificar el límite de especialistas al inicializar el formulario
            current_count = Specialist.objects.filter(client=client).count()
            if current_count >= client.specialists_limit:
                self.fields['client'].help_text = (
                    f"No se pueden crear más especialistas. "
                    f"Límite: {client.specialists_limit}, "
                    f"Actuales: {current_count}"
                )

    def clean(self):
        cleaned_data = super().clean()
        
        # Validación de contraseñas
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden.")

        # Validación del límite de especialistas
        if self.request and self.request.tenant:
            client = self.request.tenant
            current_specialists_count = Specialist.objects.filter(client=client).count()
            
            if current_specialists_count >= client.specialists_limit:
                raise ValidationError({
                    'client': f"No se pueden crear más especialistas. "
                             f"El límite es de {client.specialists_limit} especialistas "
                             f"y actualmente tiene {current_specialists_count}."
                })

        return cleaned_data

    def save(self, commit=True):
        if self.request and self.request.tenant:
            client = self.request.tenant
            # Verificar una última vez antes de guardar
            current_count = Specialist.objects.filter(client=client).count()
            if current_count >= client.specialists_limit:
                raise ValidationError(
                    f"No se pueden crear más especialistas. "
                    f"Límite alcanzado: {client.specialists_limit}"
                )

        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            specialist = super().save(commit=False)
            specialist.user = user
            if self.request and self.request.tenant:
                specialist.client = self.request.tenant
            specialist.save()

        return specialist
    
        
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
    
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['session', 'is_paid', 'payment_date', 'amount', 'payment_observation']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_observation': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'session': 'Sesión',
            'is_paid': 'Está pagado',
            'payment_date': 'Fecha de pago',
            'amount': 'Monto',
            'payment_observation': 'Observación del pago'
        }