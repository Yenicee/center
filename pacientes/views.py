from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .decorators import admin_only
from django.contrib.auth.models import User


from django.views.decorators.http import require_POST
from .models import Patient, Session, Specialist, Room, Payment
from .forms import (
    PatientForm, SessionForm,
    SpecialistForm, RoomForm,
    PaymentForm
)
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib import messages


#views para patient
@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pacientes/patient/patient_list.html', {'patients': patients})

@login_required
def patient_schedule(request, patient_id):
    # 1. Obtener el paciente
    patient = get_object_or_404(Patient, id=patient_id)

    # 2. Filtrar las sesiones del paciente según su estado
    pending_sessions = Session.objects.filter(patient=patient, status="Pendiente").order_by('date', 'time')
    completed_sessions = Session.objects.filter(patient=patient, status="Realizada").order_by('-date', '-time')
    
    # 3. Otros datos relevantes
    specialists = Specialist.objects.all()
    rooms = Room.objects.all()

    # 4. Manejar el formulario para agregar nuevas sesiones
    if request.method == 'POST':
        form = SessionForm(request.POST, request.FILES)
        if form.is_valid():
            session = form.save(commit=False)
            session.patient = patient
            session.save()
            return redirect('patient_schedule', patient_id=patient.id)
    else:
        form = SessionForm(initial={'patient': patient})
    
    # 5. Renderizar la plantilla con el contexto adecuado
    return render(request, 'pacientes/patient/patient_schedule.html', {
        'patient': patient,
        'pending_sessions': pending_sessions,  # Sesiones pendientes
        'completed_sessions': completed_sessions,  # Sesiones realizadas
        'form': form,  # Formulario para agregar sesión
        'specialists': specialists,
        'rooms': rooms,
    })

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
@admin_only
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        patient.delete()
        return redirect('patient_list')
    return render(request,'pacientes/patient/delete_patient.html', {'patient': patient})


#views para manejo de session
@login_required
def calendar_view(request):
    return render(request, 'pacientes/calendar/calendar.html')

@login_required
def new_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST, request.FILES)
        
        if form.is_valid():
         
            session = form.save()
              
            # Procesar las sesiones adicionales
            additional_dates = request.POST.getlist('additional_dates[]')
            additional_times = request.POST.getlist('additional_times[]')
            
            for date, time in zip(additional_dates, additional_times):
                # Crear una nueva sesión manteniendo el estado de pago por adelantado
                new_session = Session(
                    patient=session.patient,
                    specialist=session.specialist,
                    room=session.room,
                    date=date,
                    time=time,
                    objective='',
                    activity='',
                    materials='',
                    observation='',
                    status='Pendiente',
                    paid_in_advance=session.paid_in_advance
                )
                new_session.save()
            
            return redirect('reservation_list')
    
    else:
        form = SessionForm()
    
    return render(request, 'pacientes/session/new_session.html', {'form': form})

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

@login_required
def get_sessions(request):
    try:
        sessions = Session.objects.filter(status__in=["Pendiente", "Cancelada"])
        events = []
        
        for session in sessions:
            start_datetime = datetime.combine(session.date, session.time)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Configura el color basado en el estado de la sesión
            if session.status == "Pendiente":
                color = '#0d6efd'  # Azul para "Pendiente"
            elif session.status == "Cancelada":
                color = '#dc3545'  # Rojo para "Cancelada"

            event = {
                'id': str(session.id),
                'title': f"{session.patient.name} - {session.objective}",
                'start': start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'end': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'extendedProps': {
                    'specialist': session.specialist.user.get_full_name() or session.specialist.user.username,
                    'room': session.room.name if session.room else 'Sin sala',
                    'session_id': session.id,
                    'patient': f"{session.patient.name} {session.patient.surname}",
                    'activity': session.activity,
                    'objective': session.objective,
                    'eventType': 'session'
                },
                'backgroundColor': color,
                'borderColor': color,
                'display': 'block'
            }
            events.append(event)
        
        return JsonResponse(events, safe=False)
        
    except Exception as e:
        print(f"Error en get_sessions: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.method == 'POST':
        form = SessionForm(request.POST, request.FILES, instance=session)
        if form.is_valid():
            form.save()
            return redirect('reservation_list')
        else:
            print("Errores de validación:", form.errors)  # Para depuración
    else:
        form = SessionForm(instance=session)
    return render(request, 'pacientes/session/edit_session.html', {'form': form, 'session': session})

@require_POST
@login_required
def update_session_status(request):
    session_id = request.POST.get('session_id')
    new_status = request.POST.get('new_status')
    
    try:
        session = Session.objects.get(id=session_id)
        session.status = new_status
        session.save()
        return JsonResponse({'success': True})
    except Session.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'La sesión no existe.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Nuevas vistas para Specialist
@login_required
def specialist_list(request):
    specialists = Specialist.objects.all()
    return render(request, 'pacientes/specialist/specialist_list.html', {'specialists': specialists})

@admin_only
@login_required
def create_specialist(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST, request.FILES)
        if form.is_valid():
            # Si el formulario es válido, guarda los datos
            form.save()
            messages.success(request, 'Especialista creado exitosamente.')
            return redirect('specialist_list')
        else:
            # Manejo de errores: Agrega un mensaje y registra los errores en la consola
            messages.error(request, f'Error en el formulario: {form.errors}')
            print(form.errors)  # Útil para debug en consola
    else:
        form = SpecialistForm()
    
    return render(request, 'pacientes/specialist/new_specialist.html', {'form': form})

def check_username_availability(request):
    username = request.GET.get('username', None)
    if username and User.objects.filter(username=username).exists():
        return JsonResponse({'available': False, 'message': 'El nombre de usuario ya está en uso.'})
    return JsonResponse({'available': True})

@login_required
def view_specialist(request, specialist_id):
    specialist = get_object_or_404(Specialist, id=specialist_id)
    return render(request, 'pacientes/specialist/view_specialist.html', {
        'specialist': specialist
    })

@login_required
@admin_only
def delete_specialist(request, specialist_id):
    specialist = get_object_or_404(Specialist, id=specialist_id)
    user = specialist.user  # Obtener el usuario relacionado
    if request.method == 'POST':
        user.delete()  # Esto elimina tanto el User como el Specialist
        messages.success(request, 'Especialista eliminado exitosamente.')
        return redirect('specialist_list')
    return render(request, 'pacientes/specialist/delete_specialist.html', {'specialist': specialist})
        
#views encargadas de room
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

#views encargado de la parte de reservation_list
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

#views encargada de payment
@login_required
def payment_list(request):
    # Filtrar pagos solo de sesiones Pendientes o Realizadas
    payments = Payment.objects.filter(session__status__in=['Pendiente', 'Realizada']).order_by('-session__date')
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

@require_POST
def toggle_payment_status(request):
    payment_id = request.POST.get('payment_id')
    payment = get_object_or_404(Payment, id=payment_id)
    payment.is_paid = not payment.is_paid
    payment.save()
    return JsonResponse({'success': True, 'is_paid': payment.is_paid})

