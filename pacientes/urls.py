from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('check_availability/', views.check_availability, name='check_availability'),
    # Principal/Pacientes URLs
    path('', views.patient_list, name='patient_list'),
    path('patients/new/', views.create_patient, name='new_patient'),
    path('patient/<int:patient_id>/schedule/', views.patient_schedule, name='patient_schedule'),
    path('patient/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),
    path('patient/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    
    # Sesiones URLs
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/edit/', views.edit_session, name='edit_session'),
    path('new-session/', views.new_session, name='new_session'),
    path('update-session-status/', views.update_session_status, name='update_session_status'),
    

    # Especialistas URLs
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/new/', views.create_specialist, name='new_specialist'),
    path('specialists/<int:specialist_id>/', views.view_specialist, name='view_specialist'),
    path('specialists/<int:specialist_id>/edit/', views.edit_specialist, name='edit_specialist'),  # ← NUEVA
    path('specialists/<int:specialist_id>/delete/', views.delete_specialist, name='delete_specialist'),
    path('check-username/', views.check_username_availability, name='check_username'),

    # Equipos (catálogo)
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/new/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/edit/', views.equipment_update, name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),

    # APIs mínimas para el modal
    path('api/equipment/', views.equipment_api_list, name='equipment_api_list'),
    path('api/equipment/create/', views.equipment_api_create, name='equipment_api_create'),
    # Salas URLs
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/new/', views.create_room, name='new_room'),
    path('rooms/<int:room_id>/edit/', views.edit_room, name='edit_room'),
    path('rooms/<int:room_id>/delete/', views.delete_room, name='delete_room'),
    
    # Calendario URLs
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/sessions/', views.get_sessions, name='get_sessions'),
    
    #Pagos URLs
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.create_payment, name='create_payment'),
    path('payments/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('toggle_payment_status/', views.toggle_payment_status, name='toggle_payment_status'),
    path('sessions/<int:session_id>/toggle-payment/', views.toggle_payment, name='toggle_payment'),
    
    #Reservaciones URLs
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('sessions/<int:session_id>/cancel-or-reschedule/', views.cancel_or_reschedule_session, name='cancel_or_reschedule_session'),
    path('sessions/<int:session_id>/complete/', views.complete_session, name='complete_session'),
    
    #Login Cliente URLs
    path('login/', views.login_view, name='login'),  
    path('logout/', views.logout_view, name='logout'),  

    #Pagos
    path('finance/', views.finance_dashboard, name='finance_dashboard'),

    #Gastos
    path('finance/expenses/', views.expense_list, name='expense_list'),
    path('finance/expenses/new/', views.expense_create, name='expense_create'),
    path('finance/expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('finance/expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('finance/expenses/<int:pk>/toggle-paid/', views.toggle_expense_paid, name='toggle_expense_paid'),
    
    #Notificaciones
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/count/', views.get_notifications_count, name='notifications_count'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/generate/', views.generate_notifications, name='generate_notifications'),  # Solo para testing

] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


