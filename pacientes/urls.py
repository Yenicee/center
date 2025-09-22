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
    path('specialists/<int:specialist_id>/delete/', views.delete_specialist, name='delete_specialist'),
    path('check-username/', views.check_username_availability, name='check_username'),

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
    
    #Reservaciones URLs
    path('reservations/', views.reservation_list, name='reservation_list'),
    
    #Login Cliente URLs
    path('login/', views.login_view, name='login'),  
    path('logout/', views.logout_view, name='logout'),  

] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


