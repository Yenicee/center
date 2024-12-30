from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        exclude = ['user']  # Excluye 'user' del formulario
        labels = {
            'name': 'Consultorio',
            'admin_name': 'Nombre del administrador',
            'admin_email': 'Correo del administrador',
            'database_name': 'Nombre de la base de datos',
            'specialists_limit': 'Límite de especialistas',
            'start_date': 'Fecha de inicio',
            'monthly_payment': 'Pago mensual',
            'status': 'Estado',
            'initial_password': 'Contraseña'
        }
            
      