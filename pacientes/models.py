from django.db import models 
from django.contrib.auth.models import User
from panelAdmin.models import Client #importe app y traje modelo 

class Specialist(models.Model):
    ROLES = [
        ('especialista', 'Especialista'),
        ('administrador', 'Administrador'),
    ]

    # Relación con el modelo User de Django
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='specialists',null=True, blank=True ) 
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='specialist_profile',
    null=True
    )
    # Campos específicos del especialista
    specialty = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    dni = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(upload_to='specialist_images/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLES, default='especialista')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.role}"
    
    
class Room(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='rooms',null=True, blank=True  )
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=100)
    specialists = models.ManyToManyField(Specialist, related_name='rooms')

    def __str__(self):
        return self.name

class Patient(models.Model):
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='patients',null=True, blank=True )
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M','Male'), ('F','Female')])
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20) 
    email = models.EmailField()
    cost_session = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    
    photo = models.ImageField(upload_to='patient_photos/', blank=True, null=True)
    marital_status = models.CharField(max_length=20)
    medical_diagnosis = models.TextField()
    attachments = models.FileField(upload_to='patient_attachments/', blank=True, null=True)
    therapy = models.CharField(max_length=100)
    education = models.CharField(max_length=100, default='No especificado')
    therapist = models.ForeignKey(Specialist, on_delete=models.SET_NULL, null=True, related_name='patients')
    
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.CharField(max_length=255, blank=True)  # Changed from TextField
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)  # Updated length
    notes = models.TextField(blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('Active', 'Active'),
        ('Discharged', 'Discharged'),
        ('Suspended', 'Suspended')
    ], blank=True,
        null=True)
    def __str__(self):
        return f'{self.name} {self.surname}'


class Session(models.Model):
    STATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Realizada', 'Realizada'),
        ('Cancelada', 'Cancelada')
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sessions',null=True, blank=True )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sessions')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='sessions')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='sessions')
    date = models.DateField()
    time = models.TimeField()
    objective = models.CharField(max_length=255)
    activity = models.TextField()
    materials = models.TextField(blank=True)
    observation = models.TextField(blank=True)
    attachment = models.FileField(upload_to='session_attachments/', blank=True, null=True)
      
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendiente',
        help_text="Estado de la sesión: 'Pendiente', 'Completada o 'Cancelada'."
    )
    
    paid_in_advance = models.BooleanField(default=False, verbose_name="Pagada por adelantado")
    
    def save(self, *args, **kwargs):
        
        # Guarda la sesión normalmente
        super().save(*args, **kwargs)

        # Si está marcada como pagada por adelantado, crear el pago
        if self.paid_in_advance:
            payment, created = Payment.objects.get_or_create(
                session=self,
                defaults={
                    'is_paid': True,
                    'payment_date': self.date,
                    'amount': self.patient.cost_session
                }
            )
        # Si cambia a realizada y no está pagada por adelantado
        elif self.status == "Realizada":
            payment, created = Payment.objects.get_or_create(
                session=self,
                defaults={
                    'is_paid': False,
                    'payment_date': self.date
                }
            )
            
    def __str__(self):
        return f"Session {self.date} - Patient: {self.patient.name} {self.patient.surname}"


class Payment(models.Model):
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments',null=True, blank=True )
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='payment')
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_observation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.amount and self.session:
            self.amount = self.session.patient.cost_session
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Payment for session {self.session.date} - Patient: {self.session.patient.name} {self.session.patient.surname}"

    class Meta:
        ordering = ['-session__date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'