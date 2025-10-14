from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Patient, Session, Specialist, Room, Payment, Equipment
from panelAdmin.models import Client
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise ValidationError('Correo electrónico o contraseña incorrectos')
            if not user.is_active:
                raise ValidationError('Esta cuenta está desactivada')
            cleaned_data['user'] = user
        return cleaned_data


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
       labels = {'specialty': 'Especialidad', 'phone': 'Teléfono', 'dni': 'DNI', 'profile_image': 'Imagen de Perfil', 'role': 'Rol'}
       widgets = {'role': forms.Select(choices=Specialist.ROLES)}

   def __init__(self, *args, **kwargs):
       self.request = kwargs.pop('request', None)
       super().__init__(*args, **kwargs)
       
       if self.request and self.request.tenant:
           client = self.request.tenant
           self.fields['client'].queryset = Client.objects.filter(id=client.id)
           self.fields['client'].initial = self.fields['client'].widget.attrs['readonly'] = client
           self.fields['client'].disabled = True

           current_count = Specialist.objects.filter(client=client).count()
           if current_count >= client.specialists_limit:
               self.fields['client'].help_text = f"Límite: {client.specialists_limit}, Actuales: {current_count}"

   def clean(self):
       cleaned_data = super().clean()
       
       if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
           raise ValidationError("Las contraseñas no coinciden.")

       if self.request and self.request.tenant:
           client = self.request.tenant
           current_count = Specialist.objects.filter(client=client).count()
           
           if current_count >= client.specialists_limit:
               raise ValidationError({'client': f"Límite alcanzado: {current_count}/{client.specialists_limit}"})

       return cleaned_data

   def save(self, commit=True):
       if self.request and self.request.tenant:
           client = self.request.tenant
           if Specialist.objects.filter(client=client).count() >= client.specialists_limit:
               raise ValidationError(f"Límite de especialistas alcanzado: {client.specialists_limit}")

       user = User(**{k: self.cleaned_data[k] for k in ['username', 'email', 'first_name', 'last_name']})
       user.set_password(self.cleaned_data['password'])
       user.save() if commit else None

       specialist = super().save(commit=False)
       specialist.user = user
       specialist.client = self.request.tenant if self.request and self.request.tenant else None
       specialist.save() if commit else None

       return specialist

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'code']

class RoomForm(forms.ModelForm):
    equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkgrid'})
    )
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'location', 'specialists', 'equipment']
        widgets = {
            'specialists': forms.CheckboxSelectMultiple(attrs={'class': 'checkgrid'}),
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