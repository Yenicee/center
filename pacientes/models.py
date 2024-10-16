from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M','Male'), ('F','Female')])
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=9)
    email = models.EmailField()
    #agregar mas propiedades al modelo
    medical_history = models.TextField(blank=True, null=True) #historial medico
    allergies = models.TextField(blank=True, null=True) #alergias
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=9)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f'{self.name} {self.surname}'
    
class Activity(models.Model):
    patient = models.ForeignKey(Patient,on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    
    def __str__(self):
        return f'Actividad de {self.patient.name} o {self.date}'

class Session(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    result = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Session iniciada {self.date} de la actividad {self.activity}'
    
