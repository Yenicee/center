from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Patient, Session, Specialist, Room, Payment, Equipment, Expense
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
            'attachment', 'paid_in_advance'   # <- quitamos 'status'
        ]
        labels = {
            'date': 'Fecha',
            'time': 'Hora',
            'patient': 'Paciente',
            'specialist': 'Especialista',
            'room': 'Sala',
            'objective': 'Objetivo (opcional)',
            'activity': 'Actividad (opcional)',
            'materials': 'Materiales (opcional)',
            'observation': 'Observación (post-sesión)',
            'attachment': 'Archivo Adjunto',
            'paid_in_advance': 'Pagada',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'objective': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Puedes completarlo después'}),
            'activity': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Puedes completarlo después'}),
            'materials': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Opcional'}),
            'observation': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Se completa al cerrar'}),
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

        # Conflicto especialista
        if Session.objects.filter(specialist=specialist, date=date, time=time).exclude(pk=self.instance.pk if self.instance else None).exists():
            self.add_error('specialist', 'El especialista ya tiene una sesión en este horario.')

        # Conflicto sala
        if Session.objects.filter(room=room, date=date, time=time).exclude(pk=self.instance.pk if self.instance else None).exists():
            self.add_error('room', 'La sala ya está reservada en este horario.')

        return cleaned_data


class SpecialistForm(forms.ModelForm):
    # Campos de User para creación
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    email = forms.EmailField(required=True, label='Correo Electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    password = forms.CharField(widget=forms.PasswordInput(), label='Contraseña', required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label='Confirmar Contraseña', required=True)

    class Meta:
        model = Specialist
        fields = [
            'client', 'specialty', 'phone', 'dni', 'profile_image', 'role',
            'comp_type', 'comp_value',   # pago del especialista
        ]
        labels = {
            'specialty': 'Especialidad',
            'phone': 'Teléfono',
            'dni': 'DNI',
            'profile_image': 'Imagen de Perfil',
            'role': 'Rol',
            'comp_type': 'Tipo de pago',
            'comp_value': 'Valor',
        }
        widgets = {
            'role': forms.Select(choices=Specialist.ROLES),
            'comp_type': forms.Select(choices=Specialist.COMP_CHOICES),
            'comp_value': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Si usas tenant en request
        if self.request and getattr(self.request, "tenant", None):
            client = self.request.tenant
            self.fields['client'].queryset = Client.objects.filter(id=client.id)
            self.fields['client'].initial = client
            self.fields['client'].disabled = True

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password') or ''
        cpw = cleaned.get('confirm_password') or ''
        if pwd != cpw:
            raise ValidationError({'confirm_password': 'Las contraseñas no coinciden.'})
        if len(pwd) < 6:
            raise ValidationError({'password': 'La contraseña debe tener al menos 6 caracteres.'})
        return cleaned

    def save(self, commit=True):
        specialist = super().save(commit=False)
        # Tenant
        if self.request and getattr(self.request, "tenant", None):
            specialist.client = self.request.tenant

        # Crear user
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            specialist.user = user
            specialist.save()
        else:
            specialist.user = user

        return specialist


# ---------- EDITAR ----------
class SpecialistEditForm(forms.ModelForm):
    # Campos de User precargados
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    email = forms.EmailField(required=True, label='Correo Electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    # Contraseña opcional
    password = forms.CharField(widget=forms.PasswordInput(), label='Contraseña (opcional)', required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label='Confirmar Contraseña', required=False)

    class Meta:
        model = Specialist
        fields = [
            'client', 'specialty', 'phone', 'dni', 'profile_image', 'role',
            'comp_type', 'comp_value',
        ]
        labels = {
            'specialty': 'Especialidad',
            'phone': 'Teléfono',
            'dni': 'DNI',
            'profile_image': 'Imagen de Perfil',
            'role': 'Rol',
            'comp_type': 'Tipo de pago',
            'comp_value': 'Valor',
        }
        widgets = {
            'role': forms.Select(choices=Specialist.ROLES),
            'comp_type': forms.Select(choices=Specialist.COMP_CHOICES),
            'comp_value': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Tenant
        if self.request and getattr(self.request, "tenant", None):
            client = self.request.tenant
            self.fields['client'].queryset = Client.objects.filter(id=client.id)
            self.fields['client'].initial = client
            self.fields['client'].disabled = True

        # Precargar user
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and instance.user_id:
            u = instance.user
            self.fields['username'].initial = u.username
            self.fields['email'].initial = u.email
            self.fields['first_name'].initial = u.first_name
            self.fields['last_name'].initial = u.last_name

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password') or ''
        cpw = cleaned.get('confirm_password') or ''
        if pwd or cpw:
            if pwd != cpw:
                raise ValidationError({'confirm_password': 'Las contraseñas no coinciden.'})
            if len(pwd) < 6:
                raise ValidationError({'password': 'La contraseña debe tener al menos 6 caracteres.'})
        return cleaned

    def save(self, commit=True):
        specialist = super().save(commit=False)
        # Tenant
        if self.request and getattr(self.request, "tenant", None):
            specialist.client = self.request.tenant

        # Actualizar user existente (o crear si faltara)
        user = specialist.user if specialist.user_id else User()
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)

        if commit:
            user.save()
            specialist.user = user
            specialist.save()
        else:
            specialist.user = user

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

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name','amount','is_fixed','is_recurring','due_date','paid','paid_at','notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type':'date'}),
            'paid_at': forms.DateInput(attrs={'type':'date'}),
            'notes': forms.Textarea(attrs={'rows':3}),
        }
        labels = {
            'name': 'Nombre del ítem',
            'amount': 'Monto (S/.)',
            'is_fixed': '¿Fijo?',
            'is_recurring': '¿Recurrente?',
            'due_date': 'Fecha de pago/venc.',
            'paid': '¿Pagado?',
            'paid_at': 'Fecha de pago',
            'notes': 'Notas',
        }