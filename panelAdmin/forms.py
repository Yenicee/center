from django import forms
from .models import Client
from django.contrib.auth.models import User
            
class ClientForm(forms.ModelForm):
    schema_name = forms.CharField(
        max_length=100, 
        label='Nombre del Schema',
        help_text='⚠️ Solo letras minúsculas, números y guiones. Sin espacios ni caracteres especiales. Ejemplo: clinica-centro-salud'
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
        
        # Convertir a minúsculas y reemplazar espacios por guiones
        schema_name = schema_name.lower().strip()
        schema_name = schema_name.replace(' ', '-')
        
        # Validar que solo contenga letras, números y guiones
        import re
        if not re.match(r'^[a-z0-9-]+$', schema_name):
            raise forms.ValidationError(
                "El nombre del schema solo puede contener letras minúsculas, números y guiones. "
                "No se permiten espacios, mayúsculas ni caracteres especiales."
            )
        
        # No puede empezar ni terminar con guion
        if schema_name.startswith('-') or schema_name.endswith('-'):
            raise forms.ValidationError("El nombre del schema no puede empezar ni terminar con un guión.")
        
        # No puede tener guiones consecutivos
        if '--' in schema_name:
            raise forms.ValidationError("El nombre del schema no puede tener guiones consecutivos.")
        
        # Verifica si editamos un cliente existente
        if self.instance.pk:
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
            if self.instance.user and self.instance.user.email == email:
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
        
        # Agregar placeholder para mejor UX
        self.fields['schema_name'].widget.attrs.update({
            'placeholder': 'Ejemplo: clinica-norte, centro-medico-sur',
            'style': 'text-transform: lowercase;'
        })