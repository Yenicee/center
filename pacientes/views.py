from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy
from django.views import generic
from .models import Patient, Session, Specialist, Room, Payment
from .forms import (
    CustomUserCreationForm, PatientForm, SessionForm,
    SpecialistForm, RoomForm, ReservationFilterForm,
    PaymentForm
)
from django.http import JsonResponse
from datetime import datetime, timedelta


@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pacientes/patient/patient_list.html', {'patients': patients})

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
    
    return render(request,'pacientes/patient/patient_schedule.html', {
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
            return render(request, 'pacientes/session/session_detail.html', {
                'session': session,
                'error': 'La observación no puede estar vacía.'
            })
    return render(request, 'pacientes/session/session_detail.html', {'session': session})

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
    return render(request, 'pacientes/patient/new_patient.html',{'form': form})

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
    return render(request, 'pacientes/patient/edit_patient.html', {'form': form, 'patient': patient})

@login_required
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        patient.delete()
        return redirect('patient_list')
    return render(request,'pacientes/patient/delete_patient.html', {'patient': patient})

@login_required
def calendar_view(request):
    return render(request, 'pacientes/calendar/calendar.html')


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
    return render(request, 'pacientes/specialist/specialist_list.html', {'specialists': specialists})

@login_required
def create_specialist(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('specialist_list')
    else:
        form = SpecialistForm()
    return render(request, 'pacientes/specialist/new_specialist.html', {'form': form})

# Nuevas vistas para Room
@login_required
def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'pacientes/room/room_list.html', {'rooms': rooms})

@login_required
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'pacientes/room/new_room.html', {'form': form})

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
    return render(request, 'pacientes/room/edit_room.html', {'form': form, 'room': room})

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'pacientes/room/delete_room.html', {'room': room})


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
    return render(request, 'pacientes/session/edit_session.html', {'form': form, 'session': session})

@login_required
def reservation_list(request):
   
    today = datetime.now().date()

    thirty_days_ago = today - timedelta(days=30)
    recent_sessions = Session.objects.filter(date__gte=thirty_days_ago).order_by('date', 'time')

    reservations_by_date = {}
    for session in recent_sessions:
        date_key = session.date
        if date_key not in reservations_by_date:
            reservations_by_date[date_key] = []
        reservations_by_date[date_key].append(session)
    
    context = {
        'reservations_by_date': reservations_by_date,
    }
    return render(request, 'pacientes/reservation/reservation_list.html', context)

#nueva views agregada

@login_required
def payment_list(request):
    payments = Payment.objects.all().order_by('-session__date')
    return render(request, 'pacientes/payments/payment_list.html', {'payments': payments})

@login_required
def create_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'pacientes/payments/create_payment.html', {'form': form})

@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'pacientes/payments/edit_payment.html', 
                 {'form': form, 'payment': payment})

@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    if request.method == 'POST':
        payment.delete()
        return redirect('payment_list')
    return render(request, 'pacientes/payments/delete_payment.html', 
                 {'payment': payment})

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'pacientes/payments/payment_detail.html', 
                 {'payment': payment})