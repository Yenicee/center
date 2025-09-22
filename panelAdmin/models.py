from django.db import models
from django.contrib.auth.models import User
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    admin_name = models.CharField(max_length=255)
    admin_email = models.EmailField(null=True, blank=True)
    specialists_limit = models.PositiveIntegerField(default=4)
    start_date = models.DateField(auto_now_add=True)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('morose', 'Moroso'),
        ('suspended', 'Suspendido'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    initial_password = models.CharField(max_length=255, blank=True, null=True)

    # Campos requeridos por TenantMixin
    auto_create_schema = True
    
    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
