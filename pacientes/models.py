from django.db import models 
from django.contrib.auth.models import User
from panelAdmin.models import Client #importe app y traje modelo 
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils import timezone
      

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
    COMP_FIXED = 'fixed'
    COMP_PERCENT = 'percent'
    COMP_CHOICES = [(COMP_FIXED, 'Fijo mensual'), (COMP_PERCENT, '% por sesión')]

    comp_type = models.CharField(max_length=10, choices=COMP_CHOICES, default=COMP_FIXED)
    comp_value = models.DecimalField(max_digits=7, decimal_places=2, default=0)  
    
    def save(self, *args, **kwargs):
       
        if not self.pk and self.client:
            current_count = self.client.specialists.count()
            if current_count >= self.client.specialists_limit:
                raise ValidationError(
                    f'El cliente "{self.client.name}" ha alcanzado su límite de '
                    f'{self.client.specialists_limit} especialistas. '
                    f'Actualmente tiene {current_count} especialistas registrados.'
                )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.role}"
    
class Room(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='rooms',null=True, blank=True  )
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=100)
    specialists = models.ManyToManyField(Specialist, related_name='rooms')
    
    equipment = models.ManyToManyField('Equipment', related_name='rooms', blank=True)   

    def __str__(self):
        return self.name
    
class Equipment(models.Model):
    name = models.CharField(max_length=80, unique=True)
    code = models.SlugField(max_length=80, unique=True, blank=True, null=True)
    def __str__(self): return self.name

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
    # ── Estados del flujo
    STATUS_PENDING_UNPLANNED = 'Pendiente sin planificar'
    STATUS_PENDING_PLANNED   = 'Pendiente planificada'
    STATUS_COMPLETED         = 'Realizada'
    STATUS_CANCELED          = 'Cancelada'

    STATUS_CHOICES = [
        (STATUS_PENDING_UNPLANNED, 'Pendiente sin planificar'),
        (STATUS_PENDING_PLANNED,   'Pendiente planificada'),
        (STATUS_COMPLETED,         'Realizada'),
        (STATUS_CANCELED,          'Cancelada'),
    ]

    # ── FKs y campos base (los que ya tenías)
    client     = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    patient    = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sessions')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='sessions')
    room       = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='sessions')

    date = models.DateField()
    time = models.TimeField()

    # ── Plan de la sesión (ahora opcional para permitir “sin planificar”)
    objective   = models.CharField(max_length=255, blank=True)
    activity    = models.TextField(blank=True)
    materials   = models.TextField(blank=True)

    # ── Resultado/post-sesión
    observation = models.TextField(blank=True)
    attachment  = models.FileField(upload_to='session_attachments/', blank=True, null=True)

    # ── Estado principal (ampliamos longitud)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_UNPLANNED,
        help_text="Flujo: Pendiente sin planificar → Pendiente planificada → Realizada | Cancelada."
    )

    # ── Gestión de cancelación/reprogramación/cierre
    canceled_reason = models.CharField(max_length=50, blank=True)        # p.ej. Paciente / Terapeuta / Clínica / Reprogramada / Inasistencia
    canceled_detail = models.TextField(blank=True)
    rescheduled_to  = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='rescheduled_from')
    completed_at    = models.DateTimeField(null=True, blank=True)

    # ── Pago
    paid_in_advance = models.BooleanField(default=False, verbose_name="Pagada por adelantado")

    # ── Helpers
    def is_planned(self) -> bool:
        """Consideramos plan si hay objetivo o actividad con contenido."""
        return bool((self.objective or '').strip() or (self.activity or '').strip())

    def clean_status_by_content(self):
        """Si está pendiente, normaliza el estado según tenga plan o no."""
        if self.status in (self.STATUS_PENDING_UNPLANNED, self.STATUS_PENDING_PLANNED):
            self.status = self.STATUS_PENDING_PLANNED if self.is_planned() else self.STATUS_PENDING_UNPLANNED

    def save(self, *args, **kwargs):
        # Normaliza estado 'pendiente...' antes de guardar
        self.clean_status_by_content()
        super().save(*args, **kwargs)

        # Lógica de Payment mínima (mantiene tu comportamiento)
        from .models import Payment  # evitar ciclos en import en algunos setups
        if self.paid_in_advance:
            Payment.objects.get_or_create(
                session=self,
                defaults={
                    'is_paid': True,
                    'payment_date': self.date,
                    'amount': self.patient.cost_session
                }
            )
        elif self.status == self.STATUS_COMPLETED:
            # Si recién se completa, crea el registro de pago (impago por defecto)
            Payment.objects.get_or_create(
                session=self,
                defaults={
                    'is_paid': False,
                    'payment_date': self.date
                }
            )

    def __str__(self):
        return f"{self.date} {self.time} · {self.patient} · {self.get_status_display()}"

    @property
    def is_paid_status(self):
        p = getattr(self, 'payment', None)
        return bool(p and p.is_paid)
    
class Payment(models.Model):
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments',null=True, blank=True )
    session = models.OneToOneField('Session', on_delete=models.CASCADE, related_name='payment')
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, blank=True, default='')
    payment_observation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference = models.CharField(max_length=120, blank=True, default='')

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

class PaymentLog(models.Model):
    ACTIONS = [
        ('mark_paid', 'Marcar pagado'),
        ('mark_unpaid', 'Marcar no pagado'),
    ]
    session   = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='payment_logs')
    action    = models.CharField(max_length=20, choices=ACTIONS)
    amount    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    method    = models.CharField(max_length=30, blank=True)           # Efectivo, Tarjeta, Transferencia, etc.
    reference = models.CharField(max_length=100, blank=True)          # N° operación, último 4, etc.
    by_user   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-at']

    def __str__(self):
        return f"{self.get_action_display()} · {self.session.id} · {self.at:%Y-%m-%d %H:%M}"

#Expense
# ---- Gastos simples (MVP) ----
class Expense(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    name = models.CharField(max_length=120)                     # Luz, Alquiler, Internet, etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_fixed = models.BooleanField(default=False)               # fijo vs variable
    is_recurring = models.BooleanField(default=False)           # recurrente (manual en MVP)
    due_date = models.DateField(null=True, blank=True)         # fecha de pago/vence
    paid = models.BooleanField(default=False)
    paid_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f"{self.name} · {self.amount}"
    
    
#--Nuevo modelo agregado para notificaciones 
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('session_reminder', 'Recordatorio de sesión'),
        ('payment_overdue', 'Pago atrasado'),
        ('session_tomorrow', 'Sesión mañana'),
        ('expense_due', 'Gasto por vencer'),
        ('expense_overdue', 'Gasto vencido'),
    ]
    
    # Relaciones
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True
    )
    
    # Relaciones opcionales según el tipo de notificación
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True
    )
    
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True
    )
    
    expense = models.ForeignKey(
        Expense, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True
    )
    
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True
    )
    
    # Campos de la notificación
    notification_type = models.CharField(
        max_length=30, 
        choices=NOTIFICATION_TYPES
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Estado
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Para evitar duplicados
    reference_id = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Identificador único para evitar duplicados (ej: session_123_reminder)"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [
            models.Index(fields=['client', 'is_read', '-created_at']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
    def mark_as_read(self):
        """Marca la notificación como leída"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_session_reminder(cls, session):
        """Crea notificación de recordatorio de sesión (24h antes)"""
        
        # Verificar que la sesión sea mañana
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        if session.date != tomorrow:
            return None
        
        # Evitar duplicados
        reference = f"session_{session.id}_reminder"
        if cls.objects.filter(reference_id=reference).exists():
            return None
        
        return cls.objects.create(
            client=session.client,
            session=session,
            patient=session.patient,
            notification_type='session_tomorrow',
            title=f"Sesión mañana: {session.patient.name}",
            message=f"Recordatorio: Sesión programada para mañana {session.date.strftime('%d/%m/%Y')} a las {session.time.strftime('%H:%M')} con {session.specialist.user.get_full_name()}",
            reference_id=reference
        )
    
    @classmethod
    def create_payment_overdue(cls, payment):
        """Crea notificación de pago atrasado"""
        from django.utils import timezone
        
        # Solo si no está pagado y la fecha ya pasó
        if payment.is_paid or payment.session.date >= timezone.now().date():
            return None
        
        # Evitar duplicados
        reference = f"payment_{payment.id}_overdue"
        if cls.objects.filter(reference_id=reference).exists():
            return None
        
        days_overdue = (timezone.now().date() - payment.session.date).days
        
        return cls.objects.create(
            client=payment.client,
            payment=payment,
            session=payment.session,
            patient=payment.session.patient,
            notification_type='payment_overdue',
            title=f"Pago atrasado: {payment.session.patient.name}",
            message=f"Pago pendiente desde hace {days_overdue} días. Sesión del {payment.session.date.strftime('%d/%m/%Y')}. Monto: ${payment.amount}",
            reference_id=reference
        )
    
    @classmethod
    def create_expense_due(cls, expense):
        """Crea notificación de gasto próximo a vencer (3 días antes)"""    
        if not expense.due_date or expense.paid:
            return None
        
        # Verificar que vence en 3 días
        days_until_due = (expense.due_date - timezone.now().date()).days
        if days_until_due != 3:
            return None
        
        # Evitar duplicados
        reference = f"expense_{expense.id}_due"
        if cls.objects.filter(reference_id=reference).exists():
            return None
        
        return cls.objects.create(
            client=expense.client,
            expense=expense,
            notification_type='expense_due',
            title=f"Gasto por vencer: {expense.name}",
            message=f"El gasto '{expense.name}' vence en 3 días ({expense.due_date.strftime('%d/%m/%Y')}). Monto: ${expense.amount}",
            reference_id=reference
        )
    
    @classmethod
    def create_expense_overdue(cls, expense):
        """Crea notificación de gasto vencido"""  
        if not expense.due_date or expense.paid or expense.due_date >= timezone.now().date():
            return None
        
        # Evitar duplicados
        reference = f"expense_{expense.id}_overdue"
        if cls.objects.filter(reference_id=reference).exists():
            return None
        
        days_overdue = (timezone.now().date() - expense.due_date).days
        
        return cls.objects.create(
            client=expense.client,
            expense=expense,
            notification_type='expense_overdue',
            title=f"Gasto vencido: {expense.name}",
            message=f"El gasto '{expense.name}' está vencido desde hace {days_overdue} días. Fecha de vencimiento: {expense.due_date.strftime('%d/%m/%Y')}. Monto: ${expense.amount}",
            reference_id=reference
        )
    