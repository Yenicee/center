from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=255)  # Nombre del consultorio
    admin_name = models.CharField(max_length=255)  
    admin_email = models.EmailField()  
    database_name = models.CharField(max_length=255, unique=True)  
    specialists_limit = models.PositiveIntegerField(default=4)  
    start_date = models.DateField(auto_now_add=True) 
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('morose', 'Moroso'),
        ('suspended', 'Suspendido'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')  

    def __str__(self):
        return self.name
    
