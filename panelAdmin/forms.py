from django import forms
from .models import Client
from django.contrib.auth.models import User
            
class ClientForm(forms.ModelForm):
    schema_name = forms.CharField(
        max_length=100, 
        label='Nombre del Schema',
        help_text='Este será el identificador único del cliente en el sistema'
    )

    class Meta:
        model = Client
        fields = [
            'schema_name', 
            'name', 
            'admin_name', 
            'admin_email', 
            'specialists_limit', 
            'monthly_payment', 
            'status',
            'initial_password'
        ]
        labels = {
            'name': 'Consultorio',
            'admin_name': 'Nombre del administrador',
            'admin_email': 'Correo del administrador',
            'specialists_limit': 'Límite de especialistas',
            'monthly_payment': 'Pago mensual',
            'status': 'Estado',
            'initial_password': 'Contraseña'
        }
        widgets = {
            'initial_password': forms.PasswordInput(),
        }

    def clean_schema_name(self):
        schema_name = self.cleaned_data['schema_name']
        if Client.objects.filter(schema_name=schema_name).exists():
            raise forms.ValidationError("Este schema name ya está en uso.")
        return schema_name

    def clean_admin_email(self):
        email = self.cleaned_data['admin_email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email