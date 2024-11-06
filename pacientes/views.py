from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy
from django.views import generic
from .models import Patient, Session, Specialist, Room
from .forms import (
    CustomUserCreationForm, PatientForm, SessionForm,
    SpecialistForm, RoomForm, ReservationFilterForm
)
from django.http import JsonResponse
from datetime import datetime, timedelta


@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pacientes/patient_list.html', {'patients': patients})

@login_required
def patient_schedule(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    sessions = Session.objects.filter(patient=patient).order_by('date', 'time')
    specialists = Specialist.objects.all()
    rooms = Room.objects.all()
    
    if request.method == 'POST':
        form = SessionForm(request.POST, request.FILES)
        if form.is_valid():
            session = form.save(commit=False)
            session.patient = patient
            session.save()
            return redirect('patient_schedule', patient_id=patient.id)
    else:
        form = SessionForm(initial={'patient': patient})
    
    return render(request, 'pacientes/patient_schedule.html', {
        'patient': patient,
        'sessions': sessions,
        'form': form,
        'specialists': specialists,
        'rooms': rooms
    })

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.method == 'POST':
        observation = request.POST.get('observation')
        if observation:
            session.observation = observation
            session.save()
            return redirect('patient_schedule', patient_id=session.patient.id)
        else:
            return render(request, 'pacientes/session_detail.html', {
                'session': session,
                'error': 'La observación no puede estar vacía.'
            })
    return render(request, 'pacientes/session_detail.html', {'session': session})

class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

@login_required
def create_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('patient_list') 
    else:
        form = PatientForm()
    return render(request, 'pacientes/new_patient.html', {'form': form})

#se agrego esto para los templates de delete_patient y edit_patient
@login_required
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'pacientes/edit_patient.html', {'form': form, 'patient': patient})

@login_required
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        patient.delete()
        return redirect('patient_list')
    return render(request, 'pacientes/delete_patient.html', {'patient': patient})

@login_required
def calendar_view(request):
    return render(request, 'pacientes/calendar.html')


@login_required
def get_sessions(request):
    try:
        # Obtener todas las sesiones reservadas
        sessions = Session.objects.filter(is_reserved=True)
        print(f"Número de sesiones encontradas: {sessions.count()}")

        # Obtener todas las reservas
        reservations = Session.objects.filter(is_reserved=False)
        print(f"Número de reservas encontradas: {reservations.count()}")

        events = []

        for session in sessions:
            # Usar reserved_date y reserved_time para sesiones reservadas
            start_datetime = datetime.combine(
                session.reserved_date or session.date,
                session.reserved_time or session.time
            )
            end_datetime = start_datetime + timedelta(hours=1)

            event = {
                'id': str(session.id),
                'title': f"{session.patient.name} - {session.new_activity or session.objective}",
                'start': start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'end': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'extendedProps': {
                    'specialist': session.specialist.name,
                    'room': session.room.name if session.room else 'Sin sala',
                    'session_id': session.id,
                    'patient': f"{session.patient.name} {session.patient.surname}",
                    'activity': session.new_activity or session.activity,
                    'objective': session.objective,
                    'eventType': 'session'
                },
                'backgroundColor': '#0d6efd',
                'borderColor': '#0d6efd',
                'display': 'block'
            }
            events.append(event)

        for reservation in reservations:
            start_datetime = datetime.combine(
                reservation.reserved_date or reservation.date,
                reservation.reserved_time or reservation.time
            )
            end_datetime = start_datetime + timedelta(hours=1)
            event = {
                'id': str(reservation.id),
                'title': f"Reserva - {reservation.patient.name}",
                'start': start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'end': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'extendedProps': {
                    'room': reservation.room.name if reservation.room else 'Sin sala',
                    'session_id': reservation.id,
                    'patient': f"{reservation.patient.name} {reservation.patient.surname}",
                    'eventType': 'reservation'
                },
                'backgroundColor': '#dc3545',
                'borderColor': '#dc3545',
                'display': 'block'
            }
            events.append(event)

        return JsonResponse(events, safe=False)
    except Exception as e:
        print(f"Error en get_sessions: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

# Nuevas vistas para Specialist
@login_required
def specialist_list(request):
    specialists = Specialist.objects.all()
    return render(request, 'pacientes/specialist_list.html', {'specialists': specialists})

@login_required
def create_specialist(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('specialist_list')
    else:
        form = SpecialistForm()
    return render(request, 'pacientes/new_specialist.html', {'form': form})

# Nuevas vistas para Room
@login_required
def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'pacientes/room_list.html', {'rooms': rooms})

@login_required
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'pacientes/new_room.html', {'form': form})

#se agrego un editar sala(sirve para los templates edit_room, delete_room)
@login_required
def edit_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'pacientes/edit_room.html', {'form': form, 'room': room})

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'pacientes/delete_room.html', {'room': room})


@login_required
def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.method == 'POST':
        form = SessionForm(request.POST, request.FILES, instance=session)
        if form.is_valid():
            form.save()
            return redirect('session_detail', session_id=session.id)
    else:
        form = SessionForm(instance=session)
    return render(request, 'pacientes/edit_session.html', {'form': form, 'session': session})


#vista para las reservaciones
@login_required
def reservation_list(request):
    filter_form = ReservationFilterForm(request.GET or None)
    reserved_sessions = Session.objects.filter(is_reserved=True)
  
    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        
        if start_date:
            reserved_sessions = reserved_sessions.filter(reserved_date__gte=start_date)
        if end_date:
            reserved_sessions = reserved_sessions.filter(reserved_date__lte=end_date)
    
    elif not request.GET:
        today = datetime.now().date()
        reserved_sessions = reserved_sessions.filter(
            reserved_date__gte=today,
            reserved_date__lte=today + timedelta(days=30)
        )
  
    reserved_sessions = reserved_sessions.order_by('reserved_date', 'reserved_time')
    
    reservations_by_date = {}
    for session in reserved_sessions:
        date_key = session.reserved_date
        if date_key not in reservations_by_date:
            reservations_by_date[date_key] = []
        reservations_by_date[date_key].append(session)
    
    context = {
        'filter_form': filter_form,
        'reservations_by_date': reservations_by_date,
    }
    return render(request, 'pacientes/reservation_list.html', context)