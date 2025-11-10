from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from .models import Patient, Session, Specialist, Room, Payment, Equipment, Expense, Notification
from .forms import (
    PatientForm, SessionForm,
    SpecialistForm, RoomForm,
    PaymentForm, EmailLoginForm, EquipmentForm, ExpenseForm, SpecialistEditForm
)
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib.auth import login, logout
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.utils import timezone
from django.db.models import Sum, Q
from calendar import monthrange
import json

#views para login
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('patient_list')
        
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Obtener el tenant del usuario
            try:
                client = user.client
                if client.status == 'suspended':
                    logout(request)
                    messages.error(request, 'Esta cuenta está suspendida. Por favor contacte al administrador.')
                    return redirect('login')
            except:
                pass
                
            next_url = request.GET.get('next', 'patient_list')
            return redirect(next_url)
    else:
        form = EmailLoginForm()
    
    return render(request, 'pacientes/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

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
        error_messages = []  # Lista para acumular errores

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la sesión principal
                    session = form.save()

                    # Manejar las sesiones adicionales
                    additional_dates = request.POST.getlist('additional_dates[]')
                    additional_times = request.POST.getlist('additional_times[]')
                    additional_paid_in_advance = request.POST.getlist('additional_paid_in_advance[]')

                    for index, (date, time) in enumerate(zip(additional_dates, additional_times)):
                        # Verificar si el checkbox está marcado para esta sesión
                        is_paid_in_advance = str(index + 1) in additional_paid_in_advance

                        additional_session = Session(
                            patient=session.patient,
                            specialist=session.specialist,
                            room=session.room,
                            date=date,
                            time=time,
                            objective='No especificado',
                            activity='No especificado',
                            materials='',
                            observation='',
                            status='Pendiente',
                            paid_in_advance=is_paid_in_advance  # Asignar el valor del checkbox
                        )

                        try:
                            additional_session.full_clean()
                            additional_session.save()
                        except ValidationError as e:
                            error_messages.extend(
                                [f"{field}: {error}" for field, errors in e.message_dict.items() for error in errors]
                            )

                if error_messages:
                    for msg in error_messages:
                        messages.error(request, msg)
                    return render(request, 'pacientes/session/new_session.html', {'form': form})

                messages.success(request, 'Sesión creada correctamente, incluyendo sesiones adicionales.')
                return redirect('reservation_list')

            except ValidationError as e:
                error_messages.extend(
                    [f"{field}: {error}" for field, errors in e.message_dict.items() for error in errors]
                )

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = SessionForm()

    return render(request, 'pacientes/session/new_session.html', {'form': form})


@require_POST
@login_required
def cancel_or_reschedule_session(request, session_id):
    """
    mode = 'cancel' | 'reschedule'
    cancel: necesita canceled_reason (y optional canceled_detail)
    reschedule: date, time, room_id, copy_plan (bool), canceled_reason='Reprogramada'
    """
    session = get_object_or_404(Session, pk=session_id)

    mode = request.POST.get('mode')
    if mode not in ('cancel', 'reschedule'):
        return JsonResponse({'success': False, 'error': 'Modo inválido'}, status=400)

    if mode == 'cancel':
        reason = (request.POST.get('canceled_reason') or '').strip()
        detail = (request.POST.get('canceled_detail') or '').strip()
        if not reason:
            return JsonResponse({'success': False, 'error': 'Motivo requerido'}, status=400)

        session.status = Session.STATUS_CANCELED
        session.canceled_reason = reason
        session.canceled_detail = detail
        session.save()
        return JsonResponse({'success': True, 'status': session.status})

    # reschedule
    new_date = request.POST.get('date')
    new_time = request.POST.get('time')
    room_id  = request.POST.get('room_id')
    copy_plan = request.POST.get('copy_plan') in ('1', 'true', 'True', True)

    if not (new_date and new_time and room_id):
        return JsonResponse({'success': False, 'error': 'Fecha, hora y sala son requeridos'}, status=400)

    # Validaciones básicas de conflicto
    room = get_object_or_404(Room, pk=room_id)
    if Session.objects.filter(specialist=session.specialist, date=new_date, time=new_time).exists():
        return JsonResponse({'success': False, 'error': 'Conflicto con el especialista en la nueva fecha/hora'}, status=409)
    if Session.objects.filter(room=room, date=new_date, time=new_time).exists():
        return JsonResponse({'success': False, 'error': 'Conflicto con la sala en la nueva fecha/hora'}, status=409)

    # Crear nueva sesión
    new_session = Session.objects.create(
        client=session.client,
        patient=session.patient,
        specialist=session.specialist,
        room=room,
        date=new_date,
        time=new_time,
        objective=session.objective if copy_plan else '',
        activity=session.activity if copy_plan else '',
        materials=session.materials if copy_plan else '',
        observation='',
        status=Session.STATUS_PENDING_PLANNED if copy_plan else Session.STATUS_PENDING_UNPLANNED,
        paid_in_advance=session.paid_in_advance
    )

    # Marcar la actual como cancelada por reprogramación
    session.status = Session.STATUS_CANCELED
    session.canceled_reason = 'Reprogramada'
    session.rescheduled_to = new_session
    session.save()

    return JsonResponse({'success': True, 'new_session_id': new_session.id, 'old_status': session.status})

@require_POST
@login_required
def complete_session(request, session_id):
    """
    Cierra la sesión marcándola como 'Realizada'.
    Requiere 'observation' en el POST.
    """
    session = get_object_or_404(Session, pk=session_id)

    notes = (request.POST.get('observation') or '').strip()
    if not notes:
        return JsonResponse({'success': False, 'error': 'La observación es obligatoria para cerrar.'}, status=400)

    # Sólo permite cerrar si está pendiente
    if session.status not in (Session.STATUS_PENDING_UNPLANNED, Session.STATUS_PENDING_PLANNED):
        return JsonResponse({'success': False, 'error': 'Solo se pueden cerrar sesiones pendientes.'}, status=400)

    session.observation = notes
    session.status = Session.STATUS_COMPLETED
    session.completed_at = timezone.now()
    session.save()

    return JsonResponse({'success': True, 'status': session.status})

@login_required
def check_availability(request):
    # Obtener los parámetros de la solicitud
    dates = request.GET.getlist('dates[]')  # Lista de fechas
    times = request.GET.getlist('times[]')  # Lista de horas
    specialist_id = request.GET.get('specialist')
    room_id = request.GET.get('room')

    # Verificar que todos los parámetros requeridos estén presentes
    if not (dates and times and specialist_id and room_id):
        return JsonResponse({'error': 'Faltan parámetros obligatorios'}, status=400)

    # Inicializar listas para acumular conflictos específicos
    specialist_conflicts = []
    room_conflicts = []

    # Iterar sobre las combinaciones de fechas y horas
    for date, time in zip(dates, times):
        # Convertir la fecha y hora recibidas en objetos datetime
        session_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        session_end = session_start + timedelta(minutes=59)  # Sesión dura 1 hora

        # Verificar conflictos con especialista
        specialist_conflict = Session.objects.filter(
            specialist_id=specialist_id,
            date=date,
            time__gte=(session_start - timedelta(minutes=59)).time(),  # Inicio - 1 hora
            time__lt=session_end.time()  # Fin
        ).exists()

        if specialist_conflict:
            specialist_conflicts.append({'date': date, 'time': time})

        # Verificar conflictos con sala
        room_conflict = Session.objects.filter(
            room_id=room_id,
            date=date,
            time__gte=(session_start - timedelta(minutes=59)).time(),  # Inicio - 1 hora
            time__lt=session_end.time()  # Fin
        ).exists()

        if room_conflict:
            room_conflicts.append({'date': date, 'time': time})

    # Respuesta JSON con los resultados
    return JsonResponse({
        'specialist_conflicts': specialist_conflicts,
        'room_conflicts': room_conflicts,
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

@login_required
def get_sessions(request):
    try:  
        # ESTADOS CORRECTOS DE LA BD
        sessions = Session.objects.filter(
            status__in=["Pendiente planificada", "Realizada", "Cancelada", "Abierta"]
        )
        
        print(f"🔍 Total de sesiones en DB: {Session.objects.count()}")
        print(f"📊 Sesiones filtradas: {sessions.count()}")
        
        events = []
        
        for session in sessions:
            start_datetime = datetime.combine(session.date, session.time)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Mapeo de colores por estado
            color_map = {
                'Pendiente planificada': '#0d6efd',  
                'Realizada': '#28a745',              
                'Cancelada': '#dc3545',               
                'Abierta': '#ffc107',                
            }
            color = color_map.get(session.status, '#6c757d')  

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
                    'status': session.status, 
                    'eventType': 'session'
                },
                'backgroundColor': color,
                'borderColor': color,
                'display': 'block'
            }
            events.append(event)
        
        print(f"✅ Eventos enviados al calendario: {len(events)}")
        return JsonResponse(events, safe=False)
        
    except Exception as e:
        print(f"❌ Error en get_sessions: {str(e)}")
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

@login_required
def create_specialist(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            try:
                specialist = form.save()
                messages.success(request, 'Especialista creado exitosamente.')
                return redirect('specialist_list')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Usted esta pasando el limite para crear mas especialistas de su plan de pago.')
    else:
        form = SpecialistForm(request=request)
    
    return render(request, 'pacientes/specialist/new_specialist.html', {'form': form})

@login_required
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
def edit_specialist(request, specialist_id):
    specialist = get_object_or_404(Specialist, id=specialist_id)

    if request.method == 'POST':
        form = SpecialistEditForm(request.POST, request.FILES, instance=specialist, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialista actualizado exitosamente.')
            return redirect('specialist_list')
        else:
            messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = SpecialistEditForm(instance=specialist, request=request)

    return render(request, 'pacientes/specialist/edit_specialist.html', {
        'form': form,
        'specialist': specialist,
    })

@login_required
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
    rooms = (
        Room.objects
            .prefetch_related(Prefetch('equipment',
                                       queryset=Equipment.objects.only('id', 'name')))
            .all()
    )
    # usa el path real de tu archivo
    return render(request, "pacientes/room/room_list.html", {"rooms": rooms})

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

# --- Gestión de Equipos (página aparte, CRUD simple) ---
def equipment_list(request):
    items = Equipment.objects.order_by('name')
    return render(request, 'pacientes/equipment/list.html', {'items': items})

def equipment_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipo creado.")
            return redirect('equipment_list')
    else:
        form = EquipmentForm()
    return render(request, 'pacientes/equipment/form.html', {'form': form, 'title': 'Nuevo Equipo'})

def equipment_update(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=eq)
        if form.is_valid():
             form.save()
             messages.success(request, "Equipo actualizado.")
             return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=eq)
    return render(request, 'pacientes/equipment/form.html', {'form': form, 'title': 'Editar Equipo'})

def equipment_delete(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        eq.delete()
        messages.success(request, "Equipo eliminado.")
        return redirect('equipment_list')
    return render(request, 'pacientes/equipment/confirm_delete.html', {'item': eq})

# --- APIs para el modal (+) en el formulario de Sala ---
def equipment_api_list(request):
    data = list(Equipment.objects.order_by('name').values('id', 'name'))
    return JsonResponse({'results': data})

@require_POST
def equipment_api_create(request):
    name = (request.POST.get('name') or '').strip()
    code = (request.POST.get('code') or '').strip() or None
    if not name:
        return JsonResponse({'ok': False, 'error': 'Nombre requerido'}, status=400)
    eq, created = Equipment.objects.get_or_create(name=name, defaults={'code': code})
    return JsonResponse({'ok': True, 'id': eq.id, 'name': eq.name})

#views encargado de la parte de reservation_list
@login_required
def reservation_list(request):
   
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    recent_sessions = (
        Session.objects
        .filter(date__gte=thirty_days_ago)
        .select_related('payment', 'specialist__user', 'room', 'patient')  # ← importante
        .order_by('date', 'time')
    )   
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

@login_required
def toggle_payment_status(request):
    payment_id = request.POST.get('payment_id')
    payment = get_object_or_404(Payment, id=payment_id)
    payment.is_paid = not payment.is_paid
    payment.save()
    return JsonResponse({'success': True, 'is_paid': payment.is_paid})

@login_required
@require_POST
def toggle_payment(request, session_id):
    """
    Marca/desmarca pago de una sesión.
    Si viene 'mark' == 'paid', actualiza/crea Payment con is_paid=True y guarda amount/method/reference/payment_date.
    Si 'mark' == 'unpaid', pone is_paid=False (mantiene amount y payment_date si quieres rastrear el intento previo).
    Registra PaymentLog.
    """
    from .models import Session, Payment, PaymentLog

    session = get_object_or_404(Session, pk=session_id)

    mark = (request.POST.get('mark') or '').strip()  # 'paid' | 'unpaid'
    if mark not in ('paid', 'unpaid'):
        return JsonResponse({'success': False, 'error': 'Parámetro inválido.'}, status=400)

    # Asegura Payment
    payment, _created = Payment.objects.get_or_create(
        session=session,
        defaults={
            'client': session.client,
            'amount': session.patient.cost_session,
            'payment_date': session.date,
            'is_paid': False,
        }
    )

    if mark == 'paid':
        # Datos del modal
        amount_str = request.POST.get('amount') or ''
        method     = (request.POST.get('method') or '').strip()
        reference  = (request.POST.get('reference') or '').strip()
        date_str   = (request.POST.get('payment_date') or '').strip()

        try:
            amount = Decimal(amount_str) if amount_str else payment.amount or session.patient.cost_session
        except Exception:
            return JsonResponse({'success': False, 'error': 'Monto inválido.'}, status=400)

        # Fecha de pago
        try:
            pay_date = timezone.datetime.fromisoformat(date_str).date() if date_str else timezone.now().date()
        except Exception:
            pay_date = timezone.now().date()

        # Actualiza Payment
        payment.is_paid = True
        payment.amount = amount
        payment.payment_date = pay_date
        if reference:
            payment.payment_observation = (payment.payment_observation or '') + f"\nRef: {reference}"
        payment.save()

        # Log
        PaymentLog.objects.create(
            session=session,
            action='mark_paid',
            amount=amount,
            method=method,
            reference=reference,
            by_user=request.user,
        )

        return JsonResponse({'success': True, 'paid': True})

    # mark == 'unpaid'
    payment.is_paid = False
    payment.save()

    PaymentLog.objects.create(
        session=session,
        action='mark_unpaid',
        amount=payment.amount,
        method='',
        reference='',
        by_user=request.user,
    )

    return JsonResponse({'success': True, 'paid': False})


#Pagos
@login_required
def finance_dashboard(request):
    # Mes y año por querystring (?year=2025&month=10) o actuales
    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
    except Exception:
        year, month = timezone.now().year, timezone.now().month

    first_day = timezone.datetime(year, month, 1).date()
    last_day = timezone.datetime(year, month, monthrange(year, month)[1]).date()

    # --- INGRESOS LIQUIDADOS (basado en Payment cobrado en el rango) ---
    paid_qs = Payment.objects.filter(
        is_paid=True,
        payment_date__range=(first_day, last_day)
    )
    ingresos_liquidados = paid_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # --- INGRESOS PROYECTADOS (pendientes) ---
    # 1) Payments existentes no pagados del mes (por fecha de la sesión)
    projected_from_payments = Payment.objects.filter(
        is_paid=False,
        session__date__range=(first_day, last_day)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # 2) Sesiones del mes sin Payment (usamos patient.cost_session)
    sessions_without_payment = Session.objects.filter(
        date__range=(first_day, last_day)
    ).filter(payment__isnull=True).exclude(status=Session.STATUS_CANCELED)

    projected_from_sessions = sessions_without_payment.aggregate(
        total=Sum('patient__cost_session')
    )['total'] or Decimal('0')

    ingresos_proyectados = projected_from_payments + projected_from_sessions

    # --- EGRESOS (simples) ---
    # Por defecto mostramos egreso del mes (devengado por due_date)
    expenses_month = Expense.objects.filter(
        Q(due_date__range=(first_day, last_day)) | (Q(due_date__isnull=True) & Q(created_at__date__range=(first_day, last_day)))
    )
    egresos_total = expenses_month.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # --- NÓMINA (basada en cobrado) ---
    # Fijos (monto mensual)
    fixed_sum = Specialist.objects.filter(comp_type='fixed').aggregate(
        total=Sum('comp_value')
    )['total'] or Decimal('0')

    # Percent: sumamos por sesiones COBRADAS del mes
    percent_specialists = Specialist.objects.filter(comp_type='percent')
    # Map id -> percent Decimal
    perc_map = {s.id: (s.comp_value or Decimal('0')) for s in percent_specialists}

    paid_sessions = Session.objects.filter(
        payment__is_paid=True,
        payment__payment_date__range=(first_day, last_day),
        specialist__in=percent_specialists
    ).select_related('payment','specialist')

    percent_sum = Decimal('0')
    for s in paid_sessions:
        pct = perc_map.get(s.specialist_id, Decimal('0')) / Decimal('100')
        percent_sum += (s.payment.amount or Decimal('0')) * pct

    nomina_total = fixed_sum + percent_sum

    balance = ingresos_liquidados - (egresos_total + nomina_total)

    # Próximos pagos (egresos no pagados)
    proximos_pagos = Expense.objects.filter(paid=False).order_by('due_date')[:10]

    context = {
        'year': year, 'month': month,
        'first_day': first_day, 'last_day': last_day,
        'ingresos_proyectados': ingresos_proyectados,
        'ingresos_liquidados': ingresos_liquidados,
        'egresos_total': egresos_total,
        'nomina_total': nomina_total,
        'balance': balance,
        'proximos_pagos': proximos_pagos,
    }
    return render(request, 'pacientes/finance/dashboard.html', context)

@login_required
def expense_list(request):
    qs = Expense.objects.all().order_by('-due_date','-created_at')
    return render(request, 'pacientes/finance/expense_list.html', {'items': qs})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            # Si marcas pagado y no pones fecha, setea hoy
            if exp.paid and not exp.paid_at:
                exp.paid_at = timezone.now().date()
            exp.save()
            messages.success(request, 'Gasto creado.')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'pacientes/finance/expense_form.html', {'form': form, 'title': 'Nuevo gasto'})

@login_required
def expense_edit(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST': 
        form = ExpenseForm(request.POST, instance=exp)
        
        if not form.is_valid():
            print(f"Errores del formulario: {form.errors}")
        
        if form.is_valid():
            exp = form.save(commit=False)
            
            if exp.paid and not exp.paid_at:
                exp.paid_at = timezone.now().date()
            
            exp.save()
            
            messages.success(request, 'Gasto actualizado.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=exp)
    
    return render(request, 'pacientes/finance/expense_form.html', {'form': form, 'title': 'Editar gasto'})


@login_required
@require_POST
def toggle_expense_paid(request, pk):
    """
    Toggle del estado 'paid' de un gasto desde la lista.
    """
    try:
        expense = get_object_or_404(Expense, pk=pk)
        
        # Obtener el nuevo estado del body JSON
        data = json.loads(request.body)
        new_paid_status = data.get('paid', False)
        
        # Actualizar
        expense.paid = new_paid_status
        
        # Si se marca como pagado y no tiene fecha, asignar hoy
        if expense.paid and not expense.paid_at:
            expense.paid_at = timezone.now().date()
        
        expense.save()
        
        return JsonResponse({
            'success': True,
            'paid': expense.paid,
            'message': 'Gasto actualizado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def expense_delete(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        exp.delete()
        messages.success(request, 'Gasto eliminado.')
        return redirect('expense_list')
    return render(request, 'pacientes/finance/expense_delete.html', {'item': exp})


#Notificaciones
@login_required
def get_notifications(request):
    """
    Obtiene las notificaciones no leídas del tenant actual.
    Retorna JSON para consumir desde JavaScript.
    """
    notifications = Notification.objects.filter(
        is_read=False
    ).select_related(
        'session', 
        'patient', 
        'payment', 
        'expense'
    ).order_by('-created_at')[:20] 
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'url': _get_notification_url(notif),
        })
    
    return JsonResponse({
        'success': True,
        'notifications': data,
        'count': len(data)
    })


@login_required
def get_notifications_count(request):
    """
    Retorna solo el contador de notificaciones no leídas.
    Útil para actualizar el badge sin cargar todas las notificaciones.
    """
    count = Notification.objects.filter(is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Marca una notificación específica como leída.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Notificación no encontrada'
        }, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """
    Marca todas las notificaciones como leídas.
    """
    updated = Notification.objects.filter(is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    return JsonResponse({
        'success': True,
        'updated': updated
    })


@login_required
def generate_notifications(request):
    """
    Vista manual para generar notificaciones.
    util para testing y casos especiales en producción.
    
    Acceso: /pacientes/notifications/generate/
    """ 
    created_count = 0
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    three_days = today + timedelta(days=3)
    
    # 1. SESIONES DE MAÑANA (recordatorio 24h antes)
    tomorrow_sessions = Session.objects.filter(
        date=tomorrow,
        status__in=[Session.STATUS_PENDING_PLANNED, Session.STATUS_PENDING_UNPLANNED]
    )
    
    for session in tomorrow_sessions:
        notif = Notification.create_session_reminder(session)
        if notif:
            created_count += 1
    
    # 2. PAGOS ATRASADOS
    overdue_payments = Payment.objects.filter(
        is_paid=False,
        session__date__lt=today
    ).select_related('session', 'session__patient')
    
    for payment in overdue_payments:
        notif = Notification.create_payment_overdue(payment)
        if notif:
            created_count += 1
    
    # 3. GASTOS POR VENCER (3 días antes)
    upcoming_expenses = Expense.objects.filter(
        paid=False,
        due_date=three_days
    )
    
    for expense in upcoming_expenses:
        notif = Notification.create_expense_due(expense)
        if notif:
            created_count += 1
    
    # 4. GASTOS VENCIDOS
    overdue_expenses = Expense.objects.filter(
        paid=False,
        due_date__lt=today
    )
    
    for expense in overdue_expenses:
        notif = Notification.create_expense_overdue(expense)
        if notif:
            created_count += 1
    
    return JsonResponse({
        'success': True,
        'created': created_count,
        'message': f'Se generaron {created_count} nuevas notificaciones'
    })


def _get_notification_url(notification):
    """
    Helper: Retorna la URL apropiada según el tipo de notificación.
    """
    if notification.session:
        return f'/pacientes/sessions/{notification.session.id}/'
    elif notification.payment:
        return f'/pacientes/payments/{notification.payment.id}/'
    elif notification.expense:
        return f'/pacientes/expenses/{notification.expense.id}/edit/'
    elif notification.patient:
        return f'/pacientes/patients/{notification.patient.id}/'
    return '/pacientes/dashboard/'
