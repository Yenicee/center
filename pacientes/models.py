from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Specialist(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} {self.surname}"

class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=100)
    specialists = models.ManyToManyField(Specialist, related_name='rooms')

    def __str__(self):
        return self.name

class Patient(models.Model):
    
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M','Male'), ('F','Female')])
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20) 
    email = models.EmailField()
    
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

    def __str__(self):
        return f"Session {self.date} - Patient: {self.patient.name} {self.patient.surname}"

