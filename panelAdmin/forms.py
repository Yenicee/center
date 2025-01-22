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
            'initial_password': forms.PasswordInput(render_value=True),
        }

    def clean_schema_name(self):
        schema_name = self.cleaned_data['schema_name']
        # Verifica si editamos un cliente existente
        if self.instance.pk:
            # Si es el mismo schema_name del cliente actual, permitirlo
            if self.instance.schema_name == schema_name:
                return schema_name
      
        if Client.objects.filter(schema_name=schema_name).exists():
            raise forms.ValidationError("Este schema name ya está en uso.")
        return schema_name

    def clean_admin_email(self):
        email = self.cleaned_data['admin_email']
        # Verificar si estamos editando un cliente existente
        if self.instance.pk:
            # Si es el mismo email del cliente actual, permitirlo
            if self.instance.user.email == email:
                return email
    
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # editamos cliente existente
        if self.instance.pk:
           
            self.fields['schema_name'].widget.attrs['readonly'] = True
            self.fields['admin_email'].widget.attrs['readonly'] = True
            self.fields['initial_password'].required = False

