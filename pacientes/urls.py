from django.urls import path
from . import views
from .forms import CustomAuthenticationForm
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Principal/Pacientes URLs
    path('', views.patient_list, name='patient_list'),
    path('patients/new/', views.create_patient, name='new_patient'),
    path('patient/<int:patient_id>/schedule/', views.patient_schedule, name='patient_schedule'),
    path('patient/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),
    path('patient/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    
    # Sesiones URLs
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/edit/', views.edit_session, name='edit_session'),

    # Especialistas URLs
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/new/', views.create_specialist, name='new_specialist'),
    
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
    
    # Autenticaciones URLs
    path('register/', views.SignUpView.as_view(), name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html', 
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('accounts/password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset.html'
        ), name='password_reset'),
    path('accounts/password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done2.html'
        ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm2.html'
        ), name='password_reset_confirm'),
    path('accounts/reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete2.html'
        ), name='password_reset_complete'),
    
    #Reservaciones URLs
    path('reservations/', views.reservation_list, name='reservation_list'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


