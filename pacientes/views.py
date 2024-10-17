from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .models import Patient, Activity, Session
from .forms import CustomUserCreationForm, PatientForm,ActivityForm
from django.http import JsonResponse

@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pacientes/patient_list.html',{'patients':patients})

#vista para mostrar el cronograma de actividades de un paciente
@login_required
def patient_schedule(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    activities = Activity.objects.filter(patient=patient).order_by('date')
    
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.patient = patient
            activity.save()
            return redirect('patient_schedule', patient_id=patient.id)
    else:
        form = ActivityForm()
    
    return render(request, 'pacientes/patient_schedule.html', {
        'patient': patient,
        'activities': activities,
        'form': form
    })

@login_required
def add_session_result(request, activity_id):
    activity = get_object_or_404(Activity, id= activity_id)
    if request.method == 'POST':
        result = request.POST.get('result')
        if result:
            Session.objects.create(activity=activity,result=result)
            
            return redirect('patient_schedule',patient_id= activity.patient.id)
        else:
            return render(request,'paciente/add_session_result.html', 
                        {  'activity':activity, 
                          'error': 'el resultado no puede estar vacio.'})
    return render(request, 'pacientes/add_session_result.html', {'activity': activity})
    

class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

def create_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('patient_list') 
    else:
        form = PatientForm()
    return render(request, 'pacientes/new_patient.html', {'form': form})

def calendar_view(request):
    return render(request, 'pacientes/calendar.html')

def get_activities(request):
    activities = Activity.objects.all()
    events = []
    for activity in activities:
        events.append({
            'title': f"{activity.patient.name} - {activity.description}",
            'start': activity.date.strftime('%Y-%m-%d'),
            'url': f"/patient/{activity.patient.id}/schedule/"
        })
    return JsonResponse(events, safe=False)