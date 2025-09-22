from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Client
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import secrets

@receiver(post_save, sender=Client)
def create_user_for_client(sender, instance, created, **kwargs):
    if created and not instance.user:
        try:
            # Generar una contraseña segura si no se proporciona una
            if not instance.initial_password:
                instance.initial_password = secrets.token_urlsafe(12)
            
            # Validar la contraseña
            validate_password(instance.initial_password)
            
            # Crear el usuario
            user = User.objects.create_user(
                username=instance.admin_email,
                email=instance.admin_email,
                password=instance.initial_password
            )
            
            # Asociar el usuario al cliente
            instance.user = user
            instance.save()
            
        except ValidationError as e:
            # Manejar errores de validación de contraseña
            print(f"Error al crear usuario: {e}")
        except Exception as e:
            # Manejar otros errores
            print(f"Error inesperado: {e}")

