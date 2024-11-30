# validators.py
from django.core.exceptions import ValidationError

def validate_password_strength(value):
    if len(value) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
    if value.isdigit():
        raise ValidationError("La contraseña no puede ser completamente numérica.")
